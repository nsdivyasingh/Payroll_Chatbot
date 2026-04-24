from __future__ import annotations

from typing import Any

from audit_logger import log_audit
from classifier import classify_query
from faq_engine import retrieve_faq
from guardrails import validate_query_scope
from llm_handler import ask_llm
from query_parser import extract_query_params, normalize_time
from tool_planner import plan_tool, validate_plan
from tools import execute_tool

FALLBACK_MSG = "I could not confidently answer that. Please contact the payroll team."


def _format_with_llm(user_query: str, tool_name: str, tool_data: Any) -> str:
    if tool_name == "analyze_salary":
        answer_prompt = f"""
You are a payroll assistant.
Use ONLY the provided tool data.
Explain clearly in exactly 3 sections:
1. Salary change summary
2. Key contributing factors (LOP, tax, deductions)
3. Final conclusion

If the data does not support a reliable explanation, reply exactly:
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


def _smart_analyze_no_data_message(tool_data: dict[str, Any]) -> str:
    payload = tool_data.get("data", {}) if isinstance(tool_data, dict) else {}
    current = payload.get("current_salary", {})
    previous = payload.get("previous_salary", {})
    current_ok = isinstance(current, dict) and current.get("status") == "success"
    previous_ok = isinstance(previous, dict) and previous.get("status") == "success"

    if current_ok and not previous_ok:
        current_rows = current.get("data", [])
        if current_rows:
            row = current_rows[0]
            return (
                f"Your current salary for {row.get('month')}-{row.get('eyear')} is "
                f"{row.get('total_netpay')}. Previous month data is unavailable, so "
                "a full comparison cannot be completed."
            )
    return "Salary data for the selected period is not available yet. Please check back later or contact payroll."


def _data_aware_no_data_message(tool_name: str, plan: dict[str, Any]) -> str:
    params = plan.get("params", {})
    month = params.get("month")
    year = params.get("year")
    period = f"{month} {year}" if month and year else "the requested period"
    if tool_name == "get_salary":
        return f"No salary data available for {period}."
    if tool_name == "get_tax":
        return f"No tax data available for {period}."
    if tool_name == "get_lop":
        return f"No LOP data available for {period}."
    if tool_name == "get_ot":
        return f"No OT/allowance data available for {period}."
    return FALLBACK_MSG


def _summarize_analyze_result(tool_data: dict[str, Any]) -> str:
    payload = tool_data.get("data", {})
    current = payload.get("current_salary", {})
    previous = payload.get("previous_salary", {})
    lop = payload.get("lop", {})
    tax = payload.get("tax", {})

    current_row = (current.get("data") or [None])[0] if isinstance(current, dict) else None
    previous_row = (previous.get("data") or [None])[0] if isinstance(previous, dict) else None
    if not current_row:
        return _smart_analyze_no_data_message(tool_data)

    current_net = current_row.get("total_netpay")
    current_period = f"{current_row.get('month')}-{current_row.get('eyear')}"
    if previous_row:
        previous_net = previous_row.get("total_netpay")
        previous_period = f"{previous_row.get('month')}-{previous_row.get('eyear')}"
        delta = current_net - previous_net
        direction = "increased" if delta > 0 else "decreased" if delta < 0 else "stayed the same"
        return (
            f"Your net salary is {current_net} for {current_period}, compared to {previous_net} for "
            f"{previous_period} (it {direction} by {abs(delta)}). "
            f"LOP entries found: {len(lop.get('data', [])) if isinstance(lop, dict) else 0}. "
            f"Tax rows found: {len(tax.get('data', [])) if isinstance(tax, dict) else 0}."
        )

    return (
        f"Your current salary for {current_period} is {current_net}. Previous month data is unavailable, "
        "so a full comparison cannot be completed."
    )


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

    parsed = extract_query_params(user_query)
    normalized = normalize_time(parsed)
    if not normalized.get("time_valid", True):
        result = {
            "status": "fallback",
            "answer": normalized.get("time_error", FALLBACK_MSG),
            "source": "payroll",
        }
        log_audit({**event, **result, "stage": "time_validation"})
        return result
    category = classify_query(user_query)

    if category == "unsupported":
        result = {"status": "fallback", "answer": FALLBACK_MSG}
        log_audit(
            {
                **event,
                **result,
                "stage": "classifier",
                "category": category,
                "normalized_month": normalized.get("month_year"),
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
                "normalized_month": normalized.get("month_year"),
            }
        )
        return result

    plan = plan_tool(normalized, employee_id)
    tool_name = plan.get("tool")
    if tool_name == "fallback" or not validate_plan(plan):
        result = {
            "status": "fallback",
            "answer": FALLBACK_MSG,
            "source": "payroll",
            "tool_call": plan,
        }
        log_audit({**event, **result, "stage": "planner_validation"})
        return result

    tool_data = execute_tool(tool_name, plan.get("params", {}))

    if isinstance(tool_data, dict) and tool_data.get("status") != "success":
        if tool_name == "analyze_salary":
            result = {
                "status": "fallback",
                "answer": _smart_analyze_no_data_message(tool_data),
                "source": "payroll",
                "tool_call": plan,
                "tool_rows": len(tool_data.get("data", [])),
                "tool_result": tool_data,
            }
            log_audit({**event, **result, "stage": "tool_execution"})
            return result
        result = {
            "status": "fallback",
            "answer": _data_aware_no_data_message(tool_name, plan),
            "source": "payroll",
            "tool_call": plan,
            "tool_rows": len(tool_data.get("data", [])),
            "tool_result": tool_data,
        }
        log_audit({**event, **result, "stage": "tool_execution"})
        return result

    if tool_name == "analyze_salary":
        answer = _summarize_analyze_result(tool_data)
    else:
        answer = str(tool_data)
    if answer.strip() == FALLBACK_MSG:
        status = "fallback"
    else:
        status = "ok"
    result = {
        "status": status,
        "answer": answer,
        "source": "payroll",
        "tool_call": plan,
        "tool_rows": len(tool_data.get("data", [])) if isinstance(tool_data, dict) else 0,
        "tool_result": tool_data,
    }
    log_audit(
        {
            **event,
            **result,
            "stage": "response",
            "normalized_month": normalized.get("month_year"),
            "comparison_month": (
                f"{normalized.get('previous_month')}-{normalized.get('previous_year')}"
                if normalized.get("previous_month") and normalized.get("previous_year")
                else None
            ),
        }
    )
    return result
