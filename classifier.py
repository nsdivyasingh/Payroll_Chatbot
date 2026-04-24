from __future__ import annotations

from llm_handler import ask_llm_json


def classify_query(query: str) -> str:
    prompt = f"""
Classify this payroll chatbot user query as exactly one category.

Categories:
- "faq": policy/how-to/general process question
- "payroll": personal financial amount/details question requiring employee data
- "unsupported": unrelated to payroll or abusive/unsafe

Return strict JSON:
{{"category": "faq|payroll|unsupported"}}

Query:
{query}
"""
    try:
        result = ask_llm_json(prompt)
        category = str(result.get("category", "")).lower()
        if category in {"faq", "payroll", "unsupported"}:
            return category
    except Exception:
        pass

    fallback_keywords = ["policy", "regime", "how", "rule", "eligibility", "faq"]
    if any(k in query.lower() for k in fallback_keywords):
        return "faq"
    return "payroll"
