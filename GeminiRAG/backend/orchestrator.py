from __future__ import annotations

"""
Planner + Judge orchestration logic.

This module is UI-agnostic and defines how to:

- Call a planner LLM (via a callable you inject)
- Execute tool calls (also injected)
- Call a judge LLM
- Iterate until a final answer is accepted or a limit is reached
"""

import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .logger import Logger, default_logger
from .models import (
    JudgeResult,
    OrchestrationResult,
    OrchestrationRun,
    PlannerResult,
    SynthesizerResult,
)


# Type aliases for injected callables

PlannerCallable = Callable[..., PlannerResult]
JudgeCallable = Callable[..., JudgeResult]
ToolExecutor = Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]
SynthesizerCallable = Callable[..., SynthesizerResult]


def _extract_draft_answer(raw_text: str) -> str:
    """
    Extract a draft answer from raw LLM text.

    You can adapt this to your preferred prompt format. This implementation
    looks for markers like "=== DRAFT_ANSWER ===" and falls back to
    the entire raw text if no markers are found.
    """
    marker_start = "=== DRAFT_ANSWER ==="
    marker_end = "=== END_DRAFT_ANSWER ==="

    if marker_start in raw_text and marker_end in raw_text:
        start_idx = raw_text.index(marker_start) + len(marker_start)
        end_idx = raw_text.index(marker_end, start_idx)
        chunk = raw_text[start_idx:end_idx]
        return chunk.strip()

    # Fallback: try to find a line starting with "DRAFT_ANSWER:"
    for line in raw_text.splitlines():
        if line.strip().upper().startswith("DRAFT_ANSWER"):
            parts = line.split(":", 1)
            if len(parts) == 2:
                return parts[1].strip()

    # Final fallback: return everything
    return raw_text.strip()


def run_planner_once(
    planner: PlannerCallable,
    user_query: str,
    previous_evidence: Optional[List[Dict[str, Any]]] = None,
    logger: Optional[Logger] = None,
    **kwargs: Any,
) -> PlannerResult:
    """
    Run a single planner step.

    Parameters
    ----------
    planner:
        A callable that implements the planner LLM logic and returns PlannerResult.
    user_query:
        The original user query.
    previous_evidence:
        Evidence from previous steps, if any.
    logger:
        Optional logger; if None, uses default_logger.
    kwargs:
        Extra arguments passed to the planner callable.
    """
    logger = logger or default_logger
    logger.info("Running planner", user_query=user_query)

    # Call the planner
    result = planner(
        user_query=user_query,
        previous_evidence=previous_evidence or [],
        **kwargs,
    )

    # If the planner didn't populate draft_answer, try to extract from raw_text.
    if not result.draft_answer:
        result.draft_answer = _extract_draft_answer(result.raw_text)

    logger.info(
        "Planner finished",
        draft_answer_preview=result.draft_answer[:200],
        num_tool_calls=len(result.tool_calls),
    )
    return result


def run_judge(
    judge: JudgeCallable,
    planner_result: PlannerResult,
    logger: Optional[Logger] = None,
    **kwargs: Any,
) -> JudgeResult:
    """
    Run a judge step on the planner result.
    """
    logger = logger or default_logger
    logger.info("Running judge")

    judge_result = judge(
        planner_result=planner_result,
        **kwargs,
    )

    logger.info(
        "Judge finished",
        verdict=judge_result.verdict,
        requires_more_evidence=judge_result.requires_more_evidence,
    )
    return judge_result


def orchestrate_planner_judge(
    planner: PlannerCallable,
    judge: JudgeCallable,
    tool_executor: Optional[ToolExecutor],
    user_query: str,
    *,
    max_attempts: int = 3,
    logger: Optional[Logger] = None,
    synthesizer: Optional[SynthesizerCallable] = None,
    on_judge_result: Optional[Callable[[JudgeResult], None]] = None,
    **kwargs: Any,
) -> OrchestrationResult:
    """
    End-to-end orchestration of the planner + judge loop.

    Parameters
    ----------
    planner:
        Callable implementing planner logic (returns PlannerResult).
    judge:
        Callable implementing judge logic (returns JudgeResult).
    tool_executor:
        Callable that executes a list of tool calls and returns evidence. May be None if tools
        are disabled.
    user_query:
        User query or question to answer.
    max_attempts:
        Maximum planner-judge iterations before giving up.
    logger:
        Optional logger; if None, uses default_logger.
    synthesizer:
        Optional callable for a final synthesis pass (e.g. for style/formatting).
    kwargs:
        Extra keyword args forwarded to planner/judge as needed.

    Returns
    -------
    OrchestrationResult
    """
    logger = logger or default_logger
    start_time = time.time()
    runs: List[OrchestrationRun] = []

    evidence: List[Dict[str, Any]] = []

    last_judge_result: Optional[JudgeResult] = None

    for attempt in range(1, max_attempts + 1):
        logger.info("Orchestration attempt", attempt=attempt)

        # 1) Planner step
        is_last_attempt = (attempt == max_attempts)
        remaining_attempts = max_attempts - attempt
        
        planner_result = run_planner_once(
            planner=planner,
            user_query=user_query,
            previous_evidence=evidence,
            logger=logger,
            last_judge_result=last_judge_result,
            is_last_attempt=is_last_attempt,
            remaining_attempts=remaining_attempts,
            **kwargs,
        )

        # 2) Execute tools if needed
        if tool_executor and planner_result.tool_calls:
            logger.info(
                "Executing tools",
                num_tool_calls=len(planner_result.tool_calls),
            )
            new_evidence = tool_executor(planner_result.tool_calls)
            planner_result.evidence.extend(new_evidence)
            evidence.extend(new_evidence)
        else:
            logger.info("No tools to execute for this planner step")

        # 3) Synthesize Answer (if tools were called or just generally)
        # We ALWAYS try to synthesize if a synthesizer is provided, especially after tools.
        if synthesizer:
            logger.info("Running synthesizer")
            synth_result = synthesizer(
                user_query=user_query,
                draft_answer=planner_result.draft_answer, # Might be empty if tools were called
                evidence=evidence,
                runs=runs,
            )
            # Update the planner result with the synthesized answer for the judge
            planner_result.draft_answer = synth_result.draft_answer

        # 4) Judge step
        # We NO LONGER skip the judge if tools were called.
        # The judge evaluates the (synthesized) answer against the evidence.
        judge_result = run_judge(
            judge=judge,
            planner_result=planner_result,
            logger=logger,
            **kwargs,
        )
        
        last_judge_result = judge_result

        if on_judge_result:
            on_judge_result(judge_result)

        runs.append(
            OrchestrationRun(
                planner_result=planner_result,
                judge_result=judge_result,
                step_index=attempt,
            )
        )

        if not judge_result.requires_more_evidence and judge_result.verdict == "accept":
            logger.info("Judge accepted the answer")
            break

        logger.info(
            "Judge requested another iteration",
            requires_more_evidence=judge_result.requires_more_evidence,
        )

    # Decide final answer
    if runs:
        last_planner_result = runs[-1].planner_result
        final_answer = last_planner_result.draft_answer
        verdict = runs[-1].judge_result.verdict
    else:
        # No runs happened (unlikely); return a generic fallback.
        final_answer = "No answer generated."
        verdict = "no_runs"

    elapsed = time.time() - start_time

    return OrchestrationResult(
        final_answer=final_answer,
        verdict=verdict,
        attempts=len(runs),
        runs=runs,
        elapsed_seconds=elapsed,
        metadata={"user_query": user_query},
    )
