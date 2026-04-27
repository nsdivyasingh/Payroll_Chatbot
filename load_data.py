import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:admin123@localhost:5432/payroll_db"
engine = create_engine(DATABASE_URL)

file_path = "payroll_data.xlsx"

with engine.begin() as conn:
    conn.execute(
        text(
            """
            DROP TABLE IF EXISTS pay_register, tax_data, lop_data, ot_data CASCADE
            """
        )
    )
    with open("schema.sql", "r") as f:
        conn.execute(text(f.read()))

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
    normalized = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    df.columns = normalized
    return df

pay_df = clean_columns(pay_df)
lop_df = clean_columns(lop_df)
ot_df = clean_columns(ot_df)
tax_df = clean_columns(tax_df)

pay_df = pay_df.drop_duplicates()
lop_df = lop_df.drop_duplicates()
ot_df = ot_df.drop_duplicates()
tax_df = tax_df.drop_duplicates()

# -------------------------------
# 3. Standardize Column Names
# -------------------------------
pay_df.rename(columns={
    "employeecode": "employee_code",
    "code": "employee_code",
    "month_name": "month",
    "emonth": "month"
}, inplace=True)

lop_df.rename(columns={
    "employeecode": "employee_code",
    "employee_no": "employee_code",
    "month": "month",
    "date": "lop_date",
    "lop": "lop_days",
}, inplace=True)

ot_df.rename(columns={
    "employeecode": "employee_code",
    "paid_month": "month",
    "allowancetype": "allowance_type",
    "fromdate": "from_date",
    "todate": "to_date"
}, inplace=True)

tax_df.rename(columns={
    "employeecode": "employee_code",
    "ecode": "employee_code",
    "month": "month",
    "year": "eyear"
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

if "month" in tax_df.columns and "eyear" not in tax_df.columns:
    tax_df["eyear"] = pd.to_numeric(
        tax_df["month"].astype(str).str.split("-").str[1],
        errors="coerce"
    )

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

def split_month_year(df):
    df["month"] = df["month"].astype(str)

    df["month_clean"] = df["month"].str.split("-").str[0]
    df["year_clean"] = df["month"].str.split("-").str[1]

    return df

pay_summary_df = split_month_year(pay_df.copy())
tax_summary_df = split_month_year(tax_df.copy())

pay_summary_df["month"] = pay_summary_df["month_clean"]
pay_summary_df["eyear"] = pd.to_numeric(pay_summary_df["year_clean"], errors="coerce")
tax_summary_df["month"] = tax_summary_df["month_clean"]
tax_summary_df["eyear"] = pd.to_numeric(tax_summary_df["year_clean"], errors="coerce")

pay_summary_df.drop(columns=["month_clean", "year_clean"], inplace=True)
tax_summary_df.drop(columns=["month_clean", "year_clean"], inplace=True)

# Aggregate curated summary tables at employee+month granularity.
pay_summary_df = pay_summary_df.groupby(
    ["employee_code", "month", "eyear"],
    as_index=False
).agg({
    "gross_earning": "sum",
    "gross_deduction": "sum",
    "total_netpay": "sum",
    "income_tax_ded": "sum",
    "lopd": "sum"
})

tax_summary_df = tax_summary_df.groupby(
    ["employee_code", "month", "eyear"],
    as_index=False
).agg({
    "total_tax_liability": "sum"
})

# -------------------------------
# 5. Insert Employees (SAFE UPSERT)
# -------------------------------
all_employee_codes = pd.concat(
    [
        pay_df.get("employee_code", pd.Series(dtype="object")),
        lop_df.get("employee_code", pd.Series(dtype="object")),
        ot_df.get("employee_code", pd.Series(dtype="object")),
        tax_df.get("employee_code", pd.Series(dtype="object")),
    ],
    ignore_index=True
).dropna().astype(str).str.strip()
employees = pd.DataFrame({"employee_code": all_employee_codes.unique()})

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
    if "employee_code" not in df.columns:
        return df
    df["employee_code"] = df["employee_code"].astype(str).str.strip()
    df = df.merge(emp_map, on="employee_code", how="left")
    return df

pay_raw_df = apply_mapping(pay_df.copy())
lop_raw_df = apply_mapping(lop_df.copy())
ot_raw_df = apply_mapping(ot_df.copy())
tax_raw_df = apply_mapping(tax_df.copy())
pay_summary_df = apply_mapping(pay_summary_df)
tax_summary_df = apply_mapping(tax_summary_df)

pay_register_columns = [
    "employee_id",
    "employee_code",
    "month",
    "emonth",
    "eyear",
    "code_wday",
    "lopd",
    "actdays",
    "arrdays",
    "total_paid_days",
    "leavenchdays",
    "notpaydays",
    "notdeddays",
    "ot_hrs",
    "basic",
    "h_r_a",
    "lta",
    "gratuity",
    "leave_encash",
    "mange_allow",
    "bonus",
    "other_allowance",
    "yearly_bonus",
    "incentive",
    "night_shift_all",
    "sign_tenure_bon",
    "nontax",
    "referal_bonus",
    "notice_per_pay",
    "misc_earn",
    "salary_advance",
    "tele_reimb",
    "joibon",
    "serweigh",
    "relocation",
    "prof_developmnt",
    "maternity_bonus",
    "gross_earning",
    "pt_ded",
    "pf_ded",
    "esi_employee_ded",
    "vpf_ded",
    "income_tax_ded",
    "l_w_f_ded",
    "sal_adv_ded",
    "notice_per_ded_ded",
    "medical_ins_par_ded",
    "oth_dedu_ded",
    "other_ded_2_ded",
    "gross_deduction",
    "total_netpay",
    "remark",
]

# Build a full-fidelity pay register table with stable column contract.
pay_register_df = split_month_year(pay_raw_df.copy())
pay_register_df["month"] = pay_register_df["month_clean"]
pay_register_df["emonth"] = pay_register_df["month_clean"]
pay_register_df["eyear"] = pd.to_numeric(pay_register_df["year_clean"], errors="coerce")
pay_register_df.drop(columns=["month_clean", "year_clean"], inplace=True)

for col in pay_register_columns:
    if col not in pay_register_df.columns:
        pay_register_df[col] = None

pay_register_df = pay_register_df[pay_register_columns]
pay_register_df.dropna(subset=["employee_id", "month", "eyear"], inplace=True)
pay_register_df["eyear"] = pay_register_df["eyear"].astype(int)

# Strict column contracts for summary tables.
pay_summary_df = pay_summary_df[
    [
        "employee_id",
        "month",
        "eyear",
        "gross_earning",
        "gross_deduction",
        "total_netpay",
        "income_tax_ded",
        "lopd"
    ]
]
tax_summary_df = tax_summary_df[
    [
        "employee_id",
        "month",
        "eyear",
        "total_tax_liability"
    ]
]

for df in (pay_raw_df, lop_raw_df, ot_raw_df, tax_raw_df, pay_summary_df, tax_summary_df):
    if "month" in df.columns:
        df.dropna(subset=["month"], inplace=True)

pay_summary_df.dropna(subset=["employee_id", "month", "eyear"], inplace=True)
tax_summary_df.dropna(subset=["employee_id", "month", "eyear"], inplace=True)
pay_summary_df["eyear"] = pay_summary_df["eyear"].astype(int)
tax_summary_df["eyear"] = tax_summary_df["eyear"].astype(int)


# -------------------------------
# 8. Insert Data (batch)
# -------------------------------
with engine.begin() as conn:
    conn.execute(text("""
        DROP TABLE IF EXISTS pay_register_raw, lop_data_raw, ot_data_raw, tax_data_raw
    """))
    
    conn.execute(text("""
        TRUNCATE TABLE pay_register, tax_data
    """))

# RAW (replace)
pay_raw_df.to_sql("pay_register_raw", engine, if_exists="replace", index=False, method="multi")
lop_raw_df.to_sql("lop_data_raw", engine, if_exists="replace", index=False, method="multi")
ot_raw_df.to_sql("ot_data_raw", engine, if_exists="replace", index=False, method="multi")
tax_raw_df.to_sql("tax_data_raw", engine, if_exists="replace", index=False, method="multi")

# CURATED (append)
pay_register_df.to_sql("pay_register", engine, if_exists="append", index=False, method="multi")
tax_summary_df.to_sql("tax_data", engine, if_exists="append", index=False, method="multi")

# TRACKERS (full-fidelity replace)
lop_raw_df.to_sql("lop_data", engine, if_exists="replace", index=False, method="multi")
ot_raw_df.to_sql("ot_data", engine, if_exists="replace", index=False, method="multi")