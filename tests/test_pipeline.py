from __future__ import annotations

from datetime import datetime

import chat_service
from metadata.field_registry import FieldRegistry
from guardrails import validate_query_scope
from query_parser import extract_query_params, normalize_time
from tool_planner import plan_tool, validate_plan
from tools import analyze_salary, execute_tool, get_salary


FIXED_NOW = datetime(2026, 4, 24)


def test_parser_salary_jan() -> None:
    parsed = extract_query_params("salary in jan")
    normalized = normalize_time(parsed, now=FIXED_NOW)

    assert normalized["month"] == "Jan"
    assert normalized["year"] == 2026


def test_last_month() -> None:
    parsed = extract_query_params("salary last month")
    normalized = normalize_time(parsed, now=FIXED_NOW)

    assert normalized["month"] == "Mar"
    assert normalized["year"] == 2026


def test_plan_salary() -> None:
    plan = plan_tool(
        {
            "intent": "salary",
            "month": "Jan",
            "year": 2026,
        },
        employee_id=3,
    )

    assert plan["tool"] == "get_salary"
    assert plan["params"]["employee_id"] == 3


def test_plan_explanation() -> None:
    plan = plan_tool(
        {
            "intent": "salary_explanation",
            "month": "Apr",
            "year": 2026,
            "previous_month": "Mar",
            "previous_year": 2026,
        },
        employee_id=3,
    )

    assert plan["tool"] == "analyze_salary"
    assert plan["params"]["previous_month"] == "Mar"


def test_get_salary_contract() -> None:
    result = get_salary(3, "Jan", 2026)

    assert result["status"] in ["success", "no_data"]
    assert "tool" in result
    assert result["tool"] == "get_salary"


def test_fallback_on_invalid_plan() -> None:
    invalid_plan = {"tool": "get_salary", "params": {"employee_id": 3, "month": "Jan"}}
    assert validate_plan(invalid_plan) is False

    fallback_plan = {"tool": "fallback", "params": {}}
    assert validate_plan(fallback_plan) is True


def test_full_pipeline_salary() -> None:
    query = "salary in jan"

    parsed = extract_query_params(query)
    normalized = normalize_time(parsed, now=FIXED_NOW)
    plan = plan_tool(normalized, employee_id=3)

    assert validate_plan(plan) is True
    result = execute_tool(plan["tool"], plan["params"])

    assert plan["tool"] == "get_salary"
    assert result["status"] in ["success", "no_data"]


def test_future_date_rejected() -> None:
    parsed = extract_query_params("salary in 2030")
    normalized = normalize_time(parsed, now=FIXED_NOW)
    assert normalized["time_valid"] is False
    assert "future dates" in normalized["time_error"]


def test_guardrail_blocks_cross_employee_query() -> None:
    allowed, message = validate_query_scope("salary of employee 5")
    assert allowed is False
    assert message == "I cannot provide details regarding other employees."


def test_no_data_message_is_data_aware() -> None:
    plan = {"params": {"month": "Mar", "year": 2026}}
    msg = chat_service._data_aware_no_data_message("get_salary", plan)
    assert msg == "Couldn't find info, please contact the payroll team."


def test_partial_reasoning_message_when_previous_missing() -> None:
    tool_data = {
        "data": {
            "current_salary": {
                "status": "success",
                "data": [{"month": "Feb", "eyear": 2026, "total_netpay": 148759}],
            },
            "previous_salary": {"status": "no_data", "data": []},
            "lop": {"status": "no_data", "data": []},
            "tax": {"status": "success", "data": [{"month": "Feb", "eyear": 2026}]},
        }
    }
    msg = chat_service._summarize_analyze_result(tool_data)
    assert "Previous month data is unavailable" in msg


def test_safe_format_falls_back_when_llm_fails(monkeypatch) -> None:
    def raise_llm(*args, **kwargs):
        raise RuntimeError("llm down")

    monkeypatch.setattr(chat_service, "ask_llm", raise_llm)
    msg = chat_service._safe_format(
        "salary in jan",
        "get_salary",
        {
            "data": [
                {
                    "month": "Jan",
                    "eyear": 2026,
                    "total_netpay": 148760,
                    "gross_earning": 190998,
                    "gross_deduction": 42238,
                }
            ]
        },
        {"params": {"month": "Jan", "year": 2026}},
    )
    assert "For Jan 2026, your net salary was" in msg


def test_plan_allowance_routes_correctly() -> None:
    plan = plan_tool(
        {
            "intent": "allowance_query",
            "month": "Feb",
            "year": 2026,
        },
        employee_id=15,
    )
    assert plan["tool"] == "get_allowance_breakdown"


def test_parser_salary_explanation_intent() -> None:
    parsed = extract_query_params("why is my salary less in feb 2026")
    assert parsed["intent"] == "salary_explanation"


def test_field_registry_maps_hra() -> None:
    assert FieldRegistry.find_field("what is my hra for jun 2025") == "hra"


def test_planner_uses_get_field_value_for_field_request() -> None:
    plan = plan_tool(
        {
            "intent": "field_earning",
            "field_request": "hra",
            "month": "Jun",
            "year": 2025,
        },
        employee_id=15,
    )
    assert plan["tool"] == "get_field_value"
    assert plan["params"]["column"] == "h_r_a"


def test_reason_codes_present() -> None:
    result = analyze_salary(
        employee_id=3,
        month="Feb",
        year=2026,
        previous_month="Jan",
        previous_year=2026,
    )
    assert "reason_codes" in result["data"]
    assert result["data"]["reason_codes"]["primary_reason"] in {"tax", "lop", "deductions"}
