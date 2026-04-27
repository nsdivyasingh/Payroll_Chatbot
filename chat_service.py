from __future__ import annotations

from typing import Any

from audit_logger import log_audit, log_pipeline
from faq_engine import retrieve_faq
from guardrails import validate_query_scope
from llm_handler import ask_llm
from query_parser import extract_query_params, normalize_time
from tool_planner import plan_tool, validate_plan
from tools import execute_tool
from metadata.schema_metadata import SCHEMA_METADATA

FALLBACK_MSG = "Couldn't find info, please contact the payroll team."


def _build_recent_context(history: list[dict[str, Any]] | None, limit: int = 3) -> str:
    if not history:
        return ""
    recent = history[-limit:]
    lines = []
    for message in recent:
        role = str(message.get("role", "user")).strip().lower()
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _format_with_llm(
    query: str,
    tool_data: dict[str, Any],
    base_answer: str,
    context: str = "",
) -> str:
    print("=== USING LLM ===")
    context_block = f"Previous context:\n{context}\n\n" if context else ""
    schema_context = str(SCHEMA_METADATA)
    prompt = f"""
You are a payroll assistant.

Here is the database schema and meaning of fields:
{schema_context}

Use this information to better understand payroll terms.
Rewrite the response in a concise, professional tone without changing facts, values, periods, or conclusions.

{context_block}User question:
{query}

Tool data:
{tool_data}

Draft response to polish:
{base_answer}
"""
    print("PROMPT SENT TO LLM:\n", prompt)
    answer = ask_llm(prompt, temperature=0.1).strip()
    return answer or base_answer

def format_currency(amount):
    if amount in (None, ""):
        return "₹0"
    return f"₹{int(float(amount)):,}"


def _basic_template(tool_name: str, tool_data: dict[str, Any]) -> str:
    rows = tool_data.get("data", []) if isinstance(tool_data, dict) else []
    if tool_name == "get_salary" and rows:
        row = rows[0]
        return (
            f"Your salary for {row.get('month')}-{row.get('eyear')} is {row.get('total_netpay')} "
            f"(gross: {row.get('gross_earning')}, deductions: {row.get('gross_deduction')})."
        )
    if tool_name == "get_tax" and rows:
        row = rows[0]
        return (
            f"Your tax liability for {row.get('month')}-{row.get('eyear')} is "
            f"{row.get('total_tax_liability')}."
        )
    if tool_name == "get_lop" and rows:
        return f"You have {len(rows)} LOP entries in the requested period."
    if tool_name == "get_ot" and rows:
        return f"You have {len(rows)} OT/allowance entries in the requested period."
    if tool_name == "get_allowance_breakdown" and isinstance(tool_data, dict):
        allowance_data = tool_data.get("data", {})
        if isinstance(allowance_data, dict) and allowance_data:
            formatted = ", ".join(f"{k}: {v}" for k, v in allowance_data.items())
            return f"Allowance breakdown for the requested period: {formatted}."
    if tool_name == "analyze_salary":
        return _summarize_analyze_result(tool_data)
    return FALLBACK_MSG


def _deterministic_format(
    user_query: str,
    tool_name: str,
    tool_data: dict[str, Any],
    plan: dict[str, Any],
) -> str:
    period = "the requested period"
    params = plan.get("params", {}) if isinstance(plan, dict) else {}
    month = params.get("month")
    year = params.get("year")
    if month and year:
        period = f"{month} {year}"

    if tool_name == "get_allowance_breakdown":
        data = tool_data.get("data", {}) if isinstance(tool_data, dict) else {}
        if not isinstance(data, dict) or not data:
            return FALLBACK_MSG
        return (
            f"For {period}, your allowance components are Other Allowance {format_currency(data.get('other_allowance', 0))}, "
            f"Bonus {format_currency(data.get('bonus', 0))}, Incentive {format_currency(data.get('incentive', 0))}, "
            f"and Night Shift Allowance {format_currency(data.get('night_shift_all', 0))}."
        )

    if tool_name == "analyze_salary":
        payload = tool_data.get("data", {}) if isinstance(tool_data, dict) else {}
        current = payload.get("current_salary", {}).get("data", [])
        previous = payload.get("previous_salary", {}).get("data", [])
        reasons = payload.get("reason_codes", {})
        if not current or not previous:
            return FALLBACK_MSG
        curr = current[0]
        prev = previous[0]
        primary_reason = str(reasons.get("primary_reason", "deductions"))
        reason_text = {
            "tax": "an increase in tax deductions",
            "lop": "loss of pay (LOP) impact",
            "deductions": "an increase in overall deductions",
        }.get(primary_reason, "changes in deductions")
        lop_impact = reasons.get("lop_impact", 0) or 0
        lop_suffix = (
            " There was no LOP impact."
            if float(lop_impact) == 0
            else f" LOP impact was {lop_impact} day(s)."
        )
        change = float(reasons.get("netpay_delta", 0) or 0)
        direction = "decreased" if change < 0 else "increased" if change > 0 else "changed"
        return (
            f"Your salary {direction} in {curr.get('month')} {curr.get('eyear')} compared to "
            f"{prev.get('month')} {prev.get('eyear')} due to {reason_text}.{lop_suffix}"
        )

    rows = tool_data.get("data", []) if isinstance(tool_data, dict) else []
    if tool_name == "get_salary" and rows:
        row = rows[0]
        return (
            f"For {row.get('month')} {row.get('eyear')}, your net salary was {format_currency(row.get('total_netpay'))}, "
            f"with gross earnings of {format_currency(row.get('gross_earning'))} and total deductions of {format_currency(row.get('gross_deduction'))}."
        )
    if tool_name == "get_tax" and rows:
        row = rows[0]
        return f"For {row.get('month')} {row.get('eyear')}, your total tax liability was {format_currency(row.get('total_tax_liability'))}."
    if tool_name == "get_lop" and rows:
        lop_total = sum(float(r.get("lop_days", 0) or 0) for r in rows)
        return f"For {period}, your recorded LOP was {lop_total} day(s)."
    if tool_name == "get_ot" and rows:
        return f"I found {len(rows)} OT/allowance entry(ies) for {period}."
    if tool_name == "get_full_salary_breakdown" and isinstance(tool_data, dict):
        data = tool_data.get("data", {})
        if not isinstance(data, dict) or not data:
            return FALLBACK_MSG
        earnings = data.get("earnings", {})
        deductions = data.get("deductions", {})
        return (
            f"For {period}, your key earnings were Basic {format_currency(earnings.get('Basic', 0))}, "
            f"HRA {format_currency(earnings.get('HRA', 0))}, Bonus {format_currency(earnings.get('Bonus', 0))}, "
            f"and Other Allowance {format_currency(earnings.get('Other Allowance', 0))}. "
            f"Your key deductions were PF {format_currency(deductions.get('PF', 0))}, PT {format_currency(deductions.get('PT', 0))}, "
            f"Income Tax {format_currency(deductions.get('Income Tax', 0))}, and Other deductions {format_currency(deductions.get('Other', 0))}."
        )
    return FALLBACK_MSG


def _safe_format(
    user_query: str,
    tool_name: str,
    tool_data: dict[str, Any],
    plan: dict[str, Any],
    context: str = "",
) -> str:
    deterministic_answer = _deterministic_format(
        user_query=user_query,
        tool_name=tool_name,
        tool_data=tool_data,
        plan=plan,
    )
    if deterministic_answer == FALLBACK_MSG:
        return FALLBACK_MSG
    try:
        polished = _format_with_llm(
            query=user_query,
            tool_data=tool_data,
            base_answer=deterministic_answer,
            context=context,
        )
        return polished or deterministic_answer
    except Exception as exc:
        print(f"LLM polish skipped due to error: {exc}")
        return deterministic_answer


def _smart_analyze_no_data_message(tool_data: dict[str, Any]) -> str:
    return FALLBACK_MSG


def _data_aware_no_data_message(tool_name: str, plan: dict[str, Any]) -> str:
    if tool_name == "get_full_salary_breakdown":
        return FALLBACK_MSG
    return FALLBACK_MSG


def _summarize_analyze_result(tool_data: dict[str, Any]) -> str:
    payload = tool_data.get("data", {})
    current = payload.get("current_salary", {})
    previous = payload.get("previous_salary", {})
    reason_codes = payload.get("reason_codes", {}) if isinstance(payload, dict) else {}

    current_row = (current.get("data") or [None])[0] if isinstance(current, dict) else None
    previous_row = (previous.get("data") or [None])[0] if isinstance(previous, dict) else None
    if not current_row:
        return _smart_analyze_no_data_message(tool_data)

    current_net = current_row.get("total_netpay")
    current_period = f"{current_row.get('month')}-{current_row.get('eyear')}"
    if previous_row:
        previous_net = previous_row.get("total_netpay")
        previous_period = f"{previous_row.get('month')}-{previous_row.get('eyear')}"
        delta = reason_codes.get("netpay_delta")
        if delta is None:
            delta = current_net - previous_net
        direction = "increased" if delta > 0 else "decreased" if delta < 0 else "stayed the same"
        return (
            f"Your net salary is {current_net} for {current_period}, compared to {previous_net} for "
            f"{previous_period} (it {direction} by {abs(delta)}). "
            f"LOP impact days: {reason_codes.get('lop_impact')}. "
            f"Tax delta: {reason_codes.get('tax_delta')}. "
            f"Deduction delta: {reason_codes.get('deduction_delta')}."
        )

    return (
        f"Your current salary for {current_period} is {current_net}. Previous month data is unavailable, "
        "so a full comparison cannot be completed."
    )


def process_user_query(
    user_query: str, employee_id: int, history: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
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
    pipeline_context: dict[str, Any] = {
        "employee_id": employee_id,
        "query": user_query,
        "parsed": parsed,
        "normalized": normalized,
    }
    if not normalized.get("time_valid", True):
        result = {
            "status": "fallback",
            "answer": FALLBACK_MSG,
            "source": "payroll",
        }
        log_pipeline({**pipeline_context, "result": result, "stage": "time_validation"})
        log_audit({**event, **result, "stage": "time_validation"})
        return result
    faq_hit = retrieve_faq(user_query, threshold=0.65)
    if faq_hit:
        result = {
            "status": "ok",
            "answer": faq_hit["answer"],
            "source": "faq",
        }
        log_audit({**event, **result, "stage": "faq"})
        return result

    plan = plan_tool(normalized, employee_id)
    tool_name = plan.get("tool")
    pipeline_context["plan"] = plan
    if tool_name == "fallback" or not validate_plan(plan):
        result = {
            "status": "fallback",
            "answer": FALLBACK_MSG,
            "source": "payroll",
            "tool_call": plan,
        }
        log_pipeline({**pipeline_context, "result": result, "stage": "planner_validation"})
        log_audit({**event, **result, "stage": "planner_validation"})
        return result

    tool_data = execute_tool(tool_name, plan.get("params", {}))
    pipeline_context["tool_name"] = tool_name
    pipeline_context["tool_result"] = tool_data

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
            log_pipeline({**pipeline_context, "result": result, "stage": "tool_execution"})
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
        log_pipeline({**pipeline_context, "result": result, "stage": "tool_execution"})
        log_audit({**event, **result, "stage": "tool_execution"})
        return result

    context = _build_recent_context(history, limit=3)
    answer = _safe_format(
        user_query=user_query,
        tool_name=tool_name,
        tool_data=tool_data,
        plan=plan,
        context=context,
    )
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
    log_pipeline({**pipeline_context, "result": result, "stage": "response"})
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
