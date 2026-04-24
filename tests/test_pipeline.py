from __future__ import annotations

from datetime import datetime

from query_parser import extract_query_params, normalize_time
from tool_planner import plan_tool, validate_plan
from tools import execute_tool, get_salary


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
