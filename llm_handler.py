import json
from typing import Any, Dict

import requests

URL = "http://localhost:11434/api/generate"
MODEL = "phi3"
OLLAMA_URL = URL
OLLAMA_MODEL = MODEL

TOOL_SCHEMAS = [
    {
        "name": "get_salary",
        "description": "Fetch salary/net-pay/earnings/deductions for logged-in employee.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {
                    "type": ["string", "null"],
                    "description": "Month in Mon-YYYY format like Sep-2025",
                }
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_lop",
        "description": "Fetch loss-of-pay dates and lop days for logged-in employee.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {
                    "type": ["string", "null"],
                    "description": "Month in Mon-YYYY format like Sep-2025",
                }
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_tax",
        "description": "Fetch tax liability details for logged-in employee.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {
                    "type": ["string", "null"],
                    "description": "Month in Mon-YYYY format like Sep-2025",
                }
            },
            "required": [],
            "additionalProperties": False,
        },
    },
]


def ask_llm(prompt: str, system: str | None = None, temperature: float = 0.1) -> str:
    return ""


def ask_llm_json(prompt: str, system: str | None = None) -> Dict[str, Any]:
    raw = ask_llm(prompt=prompt, system=system, temperature=0)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start : end + 1])
        raise ValueError(f"LLM did not return valid JSON: {raw}")


def get_tool_schemas() -> list[dict[str, Any]]:
    return TOOL_SCHEMAS