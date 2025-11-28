from __future__ import annotations

"""
Backend configuration utilities for the Planner + Judge Multi-Doc Agent.

Responsibilities:
- Load environment variables from .env
- Provide a structured AppConfig for downstream modules
- Optionally export Google-related env vars in a controlled way
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class AppConfig:
    """
    A minimal configuration object for the backend.

    You can freely extend this to include model names, temperature settings,
    feature flags, etc.

    Example additions:
    - model_name: str
    - temperature: float
    - enable_judge: bool
    - retrieval_endpoint: str
    """

    google_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    vertexai_project: Optional[str] = None
    vertexai_location: Optional[str] = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Build an AppConfig from the current environment variables.
        """
        # Load from .env if present
        load_dotenv()

        return cls(
            google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
            vertexai_project=os.getenv("VERTEXAI_PROJECT"),
            vertexai_location=os.getenv("VERTEXAI_LOCATION"),
        )


def export_google_env(api_key: Optional[str]) -> None:
    """
    Explicitly export GOOGLE_API_KEY into the environment.

    This is used by the Google GenAI SDK. Frontends can call this explicitly
    rather than having the SDK mutate env vars in the background.

    Parameters
    ----------
    api_key:
        The Google API key to export. If None or empty, nothing is done.
    """
    if not api_key:
        return
    os.environ["GOOGLE_API_KEY"] = api_key
