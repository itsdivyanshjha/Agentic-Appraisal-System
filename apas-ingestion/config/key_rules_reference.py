"""Gold-standard key_rules reference — moved from document_registry.py.

These 52 hand-crafted rules serve as validation targets for the
LLM-extracted structured rules. Compare extraction output against
these to verify coverage and quality.

DO NOT USE IN PIPELINE — this file is for validation only.
"""

KEY_RULES_REFERENCE = {
    "OM-1": [
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
    "OM-2": [
        {"clause": "core", "rule": "IPA mandatory before any ministry proceeds with scheme or project", "direction": "Prior clearance required", "ministry_must_show": "IPA obtained from DoE"},
        {"clause": "disclosure", "rule": "List of schemes/projects <500Cr approved in last 2 FY + current FY must be submitted", "direction": "Transparency", "ministry_must_show": "Complete list of recent approvals"},
        {"clause": "enforcement", "rule": "DoE can reduce or stop budget support if IPA violated", "direction": "Consequence for non-compliance", "ministry_must_show": "Compliance confirmation"},
        {"clause": "exemptions", "rule": "Budget-announced schemes and CCS items exempt from IPA", "direction": "Limited exceptions", "ministry_must_show": "Exemption basis if claimed"},
    ],
    "OM-3": [
        {"clause": "core", "rule": "OOMF submission mandatory for schemes seeking XVI FC continuation", "direction": "Performance data required", "ministry_must_show": "Complete OOMF with targets and achievements"},
        {"clause": "format", "rule": "EFC memo must follow Annexure IV-A of OM dated 05.08.2016", "direction": "Use base format", "ministry_must_show": "Correctly formatted EFC memo"},
        {"clause": "risk-high", "rule": "Achievement below 60% flagged as High Risk", "direction": "Automatic risk classification", "ministry_must_show": "Justification for underperformance"},
        {"clause": "risk-medium", "rule": "Achievement 60-90% flagged as Medium Risk", "direction": "Needs attention", "ministry_must_show": "Improvement plan"},
        {"clause": "risk-good", "rule": "Achievement above 90% eligible for scaling", "direction": "Positive signal", "ministry_must_show": "Scaling proposal if applicable"},
    ],
    "OM-4": [
        {"clause": "classification", "rule": "CSS classified as Core of Core, Core, or Optional", "direction": "Priority tagging mandatory", "ministry_must_show": "Justify category selection"},
        {"clause": "umbrella", "rule": "Similar schemes must be grouped under umbrella structure", "direction": "Reduce fragmentation", "ministry_must_show": "Umbrella design with sub-components"},
        {"clause": "overlap", "rule": "Overlaps with other schemes must be identified and removed", "direction": "Efficiency and clarity", "ministry_must_show": "Mapping with other schemes, eliminate repetition"},
        {"clause": "funding", "rule": "Centre-State sharing ratio must be clearly specified", "direction": "Transparency in financing", "ministry_must_show": "% share for every component"},
        {"clause": "niti-role", "rule": "NITI Aayog guides restructuring and rationalisation", "direction": "Central coordination", "ministry_must_show": "Consultation with NITI during design"},
    ],
    "OM-5": [
        {"clause": "5.5x", "rule": "Eligible outlay formula (5.5x of average last 4 years AE) is mandatory ceiling check", "direction": "Spending cap mechanism", "ministry_must_show": "Calculate eligible outlay, declare if within limit, justify if exceeding"},
        {"clause": "evaluation", "rule": "Third-party evaluation findings + ministry comments required", "direction": "Evidence-based continuation", "ministry_must_show": "Evaluation report with response to each finding"},
        {"clause": "rationalisation", "rule": "Components dropped/merged/modified/new must be listed separately", "direction": "Show restructuring", "ministry_must_show": "Detailed list with reasons for each change"},
        {"clause": "sunset", "rule": "Sunset clause plan compulsory", "direction": "Ensure eventual closure", "ministry_must_show": "Exit/tapering/completion strategy"},
        {"clause": "hr-liability", "rule": "All posts created and financial burden must be declared", "direction": "HR liability visibility", "ministry_must_show": "Regular/contractual posts, persons, annual cost"},
        {"clause": "flow-diagrams", "rule": "Implementation flow + fund flow diagrams required", "direction": "Governance clarity", "ministry_must_show": "GOI->State->District->field diagram + CFI->intermediaries->beneficiary chart"},
        {"clause": "centre-state", "rule": "Centre-State sharing ratio variations need justification", "direction": "Prevent arbitrary funding", "ministry_must_show": "Component-wise share with justification for non-uniformity"},
        {"clause": "cost-norms", "rule": "Changes in cost norms must be explained", "direction": "Financial prudence", "ministry_must_show": "Old vs new cost norms with reasons"},
    ],
    "OM-6": [
        {"clause": "fresh-appraisal", "rule": "Every scheme must undergo fresh appraisal — no automatic continuation", "direction": "Mandatory evaluation", "ministry_must_show": "Updated DPR & financials"},
        {"clause": "sunset", "rule": "Schemes end with Finance Commission period unless approved again", "direction": "Expiry is default", "ministry_must_show": "Seek approval before deadline"},
        {"clause": "unspent", "rule": "Unspent balances must be adjusted before fresh allocation", "direction": "Financial discipline", "ministry_must_show": "Declare balances"},
        {"clause": "new-components", "rule": "New components cannot be added without separate approval", "direction": "Control expansion", "ministry_must_show": "Seek fresh sanction"},
        {"clause": "scope-change", "rule": "Change in cost or scope requires revised EFC/SFC note", "direction": "Prevent informal changes", "ministry_must_show": "Submit revised approval"},
        {"clause": "non-compliance", "rule": "Expenditure without approval may not be regularised", "direction": "Serious warning", "ministry_must_show": "Do not commit funds without approval"},
        {"clause": "outcome-budget", "rule": "Must align with Output-Outcome Monitoring Framework", "direction": "Performance linkage", "ministry_must_show": "Measurable targets aligned with OOMF"},
    ],
    "OM-7": [
        {"clause": "completeness", "rule": "Proposal must be fully complete before appraisal — all annexures, data, approvals attached", "direction": "No incomplete submissions", "ministry_must_show": "All documents attached"},
        {"clause": "no-duplication", "rule": "Must not overlap with existing schemes — comparison mandatory", "direction": "Avoid duplication", "ministry_must_show": "Comparison & gap analysis"},
        {"clause": "evidence", "rule": "Need must be data-backed with baseline/survey", "direction": "Evidence-based design", "ministry_must_show": "Baseline data or survey"},
        {"clause": "costing", "rule": "Year-wise and component-wise break-up mandatory", "direction": "Detailed financials", "ministry_must_show": "Financial tables"},
        {"clause": "recurring-liability", "rule": "Future financial burden must be declared", "direction": "Sustainability check", "ministry_must_show": "Liability projections"},
        {"clause": "fund-flow", "rule": "Clear release & utilization mechanism via PFMS/DBT", "direction": "Financial transparency", "ministry_must_show": "Fund flow design"},
        {"clause": "sunset", "rule": "Fixed scheme duration required with exit/closure plan", "direction": "Time-bound", "ministry_must_show": "Duration and exit strategy"},
        {"clause": "certification", "rule": "Ministry certifies accuracy of all information", "direction": "Accountability", "ministry_must_show": "Signed confirmation"},
    ],
}
