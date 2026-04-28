from sqlalchemy import text
from query_engine import engine

ALLOWED_TABLES = ["pay_register_raw", "tax_data", "ot_data", "lop_data"]

ALLOWED_COLUMNS = {
    "pay_register_raw": ["basic", "h_r_a", "bonus", "incentive", "other_allowance", "gross_deduction"],
    "tax_data": ["total_tax_liability"],
    "ot_data": ["paid_amount", "allowancetype"],
    "lop_data": ["lop_days"]
}

def execute_safe_query(plan, employee_id):
    if not plan:
        return None

    table = plan.get("table")
    cols = plan.get("columns", [])
    agg = plan.get("aggregation", "none")
    filters = plan.get("filters", {})

    if table not in ALLOWED_TABLES:
        return None

    for c in cols:
        if c not in ALLOWED_COLUMNS.get(table, []):
            return None

    if agg == "sum":
        query = f"SELECT SUM({' + '.join(cols)}) as result"
    else:
        query = f"SELECT {', '.join(cols)}"

    query += f" FROM {table} WHERE employee_id = :emp_id"

    params = {"emp_id": employee_id}

    if filters.get("month"):
        query += " AND month = :month"
        params["month"] = filters["month"]

    if filters.get("year"):
        query += " AND eyear = :year"
        params["year"] = filters["year"]

    query += " LIMIT 50"

    try:
        with engine.connect() as conn:
            return conn.execute(text(query), params).mappings().fetchall()
    except:
        return None