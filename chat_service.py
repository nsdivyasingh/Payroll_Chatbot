from __future__ import annotations

import os
from typing import Any

from audit_logger import log_audit, log_pipeline
from faq_engine import retrieve_faq
from guardrails import validate_query_scope
from llm_handler import ask_llm
from metadata.field_registry import FieldRegistry
from query_parser import extract_query_params, normalize_time
from tool_planner import plan_tool, validate_plan
from tools import execute_tool
from metadata.schema_metadata import PAYROLL_FIELDS as SCHEMA_METADATA
from metadata.policy_rules import SYSTEM_POLICIES
from query_engine import engine
from sqlalchemy import text
from llm_smart_roter import route_query_with_llm
from safe_query_engine import execute_safe_query

FIELD_DESCRIPTIONS = SCHEMA_METADATA.get("FIELD_DESCRIPTIONS", {})
RELATIONSHIPS = SCHEMA_METADATA.get("RELATIONSHIPS", {})
NORMALIZED_FIELDS = SCHEMA_METADATA.get("NORMALIZED_FIELDS", {})

FALLBACK_MSG = "Couldn't find info, please contact the payroll team."

def _get_latest_month_from_db(employee_id: int) -> tuple[str | None, int | None]:
    query = text("""
        SELECT month, eyear 
        FROM pay_register 
        WHERE employee_id = :emp_id 
        ORDER BY eyear DESC, 
            CASE month 
                WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 WHEN 'Mar' THEN 3 WHEN 'Apr' THEN 4 
                WHEN 'May' THEN 5 WHEN 'Jun' THEN 6 WHEN 'Jul' THEN 7 WHEN 'Aug' THEN 8 
                WHEN 'Sep' THEN 9 WHEN 'Oct' THEN 10 WHEN 'Nov' THEN 11 WHEN 'Dec' THEN 12 ELSE 0 
            END DESC 
        LIMIT 1
    """)
    with engine.connect() as conn:
        row = conn.execute(query, {"emp_id": employee_id}).fetchone()
        if row:
            return row[0], row[1]
    return None, None

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

def normalize_tool_data(data):
    normalized = {}

    for key, value in data.items():
        mapped = False

        for canonical, variants in NORMALIZED_FIELDS.items():
            if key in variants:
                normalized[canonical] = value
                mapped = True
                break

        if not mapped:
            normalized[key] = value

    return normalized

def _format_with_llm(
    query: str,
    tool_data: dict[str, Any],
    base_answer: str,
    context: str = "",
) -> str:
    print("=== USING LLM ===")
    context_block = f"Previous context:\n{context}\n\n" if context else ""
    schema_context = str(SCHEMA_METADATA)
    policy_context = str(SYSTEM_POLICIES)
    prompt = f"""
Follow these system rules strictly:

{policy_context}

You are a payroll assistant.

Field meanings:
{FIELD_DESCRIPTIONS}

Important relationships:
{RELATIONSHIPS}

Use this to explain answers clearly.

User query:
{query}

Tool data:
{tool_data}

Draft response to polish:
{base_answer}
"""
    if os.getenv("DEBUG_LLM_PROMPT", "").lower() == "true":
        safe_prompt = prompt.encode("cp1252", errors="replace").decode("cp1252")
        print("PROMPT SENT TO LLM:\n", safe_prompt)
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
    if tool_name == "get_ot_reimbursement" and rows:
        return f"You have {len(rows)} reimbursement/OT entries in the requested period."
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
        
        total = data.get("total_allowance", 0)
        comps = data.get("components", {})
        return (
            f"For {period}, your total allowance received was {format_currency(total)}. "
            f"This includes Other Allowance {format_currency(comps.get('other_allowance', 0))}, "
            f"Bonus {format_currency(comps.get('bonus', 0))}, Incentive {format_currency(comps.get('incentive', 0))}, "
            f"and Night Shift Allowance {format_currency(comps.get('night_shift_all', 0))}."
        )

    if tool_name == "analyze_salary":
        data = tool_data.get("data", {})
        primary = data.get("primary_reason")
        reasons = data.get("reasons", [])
        response = ""
        if primary:
            response += f"Your salary decreased primarily due to {primary}. "
        response += " ".join(reasons)
        return response.strip()

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
        
    if tool_name == "get_ot_reimbursement" and rows:
        lines = []
        for r in rows:
            amt = format_currency(r.get("paid_amount", 0))
            a_type = str(r.get("allowance_type") or "Reimbursement/OT").title()
            start_date = str(r.get("from_date") or "").split(" ")[0]
            end_date = str(r.get("to_date") or "").split(" ")[0]
            lines.append(f"{a_type} of {amt} (Period: {start_date} to {end_date})")
        return f"For {period}, we identified: " + ", ".join(lines) + "."

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


def _format_field_response(
    field_key: str | None,
    tool_data: dict[str, Any],
    month: str | None,
    year: int | None,
) -> str:
    if not field_key:
        return FALLBACK_MSG
    field_meta = FieldRegistry.get_field(field_key)
    if not field_meta:
        return FALLBACK_MSG
    value = tool_data.get("value")
    if value in (None, ""):
        return FALLBACK_MSG

    if field_meta.get("unit") == "amount":
        formatted_value = format_currency(value)
    else:
        if field_key == "tax_regime":
            value = SYSTEM_POLICIES["tax_regime_mapping"].get(value, value)
        formatted_value = str(value)

    response = field_meta.get("response_template", "{value}").format(
        value=formatted_value,
        month=month or tool_data.get("month") or "the requested period",
        year=year or tool_data.get("year") or "",
    )
    
    if field_key == "tax_regime":
        if "regime" in str(value).lower():
            response = str(value)
        else:
            response = f"Your tax regime is {formatted_value}."
    if tool_data.get("status") == "success_fallback":
        fallback_to = tool_data.get("fallback_to")
        original = tool_data.get("original_request")
        return (
            f"I don't have payroll records for {original} yet. "
            f"Here is the latest available month {fallback_to}. {response}"
        )
    return response


def _safe_format(
    user_query: str,
    tool_name: str,
    tool_data: dict[str, Any],
    plan: dict[str, Any],
    context: str = "",
) -> str:
    if tool_name == "get_field_value":
        params = plan.get("params", {}) if isinstance(plan, dict) else {}
        deterministic_answer = _format_field_response(
            field_key=params.get("field_key"),
            tool_data=tool_data,
            month=params.get("month"),
            year=params.get("year"),
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
    reasons = tool_data.get("data", {}).get("reasons", [])
    if not reasons:
        return "Your salary change does not show significant variation."
    return " ".join(reasons)


def process_user_query(
    user_query: str, employee_id: int, history: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    event = {
        "employee_id": employee_id,
        "query": user_query,
    }

    # ENFORCE SECURITY
    q_lower = user_query.lower()
    if "employee" in q_lower or "emp" in q_lower:
        if str(employee_id) not in user_query:
            result = {"status": "blocked", "answer": SYSTEM_POLICIES["employee_scope"]["response"], "source": "payroll"}
            log_audit({**event, **result, "stage": "security_policy"})
            return result

    # BLOCK PERSONAL DATA
    personal_keywords = ["pf code", "name", "bank", "pan", "ifsc"]
    if any(word in user_query.lower() for word in personal_keywords):
        result = {"status": "blocked", "answer": SYSTEM_POLICIES["personal_data_block"]["response"], "source": "payroll"}
        log_audit({**event, **result, "stage": "security_policy"})
        return result

    allowed, reason = validate_query_scope(user_query)
    if not allowed:
        result = {"status": "blocked", "answer": reason}
        log_audit({**event, **result, "stage": "guardrails"})
        return result

    parsed = extract_query_params(user_query)
    
    # DEFAULT MONTH LOGIC
    if not parsed.get("month"):
        m, y = _get_latest_month_from_db(employee_id)
        if m and y:
            parsed["month"] = m
            parsed["year"] = y

    normalized = normalize_time(parsed)
    print("DEBUG NORMALIZED:", normalized)
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

    # For direct field lookups, bypass FAQ to preserve deterministic field routing.
    faq_hit = None
    if not normalized.get("field_request"):
        faq_hit = retrieve_faq(user_query, threshold=0.65)
    if faq_hit:
        result = {
            "status": "ok",
            "answer": faq_hit["answer"],
            "source": "faq",
        }
        log_audit({**event, **result, "stage": "faq"})
        return result

    plan = plan_tool(normalized, employee_id, user_query)
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

    if isinstance(tool_data, dict) and tool_data.get("status") not in {"success", "success_fallback"}:

        # -----------------------------
        # SAFE FALLBACK ENGINE (NEW)
        # -----------------------------
        plan_llm = route_query_with_llm(user_query, SCHEMA_METADATA)

        if plan_llm:
            fallback_result = execute_safe_query(plan_llm, employee_id)

            if fallback_result:
                result = {
                    "status": "ok",
                    "answer": f"Here is what I found: {fallback_result}",
                    "source": "fallback_engine",
                    "tool_call": plan,
                    "tool_result": fallback_result,
                }
                log_pipeline({**pipeline_context, "result": result, "stage": "fallback_engine"})
                log_audit({**event, **result, "stage": "fallback_engine"})
                return result

        # EXISTING LOGIC CONTINUES (UNCHANGED)
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
            "tool_rows": len(tool_data.get("data") or []),
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
