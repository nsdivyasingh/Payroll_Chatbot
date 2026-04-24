from sqlalchemy import create_engine, text

# create connection to your DB
engine = create_engine("postgresql://postgres:admin123@localhost:5432/payroll_db")

def get_salary(employee_id, month=None):
    if month is None:
        query = text("""
            SELECT total_netpay, gross_earning, gross_deduction
            FROM pay_register
            WHERE employee_id = :emp_id
        """)
        params = {"emp_id": employee_id}
    else:
        query = text("""
            SELECT total_netpay, gross_earning, gross_deduction
            FROM pay_register
            WHERE employee_id = :emp_id AND month = :month
        """)
        params = {"emp_id": employee_id, "month": month}

    with engine.connect() as conn:
        result = conn.execute(query, params).fetchone()

    return result