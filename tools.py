from __future__ import annotations

from typing import Any

from sqlalchemy import text

from query_engine import engine

ALLOWED_TOOLS = {"get_salary", "get_lop", "get_tax", "get_ot", "analyze_salary"}


def _normalize_month_year(month: str | None, year: int | None) -> tuple[str | None, int | None]:
    if month is None:
        return None, year
    clean_month = month.strip()
    if not clean_month:
        return None, year
    if "-" in clean_month and year is None:
        month_part, year_part = clean_month.split("-", 1)
        try:
            return month_part.strip(), int(year_part.strip())
        except ValueError:
            return clean_month, None
    return clean_month, year


def _validate_inputs(employee_id: int, month: str | None, year: int | None) -> dict[str, Any] | None:
    if employee_id is None:
        return {"status": "error", "message": "employee_id is required", "data": []}
    try:
        employee_id = int(employee_id)
    except (TypeError, ValueError):
        return {"status": "error", "message": "employee_id must be an integer", "data": []}
    if employee_id <= 0:
        return {"status": "error", "message": "employee_id must be positive", "data": []}
    if month is not None and not str(month).strip():
        return {"status": "error", "message": "month cannot be empty", "data": []}
    if year is not None:
        try:
            int(year)
        except (TypeError, ValueError):
            return {"status": "error", "message": "year must be an integer", "data": []}
    return None


def employee_exists(employee_id: int) -> bool:
    query = text("SELECT 1 FROM employee_master WHERE employee_id = :emp_id LIMIT 1")
    with engine.connect() as conn:
        row = conn.execute(query, {"emp_id": employee_id}).fetchone()
    return row is not None


def get_salary(employee_id: int, month: str | None = None, year: int | None = None) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_salary", **validation_error}
    if not employee_exists(employee_id):
        return {"tool": "get_salary", "status": "no_data", "message": "Employee not found", "data": []}

    if month and year is not None:
        query = text(
            """
            SELECT month, eyear, total_netpay, gross_earning, gross_deduction
            FROM pay_register
            WHERE employee_id = :emp_id AND month = :month AND eyear = :year
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id, "month": month, "year": year}
    elif month:
        query = text(
            """
            SELECT month, eyear, total_netpay, gross_earning, gross_deduction
            FROM pay_register
            WHERE employee_id = :emp_id AND month = :month
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id, "month": month}
    else:
        query = text(
            """
            SELECT month, eyear, total_netpay, gross_earning, gross_deduction
            FROM pay_register
            WHERE employee_id = :emp_id
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id}

    print(f"[QUERY] salary -> emp={employee_id}, month={month}, year={year}")
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(query, params).fetchall()]
    if not rows:
        return {"tool": "get_salary", "status": "no_data", "message": "No salary data found", "data": []}
    return {"tool": "get_salary", "status": "success", "data": rows}


def get_lop(employee_id: int, month: str | None = None, year: int | None = None) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_lop", **validation_error}
    if not employee_exists(employee_id):
        return {"tool": "get_lop", "status": "no_data", "message": "Employee not found", "data": []}

    if month and year is not None:
        query = text(
            """
            SELECT month, lop_date, lop_days
            FROM lop_data
            WHERE employee_id = :emp_id AND month = :month
            AND EXTRACT(YEAR FROM lop_date) = :year
            ORDER BY lop_date DESC
            LIMIT 15
            """
        )
        params = {"emp_id": employee_id, "month": month, "year": year}
    elif month:
        query = text(
            """
            SELECT month, lop_date, lop_days
            FROM lop_data
            WHERE employee_id = :emp_id AND month = :month
            ORDER BY lop_date DESC
            LIMIT 15
            """
        )
        params = {"emp_id": employee_id, "month": month}
    else:
        query = text(
            """
            SELECT month, lop_date, lop_days
            FROM lop_data
            WHERE employee_id = :emp_id
            ORDER BY lop_date DESC
            LIMIT 15
            """
        )
        params = {"emp_id": employee_id}

    print(f"[QUERY] lop -> emp={employee_id}, month={month}, year={year}")
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(query, params).fetchall()]
    if not rows:
        return {"tool": "get_lop", "status": "no_data", "message": "No LOP data found", "data": []}
    return {"tool": "get_lop", "status": "success", "data": rows}


def get_tax(employee_id: int, month: str | None = None, year: int | None = None) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_tax", **validation_error}
    if not employee_exists(employee_id):
        return {"tool": "get_tax", "status": "no_data", "message": "Employee not found", "data": []}

    if month and year is not None:
        query = text(
            """
            SELECT month, eyear, total_tax_liability
            FROM tax_data
            WHERE employee_id = :emp_id AND month = :month AND eyear = :year
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id, "month": month, "year": year}
    elif month:
        query = text(
            """
            SELECT month, eyear, total_tax_liability
            FROM tax_data
            WHERE employee_id = :emp_id AND month = :month
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id, "month": month}
    else:
        query = text(
            """
            SELECT month, eyear, total_tax_liability
            FROM tax_data
            WHERE employee_id = :emp_id
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id}

    print(f"[QUERY] tax -> emp={employee_id}, month={month}, year={year}")
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(query, params).fetchall()]
    if not rows:
        return {"tool": "get_tax", "status": "no_data", "message": "No tax data found", "data": []}
    return {"tool": "get_tax", "status": "success", "data": rows}


def get_ot(employee_id: int, month: str | None = None, year: int | None = None) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_ot", **validation_error}
    if not employee_exists(employee_id):
        return {"tool": "get_ot", "status": "no_data", "message": "Employee not found", "data": []}

    if month and year is not None:
        query = text(
            """
            SELECT month, allowance_type, from_date, to_date, component_in_pay_slip, paid_amount
            FROM ot_data
            WHERE employee_id = :emp_id AND month = :month
            AND EXTRACT(YEAR FROM from_date) = :year
            ORDER BY from_date DESC
            LIMIT 20
            """
        )
        params = {"emp_id": employee_id, "month": month, "year": year}
    elif month:
        query = text(
            """
            SELECT month, allowance_type, from_date, to_date, component_in_pay_slip, paid_amount
            FROM ot_data
            WHERE employee_id = :emp_id AND month = :month
            ORDER BY from_date DESC
            LIMIT 20
            """
        )
        params = {"emp_id": employee_id, "month": month}
    else:
        query = text(
            """
            SELECT month, allowance_type, from_date, to_date, component_in_pay_slip, paid_amount
            FROM ot_data
            WHERE employee_id = :emp_id
            ORDER BY from_date DESC
            LIMIT 20
            """
        )
        params = {"emp_id": employee_id}

    print(f"[QUERY] ot -> emp={employee_id}, month={month}, year={year}")
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(query, params).fetchall()]
    if not rows:
        return {"tool": "get_ot", "status": "no_data", "message": "No OT/allowance data found", "data": []}
    return {"tool": "get_ot", "status": "success", "data": rows}


def analyze_salary(
    employee_id: int,
    month: str | None,
    year: int | None,
    previous_month: str | None,
    previous_year: int | None,
) -> dict[str, Any]:
    print(
        f"[QUERY] analyze_salary -> emp={employee_id}, month={month}, year={year}, "
        f"prev_month={previous_month}, prev_year={previous_year}"
    )
    current = get_salary(employee_id=employee_id, month=month, year=year)
    previous = get_salary(employee_id=employee_id, month=previous_month, year=previous_year)
    lop = get_lop(employee_id=employee_id, month=month, year=year)
    tax = get_tax(employee_id=employee_id, month=month, year=year)

    if current.get("status") != "success":
        return {
            "tool": "analyze_salary",
            "status": "no_data",
            "message": "No salary data found for analysis",
            "data": {
                "current_salary": current,
                "previous_salary": previous,
                "lop": lop,
                "tax": tax,
            },
        }

    return {
        "tool": "analyze_salary",
        "status": "success",
        "data": {
            "current_salary": current,
            "previous_salary": previous,
            "lop": lop,
            "tax": tax,
        },
    }


def execute_tool(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
    tool = str(tool_name).strip().lower()
    if tool not in ALLOWED_TOOLS:
        return {
            "tool": tool_name,
            "status": "error",
            "message": f"Unsupported tool '{tool_name}'",
            "data": [],
        }

    employee_id = params.get("employee_id")
    month = params.get("month")
    year = params.get("year")
    if tool == "get_salary":
        return get_salary(employee_id=employee_id, month=month, year=year)
    if tool == "get_lop":
        return get_lop(employee_id=employee_id, month=month, year=year)
    if tool == "get_tax":
        return get_tax(employee_id=employee_id, month=month, year=year)
    if tool == "get_ot":
        return get_ot(employee_id=employee_id, month=month, year=year)
    return analyze_salary(
        employee_id=employee_id,
        month=month,
        year=year,
        previous_month=params.get("previous_month"),
        previous_year=params.get("previous_year"),
    )
