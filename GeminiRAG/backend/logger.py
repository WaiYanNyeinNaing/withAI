from __future__ import annotations

"""
Minimal logging utilities, UI-agnostic.

This is deliberately simple and can be replaced with your preferred logging
framework (structlog, stdlib logging, OpenTelemetry, etc.).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LogEvent:
    """
    A single log event, with optional structured metadata.
    """

    message: str
    level: str = "INFO"
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Logger:
    """
    In-memory logger that stores events in a list.

    This is helpful for:
    - Tests
    - Short-lived CLI runs
    - Sending events to a frontend via a callback
    """

    events: List[LogEvent] = field(default_factory=list)

    def log(self, message: str, level: str = "INFO", **data: Any) -> None:
        event = LogEvent(message=message, level=level, data=data)
        self.events.append(event)
        # You can also print to stdout here if desired:
        # print(f"[{level}] {message} | data={data}")

    def info(self, message: str, **data: Any) -> None:
        self.log(message, level="INFO", **data)

    def warning(self, message: str, **data: Any) -> None:
        self.log(message, level="WARNING", **data)

    def error(self, message: str, **data: Any) -> None:
        self.log(message, level="ERROR", **data)

    def to_dict(self) -> List[Dict[str, Any]]:
        """
        Convert all events to a list of dicts for JSON export or UI usage.
        """
        return [
            {"message": e.message, "level": e.level, "data": e.data}
            for e in self.events
        ]


# A simple module-level default logger you can re-use.
default_logger = Logger()
