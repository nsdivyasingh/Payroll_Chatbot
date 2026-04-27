# metadata/schema_metadata.py

SCHEMA_METADATA = {
    "pay_register_raw": {
        "description": "Detailed payroll data including earnings and deductions per employee per month",
        "columns": {
            "basic": "Base salary component",
            "h_r_a": "House Rent Allowance",
            "lta": "Leave Travel Allowance",
            "bonus": "Performance or fixed bonus",
            "other_allowance": "Miscellaneous allowances paid",
            "pf_ded": "Provident Fund deduction",
            "pt_ded": "Professional Tax deduction",
            "income_tax_ded": "Income tax deducted for the month",
            "gross_earning": "Total earnings before deductions",
            "gross_deduction": "Total deductions",
            "total_netpay": "Final salary after deductions",
        }
    },

    "lop_data": {
        "description": "Loss of Pay (LOP) tracking for employees",
        "columns": {
            "lop_days": "Number of unpaid leave days",
            "lop_date": "Date when leave was recorded",
        }
    },

    "tax_data": {
        "description": "Employee tax summary",
        "columns": {
            "total_tax_liability": "Total tax owed by employee",
        }
    },

    "ot_data": {
        "description": "Overtime and allowance tracking",
        "columns": {
            "allowancetype": "Type of allowance (e.g. night shift)",
            "paid_amount": "Amount paid for allowance",
        }
    }
}