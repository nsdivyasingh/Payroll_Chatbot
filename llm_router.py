import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = """
You are a payroll query planner.

Return ONLY valid JSON. No text.

Schema:
{
  "intent": "...",
  "tool": "...",
  "params": {
    "month": "...",
    "year": 2026
  }
}

Rules:

- Any query asking:
  "why salary", "salary reduced", "salary less", "reason for salary", "salary deduction reason"
  → intent = salary_explanation

- Queries asking:
  "what are deductions", "show deductions", "deduction breakdown"
  → intent = deduction_query

- allowance / reimbursement → get_ot

- tax → get_tax

- salary summary → get_salary

IMPORTANT:
"reason for salary deduction" is NOT a deduction query.
It is a salary_explanation query.

Special rule:
- If intent = salary_explanation AND month = Jan → use get_full_salary_breakdown

Never leave required fields null.
"""

def llm_plan(query: str):
    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": "phi3",
                "prompt": SYSTEM_PROMPT + f"\nQuery: {query}",
                "stream": False
            },
            timeout=6
        )

        text = res.json().get("response", "").strip()
        return json.loads(text)

    except:
        return None