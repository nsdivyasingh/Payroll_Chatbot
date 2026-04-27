# === NEW: Complete Field Registry for Your Payroll Schema ===
# This replaces the scattered intent/tool mapping with a unified schema

from typing import Dict, Any, List

class FieldRegistry:
    """Maps user queries to database fields with metadata"""
    
    FIELDS: Dict[str, Dict[str, Any]] = {
        # ==================== EARNINGS ====================
        "basic": {
            "table": "pay_register",
            "column": "BASIC",
            "category": "earning",
            "unit": "amount",
            "aliases": ["basic", "basic salary", "base salary"],
            "semantic": "Base salary component",
            "response_template": "Your basic salary for {month} {year} is ₹{value}."
        },
        
        "hra": {
            "table": "pay_register",
            "column": "H.R.A",
            "category": "earning",
            "unit": "amount",
            "aliases": ["hra", "house rent", "house rent allowance"],
            "semantic": "House Rent Allowance",
            "response_template": "Your House Rent Allowance (HRA) for {month} {year} is ₹{value}."
        },
        
        "lta": {
            "table": "pay_register",
            "column": "LTA",
            "category": "earning",
            "unit": "amount",
            "aliases": ["lta", "leave travel", "leave travel allowance"],
            "semantic": "Leave Travel Allowance",
            "response_template": "Your Leave Travel Allowance (LTA) for {month} {year} is ₹{value}."
        },
        
        "bonus": {
            "table": "pay_register",
            "column": "BONUS.",
            "category": "earning",
            "unit": "amount",
            "aliases": ["bonus"],
            "semantic": "Performance or fixed bonus",
            "response_template": "Your bonus for {month} {year} is ₹{value}."
        },
        
        "night_shift_allowance": {
            "table": "pay_register",
            "column": "NIGHT SHIFT ALL",
            "category": "earning",
            "unit": "amount",
            "aliases": ["night shift", "nsa", "night shift allowance"],
            "semantic": "Night Shift Allowance",
            "response_template": "Your Night Shift Allowance for {month} {year} is ₹{value}."
        },
        
        "other_allowance": {
            "table": "pay_register",
            "column": "OTHER ALLOWANCE",
            "category": "earning",
            "unit": "amount",
            "aliases": ["other allowance", "misc allowance"],
            "semantic": "Miscellaneous allowances",
            "response_template": "Your Other Allowance for {month} {year} is ₹{value}."
        },
        
        "incentive": {
            "table": "pay_register",
            "column": "INCENTIVE",
            "category": "earning",
            "unit": "amount",
            "aliases": ["incentive"],
            "semantic": "Performance incentive",
            "response_template": "Your incentive for {month} {year} is ₹{value}."
        },
        
        # ==================== DEDUCTIONS ====================
        "pf": {
            "table": "pay_register",
            "column": "PF_DED",
            "category": "deduction",
            "unit": "amount",
            "aliases": ["pf", "provident fund", "pf deduction"],
            "semantic": "Provident Fund deduction",
            "response_template": "Your Provident Fund (PF) deduction for {month} {year} is ₹{value}."
        },
        
        "pt": {
            "table": "pay_register",
            "column": "PT_DED",
            "category": "deduction",
            "unit": "amount",
            "aliases": ["pt", "professional tax"],
            "semantic": "Professional Tax deduction",
            "response_template": "Your Professional Tax (PT) deduction for {month} {year} is ₹{value}."
        },
        
        "income_tax": {
            "table": "pay_register",
            "column": "INCOME TAX_DED",
            "category": "deduction",
            "unit": "amount",
            "aliases": ["income tax", "tax deduction", "income tax ded"],
            "semantic": "Income Tax deduction",
            "response_template": "Your Income Tax deduction for {month} {year} is ₹{value}."
        },
        
        # ==================== TAX DETAILS (ITax Reco) ====================
        "net_taxable_income": {
            "table": "tax_data",
            "column": "NET TAXABLE INCOME",
            "category": "tax",
            "unit": "amount",
            "aliases": ["net taxable income", "taxable income"],
            "semantic": "Employee's taxable income after deductions",
            "response_template": "Your net taxable income for {month} {year} is ₹{value}.",
            "source": "ITax Reco"
        },
        
        "surcharge": {
            "table": "tax_data",
            "column": "SURCHARGE ON INCOME TAX",
            "category": "tax",
            "unit": "amount",
            "aliases": ["surcharge", "surcharge on tax"],
            "semantic": "Surcharge on income tax",
            "response_template": "Your surcharge on income tax for {month} {year} is ₹{value}.",
            "source": "ITax Reco"
        },
        
        "tax_due": {
            "table": "tax_data",
            "column": "INCOME TAX DUE",
            "category": "tax",
            "unit": "amount",
            "aliases": ["tax due", "income tax due", "tax owed"],
            "semantic": "Remaining tax amount to be paid",
            "response_template": "Your remaining income tax due for {month} {year} is ₹{value}.",
            "source": "ITax Reco"
        },
        
        "total_tax_liability": {
            "table": "tax_data",
            "column": "TOTAL TAX LIABILITY",
            "category": "tax",
            "unit": "amount",
            "aliases": ["total tax", "tax liability", "total tax liability"],
            "semantic": "Total tax obligation",
            "response_template": "Your total tax liability for {month} {year} is ₹{value}.",
            "source": "ITax Reco"
        },
        
        "tax_paid_till_date": {
            "table": "tax_data",
            "column": "TOTAL INCOME TAX PAID FROM SALARY TILL DATE",
            "category": "tax",
            "unit": "amount",
            "aliases": ["tax paid till date", "total tax paid"],
            "semantic": "Cumulative tax paid from salary",
            "response_template": "Your total income tax paid till {month} {year} is ₹{value}.",
            "source": "ITax Reco"
        },
        
        "tax_regime": {
            "table": "tax_data",
            "column": "TAX REGIME",
            "category": "tax",
            "unit": "text",
            "aliases": ["tax regime", "which regime", "regime", "old regime", "new regime"],
            "semantic": "Tax regime (Old or New)",
            "response_template": "You are under the {value} tax regime for {month} {year}.",
            "source": "ITax Reco"
        },
        
        # ==================== TOTALS ====================
        "gross_salary": {
            "table": "tax_data",  # From ITax Reco for consistency
            "column": "TOTAL GROSS SALARY",
            "category": "total",
            "unit": "amount",
            "aliases": ["gross salary", "total gross", "total gross salary"],
            "semantic": "Total gross earnings",
            "response_template": "Your total gross salary for {month} {year} is ₹{value}.",
            "source": "ITax Reco"
        },
        
        "net_pay": {
            "table": "pay_register",
            "column": "TOTAL_NETPAY",
            "category": "total",
            "unit": "amount",
            "aliases": ["net pay", "take home", "net salary", "net take home"],
            "semantic": "Final salary after deductions",
            "response_template": "Your net pay for {month} {year} is ₹{value}."
        },
        
        "gross_earning": {
            "table": "pay_register",
            "column": "GROSS_EARNING",
            "category": "total",
            "unit": "amount",
            "aliases": ["gross earnings", "earnings", "gross"],
            "semantic": "Total earnings before deductions",
            "response_template": "Your gross earnings for {month} {year} is ₹{value}."
        },
        
        "gross_deduction": {
            "table": "pay_register",
            "column": "GROSS_DEDUCTION",
            "category": "total",
            "unit": "amount",
            "aliases": ["gross deduction", "total deductions", "deductions"],
            "semantic": "Total deductions from salary",
            "response_template": "Your total deductions for {month} {year} is ₹{value}."
        },
    }
    
    @staticmethod
    def find_field(query: str) -> str | None:
        """
        Search for field request in query using aliases
        
        Args:
            query: User's question
            
        Returns:
            Field key if found, None otherwise
        """
        q = query.lower().strip()
        
        for field_key, field_data in FieldRegistry.FIELDS.items():
            for alias in field_data["aliases"]:
                if alias.lower() in q:
                    return field_key
        
        return None
    
    @staticmethod
    def get_field(field_key: str) -> Dict[str, Any] | None:
        """Get field metadata by key"""
        return FieldRegistry.FIELDS.get(field_key)
    
    @staticmethod
    def get_table_column(field_key: str) -> tuple[str, str] | None:
        """Get (table, column) pair for a field"""
        field = FieldRegistry.get_field(field_key)
        if field:
            return (field["table"], field["column"])
        return None


# === Example Usage ===

if __name__ == "__main__":
    # Example 1: Find field in query
    query1 = "What is my net taxable income for Jan 2026?"
    field = FieldRegistry.find_field(query1)
    print(f"Query: {query1}")
    print(f"Detected Field: {field}")
    if field:
        metadata = FieldRegistry.get_field(field)
        print(f"Table: {metadata['table']}")
        print(f"Column: {metadata['column']}")
        print()
    
    # Example 2: Find different field
    query2 = "What is my HRA?"
    field = FieldRegistry.find_field(query2)
    print(f"Query: {query2}")
    print(f"Detected Field: {field}")
    if field:
        metadata = FieldRegistry.get_field(field)
        print(f"Response Template: {metadata['response_template']}")
        print()
    
    # Example 3: Not found
    query3 = "What is my father's name?"
    field = FieldRegistry.find_field(query3)
    print(f"Query: {query3}")
    print(f"Detected Field: {field}")
