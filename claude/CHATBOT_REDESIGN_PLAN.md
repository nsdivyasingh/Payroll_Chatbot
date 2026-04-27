# Payroll Chatbot - Schema Analysis & Redesign Plan

## Your Actual Database Schema (Complete)

### Source Data (payroll_data.xlsx)

**1. LOP Tracker** (32 rows)
- Columns: Month, Consultant Name, Employee No, Date, LOP
- Purpose: Track loss of pay events
- Key Issue: Employee No is string (not integer), needs normalization

**2. SAOT Tracker** (Shift Allowance/OT) (32 rows)
- Columns: EmployeeCode, EmployeeName, AllowanceType, FromDate, ToDate, Component in Pay slip, Paid Month, Paid Amount
- Purpose: Track reimbursements and shift allowances
- Key Field: FromDate/ToDate (this answers "reimbursement for which period?")
- Example: "Reimbursement: Rs 4,672 (period: 2025-03-01 to 2025-03-31, paid in: Apr 2025)"

**3. Pay Register** (56 rows, 82 columns)
- Core payroll data per employee per month
- Key columns:
  - Time: EMONTH (text), EYEAR (int)
  - Employee: CODE, NAME
  - Earnings (46-67): BASIC, H.R.A, LTA, BONUS, OTHER ALLOWANCE, INCENTIVE, NIGHT SHIFT ALL, etc.
  - Deductions (69-79): PT_DED, PF_DED, INCOME TAX_DED, etc.
  - Totals: GROSS_EARNING, GROSS_DEDUCTION, TOTAL_NETPAY

**4. ITax Reco** (Income Tax Reconciliation) (39 rows, 215 columns!)
- Comprehensive tax data
- Key columns (the ones test cases ask for):
  - Column 41: NET TAXABLE INCOME (net_taxable_income)
  - Column 43: INCOME TAX PAYABLE
  - Column 44: SURCHARGE ON INCOME TAX (surcharge)
  - Column 46: TOTAL TAX LIABILITY
  - Column 50: TOTAL INCOME TAX PAID FROM SALARY TILL DATE
  - Column 52: INCOME TAX DUE (tax_due)
  - Column 7: GROSS SALARY
  - Column 9: TOTAL GROSS SALARY
  - Column 215: TAX REGIME (Old Regime / New Regime)

---

## Problem Analysis vs Current Implementation

### What Test Cases Expect vs What You're Returning

| Test Case Query | Expected Data | Current Result | Root Cause |
|---|---|---|---|
| "What is my net taxable income for Jan 2026?" | ITax Reco column 41: NET TAXABLE INCOME | get_tax returns only total_tax_liability | Parser sees "tax" → calls get_tax, doesn't know about net_taxable_income column |
| "What is my surcharge on income tax?" | ITax Reco column 44: SURCHARGE | Returns: "total_tax_liability" | Same - not field-aware |
| "What is my tax regime?" | ITax Reco column 215: TAX REGIME | Fallback message | Intent parser doesn't have "tax_regime" keyword |
| "What is my total gross salary?" | ITax Reco column 9: TOTAL GROSS SALARY | get_full_salary_breakdown returns components | Tool planner returns breakdown, not total |
| "Reimbursement for which period?" | SAOT Tracker FromDate+ToDate | "I found X entries" | OT tool doesn't extract/display work period |
| "LTA for Jun 2025?" | Pay Register column "LTA" | Fallback (deduction_query gets full breakdown) | No specific field extractor for individual components |
| "HRA for Jun 2025?" | Pay Register column "H.R.A" | Same as above | Same reason |

---

## Why Your Current Approach Fails

### Your Pipeline
```
Query → Intent Parser (keyword matching) → Tool Planner (intent→tool) 
  → Tool Executor (hardcoded SQL) → Template Formatter (7 templates)
```

### The Fundamental Issue

**Intent ≠ What We Actually Need**

Your approach:
- Query: "net taxable income" → Parser finds "tax" → Maps to intent: "tax" → Calls get_tax → Returns total_tax_liability

What should happen:
- Query: "net taxable income" → Parser identifies field request for "net_taxable_income" → Maps to table.column "ITax_Reco.NET_TAXABLE_INCOME" → Builds SQL → Formats response

---

## Solution: Field-Aware Architecture

### Step 1: Create Complete Field Registry

Instead of just 7 tools, map ALL queryable fields:

```python
PAYROLL_FIELD_REGISTRY = {
    # EARNINGS COMPONENTS (from Pay Register)
    "basic": {
        "table": "pay_register",
        "column": "BASIC",
        "type": "earning",
        "aliases": ["basic salary", "base salary"],
        "semantic": "Base salary component"
    },
    "hra": {
        "table": "pay_register",
        "column": "H.R.A",
        "type": "earning",
        "aliases": ["house rent allowance"],
        "semantic": "House Rent Allowance"
    },
    "lta": {
        "table": "pay_register",
        "column": "LTA",
        "type": "earning",
        "aliases": ["leave travel allowance"],
        "semantic": "Leave Travel Allowance"
    },
    "bonus": {
        "table": "pay_register",
        "column": "BONUS.",
        "type": "earning",
        "aliases": ["bonus"],
        "semantic": "Performance or fixed bonus"
    },
    "night_shift_allowance": {
        "table": "pay_register",
        "column": "NIGHT SHIFT ALL",
        "type": "earning",
        "aliases": ["night shift", "nsa"],
        "semantic": "Night Shift Allowance"
    },
    "other_allowance": {
        "table": "pay_register",
        "column": "OTHER ALLOWANCE",
        "type": "earning",
        "aliases": ["other allowance"],
        "semantic": "Miscellaneous allowances"
    },
    
    # DEDUCTION COMPONENTS
    "pf": {
        "table": "pay_register",
        "column": "PF_DED",
        "type": "deduction",
        "aliases": ["provident fund", "pf deduction"],
        "semantic": "Provident Fund deduction"
    },
    "pt": {
        "table": "pay_register",
        "column": "PT_DED",
        "type": "deduction",
        "aliases": ["professional tax"],
        "semantic": "Professional Tax deduction"
    },
    "income_tax": {
        "table": "pay_register",
        "column": "INCOME TAX_DED",
        "type": "deduction",
        "aliases": ["tax deduction", "income tax"],
        "semantic": "Income Tax deduction"
    },
    
    # TAX-SPECIFIC FIELDS (from ITax Reco)
    "net_taxable_income": {
        "table": "tax_data",
        "column": "NET TAXABLE INCOME",
        "type": "tax",
        "aliases": ["net taxable income", "taxable income"],
        "semantic": "Employee's taxable income after deductions"
    },
    "surcharge": {
        "table": "tax_data",
        "column": "SURCHARGE ON INCOME TAX",
        "type": "tax",
        "aliases": ["surcharge"],
        "semantic": "Surcharge on income tax"
    },
    "tax_due": {
        "table": "tax_data",
        "column": "INCOME TAX DUE",
        "type": "tax",
        "aliases": ["tax due", "tax owed"],
        "semantic": "Remaining tax amount to be paid"
    },
    "total_tax_liability": {
        "table": "tax_data",
        "column": "TOTAL TAX LIABILITY",
        "type": "tax",
        "aliases": ["total tax", "tax liability"],
        "semantic": "Total tax obligation"
    },
    "tax_regime": {
        "table": "tax_data",
        "column": "TAX REGIME",
        "type": "tax",
        "aliases": ["tax regime", "which regime", "regime"],
        "semantic": "Old Regime or New Regime"
    },
    
    # TOTALS
    "gross_salary": {
        "table": "tax_data",  # Use ITax for consistency
        "column": "TOTAL GROSS SALARY",
        "type": "total",
        "aliases": ["gross salary", "total gross salary"],
        "semantic": "Total gross earnings"
    },
    "net_pay": {
        "table": "pay_register",
        "column": "TOTAL_NETPAY",
        "type": "total",
        "aliases": ["net pay", "take home"],
        "semantic": "Final salary after deductions"
    },
    "gross_earning": {
        "table": "pay_register",
        "column": "GROSS_EARNING",
        "type": "total",
        "aliases": ["earnings", "gross earnings"],
        "semantic": "Total before deductions"
    },
    "gross_deduction": {
        "table": "pay_register",
        "column": "GROSS_DEDUCTION",
        "type": "total",
        "aliases": ["total deductions", "deductions"],
        "semantic": "Total deductions from salary"
    },
}
```

### Step 2: New Pipeline Architecture

```
Query
  ↓
[PARSER] Extract: question_type, field_request, employee_id, date_range
  ↓
[FIELD_MATCHER] Look up field in registry → get (table, column, metadata)
  ↓
[QUERY_BUILDER] Construct SQL (with date fallback logic)
  ↓
[EXECUTOR] Run query, handle no_data cases
  ↓
[FORMATTER] Use field metadata + LLM for natural response
```

### Step 3: Enhanced Parser

New parser needs to:

1. **Recognize field requests** (not just intents)
   ```
   "net taxable income" → field: "net_taxable_income"
   "HRA for June" → field: "hra", time: June
   "surcharge" → field: "surcharge"
   ```

2. **Extract structured data**
   ```python
   parsed = {
       "employee_id": <from context>,
       "field_request": "net_taxable_income",  # NEW
       "time": {"month": "Jan", "year": 2026},
       "comparison": False,
       "question_type": "single_field"  # vs "comparison", "breakdown", etc.
   }
   ```

3. **Handle variations**
   - "What is my HRA?" = field request
   - "HRA for May 2025?" = field request + time
   - "HRA vs May 2024?" = comparative
   - "Total deductions?" = aggregate

---

## Implementation Plan

### Phase 1: Build Field Registry (1-2 hours)
- Document all 50+ queryable fields
- Map to actual table.column names
- Add aliases and semantic meaning

### Phase 2: Enhance Parser (2-3 hours)
- Add field extraction alongside intent
- Implement field lookup in registry
- Handle aliases ("HRA" = "house rent allowance")

### Phase 3: Build Query Mapper (3-4 hours)
- Take parsed field request + registry data
- Build dynamic SQL based on:
  - Table name
  - Column name
  - Date filters
  - Date fallback logic (future month → latest available)

### Phase 4: Flexible Formatter (2-3 hours)
- Replace hardcoded templates with dynamic formatting
- Use field metadata to decide response format
- Keep LLM polish for natural language

### Phase 5: Handle Special Cases (3-4 hours)
- Reimbursement queries (need FromDate/ToDate extraction)
- Multi-field responses (field + period)
- Comparisons (Jan vs Feb)

---

## Specific Fixes Needed

### 1. For "Net Taxable Income" Questions
**Problem:** Query parser doesn't recognize "net_taxable_income" as a field
**Fix:** Add to field registry, update parser to extract it

**Current Code:**
```python
# query_parser.py
if any(kw in q for kw in ["tax", "tds", "regime"]):
    parsed["intent"] = "tax"
```

**New Code:**
```python
# Extract field specifically
if "net taxable" in q or "taxable income" in q:
    parsed["field_request"] = "net_taxable_income"
```

---

### 2. For Reimbursement Period Questions
**Problem:** OT data has FromDate/ToDate but response is generic
**Fix:** Extract and format period information

**Expected Response:**
"I checked what was paid along with your May 2025 salary. You received Conveyance Reimbursement of Rs 2,990. It relates to the period 2025-03-01 to 2025-03-31, and it was paid in May 2025."

**Required Query:**
```sql
SELECT 
    paid_amount,
    component_in_pay_slip,
    from_date,
    to_date,
    paid_month
FROM ot_data
WHERE employee_id = :emp_id 
  AND paid_month = :month-:year
```

---

### 3. For Future Month Fallback
**Problem:** Apr 2026 doesn't exist, should fall back to latest (Jun 2025)
**Fix:** Add fallback logic to query executor

```python
def execute_with_fallback(table, column, employee_id, month, year):
    # Try exact month
    result = query(table, column, employee_id, month, year)
    
    if not result:
        # Fall back to latest available
        latest = query_latest_available(table, employee_id)
        return {
            "result": latest,
            "fallback": True,
            "original_month": month,
            "latest_month": latest_month
        }
```

---

### 4. For Tax Regime Questions
**Problem:** "Which regime am I under?" not recognized
**Fix:** Add tax_regime field to registry with proper aliases

---

## Quick Win: Immediate Changes

You can fix ~50% of failing tests with minimal changes:

### Change 1: Expand schema metadata (5 min)
```python
# metadata/schema_metadata.py
PAYROLL_FIELDS = {
    "net_taxable_income": ("tax_data", "NET TAXABLE INCOME"),
    "surcharge": ("tax_data", "SURCHARGE ON INCOME TAX"),
    "tax_due": ("tax_data", "INCOME TAX DUE"),
    "tax_regime": ("tax_data", "TAX REGIME"),
    "total_gross_salary": ("tax_data", "TOTAL GROSS SALARY"),
    "hra": ("pay_register", "H.R.A"),
    "lta": ("pay_register", "LTA"),
    # ... add 30+ more
}
```

### Change 2: Enhance parser intent detection (10 min)
```python
# query_parser.py - add field extraction
def extract_field_request(query: str) -> str | None:
    q = query.lower()
    for field, aliases in FIELD_ALIASES.items():
        if any(alias in q for alias in aliases):
            return field
    return None
```

### Change 3: Add fallback month logic (15 min)
```python
# tools.py - modify get_tax, get_salary, etc.
def get_salary_with_fallback(employee_id, month, year):
    result = get_salary(employee_id, month, year)
    if not result.get("data"):
        # Try latest
        latest = get_latest_salary(employee_id)
        return {
            **result,
            "data": latest["data"],
            "fallback": f"No data for {month}-{year}, showing {latest_month}"
        }
```

---

## My Recommendation

### For Next 2 Days:
1. **Day 1:** Build complete field registry (all 50+ fields)
2. **Day 2:** Implement field extraction in parser + fallback logic

This alone will fix ~60% of failing test cases.

### Then (Longer Term):
Build the dynamic query mapper (Phase 3-4 above) for remaining cases.

---

## Your Architecture is NOT Broken

The good news: Your deterministic approach is sound. You just need to:
1. Add **field-level awareness** (not just intent-level)
2. Add **date fallback logic**
3. Expand **metadata to include all columns**

The bad news: Keyword-based intent recognition can't scale to 50+ unique field types.

The solution: **Schema-driven field extraction** instead of keyword guessing.

---

## Questions for Clarification

1. **Employee ID mapping:** 
   - In LOP Tracker: "1001068" (numeric string)
   - In Pay Register: "1001452" (integer)
   - In SAOT: "1001476" (object type)
   - Are these all the same employee_id? How to normalize?

2. **Month format:**
   - Pay Register: "January", "January   " (with spaces?)
   - SAOT Tracker: "Sep-25"
   - ITax Reco: "Jan"
   - How is this normalized in your DB?

3. **Employee session:**
   - How do you know which employee_id is logged in?
   - Is it passed to `process_user_query(user_query, employee_id, ...)`?

---

