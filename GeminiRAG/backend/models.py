from __future__ import annotations

"""
Data models used by the Planner + Judge orchestration.

These are intentionally lightweight and reusable. You can:
- Extend them with additional fields
- Add validation logic
- Serialize them for logging or persistence
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PlannerResult:
    """
    Output of a planner LLM step.
    """

    raw_text: str
    draft_answer: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class JudgeResult:
    """
    Output of a judge LLM step.
    """

    verdict: str  # e.g. "accept", "revise", "needs_more_evidence"
    explanation: str
    requires_more_evidence: bool = False


@dataclass
class OrchestrationRun:
    """
    A single iteration in the planner-judge loop.
    """

    planner_result: PlannerResult
    judge_result: JudgeResult
    step_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationResult:
    """
    Final result of the multi-step orchestration.
    """

    final_answer: str
    verdict: str
    attempts: int
    runs: List[OrchestrationRun] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SynthesizerResult:
    """
    Optional final synthesis pass result.
    """

    raw_text: str
    draft_answer: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
