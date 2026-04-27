from __future__ import annotations

from typing import Any

from sqlalchemy import text

from query_engine import engine
from metadata.field_registry import FieldRegistry

ALLOWED_TOOLS = {
    "get_salary",
    "get_lop",
    "get_tax",
    "get_ot",
    "get_ot_reimbursement",
    "analyze_salary",
    "get_full_salary_breakdown",
    "get_allowance_breakdown",
    "get_field_value",
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
            SELECT month, eyear, total_netpay, gross_earning, gross_deduction, income_tax_ded
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
            SELECT month, eyear, total_netpay, gross_earning, gross_deduction, income_tax_ded
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
            SELECT month, eyear, total_netpay, gross_earning, gross_deduction, income_tax_ded
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

def get_ot_reimbursement(employee_id: int, month: str | None = None, year: int | None = None) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_ot_reimbursement", **validation_error}
    if not employee_exists(employee_id):
        return {"tool": "get_ot_reimbursement", "status": "no_data", "message": "Employee not found", "data": []}

    query_str = """
        SELECT month, allowance_type, from_date, to_date, paid_amount
        FROM ot_data
        WHERE employee_id = :emp_id
    """
    params = {"emp_id": employee_id}
    
    if month and year is not None:
        query_str += " AND month = :month AND EXTRACT(YEAR FROM from_date) = :year "
        params.update({"month": month, "year": year})
    elif month:
        query_str += " AND month = :month "
        params.update({"month": month})
    
    query_str += " ORDER BY from_date DESC LIMIT 20 "

    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(text(query_str), params).fetchall()]
    
    if not rows:
        return {"tool": "get_ot_reimbursement", "status": "no_data", "message": "No reimbursement data found", "data": []}

    return {"tool": "get_ot_reimbursement", "status": "success", "data": rows}

def _first_row(payload: dict[str, Any]) -> dict[str, Any] | None:
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    return rows[0] if rows else None


def analyze_salary(employee_id, month, year, previous_month, previous_year):

    current = get_salary(employee_id, month, year)
    previous = get_salary(employee_id, previous_month, previous_year)

    tax_current = get_tax(employee_id, month, year)
    tax_previous = get_tax(employee_id, previous_month, previous_year)

    lop_current = get_lop(employee_id, month, year)

    if current.get("status") != "success":
        reasons = []
        if lop_current.get("status") == "success":
            lop_days = sum(float(row.get("lop_days", 0) or 0) for row in lop_current["data"])
            reasons.append(f"We could not find your precise salary records for {month} {year}, but we found {lop_days} days of LOP registered.")
        else:
            reasons.append(f"We could not find any salary or LOP records for {month} {year}.")
            
        return {
            "tool": "analyze_salary",
            "status": "success",
            "data": {
                "current": None,
                "previous": None,
                "reasons": reasons,
                "primary_reason": "missing_current_data"
            }
        }

    curr = current["data"][0]
    prev = previous["data"][0] if previous.get("status") == "success" else None

    reasons = []
    primary_reason = None
    tax_delta = 0
    ded_delta = 0
    lop_days = 0

    if not prev:
        reasons.append("Previous month data is not available for comparison, so analysis is based only on current salary components.")
    else:
        # 🔥 1. NET PAY CHANGE
        delta = curr.get("total_netpay", 0) - prev.get("total_netpay", 0)
        if delta < 0:
            reasons.append(f"Your net salary decreased by {abs(delta)} compared to previous month.")

        # 🔥 2. TAX IMPACT
        tax_delta = curr.get("income_tax_ded", 0) - prev.get("income_tax_ded", 0)
        if tax_delta > 0:
            reasons.append("There was an increase in tax deductions.")

        # 🔥 4. DEDUCTION CHANGE
        ded_delta = curr.get("gross_deduction", 0) - prev.get("gross_deduction", 0)
        if ded_delta > 0:
            reasons.append("Your total deductions increased.")

    # 🔥 3. LOP IMPACT
    if lop_current.get("status") == "success":
        lop_days = sum(float(row.get("lop_days", 0) or 0) for row in lop_current["data"])
        if lop_days > 0:
            reasons.append(f"You had {lop_days} LOP days affecting your salary.")
    elif lop_current.get("status") == "no_data":
        reasons.append("There was no loss of pay affecting your salary.")

    # PRIMARY REASON PRIORITY
    if tax_delta > 0:
        primary_reason = "an increase in tax deductions"
    elif ded_delta > 0:
        primary_reason = "an increase in total deductions"
    elif lop_days > 0:
        primary_reason = "loss of pay (LOP)"

    if not reasons:
        reasons = ["There is no significant change in salary components for this period."]

    return {
        "tool": "analyze_salary",
        "status": "success",
        "data": {
            "current": curr,
            "previous": prev,
            "reasons": reasons,
            "primary_reason": primary_reason
        }
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
        if tool == "get_ot_reimbursement":
            return get_ot_reimbursement(employee_id=employee_id, month=month, year=year)
        if tool == "get_allowance_breakdown":
            return get_allowance_breakdown(employee_id=employee_id, month=month, year=year)
        if tool == "get_field_value":
            return get_field_value(
                employee_id=employee_id,
                field_key=params.get("field_key"),
                table=params.get("table"),
                column=params.get("column"),
                month=month,
                year=year,
            )
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

def get_allowance_breakdown(
    employee_id: int, month: str | None = None, year: int | None = None
) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_allowance_breakdown", **validation_error}
    if not employee_exists(employee_id):
        return {
            "tool": "get_allowance_breakdown",
            "status": "no_data",
            "message": "Employee not found",
            "data": {},
        }
    if month is None or year is None:
        return {
            "tool": "get_allowance_breakdown",
            "status": "error",
            "message": "month and year are required for allowance breakdown",
            "data": {},
        }

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
    print(f"[QUERY] allowance_breakdown -> emp={employee_id}, month={month}, year={year}")

    with engine.connect() as conn:
        result = conn.execute(
            text(query),
            {"emp_id": employee_id, "month_year": month_year}
        ).mappings().fetchone()

    if not result:
        return {
            "tool": "get_allowance_breakdown",
            "status": "no_data",
            "message": "No allowance breakdown data found",
            "data": {},
        }

    data = dict(result)
    
    total = sum([
        float(data.get("bonus") or 0),
        float(data.get("incentive") or 0),
        float(data.get("other_allowance") or 0),
        float(data.get("night_shift_all") or 0),
    ])

    return {
        "tool": "get_allowance_breakdown",
        "status": "success",
        "data": {
            "total_allowance": total,
            "components": data
        }
    }


def _month_sort_case(alias: str = "month") -> str:
    return (
        f"CASE {alias} "
        "WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 WHEN 'Mar' THEN 3 WHEN 'Apr' THEN 4 "
        "WHEN 'May' THEN 5 WHEN 'Jun' THEN 6 WHEN 'Jul' THEN 7 WHEN 'Aug' THEN 8 "
        "WHEN 'Sep' THEN 9 WHEN 'Oct' THEN 10 WHEN 'Nov' THEN 11 WHEN 'Dec' THEN 12 "
        "ELSE 0 END"
    )


def get_field_value(
    employee_id: int,
    field_key: str,
    table: str,
    column: str,
    month: str | None = None,
    year: int | None = None,
) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_field_value", **validation_error}
    if not employee_exists(employee_id):
        return {
            "tool": "get_field_value",
            "status": "no_data",
            "message": "Employee not found",
            "data": None,
        }

    field_meta = FieldRegistry.get_field(str(field_key or ""))
    if not field_meta:
        return {
            "tool": "get_field_value",
            "status": "error",
            "message": f"Unknown field '{field_key}'",
            "data": None,
        }
    if table != field_meta["table"] or column != field_meta["column"]:
        return {
            "tool": "get_field_value",
            "status": "error",
            "message": "Field/table/column mismatch",
            "data": None,
        }

    month_case = _month_sort_case("month")
    month_year = f"{month}-{year}" if month and year is not None else None
    if month and year is not None:
        query = text(
            f"""
            SELECT {column} AS value, month, eyear
            FROM {table}
            WHERE employee_id = :emp_id
              AND (month = :month OR month = :month_year)
              AND eyear = :year
            LIMIT 1
            """
        )
        params = {"emp_id": employee_id, "month": month, "month_year": month_year, "year": year}
    else:
        query = text(
            f"""
            SELECT {column} AS value, month, eyear
            FROM {table}
            WHERE employee_id = :emp_id
            ORDER BY eyear DESC, {month_case} DESC
            LIMIT 1
            """
        )
        params = {"emp_id": employee_id}

    print(
        f"[QUERY] field_value -> field={field_key}, table={table}, column={column}, "
        f"emp={employee_id}, month={month}, year={year}"
    )
    with engine.connect() as conn:
        row = conn.execute(query, params).mappings().fetchone()

    if not row and month and year is not None:
        fallback_query = text(
            f"""
            SELECT {column} AS value, month, eyear
            FROM {table}
            WHERE employee_id = :emp_id
            ORDER BY eyear DESC, {month_case} DESC
            LIMIT 1
            """
        )
        with engine.connect() as conn:
            row = conn.execute(fallback_query, {"emp_id": employee_id}).mappings().fetchone()
        if row:
            data = dict(row)
            fallback_month = str(data.get("month") or "")
            fallback_year = data.get("eyear")
            if "-" in fallback_month:
                fallback_to = fallback_month
            else:
                fallback_to = f"{fallback_month}-{fallback_year}"
            return {
                "tool": "get_field_value",
                "status": "success_fallback",
                "field_key": field_key,
                "value": data.get("value"),
                "month": data.get("month"),
                "year": data.get("eyear"),
                "fallback_to": fallback_to,
                "original_request": f"{month}-{year}",
                "data": data,
            }

    if not row:
        return {
            "tool": "get_field_value",
            "status": "no_data",
            "message": f"No data found for {field_key}",
            "data": None,
        }

    data = dict(row)
    return {
        "tool": "get_field_value",
        "status": "success",
        "field_key": field_key,
        "value": data.get("value"),
        "month": data.get("month"),
        "year": data.get("eyear"),
        "data": data,
    }

# tools.py - modify get_tax, get_salary, etc.
def get_salary_with_fallback(employee_id, month, year):
    result = get_salary(employee_id, month, year)
    if not result.get("data"):
        # Try latest
        latest = get_latest_salary(employee_id)
        return {
            **result,
            "data": latest["data"],
            "fallback": f"No data for {month}-{year}, showing {latest_month}"
        }