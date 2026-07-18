"""Extract structured JSON from LLM responses."""

import json
import re


def extract_json(text: str) -> dict:
    """Extract first JSON object from model output."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group(0))
