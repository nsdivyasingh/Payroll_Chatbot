# metadata/schema_metadata.py

PAYROLL_FIELDS = {

    # -----------------------------
    # TAX DATA
    # -----------------------------
    "total_gross_salary": ("tax_data", "total_gross_salary"),
    "net_taxable_income": ("tax_data", "net_taxable_income"),
    "income_tax_payable": ("tax_data", "income_tax_payable"),
    "surcharge": ("tax_data", "surcharge_on_income_tax"),
    "cess": ("tax_data", "health_and_education_cess"),
    "total_tax_liability": ("tax_data", "total_tax_liability"),

    # -----------------------------
    # CORE SALARY
    # -----------------------------
    "net_salary": ("pay_register_raw", "total_netpay"),
    "gross_salary": ("pay_register_raw", "gross_earning"),
    "total_deductions": ("pay_register_raw", "gross_deduction"),

    # -----------------------------
    # EARNINGS
    # -----------------------------
    "basic_salary": ("pay_register_raw", "basic"),
    "hra": ("pay_register_raw", "h_r_a"),
    "lta": ("pay_register_raw", "lta"),
    "gratuity": ("pay_register_raw", "gratuity"),
    "leave_encashment": ("pay_register_raw", "leave_encash"),
    "management_allowance": ("pay_register_raw", "mange_allow"),
    "bonus": ("pay_register_raw", "bonus"),
    "other_allowance": ("pay_register_raw", "other_allowance"),
    "yearly_bonus": ("pay_register_raw", "yearly_bonus"),
    "incentive": ("pay_register_raw", "incentive"),
    "night_shift_allowance": ("pay_register_raw", "night_shift_all"),
    "sign_tenure_bonus": ("pay_register_raw", "sign_tenure_bon"),
    "referral_bonus": ("pay_register_raw", "referal_bonus"),
    "notice_period_pay": ("pay_register_raw", "notice_per_pay"),
    "misc_earnings": ("pay_register_raw", "misc_earn"),
    "salary_advance": ("pay_register_raw", "salary_advance"),
    "tele_reimbursement": ("pay_register_raw", "tele_reimb"),
    "joining_bonus": ("pay_register_raw", "joibon"),
    "relocation_allowance": ("pay_register_raw", "relocation"),
    "professional_development": ("pay_register_raw", "prof_developmnt"),
    "maternity_bonus": ("pay_register_raw", "maternity_bonus"),

    # -----------------------------
    # DEDUCTIONS
    # -----------------------------
    "pf_deduction": ("pay_register_raw", "pf_ded"),
    "pt_deduction": ("pay_register_raw", "pt_ded"),
    "esi_deduction": ("pay_register_raw", "esi_employee_ded"),
    "vpf_deduction": ("pay_register_raw", "vpf_ded"),
    "income_tax_deduction": ("pay_register_raw", "income_tax_ded"),
    "lwf_deduction": ("pay_register_raw", "l_w_f_ded"),
    "salary_advance_deduction": ("pay_register_raw", "sal_adv_ded"),
    "notice_period_deduction": ("pay_register_raw", "notice_per_ded_ded"),
    "medical_insurance_deduction": ("pay_register_raw", "medical_ins_par_ded"),
    "other_deductions": ("pay_register_raw", "oth_dedu_ded"),
    "other_deduction_2": ("pay_register_raw", "other_ded_2_ded"),

    # -----------------------------
    # WORK & ATTENDANCE
    # -----------------------------
    "working_days": ("pay_register_raw", "wday"),
    "lop_days": ("pay_register_raw", "lopd"),
    "actual_days": ("pay_register_raw", "actdays"),
    "arrear_days": ("pay_register_raw", "arrdays"),
    "paid_days": ("pay_register_raw", "total_paid_days"),
    "leave_encash_days": ("pay_register_raw", "leavenchdays"),
    "not_paid_days": ("pay_register_raw", "notpaydays"),

    # -----------------------------
    # LOP TABLE
    # -----------------------------
    "lop_date": ("lop_data", "lop_date"),
    "lop_days_tracker": ("lop_data", "lop_days"),

    # -----------------------------
    # OT / ALLOWANCE TABLE
    # -----------------------------
    "allowance_type": ("ot_data", "allowancetype"),
    "allowance_amount": ("ot_data", "paid_amount"),
    "allowance_from_date": ("ot_data", "fromdate"),
    "allowance_to_date": ("ot_data", "todate"),
    "allowance_component": ("ot_data", "component_in_pay_slip"),

    "FIELD_DESCRIPTIONS": {

    "pf_deduction": "Provident Fund contribution deducted from salary",
    "pt_deduction": "Professional tax deducted as per state rules",
    "income_tax_deduction": "Income tax deducted for the month",
    "net_salary": "Final take-home salary after all deductions",
    "gross_salary": "Total earnings before deductions",
    "other_allowance": "Miscellaneous allowances paid in salary",
    "bonus": "Additional bonus paid to employee",
    "incentive": "Performance-based incentive payment",
    "lop_days": "Number of unpaid leave days affecting salary",
}

}