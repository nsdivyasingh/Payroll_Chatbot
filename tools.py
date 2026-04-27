from __future__ import annotations

from typing import Any

from sqlalchemy import text

from query_engine import engine

ALLOWED_TOOLS = {
    "get_salary",
    "get_lop",
    "get_tax",
    "get_ot",
    "analyze_salary",
    "get_full_salary_breakdown",
}


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
            WHERE employee_id = :emp_id
            AND month = :month
            AND eyear = :year
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


def _first_row(payload: dict[str, Any]) -> dict[str, Any] | None:
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    return rows[0] if rows else None


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
    previous_tax = get_tax(employee_id=employee_id, month=previous_month, year=previous_year)

    current_row = _first_row(current) or {}
    previous_row = _first_row(previous) or {}
    tax_current_row = _first_row(tax) or {}
    tax_previous_row = _first_row(previous_tax) or {}
    lop_rows = lop.get("data", []) if isinstance(lop, dict) else []

    netpay_delta = None
    deduction_delta = None
    tax_delta = None
    if current_row and previous_row:
        netpay_delta = current_row.get("total_netpay", 0) - previous_row.get("total_netpay", 0)
        deduction_delta = current_row.get("gross_deduction", 0) - previous_row.get("gross_deduction", 0)
    if tax_current_row and tax_previous_row:
        tax_delta = tax_current_row.get("total_tax_liability", 0) - tax_previous_row.get("total_tax_liability", 0)
    lop_impact = sum(float(row.get("lop_days", 0) or 0) for row in lop_rows)
    primary_reason = None
    safe_tax_delta = tax_delta if tax_delta is not None else 0
    safe_deduction_delta = deduction_delta if deduction_delta is not None else 0
    if abs(safe_tax_delta) > abs(safe_deduction_delta):
        primary_reason = "tax"
    elif lop_impact > 0:
        primary_reason = "lop"
    else:
        primary_reason = "deductions"

    reason_codes = {
        "netpay_delta": netpay_delta,
        "deduction_delta": deduction_delta,
        "tax_delta": tax_delta,
        "lop_impact": lop_impact,
        "primary_reason": primary_reason,
    }

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
                "previous_tax": previous_tax,
                "reason_codes": reason_codes,
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
            "previous_tax": previous_tax,
            "reason_codes": reason_codes,
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
    try:
        if tool == "get_salary":
            return get_salary(employee_id=employee_id, month=month, year=year)
        if tool == "get_lop":
            return get_lop(employee_id=employee_id, month=month, year=year)
        if tool == "get_tax":
            return get_tax(employee_id=employee_id, month=month, year=year)
        if tool == "get_ot":
            return get_ot(employee_id=employee_id, month=month, year=year)
        if tool == "get_full_salary_breakdown":
            return get_full_salary_breakdown(employee_id=employee_id, month=month, year=year)
        return analyze_salary(
            employee_id=employee_id,
            month=month,
            year=year,
            previous_month=params.get("previous_month"),
            previous_year=params.get("previous_year"),
        )
    except Exception as exc:
        return {
            "tool": tool_name,
            "status": "error",
            "message": str(exc),
            "data": [],
        }


def get_full_salary_breakdown(
    employee_id: int, month: str | None = None, year: int | None = None
) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_full_salary_breakdown", **validation_error}
    if not employee_exists(employee_id):
        return {
            "tool": "get_full_salary_breakdown",
            "status": "no_data",
            "message": "Employee not found",
            "data": {},
        }
    if month is None or year is None:
        return {
            "tool": "get_full_salary_breakdown",
            "status": "error",
            "message": "month and year are required for detailed breakdown",
            "data": {},
        }

    month_year = f"{month}-{year}"
    query = """
    SELECT 
        basic,
        h_r_a,
        bonus,
        other_allowance,
        pt_ded,
        pf_ded,
        income_tax_ded,
        other_ded_2_ded,
        gross_deduction,
        total_netpay
    FROM pay_register_raw
    WHERE employee_id = :emp_id
      AND month = :month_year
    """

    print(f"[QUERY] full_breakdown -> emp={employee_id}, month={month}, year={year}")
    with engine.connect() as conn:
        result = (
            conn.execute(
                text(query),
                {
                    "emp_id": employee_id,
                    "month_year": month_year,
                },
            )
            .mappings()
            .fetchone()
        )
    print("DEBUG PARAMS:", employee_id, month, year)
    print("DEBUG RESULT:", result)

    if not result:
        return {
            "tool": "get_full_salary_breakdown",
            "status": "no_data",
            "message": "No breakdown data found",
            "data": {},
        }

    data = dict(result)
    earnings = {
        "Basic": data.get("basic"),
        "HRA": data.get("h_r_a"),
        "Bonus": data.get("bonus"),
        "Other Allowance": data.get("other_allowance"),
    }
    deductions = {
        "PF": data.get("pf_ded"),
        "PT": data.get("pt_ded"),
        "Income Tax": data.get("income_tax_ded"),
        "Other": data.get("other_ded_2_ded"),
    }
    return {
        "tool": "get_full_salary_breakdown",
        "status": "success",
        "data": {
            "earnings": earnings,
            "deductions": deductions,
            "gross_deduction": data.get("gross_deduction"),
            "netpay": data.get("total_netpay"),
        },
    }   

def get_allowance_breakdown(employee_id, month, year):
    month_year = f"{month}-{year}"

    query = """
    SELECT 
        other_allowance,
        bonus,
        incentive,
        night_shift_all
    FROM pay_register_raw
    WHERE employee_id = :emp_id
      AND month = :month_year
    """

    with engine.connect() as conn:
        result = conn.execute(
            text(query),
            {"emp_id": employee_id, "month_year": month_year}
        ).mappings().fetchone()

    if not result:
        return {"status": "no_data"}
    elif "allowance" in query:
        return {
            "tool": "get_allowance_breakdown",
            "params": {...}
        }

    return {
        "status": "success",
        "data": dict(result)
    }