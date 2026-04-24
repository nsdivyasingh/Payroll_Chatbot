from __future__ import annotations

from sqlalchemy import text

from query_engine import engine


def employee_exists(employee_id: int) -> bool:
    query = text("SELECT 1 FROM employee_master WHERE employee_id = :emp_id LIMIT 1")
    with engine.connect() as conn:
        row = conn.execute(query, {"emp_id": employee_id}).fetchone()
    return row is not None


def get_salary(employee_id: int, month: str | None = None):
    if month:
        query = text(
            """
            SELECT month, total_netpay, gross_earning, gross_deduction
            FROM pay_register
            WHERE employee_id = :emp_id AND month = :month
            ORDER BY month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id, "month": month}
    else:
        query = text(
            """
            SELECT month, total_netpay, gross_earning, gross_deduction
            FROM pay_register
            WHERE employee_id = :emp_id
            ORDER BY month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id}

    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(query, params).fetchall()]


def get_lop(employee_id: int, month: str | None = None):
    if month:
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

    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(query, params).fetchall()]


def get_tax(employee_id: int, month: str | None = None):
    if month:
        query = text(
            """
            SELECT month, total_tax_liability
            FROM tax_data
            WHERE employee_id = :emp_id AND month = :month
            ORDER BY month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id, "month": month}
    else:
        query = text(
            """
            SELECT month, total_tax_liability
            FROM tax_data
            WHERE employee_id = :emp_id
            ORDER BY month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id}

    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(query, params).fetchall()]
