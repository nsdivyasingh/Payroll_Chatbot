from __future__ import annotations


def plan_tool(parsed_query: dict, employee_id: int) -> dict:
    intent = parsed_query.get("intent")
    month = parsed_query.get("month")
    year = parsed_query.get("year")

    base_params = {
        "employee_id": employee_id,
        "month": month,
        "year": year,
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
        return {"tool": "get_full_salary_breakdown", "params": base_params}
    if intent == "salary_explanation":
        return {
            "tool": "analyze_salary",
            "params": {
                **base_params,
                "previous_month": parsed_query.get("previous_month"),
                "previous_year": parsed_query.get("previous_year"),
            },
        }
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
    # All non-fallback tools need month/year for deterministic period targeting.
    if params.get("month") in (None, "") or params.get("year") in (None, ""):
        return False
    if tool == "analyze_salary":
        if params.get("previous_month") in (None, "") or params.get("previous_year") in (None, ""):
            return False
    return True


