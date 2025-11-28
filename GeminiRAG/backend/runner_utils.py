from __future__ import annotations

"""
Runner utilities for Google ADK / GenAI agents.

This module is UI-agnostic. It provides:
- _ensure_loop(): ensure an asyncio event loop
- _extract_text_from_event(): robust text extraction from streaming events
- _maybe_log_function_call_from_event(): inspect events for function_call parts and log them
- run_agent(): run a message and collect full text output

You can adapt this to your favorite GenAI SDK or event format.
"""

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .logger import Logger, default_logger


def _ensure_loop() -> asyncio.AbstractEventLoop:
    """
    Ensure there is an active asyncio event loop and return it.

    This is helpful in environments where no loop is running yet
    (e.g. some scripts or REPLs).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except (RuntimeError, AssertionError):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def _extract_text_from_event(event: Dict[str, Any]) -> str:
    """
    Extract text content from a streaming event.

    This is dependent on your SDK's event shape. The implementation here is
    intentionally generic and can be adapted.
    """
    # A common pattern: event["delta"] may contain text.
    delta = event.get("delta") or event.get("text_delta")
    if isinstance(delta, str):
        return delta

    # Another pattern: event["message"]["content"] is the complete text.
    msg = event.get("message")
    if isinstance(msg, dict) and isinstance(msg.get("content"), str):
        return msg["content"]

    # Fallback: no text
    return ""


def _maybe_log_function_call_from_event(
    event: Dict[str, Any],
    logger: Logger,
) -> None:
    """
    Inspect an event for function_call / tool_call metadata and log it.

    You can adapt this to your event schema.
    """
    # Example: event["tool_call"] might hold info about a function call.
    tool_call = event.get("tool_call")
    if not tool_call:
        return

    name = tool_call.get("name")
    args = tool_call.get("arguments")
    logger.info("Tool call from event", tool_name=name, tool_args=args)


async def _run_agent_async(
    *,
    events_stream_fn: Callable[..., Awaitable[Any]],
    user_message: str,
    logger: Optional[Logger] = None,
    on_text_delta: Optional[Callable[[str], None]] = None,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    **kwargs: Any,
) -> str:
    """
    Internal async helper that:

    - Calls an events_stream_fn that yields streaming events
    - Extracts text deltas
    - Logs tool calls if present
    - Aggregates final text
    """
    logger = logger or default_logger
    logger.info("Starting run_agent", user_message=user_message)

    final_text_chunks: List[str] = []

    async for event in events_stream_fn(user_message=user_message, **kwargs):
        # Optional external event hook (e.g. UI, logging)
        if on_event is not None:
            on_event(event)

        # Log function/tool calls if present
        _maybe_log_function_call_from_event(event, logger)

        # Extract text delta
        delta_text = _extract_text_from_event(event)
        if delta_text:
            final_text_chunks.append(delta_text)
            if on_text_delta is not None:
                on_text_delta(delta_text)

    final_text = "".join(final_text_chunks)
    logger.info("Completed run_agent", final_text_preview=final_text[:200])
    return final_text


def run_agent(
    *,
    events_stream_fn: Callable[..., Awaitable[Any]],
    user_message: str,
    logger: Optional[Logger] = None,
    on_text_delta: Optional[Callable[[str], None]] = None,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    **kwargs: Any,
) -> str:
    """
    Run an agent that exposes a streaming events function and return the final text.

    Parameters
    ----------
    events_stream_fn:
        Async function that, given user_message and **kwargs, returns an async
        iterator of events.
    user_message:
        The user text to send.
    logger:
        Optional Logger. If None, default_logger is used.
    on_text_delta:
        Optional callback that receives text chunks as they arrive.
    on_event:
        Optional callback that receives raw events.
    kwargs:
        Extra args forwarded to events_stream_fn.

    Returns
    -------
    str
        The final text aggregated from all streaming events.
    """
    loop = _ensure_loop()
    return loop.run_until_complete(
        _run_agent_async(
            events_stream_fn=events_stream_fn,
            user_message=user_message,
            logger=logger,
            on_text_delta=on_text_delta,
            on_event=on_event,
            **kwargs,
        )
    )
