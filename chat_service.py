from __future__ import annotations

from typing import Any

from audit_logger import log_audit
from classifier import classify_query
from faq_engine import retrieve_faq
from guardrails import validate_query_scope
from llm_handler import ask_llm
from normalizer import normalize_query_dates
from tool_planner import choose_tool_call
from tools import get_lop, get_salary, get_tax

FALLBACK_MSG = "I could not confidently answer that. Please contact the payroll team."


def _format_with_llm(user_query: str, tool_name: str, tool_data: Any) -> str:
    answer_prompt = f"""
You are a payroll assistant.
Respond only from the tool data.
If answer is not fully supported by tool data, reply exactly:
{FALLBACK_MSG}

User query:
{user_query}

Tool:
{tool_name}

Tool data:
{tool_data}
"""
    answer = ask_llm(answer_prompt, temperature=0.1).strip()
    return answer or FALLBACK_MSG


def process_user_query(user_query: str, employee_id: int) -> dict[str, Any]:
    event = {
        "employee_id": employee_id,
        "query": user_query,
    }

    allowed, reason = validate_query_scope(user_query)
    if not allowed:
        result = {"status": "blocked", "answer": reason}
        log_audit({**event, **result, "stage": "guardrails"})
        return result

    normalized = normalize_query_dates(user_query)
    category = classify_query(user_query)

    if category == "unsupported":
        result = {"status": "fallback", "answer": FALLBACK_MSG}
        log_audit(
            {
                **event,
                **result,
                "stage": "classifier",
                "category": category,
                "normalized_month": normalized.target_month,
            }
        )
        return result

    if category == "faq":
        faq_hit = retrieve_faq(user_query, threshold=0.5)
        if faq_hit:
            result = {
                "status": "ok",
                "answer": faq_hit["answer"],
                "source": "faq",
            }
        else:
            result = {"status": "fallback", "answer": FALLBACK_MSG, "source": "faq"}
        log_audit(
            {
                **event,
                **result,
                "stage": "faq",
                "category": category,
                "normalized_month": normalized.target_month,
            }
        )
        return result

    tool_call = choose_tool_call(user_query, normalized_month=normalized.target_month)
    tool_name = tool_call.get("tool")
    month = tool_call.get("month")
    confidence = tool_call.get("confidence", "low")

    if confidence == "low":
        result = {
            "status": "fallback",
            "answer": FALLBACK_MSG,
            "source": "payroll",
            "tool_call": tool_call,
        }
        log_audit({**event, **result, "stage": "planner_confidence"})
        return result

    if tool_name == "get_salary":
        if normalized.comparison_month and month is None:
            tool_data = {
                "latest_salary_rows": get_salary(employee_id=employee_id, month=None),
                "comparison_month": normalized.comparison_month,
                "comparison_month_rows": get_salary(
                    employee_id=employee_id, month=normalized.comparison_month
                ),
            }
        else:
            tool_data = get_salary(employee_id=employee_id, month=month)
    elif tool_name == "get_lop":
        tool_data = get_lop(employee_id=employee_id, month=month)
    elif tool_name == "get_tax":
        tool_data = get_tax(employee_id=employee_id, month=month)
    else:
        result = {
            "status": "fallback",
            "answer": FALLBACK_MSG,
            "source": "payroll",
            "tool_call": tool_call,
        }
        log_audit({**event, **result, "stage": "planner"})
        return result

    is_empty = not tool_data
    if isinstance(tool_data, dict):
        is_empty = not any(tool_data.values())
    if is_empty:
        result = {
            "status": "fallback",
            "answer": FALLBACK_MSG,
            "source": "payroll",
            "tool_call": tool_call,
            "tool_rows": 0,
        }
        log_audit({**event, **result, "stage": "tool_execution"})
        return result

    answer = _format_with_llm(user_query=user_query, tool_name=tool_name, tool_data=tool_data)
    if answer.strip() == FALLBACK_MSG:
        status = "fallback"
    else:
        status = "ok"
    result = {
        "status": status,
        "answer": answer,
        "source": "payroll",
        "tool_call": tool_call,
        "tool_rows": len(tool_data) if isinstance(tool_data, list) else 1,
    }
    log_audit(
        {
            **event,
            **result,
            "stage": "response",
            "normalized_month": normalized.target_month,
            "comparison_month": normalized.comparison_month,
        }
    )
    return result
