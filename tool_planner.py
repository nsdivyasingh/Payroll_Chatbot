from __future__ import annotations

from llm_handler import ask_llm_json, get_tool_schemas

ALLOWED_TOOLS = {"get_salary", "get_lop", "get_tax"}


def choose_tool_call(query: str, normalized_month: str | None = None) -> dict:
    q = query.lower()

    # Deterministic first-pass mapping for stability.
    if any(k in q for k in ["lop", "loss of pay"]):
        return {
            "tool": "get_lop",
            "month": normalized_month,
            "reason": "deterministic_lop_keyword",
            "confidence": "high",
        }
    if any(k in q for k in ["tax", "regime", "tds"]):
        return {
            "tool": "get_tax",
            "month": normalized_month,
            "reason": "deterministic_tax_keyword",
            "confidence": "high",
        }
    if any(
        k in q
        for k in [
            "salary",
            "net pay",
            "deduction",
            "gross",
            "allowance",
            "reimbursement",
            "pf",
            "pt",
        ]
    ):
        return {
            "tool": "get_salary",
            "month": normalized_month,
            "reason": "deterministic_salary_keyword",
            "confidence": "high",
        }

    tool_schemas = get_tool_schemas()
    prompt = f"""
You are a payroll tool planner.
Choose exactly one tool for the query using this tool schema:
{tool_schemas}

Month extraction:
- Use normalized month if provided.
- If no month is available, month should be null.

Return strict JSON only:
{{
  "tool": "get_salary|get_lop|get_tax|none",
  "month": "Mon-YYYY or null",
  "reason": "short reason",
  "confidence": "high|medium|low"
}}

Query:
{query}

Deterministic normalized month:
{normalized_month}
"""
    try:
        result = ask_llm_json(prompt)
    except Exception:
        return {
            "tool": "none",
            "month": normalized_month,
            "reason": "planner_failed",
            "confidence": "low",
        }

    tool = str(result.get("tool", "none")).strip().lower()
    month = result.get("month")
    if tool not in ALLOWED_TOOLS:
        tool = "none"
    if not isinstance(month, str) or not month.strip():
        month = normalized_month
    return {
        "tool": tool,
        "month": month,
        "reason": str(result.get("reason", "")),
        "confidence": str(result.get("confidence", "low")).lower(),
    }
