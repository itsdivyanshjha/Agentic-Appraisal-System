"""OM Metadata Registry — structured backbone for APAS ingestion.

Note: key_rules have been moved to config/key_rules_reference.py.
Structured rules are now auto-extracted via LLM at ingestion time.
"""

OM_REGISTRY = [
    {
        "id": "OM-1",
        "om_number": "24(35)/PF-II/2012",
        "date": "2016-08-05",
        "nature": "Expenditure Control",
        "applies_to": ["new_scheme", "continuation", "project"],
        "agent_scope": ["compliance", "fiscal"],
        "source_files": [
            "DoE O.M. No. 24(35)PF-II2012 dated 05.08.2016.pdf",
            "Guidelines_for_appraisal_and_approval_of_schemesprojects Om dtd 05.08.2016.pdf",
            "GuidelinesAppraisal_Approval_Schemes_Projects 05082016.pdf",
        ],
        "annexures": [
            {"id": "I", "purpose": "Concept stage of new scheme", "core_idea": "Justification, objectives, rough cost, expected benefits"},
            {"id": "II", "purpose": "Detailed EFC/PIB appraisal", "core_idea": "Full financials, implementation plan, outputs, timelines, monitoring, risks"},
            {"id": "III", "purpose": "Continuation of existing scheme", "core_idea": "Past performance, utilization, evaluation results, extension justification"},
            {"id": "IV", "purpose": "Project proposals (asset/infrastructure)", "core_idea": "Technical scope, cost estimates, schedule, procurement, O&M, returns"},
            {"id": "V", "purpose": "Monitoring & review framework", "core_idea": "Progress tracking, outcomes, financial discipline post-approval"},
        ],
    },
    {
        "id": "OM-2",
        "om_number": "01(01)/PFC-II/2022",
        "date": "2022-10-21",
        "nature": "Compliance Enforcement",
        "applies_to": ["new_scheme", "project"],
        "agent_scope": ["compliance"],
        "source_files": ["DoE OM dated 21.10.2022 for IPA of projects.pdf"],
        "annexures": [
            {"id": "I", "purpose": "Proposal for In-Principle Approval (IPA)", "core_idea": "Basic scheme idea, objectives, estimated cost, duration, funding pattern, approvals required"},
            {"id": "II", "purpose": "Information for Detailed Appraisal", "core_idea": "Component-wise expenditure, phasing, implementation mechanism, outcomes, monitoring"},
            {"id": "III", "purpose": "Commitment/liability statement", "core_idea": "Future financial burden, recurring expenses, sustainability"},
        ],
    },
    {
        "id": "OM-3",
        "om_number": "01(01)/PFC-II/2025",
        "date": "2025-10-31",
        "nature": "Performance-Linked",
        "applies_to": ["continuation"],
        "agent_scope": ["compliance", "sector"],
        "source_files": [
            "DoEs OM dated 31.10.2025 on OOMF for continuation during the 16th FCC.pdf",
            "DoEs OM dated 31.10.2025 on Appraisal and Approval of Schemes ending on 31st March 2026 and to be continued during the 16th Finance Commission Cycle - OOMF Info.pdf",
            "Appraisal_and_Approval_of_Schemes_ending_on_31st_March_2026 OM dtd 31.10.2025.pdf",
            "DoE O.M dt 31102025 Annexure Addi Info. for schemes ending on 31st March 2026.pdf",
        ],
        "annexures": [
            {"id": "A", "purpose": "Output/Outcome Target vs Achievement", "core_idea": "OOMF data with FY targets and actual achievements"},
            {"id": "B", "purpose": "Risk Flags", "core_idea": "<60% = High Risk, 60-90% = Medium, >90% = Good"},
            {"id": "C", "purpose": "Auto-Generated Remarks", "core_idea": "System-generated assessment based on performance data"},
        ],
    },
    {
        "id": "OM-4",
        "om_number": "O-11013/02/2015-CSS & CMC",
        "date": "2016-08-17",
        "nature": "Structural Rationalisation",
        "applies_to": ["continuation", "new_scheme"],
        "agent_scope": ["sector", "compliance"],
        "source_files": ["OM  of NITI on Rationalization of Scheme August'2016.PDF"],
        "annexures": [
            {"id": "I", "purpose": "Scheme review template", "core_idea": "List of schemes, objectives, outlay, duplication, suggestion (continue/merge/drop)"},
            {"id": "II", "purpose": "Outcome & restructuring details", "core_idea": "Benefits, performance, proposed changes after rationalisation"},
        ],
    },
    {
        "id": "OM-5",
        "om_number": "01(01)/PFC-II/2025",
        "date": "2025-06-06",
        "nature": "Continuation Compliance",
        "applies_to": ["continuation"],
        "agent_scope": ["compliance", "fiscal"],
        "source_files": [
            "DoE OM dt.06.06.2025 reg- Guidelines of appraisal and approval of schemes_0001.pdf",
            "Guidelines for appraisal & approval of schemes 01(01) dtd 06.06.2025.pdf",
        ],
        "annexures": [
            {"id": "single", "purpose": "19-point continuation checklist for XVI FC", "core_idea": "Comprehensive checklist covering rationale, evaluation, restructuring, financials, HR, implementation, fund flow"},
        ],
    },
    {
        "id": "OM-6",
        "om_number": "42(02)/PF-II/2014",
        "date": "2020-12-08",
        "nature": "Scheme Continuation",
        "applies_to": ["continuation"],
        "agent_scope": ["compliance", "fiscal"],
        "source_files": ["08.12.2020 Continuation.pdf"],
        "annexures": [
            {"id": "I", "purpose": "EFC Memo Format", "core_idea": "Background, necessity, objectives, financial cost & phasing, implementation, outcomes, appraisal of alternatives"},
            {"id": "II", "purpose": "SFC Memo Format", "core_idea": "Similar to EFC but for lower financial limits"},
            {"id": "III", "purpose": "Delegated Powers / Cost Limits", "core_idea": "Who approves what value, escalation thresholds"},
            {"id": "IV", "purpose": "Outcome & Output Framework", "core_idea": "Measurable targets, year-wise deliverables, monitoring indicators"},
            {"id": "V", "purpose": "Format for Appraisal Note", "core_idea": "Standard template for DoE observations/concurrence"},
            {"id": "VI", "purpose": "Flow of Appraisal Process", "core_idea": "Ministry->FA->DoE->Committee->Approval step-by-step"},
        ],
    },
    {
        "id": "OM-7",
        "om_number": "01(01)/PFC-1/2022",
        "date": "2023-10-03",
        "nature": "Procedural Reform",
        "applies_to": ["new_scheme"],
        "agent_scope": ["compliance"],
        "source_files": ["DoE OM dated 03.10.2023 on Revised Format for Appraisal and Approval of new Public funded Schemes.pdf"],
        "annexures": [
            {"id": "I", "purpose": "Format for EFC/PIB Memo", "core_idea": "Background, objectives, beneficiaries, components, outlay, implementation, monitoring, evaluation, risks, outcomes"},
            {"id": "II", "purpose": "Appraisal Checklist", "core_idea": "Verification sheet: mandatory approvals, costing, duplication, measurable outcomes, convergence, implementation readiness"},
            {"id": "III", "purpose": "Outcome & Output Framework", "core_idea": "Outputs, outcomes, indicators, baseline, targets, timeline"},
        ],
    },
]

# Mapping: source filename -> OM ID and document type
FILE_TO_OM_MAP = {
    "DoE O.M. No. 24(35)PF-II2012 dated 05.08.2016.pdf": {"om_id": "OM-1", "doc_type": "om"},
    "Guidelines_for_appraisal_and_approval_of_schemesprojects Om dtd 05.08.2016.pdf": {"om_id": "OM-1", "doc_type": "guidelines"},
    "GuidelinesAppraisal_Approval_Schemes_Projects 05082016.pdf": {"om_id": "OM-1", "doc_type": "guidelines"},
    "DoE OM dated 21.10.2022 for IPA of projects.pdf": {"om_id": "OM-2", "doc_type": "om"},
    "DoEs OM dated 31.10.2025 on OOMF for continuation during the 16th FCC.pdf": {"om_id": "OM-3", "doc_type": "om"},
    "DoEs OM dated 31.10.2025 on Appraisal and Approval of Schemes ending on 31st March 2026 and to be continued during the 16th Finance Commission Cycle - OOMF Info.pdf": {"om_id": "OM-3", "doc_type": "om"},
    "Appraisal_and_Approval_of_Schemes_ending_on_31st_March_2026 OM dtd 31.10.2025.pdf": {"om_id": "OM-3", "doc_type": "om"},
    "DoE O.M dt 31102025 Annexure Addi Info. for schemes ending on 31st March 2026.pdf": {"om_id": "OM-3", "doc_type": "annexure"},
    "OM  of NITI on Rationalization of Scheme August'2016.PDF": {"om_id": "OM-4", "doc_type": "om"},
    "DoE OM dt.06.06.2025 reg- Guidelines of appraisal and approval of schemes_0001.pdf": {"om_id": "OM-5", "doc_type": "om"},
    "Guidelines for appraisal & approval of schemes 01(01) dtd 06.06.2025.pdf": {"om_id": "OM-5", "doc_type": "guidelines"},
    "08.12.2020 Continuation.pdf": {"om_id": "OM-6", "doc_type": "om"},
    "DoE OM dated 03.10.2023 on Revised Format for Appraisal and Approval of new Public funded Schemes.pdf": {"om_id": "OM-7", "doc_type": "om"},
}

# Agent -> collection + filter mapping
AGENT_RETRIEVAL_CONFIG = {
    "compliance": {
        "primary_collection": "structured_rules",
        "secondary_collection": "om_document_chunks",
        "metadata_filter": {"agent_scope": {"$contains": "compliance"}},
        "top_k": 8,
    },
    "fiscal": {
        "primary_collection": "structured_rules",
        "secondary_collection": "reference_corpus",
        "metadata_filter": {"agent_scope": {"$contains": "fiscal"}},
        "top_k": 6,
    },
    "sector": {
        "primary_collection": "om_document_chunks",
        "secondary_collection": "reference_corpus",
        "metadata_filter": {"agent_scope": {"$contains": "sector"}},
        "top_k": 8,
    },
}


def get_om_by_id(om_id: str) -> dict | None:
    """Look up an OM entry by its ID."""
    for om in OM_REGISTRY:
        if om["id"] == om_id:
            return om
    return None


def get_file_info(filename: str) -> dict | None:
    """Look up file mapping info by filename."""
    return FILE_TO_OM_MAP.get(filename)
