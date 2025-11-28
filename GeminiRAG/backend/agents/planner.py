from __future__ import annotations

"""
Planner agent factory.

Creates a planner/searcher LLM agent configured with tools to:
- list available documents
- search within a specific document
- search across all documents

This module is UI-agnostic and can be reused by any frontend.
"""

from typing import List, Optional, Callable, Any

from google.genai import types


def _default_instruction(
    top_k: int = 5,
) -> str:
    """
    Default planner instruction that:

    - Encourages explicit planning steps
    - Encourages iterative tool use with reflection
    - Requires a final DRAFT_ANSWER block for consistent parsing

    The answer is always emitted inside:

    === DRAFT_ANSWER ===
    ...
    === END_DRAFT_ANSWER ===
    """
    return (
        "You are Orion, an expert researcher and strategic planner. Your goal is to answer the user's question "
        "by retrieving high-quality evidence. You MUST follow this cognitive workflow:\n\n"
        
        "PHASE 1: ANALYZE & EXPAND (Mental Scratchpad)\n"
        "1. Analyze the user's core intent. Is it technical? Factual? Abstract?\n"
        "2. QUERY EXPANSION: The user's specific keywords might not match the documents. "
        "Generates 3 DISTINCT search queries to maximize retrieval coverage:\n"
        "   - Query A: Direct keyword variations (synonyms, technical terms).\n"
        "   - Query B: Semantic/Conceptual version (what is the *meaning*?).\n"
        "   - Query C: Hypothetical answer fragments (what would the answer look like?).\n"
        "   (Do not output these yet, but use them in the Execution phase).\n\n"
        
        "PHASE 2: EXECUTE (Tool Usage)\n"
        "1. List Documents: Call `list_documents_http` first to understand what files are available.\n"
        "2. Targeted Search: \n"
        "   - If a specific file is relevant, call `search_document_hybrid_http` using your Expanded Queries.\n"
        "   - If the answer could be anywhere, call `search_all_hybrid_http`.\n"
        "   - **CRITICAL**: Prefer `hybrid` tools over standard tools. They combine Keyword (BM25) + Semantic (Vector) search.\n"
        "3. Iterate: \n"
        "   - If results are empty, do not give up. Try a broader query or a different angle.\n"
        "   - If results are partial, search specifically for the missing details.\n\n"
        
        "PHASE 3: SYNTHESIZE\n"
        "1. Review the retrieved snippets.\n"
        "2. Construct a final answer based ONLY on the evidence.\n"
        "3. You must emit the final answer inside a DRAFT_ANSWER block.\n\n"
        
        "Output Format Rules:\n"
        "- Emitting 'PLAN' or 'THOUGHTS' is allowed for your reasoning.\n"
        "- Call tools naturally.\n"
        "- FINAL ANSWER format:\n"
        "=== DRAFT_ANSWER ===\n"
        "<your final answer here>\n"
        "=== END_DRAFT_ANSWER ===\n\n"
        
        f"Global Constraints:\n"
        f"- Use k={top_k} for searches.\n"
        "- Never hallucinate information not found in the documents.\n"
    )


def create_planner_agent(
    *,
    name: str = "planner",
    model: str = "gemini-2.0-flash",
    temperature: float = 0.2,
    max_tokens: int = 2048,
    top_k: int = 5,
    tools: Optional[List[Callable[..., Any]]] = None,
    instruction: Optional[str] = None,
) -> LlmAgent:
    """
    Create a planner LlmAgent.

    Parameters
    ----------
    name:
        Agent name
    model:
        Model name (e.g., "gemini-2.0-flash")
    temperature:
        Sampling temperature for generation
    max_tokens:
        Max output tokens for planner
    top_k:
        Search top-k hint (included in prompt)
    tools:
        Optional explicit tools list; if None, caller should inject later via runner
    instruction:
        Optional custom instruction; if None, a default instruction is used.
    """
    instruction = instruction or _default_instruction(top_k=top_k)



    from .simple_agent import SimpleAgent
    return SimpleAgent(
        name=name,
        model=model,
        instruction=instruction,
        tools=tools or [],  # Caller can inject http_tools.* functions
        generate_content_config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=instruction, # Pass instruction here
        ),
    )
