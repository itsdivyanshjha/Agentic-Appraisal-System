"""LLM-assisted structured rule extraction from document chunks.

Uses GPT-4o-mini via OpenRouter to extract structured rules
(clause_ref, rule_statement, direction, ministry_must_show)
from tagged PDF chunks. Replaces hand-crafted key_rules.
"""

import hashlib
import json
import logging
import time
from pathlib import Path

from openai import OpenAI

from config.settings import OPENROUTER_API_KEY, EXTRACTION_MODEL, EXTRACTION_CACHE_DIR

logger = logging.getLogger(__name__)

# Initialize OpenAI client with OpenRouter base URL
_client = None


def _get_client() -> OpenAI:
    """Get or initialize the OpenRouter client (singleton)."""
    global _client
    if _client is None:
        if not OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Add it to .env for LLM extraction."
            )
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
    return _client


# --- Caching ---

def _cache_key(chunk_text: str) -> str:
    """Generate a cache key from chunk text."""
    return hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    """Load the extraction cache from disk."""
    cache_path = EXTRACTION_CACHE_DIR / "extraction_cache.json"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Cache file corrupted, starting fresh")
    return {}


def _save_cache(cache: dict):
    """Save the extraction cache to disk."""
    EXTRACTION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = EXTRACTION_CACHE_DIR / "extraction_cache.json"
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


# --- Prompt ---

SYSTEM_PROMPT = """You are a government policy analyst specializing in Indian Department of Expenditure (DoE) Office Memoranda.

Your task: Given a chunk of text from a government OM document, extract ALL distinct rules, directives, or requirements contained in it.

For each rule, produce a JSON object with exactly these fields:
- "clause_ref": A short semantic label for the clause (e.g., "4(i)", "8-thresholds", "risk-high", "sunset", "centre-state"). Use the actual clause/para number if visible, or a descriptive hyphenated label if the chunk covers a thematic rule.
- "rule_statement": A compressed, unambiguous paraphrase of the rule (max 200 chars). Do NOT copy verbose prose — distill the core directive.
- "direction": The normative instruction in 2-6 words (e.g., "Prior clearance required", "Fresh appraisal mandatory", "Financial discipline").
- "ministry_must_show": What the ministry must demonstrate or submit to comply (max 120 chars).

Return a JSON array. If the chunk is purely administrative (letterhead, date, address, signatures) or contains no actionable rules, return an empty array [].

IMPORTANT:
- Extract EVERY distinct rule. A single chunk may contain 1-5 rules.
- Tables with thresholds/bands should produce one rule per row.
- Do NOT invent rules not present in the text.
- Keep rule_statement as a paraphrase, not a verbatim copy."""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """OM context: OM 24(35)/PF-II/2012 dated 2016-08-05, Nature: Expenditure Control

Chunk text:
4. General Principles
(i) No new Centrally Sponsored Scheme (CSS) or Central Sector (CS) Scheme shall be initiated without obtaining in-principle approval of Department of Expenditure in advance.
(ii) The Budget provisions for any scheme shall be consistent with the approved scheme architecture and financial parameters."""
    },
    {
        "role": "assistant",
        "content": json.dumps([
            {
                "clause_ref": "4(i)",
                "rule_statement": "No new CSS or CS scheme without prior in-principle approval from DoE",
                "direction": "Prior clearance required",
                "ministry_must_show": "Attach DoE in-principle approval reference"
            },
            {
                "clause_ref": "4(ii)",
                "rule_statement": "Budget provisions must match approved scheme architecture and financial parameters",
                "direction": "No deviation from approvals",
                "ministry_must_show": "Outlay consistent with approved scheme design"
            }
        ], indent=2)
    },
    {
        "role": "user",
        "content": """OM context: OM 01(01)/PFC-II/2025 dated 2025-10-31, Nature: Performance-Linked

Chunk text:
Annexure B - Risk Classification Framework
Achievement below 60% of targets: High Risk — scheme flagged for detailed review
Achievement 60-90%: Medium Risk — needs corrective action plan
Achievement above 90%: Good — eligible for scaling up"""
    },
    {
        "role": "assistant",
        "content": json.dumps([
            {
                "clause_ref": "risk-high",
                "rule_statement": "Achievement below 60% of targets flagged as High Risk requiring detailed review",
                "direction": "Automatic risk classification",
                "ministry_must_show": "Justification for underperformance and remedial plan"
            },
            {
                "clause_ref": "risk-medium",
                "rule_statement": "Achievement 60-90% flagged as Medium Risk requiring corrective action",
                "direction": "Needs attention",
                "ministry_must_show": "Corrective action plan with timeline"
            },
            {
                "clause_ref": "risk-good",
                "rule_statement": "Achievement above 90% rated Good and eligible for scaling up",
                "direction": "Positive signal",
                "ministry_must_show": "Scaling proposal if applicable"
            }
        ], indent=2)
    },
]


def extract_rules_from_chunk(
    chunk_text: str,
    om_number: str,
    om_date: str,
    nature: str,
    cache: dict | None = None,
) -> list[dict]:
    """Extract structured rules from a single chunk using LLM.

    Args:
        chunk_text: The raw chunk text.
        om_number: OM reference number.
        om_date: OM date string.
        nature: OM nature/subject.
        cache: Optional cache dict for reuse across calls.

    Returns:
        List of extracted rule dicts, each with clause_ref, rule_statement,
        direction, ministry_must_show.
    """
    # Check cache
    key = _cache_key(chunk_text)
    if cache is not None and key in cache:
        logger.debug(f"Cache hit for chunk {key[:12]}...")
        return cache[key]

    # Skip very short chunks (likely headers/footers)
    if len(chunk_text.strip()) < 50:
        result = []
        if cache is not None:
            cache[key] = result
        return result

    # Build user message with OM context
    user_message = (
        f"OM context: OM {om_number} dated {om_date}, Nature: {nature}\n\n"
        f"Chunk text:\n{chunk_text}"
    )

    # Call LLM with retry
    client = _get_client()
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=EXTRACTION_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *FEW_SHOT_EXAMPLES,
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=2000,
            )

            raw_content = response.choices[0].message.content.strip()

            # Parse JSON from response (handle markdown code blocks)
            if raw_content.startswith("```"):
                # Strip markdown fences
                lines = raw_content.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block or not line.strip().startswith("```"):
                        json_lines.append(line)
                raw_content = "\n".join(json_lines)

            rules = json.loads(raw_content)

            if not isinstance(rules, list):
                logger.warning(f"LLM returned non-list: {type(rules)}")
                rules = []

            # Validate each rule has required fields
            validated = []
            required_fields = {"clause_ref", "rule_statement", "direction", "ministry_must_show"}
            for rule in rules:
                if isinstance(rule, dict) and required_fields.issubset(rule.keys()):
                    validated.append({
                        "clause_ref": str(rule["clause_ref"]).strip(),
                        "rule_statement": str(rule["rule_statement"]).strip()[:200],
                        "direction": str(rule["direction"]).strip()[:80],
                        "ministry_must_show": str(rule["ministry_must_show"]).strip()[:120],
                    })
                else:
                    logger.warning(f"Skipping invalid rule: {rule}")

            # Cache result
            if cache is not None:
                cache[key] = validated
            return validated

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Failed to parse LLM response after {max_retries} attempts")
                if cache is not None:
                    cache[key] = []
                return []

        except Exception as e:
            logger.warning(f"LLM call failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"LLM extraction failed after {max_retries} attempts: {e}")
                if cache is not None:
                    cache[key] = []
                return []

    return []


def extract_rules_batch(
    tagged_chunks: list[dict],
) -> list[dict]:
    """Extract structured rules from all tagged chunks.

    Args:
        tagged_chunks: List of tagged chunk dicts (from metadata_tagger).
            Each must have: text, om_number, date, nature.

    Returns:
        List of all extracted rule dicts, each enriched with om_id and
        agent_scope from the source chunk.
    """
    cache = _load_cache()
    all_rules = []
    chunks_processed = 0
    cache_hits = 0

    for chunk in tagged_chunks:
        key = _cache_key(chunk["text"])
        was_cached = key in cache

        rules = extract_rules_from_chunk(
            chunk_text=chunk["text"],
            om_number=chunk.get("om_number", "unknown"),
            om_date=chunk.get("date", "unknown"),
            nature=chunk.get("nature", "unknown"),
            cache=cache,
        )

        if was_cached:
            cache_hits += 1

        # Enrich each rule with source metadata
        for rule in rules:
            rule["om_id"] = chunk.get("om_id", "unknown")
            rule["om_number"] = chunk.get("om_number", "unknown")
            rule["date"] = chunk.get("date", "unknown")
            rule["nature"] = chunk.get("nature", "unknown")
            rule["applies_to"] = chunk.get("applies_to", "")
            rule["agent_scope"] = chunk.get("agent_scope", "")

        all_rules.extend(rules)
        chunks_processed += 1

        # Save cache periodically (every 20 chunks)
        if chunks_processed % 20 == 0:
            _save_cache(cache)

    # Final cache save
    _save_cache(cache)

    logger.info(
        f"Extraction complete: {len(all_rules)} rules from {chunks_processed} chunks "
        f"({cache_hits} cache hits)"
    )
    return all_rules
