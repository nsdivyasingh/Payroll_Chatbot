CREATE TABLE IF NOT EXISTS pay_register (
    employee_id INT,
    month TEXT,
    eyear INT,
    gross_earning FLOAT,
    gross_deduction FLOAT,
    total_netpay FLOAT,
    income_tax_ded FLOAT,
    lopd FLOAT,
    PRIMARY KEY (employee_id, month, eyear)
);

CREATE TABLE IF NOT EXISTS tax_data (
    employee_id INT,
    month TEXT,
    eyear INT,
    total_tax_liability FLOAT,
    PRIMARY KEY (employee_id, month, eyear)
);

CREATE TABLE IF NOT EXISTS lop_data (
    employee_id INT,
    employee_code TEXT,
    consultant_name TEXT,
    lop_date DATE,
    lop_days FLOAT,
    month TEXT
);

CREATE TABLE IF NOT EXISTS ot_data (
    employee_id INT,
    employee_code TEXT,
    allowance_type TEXT,
    from_date DATE,
    to_date DATE,
    component_in_pay_slip TEXT,
    paid_amount FLOAT,
    month TEXT
);