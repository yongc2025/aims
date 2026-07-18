"""LLM provider factory."""

import os

from .opencode import OpenCodeClient


def get_llm_client():
    provider = os.getenv("LLM_PROVIDER", "opencode").lower()

    if provider == "opencode":
        return OpenCodeClient()

    raise ValueError(f"Unsupported LLM provider: {provider}")
