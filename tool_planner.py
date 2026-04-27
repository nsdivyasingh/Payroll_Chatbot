from __future__ import annotations

from metadata.field_registry import FieldRegistry


def plan_tool(parsed_query: dict, employee_id: int, user_query: str = "") -> dict:
    intent = parsed_query.get("intent")
    field_request = parsed_query.get("field_request")
    month = parsed_query.get("month")
    year = parsed_query.get("year")

    base_params = {
        "employee_id": employee_id,
        "month": month,
        "year": year,
    }

    q = user_query.lower()
    
    # -----------------------------
    # BASIC SALARY / DEDUCTION QUERIES
    # -----------------------------
    if "salary" in q and "why" not in q:
        return {"tool": "get_salary", "params": base_params}

    if "deduction" in q and "tax" not in q:
        return {"tool": "get_full_salary_breakdown", "params": base_params}

    if "earning" in q:
        return {"tool": "get_full_salary_breakdown", "params": base_params}

    if "pf" in q:
        return {"tool": "get_salary", "params": base_params}

    if "reimbursement" in q:
        return {"tool": "get_ot_reimbursement", "params": base_params}

    query_type_str = parsed_query.get("query_type")
    if query_type_str == "ot_reimbursement":
        return {"tool": "get_ot_reimbursement", "params": base_params}

    if intent == "salary_explanation":
        return {
            "tool": "analyze_salary",
            "params": {
                **base_params,
                "previous_month": parsed_query.get("previous_month"),
                "previous_year": parsed_query.get("previous_year"),
            },
        }

    if field_request:
        field_meta = FieldRegistry.get_field(field_request)
        if field_meta:
            return {
                "tool": "get_field_value",
                "params": {
                    **base_params,
                    "field_key": field_request,
                    "table": field_meta["table"],
                    "column": field_meta["column"],
                },
            }

    # Strict deterministic routing by parsed intent.
    if intent == "salary":
        return {"tool": "get_salary", "params": base_params}
    if intent == "tax":
        return {"tool": "get_tax", "params": base_params}
    if intent == "lop":
        return {"tool": "get_lop", "params": base_params}
    if intent == "ot_query":
        return {"tool": "get_ot", "params": base_params}
    if intent == "allowance_query":
        return {"tool": "get_allowance_breakdown", "params": base_params}
    if intent == "deduction_query":
        if "deduction" in user_query.lower() and "tax" not in user_query.lower():
            return {"tool": "get_salary", "params": base_params}
        return {"tool": "get_full_salary_breakdown", "params": base_params}
    return {"tool": "fallback", "params": {}}


def validate_plan(plan: dict) -> bool:
    tool = plan.get("tool")
    if tool == "fallback":
        return True
    params = plan.get("params", {})
    if not isinstance(params, dict):
        return False
    if params.get("employee_id") in (None, ""):
        return False
    if tool == "get_field_value":
        return bool(params.get("field_key") and params.get("table") and params.get("column"))
    # All non-fallback tools need month/year for deterministic period targeting.
    if params.get("month") in (None, "") or params.get("year") in (None, ""):
        return False
    if tool == "analyze_salary":
        if params.get("previous_month") in (None, "") or params.get("previous_year") in (None, ""):
            return False
    return True


