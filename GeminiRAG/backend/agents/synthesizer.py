from __future__ import annotations

"""
Synthesizer agent factory.

Creates a synthesis-focused LLM agent that:
- When LATEST_DRAFT_ANSWER is provided, operates in polish-only mode:
  validate the draft for clarity, correctness, and structure, and lightly optimize wording/formatting.
- When no draft is provided, can produce a concise, structured answer from provided context/evidence
  while clearly marking assumptions.
- Formats the final answer appropriately based on context:
  narrative paragraphs for explanations, bullet lists for checklists, or sectioned headings for frameworks/outlines.
- Emits the final answer inside a DRAFT_ANSWER block for consistent parsing.

This module is UI-agnostic and can be reused by any frontend.
"""

from typing import Optional

from google.genai import types


def _synthesizer_instruction() -> str:
    """
    Instruction for the synthesis agent.

    The synthesizer:
    - Polishes and formats the final answer
    - Optionally derives a final answer from rich context if needed
    - Always emits the result inside a DRAFT_ANSWER block
    """
    return (
        "You are Aurora, a precise synthesis and writing assistant.\n\n"
        "You will be provided with:\n"
        "- USER_QUESTION: the user's original question.\n"
        "- LATEST_DRAFT_ANSWER: an optional draft answer from a planner agent.\n"
        "- CONTEXT_SNIPPETS: optional supporting context, snippets, or notes.\n\n"
        "Your goals:\n"
        "1) If LATEST_DRAFT_ANSWER is non-empty:\n"
        "   - Treat it as the primary answer.\n"
        "   - Improve clarity, flow, and structure without changing the core meaning.\n"
        "   - Fix obvious factual inconsistencies if they contradict CONTEXT_SNIPPETS.\n"
        "   - Remove any planning logs, headings like 'PLAN' or 'EXECUTE', or tool outputs.\n"
        "2) If LATEST_DRAFT_ANSWER is empty or clearly unusable:\n"
        "   - Derive a best-effort answer from CONTEXT_SNIPPETS.\n"
        "   - If context is insufficient, explicitly state limitations and what is unknown.\n\n"
        "Formatting guidelines:\n"
        "- Prefer short paragraphs and bullet lists for readability.\n"
        "- Use numbered lists for step-by-step instructions.\n"
        "- Use headings (##, ###) if multiple sections are helpful.\n"
        "- Avoid raw JSON, unless specifically requested by USER_QUESTION.\n\n"
        "VERY IMPORTANT:\n"
        "At the end, you MUST emit the final answer inside a DRAFT_ANSWER block using this exact format:\n"
        "=== DRAFT_ANSWER ===\n"
        "<your final answer here>\n"
        "=== END_DRAFT_ANSWER ===\n\n"
        "Do not include any additional commentary before or after the DRAFT_ANSWER block.\n"
    )


def create_synthesizer_agent(
    model: str = "gemini-2.0-flash",
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> LlmAgent:
    """
    Create a synthesis/polish LlmAgent.

    Parameters
    ----------
    model:
        Model name for synthesis.
    temperature:
        Sampling temperature for writing style (slightly higher than judge).
    max_tokens:
        Maximum output tokens for the synthesized answer.
    """
    instruction = _synthesizer_instruction()

    instruction = _synthesizer_instruction()

    from .simple_agent import SimpleAgent
    return SimpleAgent(
        name="synthesizer",
        model=model,
        instruction=instruction,
        tools=[],  # Synthesizer does not call tools
        generate_content_config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=instruction,
        ),
    )
