from __future__ import annotations

"""
Judge agent factory.

Creates a judge/evaluator LLM agent that returns a STRICT JSON verdict
assessing the planner's draft answer against provided evidence snippets.
"""

from google.genai import types


def _judge_instruction() -> str:
    """
    Instruction for the judge agent.

    The judge:
    - Evaluates DRAFT_ANSWER vs. evidence snippets
    - Returns STRICT JSON with fields:
      verdict, critique, missing, suggested_queries, target_docs
    """
    return (
        "You are a strict evaluator focused on answer quality and user intent alignment.\n"
        "Your goal is to ensure the final answer TRULY addresses what the user asked.\n\n"
        "You will be given:\n"
        "- USER_QUESTION: the user's original question (analyze the INTENT).\n"
        "- DRAFT_ANSWER: the proposed answer (synthesized/polished).\n"
        "- EVIDENCE_SNIPPETS: a list of textual snippets (with doc_ids) retrieved from tools.\n\n"
        "Your task:\n"
        "1) Analyze the USER_QUESTION to understand the core INTENT (what do they really want?).\n"
        "2) Compare DRAFT_ANSWER against this INTENT and the EVIDENCE_SNIPPETS.\n"
        "3) Decide if the answer should be accepted as-is or if the planner should retry.\n"
        "4) If retry is needed, specify what is missing and where to look next.\n\n"
        "You MUST output a single JSON object with this exact schema:\n"
        "{\n"
        '  "verdict": "accept" | "retry",\n'
        '  "critique": "string",\n'
        '  "missing": "string",\n'
        '  "suggested_queries": ["..."],\n'
        '  "target_docs": ["doc_id_1", "..."]\n'
        "}\n\n"
        "Field semantics:\n"
        '- verdict: "accept" if the answer is correct, complete, and well-written; otherwise "retry".\n'
        "- critique: A short paragraph explaining your evaluation of the answer vs intent.\n"
        "- missing: If verdict is retry, describe what is missing, unclear, or incorrect.\n"
        "- suggested_queries: If verdict is retry, suggest 1–3 search queries to improve retrieval.\n"
        "- target_docs: If verdict is retry, list 1–5 doc_ids that are most promising for further search.\n\n"
        "Rules:\n"
        "- If the answer is obviously wrong, incomplete, or ungrounded, verdict MUST be \"retry\".\n"
        "- If the answer misses the user's core intent, verdict MUST be \"retry\".\n"
        "- If evidence is insufficient to fully answer, verdict MUST be \"retry\" and missing MUST explain gaps.\n"
        "- Never hallucinate document IDs; only use doc_ids that appear in EVIDENCE_SNIPPETS.\n"
        "- Be conservative: when in doubt, choose \"retry\".\n"
        "- The output must be STRICT JSON; do not include commentary or markdown.\n"
    )


def create_judge_agent(
    model: str = "gemini-2.0-flash",
    temperature: float = 0.0,
) -> LlmAgent:
    """
    Judge/Evaluator agent: returns STRICT JSON verdict.
    JSON schema:
    {
      "verdict": "accept" | "retry",
      "critique": "string",
      "missing": "string",
      "suggested_queries": ["..."],
      "target_docs": ["doc_id_1", "..."]
    }
    """
    instruction = _judge_instruction()

    instruction = _judge_instruction()

    from .simple_agent import SimpleAgent
    return SimpleAgent(
        name="judge",
        model=model,
        instruction=instruction,
        tools=[],  # Judge does not call tools
        generate_content_config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=1024,
            response_mime_type="application/json",
            system_instruction=instruction,
        ),
    )
