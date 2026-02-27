"""OM Metadata Registry — structured backbone for APAS ingestion."""

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
        "key_rules": [
            {"clause": "4(i)", "rule": "No new scheme without in-principle DoE approval", "direction": "Prior clearance required", "ministry_must_show": "Attach approval reference"},
            {"clause": "4(ii)", "rule": "Budget must match approved architecture", "direction": "No deviation", "ministry_must_show": "Outlay consistent with approvals"},
            {"clause": "4(iii)", "rule": "Ministries must remove redundant schemes", "direction": "Continuous restructuring", "ministry_must_show": "Provide rationalisation note"},
            {"clause": "4(iv)", "rule": "DoE may force merger/closure", "direction": "Central oversight", "ministry_must_show": "Accept integration possibility"},
            {"clause": "5", "rule": "Weak formulation leads to failure", "direction": "Invest time in design", "ministry_must_show": "Concept paper, consultation, pilots"},
            {"clause": "6", "rule": "Appraisal via SFC/EFC/DIB/PIB", "direction": "Follow proper forum", "ministry_must_show": "Memo in correct format"},
            {"clause": "7", "rule": "New institutions/SPVs require Cabinet approval", "direction": "High authority control", "ministry_must_show": "Cabinet route identified"},
            {"clause": "8", "rule": "Approval authority depends on cost", "direction": "Respect financial hierarchy", "ministry_must_show": "Correct competent authority mapped"},
            {"clause": "8-thresholds", "rule": "Up to 100Cr=Secretary, 100-500Cr=Minister, 500-1000Cr=Minister+FM, Above 1000Cr=Cabinet", "direction": "Financial hierarchy", "ministry_must_show": "Correct authority for proposed cost"},
            {"clause": "9-minor", "rule": "Up to 20% cost escalation allowed", "direction": "Minor flexibility", "ministry_must_show": "Within threshold justification"},
            {"clause": "9-major", "rule": "Beyond 20% requires Revised Cost Committee", "direction": "Fresh appraisal mandatory", "ministry_must_show": "Variation analysis + RCC report"},
            {"clause": "10", "rule": "Pre-investment allowed with FA/Secretary up to limit", "direction": "Conditional spending", "ministry_must_show": "Include in final cost"},
            {"clause": "11", "rule": "Every scheme must have sunset + review", "direction": "Time bound existence", "ministry_must_show": "End date & continuation logic"},
            {"clause": "12", "rule": "Outcomes measurable; third party evaluation; extension based on result", "direction": "Performance driven funding", "ministry_must_show": "KPIs, baseline, evaluation design"},
            {"clause": "13", "rule": "Old OMs cancelled", "direction": "Use only this framework", "ministry_must_show": "Compliance declaration"},
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
        "key_rules": [
            {"clause": "core", "rule": "IPA mandatory before any ministry proceeds with scheme or project", "direction": "Prior clearance required", "ministry_must_show": "IPA obtained from DoE"},
            {"clause": "disclosure", "rule": "List of schemes/projects <500Cr approved in last 2 FY + current FY must be submitted", "direction": "Transparency", "ministry_must_show": "Complete list of recent approvals"},
            {"clause": "enforcement", "rule": "DoE can reduce or stop budget support if IPA violated", "direction": "Consequence for non-compliance", "ministry_must_show": "Compliance confirmation"},
            {"clause": "exemptions", "rule": "Budget-announced schemes and CCS items exempt from IPA", "direction": "Limited exceptions", "ministry_must_show": "Exemption basis if claimed"},
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
        "key_rules": [
            {"clause": "core", "rule": "OOMF submission mandatory for schemes seeking XVI FC continuation", "direction": "Performance data required", "ministry_must_show": "Complete OOMF with targets and achievements"},
            {"clause": "format", "rule": "EFC memo must follow Annexure IV-A of OM dated 05.08.2016", "direction": "Use base format", "ministry_must_show": "Correctly formatted EFC memo"},
            {"clause": "risk-high", "rule": "Achievement below 60% flagged as High Risk", "direction": "Automatic risk classification", "ministry_must_show": "Justification for underperformance"},
            {"clause": "risk-medium", "rule": "Achievement 60-90% flagged as Medium Risk", "direction": "Needs attention", "ministry_must_show": "Improvement plan"},
            {"clause": "risk-good", "rule": "Achievement above 90% eligible for scaling", "direction": "Positive signal", "ministry_must_show": "Scaling proposal if applicable"},
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
        "key_rules": [
            {"clause": "classification", "rule": "CSS classified as Core of Core, Core, or Optional", "direction": "Priority tagging mandatory", "ministry_must_show": "Justify category selection"},
            {"clause": "umbrella", "rule": "Similar schemes must be grouped under umbrella structure", "direction": "Reduce fragmentation", "ministry_must_show": "Umbrella design with sub-components"},
            {"clause": "overlap", "rule": "Overlaps with other schemes must be identified and removed", "direction": "Efficiency and clarity", "ministry_must_show": "Mapping with other schemes, eliminate repetition"},
            {"clause": "funding", "rule": "Centre-State sharing ratio must be clearly specified", "direction": "Transparency in financing", "ministry_must_show": "% share for every component"},
            {"clause": "niti-role", "rule": "NITI Aayog guides restructuring and rationalisation", "direction": "Central coordination", "ministry_must_show": "Consultation with NITI during design"},
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
        "key_rules": [
            {"clause": "5.5x", "rule": "Eligible outlay formula (5.5x of average last 4 years AE) is mandatory ceiling check", "direction": "Spending cap mechanism", "ministry_must_show": "Calculate eligible outlay, declare if within limit, justify if exceeding"},
            {"clause": "evaluation", "rule": "Third-party evaluation findings + ministry comments required", "direction": "Evidence-based continuation", "ministry_must_show": "Evaluation report with response to each finding"},
            {"clause": "rationalisation", "rule": "Components dropped/merged/modified/new must be listed separately", "direction": "Show restructuring", "ministry_must_show": "Detailed list with reasons for each change"},
            {"clause": "sunset", "rule": "Sunset clause plan compulsory", "direction": "Ensure eventual closure", "ministry_must_show": "Exit/tapering/completion strategy"},
            {"clause": "hr-liability", "rule": "All posts created and financial burden must be declared", "direction": "HR liability visibility", "ministry_must_show": "Regular/contractual posts, persons, annual cost"},
            {"clause": "flow-diagrams", "rule": "Implementation flow + fund flow diagrams required", "direction": "Governance clarity", "ministry_must_show": "GOI->State->District->field diagram + CFI->intermediaries->beneficiary chart"},
            {"clause": "centre-state", "rule": "Centre-State sharing ratio variations need justification", "direction": "Prevent arbitrary funding", "ministry_must_show": "Component-wise share with justification for non-uniformity"},
            {"clause": "cost-norms", "rule": "Changes in cost norms must be explained", "direction": "Financial prudence", "ministry_must_show": "Old vs new cost norms with reasons"},
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
        "key_rules": [
            {"clause": "fresh-appraisal", "rule": "Every scheme must undergo fresh appraisal — no automatic continuation", "direction": "Mandatory evaluation", "ministry_must_show": "Updated DPR & financials"},
            {"clause": "sunset", "rule": "Schemes end with Finance Commission period unless approved again", "direction": "Expiry is default", "ministry_must_show": "Seek approval before deadline"},
            {"clause": "unspent", "rule": "Unspent balances must be adjusted before fresh allocation", "direction": "Financial discipline", "ministry_must_show": "Declare balances"},
            {"clause": "new-components", "rule": "New components cannot be added without separate approval", "direction": "Control expansion", "ministry_must_show": "Seek fresh sanction"},
            {"clause": "scope-change", "rule": "Change in cost or scope requires revised EFC/SFC note", "direction": "Prevent informal changes", "ministry_must_show": "Submit revised approval"},
            {"clause": "non-compliance", "rule": "Expenditure without approval may not be regularised", "direction": "Serious warning", "ministry_must_show": "Do not commit funds without approval"},
            {"clause": "outcome-budget", "rule": "Must align with Output-Outcome Monitoring Framework", "direction": "Performance linkage", "ministry_must_show": "Measurable targets aligned with OOMF"},
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
        "key_rules": [
            {"clause": "completeness", "rule": "Proposal must be fully complete before appraisal — all annexures, data, approvals attached", "direction": "No incomplete submissions", "ministry_must_show": "All documents attached"},
            {"clause": "no-duplication", "rule": "Must not overlap with existing schemes — comparison mandatory", "direction": "Avoid duplication", "ministry_must_show": "Comparison & gap analysis"},
            {"clause": "evidence", "rule": "Need must be data-backed with baseline/survey", "direction": "Evidence-based design", "ministry_must_show": "Baseline data or survey"},
            {"clause": "costing", "rule": "Year-wise and component-wise break-up mandatory", "direction": "Detailed financials", "ministry_must_show": "Financial tables"},
            {"clause": "recurring-liability", "rule": "Future financial burden must be declared", "direction": "Sustainability check", "ministry_must_show": "Liability projections"},
            {"clause": "fund-flow", "rule": "Clear release & utilization mechanism via PFMS/DBT", "direction": "Financial transparency", "ministry_must_show": "Fund flow design"},
            {"clause": "sunset", "rule": "Fixed scheme duration required with exit/closure plan", "direction": "Time-bound", "ministry_must_show": "Duration and exit strategy"},
            {"clause": "certification", "rule": "Ministry certifies accuracy of all information", "direction": "Accountability", "ministry_must_show": "Signed confirmation"},
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
