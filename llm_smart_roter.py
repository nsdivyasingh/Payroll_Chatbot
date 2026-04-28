import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def route_query_with_llm(query, metadata):
    prompt = f"""
Return ONLY JSON.

Schema:
{metadata}

Format:
{{
  "table": "...",
  "columns": ["..."],
  "aggregation": "sum | none",
  "filters": {{
    "month": "...",
    "year": 2026
  }}
}}

Query: {query}
"""

    try:
        res = requests.post(
            OLLAMA_URL,
            json={"model": "phi3", "prompt": prompt, "stream": False},
            timeout=5
        )
        return json.loads(res.json().get("response", ""))
    except:
        return None