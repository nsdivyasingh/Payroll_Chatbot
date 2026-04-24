import pandas as pd
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = "postgresql://postgres:admin123@localhost:5432/payroll_db"
engine = create_engine(DATABASE_URL)

file_path = "payroll_data.xlsx"

# -------------------------------
# 1. Load Data
# -------------------------------
pay_df = pd.read_excel(file_path, sheet_name="Pay Register")
lop_df = pd.read_excel(file_path, sheet_name="LOP Tracker")
ot_df = pd.read_excel(file_path, sheet_name="SAOT Tracker")
tax_df = pd.read_excel(file_path, sheet_name="ITax Reco")


# -------------------------------
# 2. Clean Columns
# -------------------------------
def clean_columns(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

pay_df = clean_columns(pay_df)
lop_df = clean_columns(lop_df)
ot_df = clean_columns(ot_df)
tax_df = clean_columns(tax_df)

pay_df = pay_df.drop_duplicates()
tax_df = tax_df.drop_duplicates()

# -------------------------------
# 3. Standardize Column Names
# -------------------------------
pay_df.rename(columns={
    "employeecode": "employee_code",
    "month_name": "month"
}, inplace=True)

lop_df.rename(columns={
    "employeecode": "employee_code",
    "month": "month",
    "date": "lop_date",
    "lop": "lop_days",
}, inplace=True)

ot_df.rename(columns={
    "employeecode": "employee_code",
    "paid_month": "month"
}, inplace=True)

tax_df.rename(columns={
    "employeecode": "employee_code",
    "month": "month"
}, inplace=True)

def month_to_mon_year(month_series, year_series=None):
    month_text = month_series.astype(str).str.strip()
    if year_series is not None:
        year_text = pd.to_numeric(year_series, errors="coerce").fillna(0).astype(int).astype(str)
        dt = pd.to_datetime(month_text + "-" + year_text, format="%B-%Y", errors="coerce")
        dt_short = pd.to_datetime(month_text + "-" + year_text, format="%b-%Y", errors="coerce")
        dt = dt.fillna(dt_short)
    else:
        dt = pd.to_datetime(month_text, format="mixed", errors="coerce")
    return dt.dt.strftime("%b-%Y")


# Normalize month values to a consistent Mon-YYYY format.
if "month" in pay_df.columns:
    pay_df["month"] = month_to_mon_year(pay_df["month"], pay_df.get("eyear"))
if "month" in lop_df.columns:
    lop_df["month"] = month_to_mon_year(lop_df["month"])
if "month" in ot_df.columns:
    ot_df["month"] = month_to_mon_year(ot_df["month"])
if "month" in tax_df.columns:
    tax_df["month"] = month_to_mon_year(tax_df["month"], tax_df.get("eyear"))

if 'month' not in pay_df.columns:
    raise Exception(f"Month column not found. Available columns: {pay_df.columns}")

# -------------------------------
# 5. Insert Employees (SAFE UPSERT)
# -------------------------------
employees = pay_df[['employee_code']].drop_duplicates()

with engine.begin() as conn:
    for _, row in employees.iterrows():
        conn.execute(text("""
            INSERT INTO employee_master (employee_code)
            VALUES (:code)
            ON CONFLICT (employee_code) DO NOTHING
        """), {"code": row['employee_code']})


# -------------------------------
# 6. Fetch Mapping
# -------------------------------
emp_map = pd.read_sql(
    "SELECT employee_id, employee_code FROM employee_master",
    engine
)


# -------------------------------
# 7. Apply Mapping to ALL tables
# -------------------------------
def apply_mapping(df):
    df = df.merge(emp_map, on="employee_code", how="left")
    df.drop(columns=["employee_code"], inplace=True)
    return df


def align_to_table_columns(df, table_name):
    inspector = inspect(engine)
    table_columns = [col["name"] for col in inspector.get_columns(table_name)]
    if not table_columns:
        raise Exception(f"No columns found for table '{table_name}'")

    common_columns = [col for col in df.columns if col in table_columns]
    missing_required = [col for col in ("employee_id", "month") if col in table_columns and col not in common_columns]
    if missing_required:
        raise Exception(
            f"Missing required columns for table '{table_name}': {missing_required}. "
            f"Available DataFrame columns: {list(df.columns)}"
        )

    dropped_columns = [col for col in df.columns if col not in table_columns]
    if dropped_columns:
        print(f"[INFO] Dropping extra columns for '{table_name}': {dropped_columns}")

    return df[common_columns]

pay_df = apply_mapping(pay_df)
lop_df = apply_mapping(lop_df)
ot_df = apply_mapping(ot_df)
tax_df = apply_mapping(tax_df)

for df in (pay_df, lop_df, ot_df, tax_df):
    if "month" in df.columns:
        df.dropna(subset=["month"], inplace=True)

lop_df = align_to_table_columns(lop_df, "lop_data")
ot_df = align_to_table_columns(ot_df, "ot_data")
tax_df = align_to_table_columns(tax_df, "tax_data")


# -------------------------------
# 8. Insert Data (batch)
# -------------------------------
pay_df.to_sql("pay_register", engine, if_exists="replace", index=False)
lop_df.to_sql("lop_data", engine, if_exists="replace", index=False, method="multi")
ot_df.to_sql("ot_data", engine, if_exists="replace", index=False, method="multi")
tax_df.to_sql("tax_data", engine, if_exists="replace", index=False, method="multi")