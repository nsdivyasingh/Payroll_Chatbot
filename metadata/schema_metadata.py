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
    # -----------------------------
    # CORE SALARY
    # -----------------------------
    "net_salary": "Final take-home salary after subtracting all deductions from total earnings.",
    "gross_salary": "Total earnings including salary components, allowances, bonuses, and reimbursements before deductions.",
    "total_deductions": "Total amount deducted from gross salary including taxes and other deductions.",

    # -----------------------------
    # EARNINGS
    # -----------------------------
    "basic_salary": "Fixed base salary component of the employee.",
    "hra": "House Rent Allowance provided to employees to cover housing expenses.",
    "lta": "Leave Travel Allowance provided for travel expenses during leave.",
    "gratuity": "Lump sum amount paid after long-term service, usually after 5 years.",
    "leave_encashment": "Payment received for unused paid leaves.",
    "management_allowance": "Additional pay given for managerial or leadership responsibilities.",
    "bonus": "Reward paid for exceptional performance or project completion.",
    "yearly_bonus": "Annual bonus paid based on company performance and eligibility.",
    "incentive": "Performance-based additional earnings to motivate employees.",
    "night_shift_allowance": "Compensation for working night shifts or extended hours.",
    "nontax": "Earnings that are exempt from taxation.",
    "referral_bonus": "Amount received for referring candidates to the company.",
    "misc_earnings": "Other miscellaneous earnings not categorized elsewhere.",
    "salary_advance": "Advance salary taken by employee before regular payout.",
    "tele_reimbursement": "Reimbursement for telephone or communication expenses.",
    "joining_bonus": "One-time bonus given when joining the company.",
    "relocation_allowance": "Allowance provided for relocation expenses.",
    "professional_development": "Allowance for training, certifications, or skill development.",
    "maternity_bonus": "Bonus provided under maternity benefits.",

    # -----------------------------
    # DEDUCTIONS
    # -----------------------------
    "pf_deduction": "Provident Fund contribution deducted as retirement savings.",
    "pt_deduction": "Professional tax deducted as per state government rules.",
    "esi_deduction": "Employee State Insurance contribution.",
    "vpf_deduction": "Voluntary Provident Fund contribution.",
    "income_tax_deduction": "Monthly income tax deducted from salary.",
    "lwf_deduction": "Labour Welfare Fund contribution.",
    "salary_advance_deduction": "Recovery of previously taken salary advance.",
    "notice_period_deduction": "Deduction for incomplete notice period.",
    "medical_insurance_deduction": "Amount deducted for medical insurance.",
    "other_deductions": "Miscellaneous deductions not categorized.",
    "other_deduction_2": "Additional deduction category.",
    
    # -----------------------------
    # WORK & ATTENDANCE
    # -----------------------------
    "working_days": "Total number of working days in the month.",
    "lop_days": "Number of unpaid leave days taken by employee.",
    "actual_days": "Number of days the employee actively worked.",
    "paid_days": "Number of days for which salary is paid.",
    "arrear_days": "Adjustment days for salary arrears.",
    "leave_encash_days": "Number of leave days encashed.",
    "not_paid_days": "Days not paid due to absence or leave.",
    
    # -----------------------------
    # TAX
    # -----------------------------
    "total_gross_salary": "Total annual earnings of the employee (CTC).",
    "net_taxable_income": "Income amount on which tax is calculated.",
    "income_tax_payable": "Total income tax payable by employee.",
    "surcharge": "Additional tax applied on income tax.",
    "cess": "Health and education cess applied on tax.",
    "total_tax_liability": "Total tax obligation including surcharge and cess.",

    },

    "RELATIONSHIPS": {

    "salary_computation": """
    Net Salary = Gross Earnings - Total Deductions.
    """,

    "salary_reduction_reasoning": """
    Salary reduction should be determined by comparing current month and previous month.

    Compare:
    - Gross earnings (basic, hra, allowances, bonus, incentives)
    - Total deductions (tax, PF, PT, etc.)
    - LOP days (loss of pay)
    
    Salary may reduce due to:
    - Increase in deductions (especially tax)
    - Decrease in earnings
    - Increase in LOP (unpaid leaves)
    """,

    "earnings_dependency": """
    Gross earnings depend on:
    - Working days (wday)
    - Actual days worked (actdays)
    - Paid days (total_paid_days)
    - Salary components (basic, hra, allowances, incentives, bonuses)
    """,

    "deduction_dependency": """
    Total deductions depend on:
    - Tax deductions (income_tax_ded)
    - Statutory deductions (pf_ded, pt_ded)
    - Insurance and other deductions
    """,

    "lop_relation": """
    LOP (Loss of Pay) directly reduces an employee’s salary by decreasing payable working days.

    There are two representations of LOP in the system:

    1. pay_register (monthly payroll summary):
    - lopd → Total number of LOP days considered for salary calculation in that month.

    2. lop_data (detailed tracker):
    - month → The payroll month in which the LOP deduction was applied (i.e., when salary was reduced).
    - lop_date → The actual calendar date on which the employee took unpaid leave.
    - lop_days → Number of unpaid leave days taken on that specific date.

    Important interpretation:
    - lop_date tells WHEN the leave was taken.
    - month tells WHEN the salary impact happened.
    - lop_days represents the magnitude of impact.

    For reasoning:
    - Salary reduction may occur if lop_days increases.
    - Even if leave was taken in one month, the deduction may reflect in another payroll month.
    """,

    "allowance_relation": """
    Allowances may come from:
    - pay_register (monthly salary components)
    - ot_data (special allowances, reimbursements)

    ot_data:
    - month = payment month
    - from_date/to_date = period worked
    - allowancetype = category
    - component_in_pay_slip = label shown in payslip
    """
},
    
    "NORMALIZED_FIELDS": {
        "lop_days": ["lopd", "lop_days"],
        "net_salary": ["total_netpay"],
        "gross_salary": ["gross_earning"],
        "total_deductions": ["gross_deduction"]
    }   

}

