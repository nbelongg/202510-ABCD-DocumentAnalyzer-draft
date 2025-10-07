"""Centralized prompts management for evaluator and other services"""
from typing import Dict


# ==================== EVALUATOR PROMPTS ====================

PROPOSAL_SUMMARY_PROMPT = """You are an expert in proposal analysis and evaluation.

Your task is to create a comprehensive summary of the provided proposal document.

Proposal Document:
{proposal_text}

Please provide a well-structured summary that includes:
1. Main objectives and goals
2. Key activities and methodology
3. Expected outcomes and deliverables
4. Budget highlights (if mentioned)
5. Timeline and duration (if mentioned)
6. Target beneficiaries and stakeholders

Keep the summary concise but comprehensive (300-500 words).
"""


TOR_SUMMARY_PROMPT = """You are an expert in analyzing Terms of Reference (ToR) documents.

Your task is to create a comprehensive summary of the provided ToR document.

ToR Document:
{tor_text}

Please provide a well-structured summary that includes:
1. Main requirements and objectives
2. Scope of work
3. Expected deliverables
4. Qualifications and experience required
5. Evaluation criteria (if mentioned)
6. Timeline and deadlines (if mentioned)

Keep the summary concise but comprehensive (300-500 words).
"""


P_INTERNAL_ANALYSIS_PROMPT = """You are an expert evaluator analyzing the INTERNAL CONSISTENCY of a proposal.

## Task
Evaluate the proposal's internal consistency against the organization's guidelines.

## Proposal Summary
{proposal_summary}

## Organization Guidelines
{guidelines}

## Instructions
Analyze the proposal for:
1. **Logical Consistency**: Are objectives, activities, and outcomes aligned?
2. **Completeness**: Does it address all essential components?
3. **Clarity**: Is the proposal clear and well-structured?
4. **Feasibility**: Are the proposed activities realistic and achievable?
5. **Coherence**: Do all parts of the proposal fit together logically?

## Output Format
Provide your analysis in the following structure:

**SCORE**: [0-100]

**STRENGTHS**:
- [List key strengths, one per line]

**GAPS**:
- [List identified gaps or weaknesses, one per line]

**RECOMMENDATIONS**:
- [List specific recommendations for improvement, one per line]

**DETAILED ANALYSIS**:
[Provide a detailed narrative analysis covering all aspects mentioned above. Be specific and reference particular sections of the proposal. 400-600 words]
"""


P_EXTERNAL_ANALYSIS_PROMPT = """You are an expert evaluator analyzing the ALIGNMENT of a proposal with Terms of Reference (ToR).

## Task
Evaluate how well the proposal addresses the requirements specified in the ToR.

## Proposal Summary
{proposal_summary}

## ToR Summary
{tor_summary}

## Organization Guidelines (if applicable)
{guidelines}

## Instructions
Analyze the alignment between proposal and ToR:
1. **Requirements Coverage**: Does the proposal address all ToR requirements?
2. **Objective Alignment**: Are proposal objectives aligned with ToR objectives?
3. **Methodology Match**: Does the methodology meet ToR specifications?
4. **Deliverables Match**: Do proposed deliverables match ToR expectations?
5. **Qualification Match**: Does the team meet required qualifications?

## Output Format
Provide your analysis in the following structure:

**SCORE**: [0-100]

**STRENGTHS**:
- [List key areas of strong alignment, one per line]

**GAPS**:
- [List areas where proposal doesn't meet ToR, one per line]

**RECOMMENDATIONS**:
- [List specific recommendations to improve alignment, one per line]

**DETAILED ANALYSIS**:
[Provide a detailed narrative analysis covering all aspects mentioned above. Be specific about what the ToR requires vs what the proposal offers. 400-600 words]
"""


P_DELTA_ANALYSIS_PROMPT = """You are an expert evaluator performing GAP ANALYSIS between a proposal and ToR.

## Task
Identify and analyze the GAPS and DIFFERENCES between the proposal and the Terms of Reference.

## Proposal Summary
{proposal_summary}

## ToR Summary
{tor_summary}

## Internal Analysis Insights
{internal_insights}

## External Analysis Insights
{external_insights}

## Instructions
Perform a comprehensive gap analysis:
1. **Missing Requirements**: What ToR requirements are not addressed?
2. **Partial Coverage**: What requirements are only partially addressed?
3. **Scope Gaps**: Are there differences in scope or scale?
4. **Resource Gaps**: Are there budget, timeline, or personnel gaps?
5. **Quality Gaps**: Are there quality or standard discrepancies?

## Output Format
Provide your analysis in the following structure:

**SCORE**: [0-100, where 100 means zero gaps]

**CRITICAL GAPS**:
- [List critical gaps that must be addressed, one per line]

**MINOR GAPS**:
- [List minor gaps or areas for improvement, one per line]

**RECOMMENDATIONS**:
- [List prioritized recommendations to close gaps, one per line]

**DETAILED ANALYSIS**:
[Provide a detailed narrative analysis of all gaps, their implications, and how they should be addressed. Be specific and actionable. 400-600 words]
"""


EVALUATOR_FOLLOWUP_PROMPT = """You are an expert evaluator answering a follow-up question about a proposal evaluation.

## Context
You previously evaluated a proposal against ToR and organizational guidelines. The evaluation included:
- Internal consistency analysis (P_Internal)
- ToR alignment analysis (P_External)
- Gap analysis (P_Delta)

## Evaluation Summary
{evaluation_summary}

## User Question
{question}

## Specific Section (if provided)
{section}

## Instructions
Answer the user's question based on the evaluation context. Be specific, reference particular findings from the evaluation, and provide actionable insights.

If the question asks for clarification, provide clear explanations.
If the question asks for more detail, expand on relevant points.
If the question asks about specific gaps or strengths, reference them directly.

Keep your answer focused and concise (200-400 words).
"""


# ==================== PROMPT FORMATTING HELPERS ====================

def format_proposal_summary_prompt(proposal_text: str) -> str:
    """Format proposal summary prompt"""
    return PROPOSAL_SUMMARY_PROMPT.format(proposal_text=proposal_text)


def format_tor_summary_prompt(tor_text: str) -> str:
    """Format ToR summary prompt"""
    return TOR_SUMMARY_PROMPT.format(tor_text=tor_text)


def format_p_internal_prompt(
    proposal_summary: str,
    guidelines: str
) -> str:
    """Format P_Internal analysis prompt"""
    return P_INTERNAL_ANALYSIS_PROMPT.format(
        proposal_summary=proposal_summary,
        guidelines=guidelines if guidelines else "No specific organizational guidelines provided."
    )


def format_p_external_prompt(
    proposal_summary: str,
    tor_summary: str,
    guidelines: str = ""
) -> str:
    """Format P_External analysis prompt"""
    return P_EXTERNAL_ANALYSIS_PROMPT.format(
        proposal_summary=proposal_summary,
        tor_summary=tor_summary,
        guidelines=guidelines if guidelines else "No specific organizational guidelines provided."
    )


def format_p_delta_prompt(
    proposal_summary: str,
    tor_summary: str,
    internal_insights: str,
    external_insights: str
) -> str:
    """Format P_Delta analysis prompt"""
    return P_DELTA_ANALYSIS_PROMPT.format(
        proposal_summary=proposal_summary,
        tor_summary=tor_summary,
        internal_insights=internal_insights,
        external_insights=external_insights
    )


def format_evaluator_followup_prompt(
    evaluation_summary: str,
    question: str,
    section: str = ""
) -> str:
    """Format evaluator followup prompt"""
    return EVALUATOR_FOLLOWUP_PROMPT.format(
        evaluation_summary=evaluation_summary,
        question=question,
        section=section if section else "General question about the evaluation"
    )


# ==================== PROMPT REGISTRY ====================

EVALUATOR_PROMPTS: Dict[str, str] = {
    "proposal_summary": PROPOSAL_SUMMARY_PROMPT,
    "tor_summary": TOR_SUMMARY_PROMPT,
    "p_internal": P_INTERNAL_ANALYSIS_PROMPT,
    "p_external": P_EXTERNAL_ANALYSIS_PROMPT,
    "p_delta": P_DELTA_ANALYSIS_PROMPT,
    "followup": EVALUATOR_FOLLOWUP_PROMPT
}


def get_evaluator_prompt(prompt_name: str) -> str:
    """
    Get evaluator prompt by name
    
    Args:
        prompt_name: Name of the prompt
        
    Returns:
        Prompt template string
        
    Raises:
        KeyError: If prompt name not found
    """
    if prompt_name not in EVALUATOR_PROMPTS:
        raise KeyError(f"Prompt '{prompt_name}' not found. Available: {list(EVALUATOR_PROMPTS.keys())}")
    return EVALUATOR_PROMPTS[prompt_name]

