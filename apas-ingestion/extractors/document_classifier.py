"""Auto-discovery and classification of government documents.

For PDFs in FILE_TO_OM_MAP, returns existing registry metadata (fast path).
For unknown PDFs, auto-extracts metadata from the first page using:
  1. PyMuPDF (page 0 text extraction — fast, free)
  2. Regex (om_number, date from header)
  3. Filename heuristics (doc_type)
  4. LLM / GPT-4o-mini (nature, applies_to, agent_scope)

Discovered metadata is cached in cache/discovered_documents.json for
human review and override.
"""

import hashlib
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

import pymupdf

from config.settings import OPENROUTER_API_KEY, EXTRACTION_MODEL, EXTRACTION_CACHE_DIR
from config.document_registry import FILE_TO_OM_MAP, OM_REGISTRY, get_om_by_id

logger = logging.getLogger(__name__)

DISCOVERED_CACHE_PATH = EXTRACTION_CACHE_DIR / "discovered_documents.json"


# --- First page extraction ---

def _extract_first_page_text(pdf_path: Path) -> str:
    """Extract text from page 0 of a PDF using PyMuPDF. Fast and free."""
    try:
        doc = pymupdf.open(str(pdf_path))
        if len(doc) == 0:
            return ""
        text = doc[0].get_text()
        # Try page 1 too if page 0 is very short
        if len(text.strip()) < 100 and len(doc) > 1:
            text += "\n" + doc[1].get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        logger.warning(f"Failed to extract first page from {pdf_path.name}: {e}")
        return ""


# --- Regex extraction ---

# OM number patterns: "No. 24(35)/PF-II/2012", "O.M. No. 01(01)/PFC-II/2025", etc.
OM_NUMBER_PATTERNS = [
    re.compile(r"(?:No\.?\s*|O\.?\s*M\.?\s*(?:No\.?\s*)?)\s*([A-Z0-9\-\(\)]+/[A-Z\-]+/\d{4})", re.IGNORECASE),
    re.compile(r"(?:No\.?\s*)\s*([A-Z0-9\-]+/\d+/\d{4}[A-Z\-\s&]*)", re.IGNORECASE),
    re.compile(r"(O-\d+/\d+/\d{4}[A-Z\-\s&]*)", re.IGNORECASE),
]

# Date patterns: "dated 05.08.2016", "dtd 31.10.2025", "dt. 06.06.2025"
DATE_PATTERNS = [
    re.compile(r"(?:dated?|dtd\.?)\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", re.IGNORECASE),
    re.compile(r"(?:dated?|dtd\.?)\s*(\d{2})(\d{2})(\d{4})", re.IGNORECASE),
]


def _regex_extract_om_number(text: str) -> str:
    """Try to extract OM reference number from text using regex."""
    for pattern in OM_NUMBER_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip().rstrip(",.")
    return ""


def _regex_extract_date(text: str) -> str:
    """Try to extract document date from text, return ISO format (YYYY-MM-DD)."""
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            day, month, year = match.group(1), match.group(2), match.group(3)
            try:
                dt = datetime(int(year), int(month), int(day))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return ""


# --- Filename heuristics ---

def _infer_doc_type(filename: str) -> str:
    """Infer document type from filename keywords."""
    name_lower = filename.lower()
    if "guideline" in name_lower:
        return "guidelines"
    if "annexure" in name_lower or "annex" in name_lower:
        return "annexure"
    if "gfr" in name_lower or "general financial" in name_lower:
        return "gfr"
    if "dfpr" in name_lower or "delegation" in name_lower or "financial powers" in name_lower:
        return "dfpr"
    if "finance commission" in name_lower or "fc_report" in name_lower:
        return "fc_report"
    if "niti" in name_lower:
        return "niti"
    if "budget" in name_lower or "expenditure budget" in name_lower or "outcome" in name_lower:
        return "budget"
    if "economic survey" in name_lower:
        return "economic_survey"
    if "fiscal" in name_lower:
        return "fiscal_policy"
    if "tax" in name_lower:
        return "tax_reform"
    if "memorandum" in name_lower or "memo" in name_lower:
        return "explanatory_memo"
    return "om"


# --- LLM classification ---

CLASSIFIER_SYSTEM_PROMPT = """You are a government document analyst for the Indian Department of Expenditure.

Given the first page text of a government document and its filename, classify it by extracting:

1. "om_number": The Office Memorandum reference number (e.g., "24(35)/PF-II/2012", "01(01)/PFC-II/2025"). Return "" if not found or not an OM.
2. "date": Document date in YYYY-MM-DD format. Return "" if unclear.
3. "nature": A 2-4 word subject label describing what this document is about. Examples: "Expenditure Control", "Compliance Enforcement", "Performance-Linked", "Structural Rationalisation", "Continuation Compliance", "Procedural Reform", "Financial Rules", "Budget Circular", "Scheme Evaluation".
4. "applies_to": Array of applicable categories from ONLY these values: ["new_scheme", "continuation", "project"]. Include all that apply based on the document content.
5. "agent_scope": Array of applicable agent scopes from ONLY these values: ["compliance", "fiscal", "sector"]. This determines which specialist agent retrieves this document:
   - "compliance" = rules about appraisal process, approvals, IPA, formats, checklists, mandatory procedures
   - "fiscal" = cost thresholds, Centre-State ratios, outlay calculations, budget provisions, financial limits
   - "sector" = NITI rationalisation, OOMF performance, evaluation, scheme restructuring, sector assessment
6. "agent_scope_confidence": "high" if the scope is clearly evident from the text, "low" if uncertain.

Return a single JSON object. Do NOT return an array."""


def _llm_classify(first_page_text: str, filename: str) -> dict:
    """Use LLM to classify document metadata."""
    if not OPENROUTER_API_KEY:
        logger.warning("No OPENROUTER_API_KEY — using regex/filename heuristics only")
        return {}

    from openai import OpenAI

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    user_message = (
        f"Filename: {filename}\n\n"
        f"First page text:\n{first_page_text[:3000]}"
    )

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=EXTRACTION_MODEL,
                messages=[
                    {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=500,
            )

            raw = response.choices[0].message.content.strip()

            # Strip markdown fences if present
            if raw.startswith("```"):
                lines = raw.split("\n")
                json_lines = [l for l in lines if not l.strip().startswith("```")]
                raw = "\n".join(json_lines)

            result = json.loads(raw)
            if isinstance(result, dict):
                return result

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"LLM classification attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)

    return {}


# --- OM ID generation ---

def _generate_om_id(om_number: str, existing_ids: set) -> str:
    """Generate a deterministic OM ID for an auto-discovered document."""
    # Check if this om_number matches an existing OM in the registry
    for om in OM_REGISTRY:
        if om["om_number"] == om_number:
            return om["id"]

    # Generate new auto-ID
    counter = 1
    while f"OM-AUTO-{counter}" in existing_ids:
        counter += 1
    return f"OM-AUTO-{counter}"


# --- Discovery cache ---

def _load_discovered_cache() -> dict:
    """Load the discovered documents cache."""
    if DISCOVERED_CACHE_PATH.exists():
        try:
            return json.loads(DISCOVERED_CACHE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Discovered documents cache corrupted, starting fresh")
    return {}


def _save_discovered_cache(cache: dict):
    """Save the discovered documents cache."""
    EXTRACTION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DISCOVERED_CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# --- Main entry point ---

def classify_document(pdf_path: Path) -> dict:
    """Classify a PDF document, returning metadata for tagging.

    For registered PDFs (in FILE_TO_OM_MAP), returns registry metadata.
    For unknown PDFs, auto-discovers metadata and caches the result.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Dict with: om_id, om_number, date, nature, applies_to (comma-joined),
        agent_scope (comma-joined), doc_type, source (registry/auto-discovered).
    """
    filename = pdf_path.name

    # Fast path: registered document
    if filename in FILE_TO_OM_MAP:
        file_info = FILE_TO_OM_MAP[filename]
        om = get_om_by_id(file_info["om_id"])
        if om:
            return {
                "om_id": om["id"],
                "om_number": om["om_number"],
                "date": om["date"],
                "nature": om["nature"],
                "applies_to": ",".join(om["applies_to"]),
                "agent_scope": ",".join(om["agent_scope"]),
                "doc_type": file_info["doc_type"],
                "source": "registry",
            }

    # Check discovery cache (with human_reviewed flag)
    discovered_cache = _load_discovered_cache()
    if filename in discovered_cache:
        cached = discovered_cache[filename]
        logger.info(f"Using cached classification for {filename}")
        return cached

    # Auto-discover: extract first page
    logger.info(f"Auto-discovering metadata for: {filename}")
    first_page = _extract_first_page_text(pdf_path)

    # Layer 1: Regex extraction
    om_number = _regex_extract_om_number(first_page)
    date = _regex_extract_date(first_page)

    # Layer 2: Filename heuristic
    doc_type = _infer_doc_type(filename)

    # Layer 3: LLM classification
    llm_result = _llm_classify(first_page, filename)

    # Merge: regex takes priority for om_number/date, LLM fills the rest
    if not om_number and llm_result.get("om_number"):
        om_number = llm_result["om_number"]
    if not date and llm_result.get("date"):
        date = llm_result["date"]

    nature = llm_result.get("nature", "Unknown")
    applies_to = llm_result.get("applies_to", ["new_scheme", "continuation", "project"])
    agent_scope = llm_result.get("agent_scope", ["compliance", "fiscal", "sector"])
    confidence = llm_result.get("agent_scope_confidence", "low")

    # Safety: low confidence → default to all scopes (fail-open)
    if confidence == "low":
        agent_scope = ["compliance", "fiscal", "sector"]
        logger.warning(f"Low confidence scope for {filename}, defaulting to all scopes")

    # Ensure lists
    if isinstance(applies_to, str):
        applies_to = [applies_to]
    if isinstance(agent_scope, str):
        agent_scope = [agent_scope]

    # Generate OM ID
    all_existing_ids = {om["id"] for om in OM_REGISTRY}
    all_existing_ids.update(
        v.get("om_id", "") for v in discovered_cache.values()
    )
    om_id = _generate_om_id(om_number, all_existing_ids)

    # Build metadata
    metadata = {
        "om_id": om_id,
        "om_number": om_number or "unknown",
        "date": date or "unknown",
        "nature": nature,
        "applies_to": ",".join(applies_to),
        "agent_scope": ",".join(agent_scope),
        "doc_type": doc_type,
        "source": "auto-discovered",
        "human_reviewed": False,
        "discovered_at": datetime.now().isoformat(),
    }

    # Save to discovery cache
    discovered_cache[filename] = metadata
    _save_discovered_cache(discovered_cache)

    logger.info(
        f"Auto-classified {filename}: om_id={om_id}, nature={nature}, "
        f"scope={agent_scope}, confidence={confidence}"
    )
    return metadata
