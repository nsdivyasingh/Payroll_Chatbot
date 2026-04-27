# Payroll Chatbot - Step-by-Step Implementation Guide

## Current Status
- ✅ Parser extracts: intent, month, year
- ❌ Parser doesn't extract: specific field requests
- ❌ No field-to-database mapping
- ❌ No date fallback logic
- ❌ No handling for special cases (reimbursement periods, tax regime, etc.)

---

## STEP 1: Enhance the Query Parser (2-3 hours)

### What to Change
File: `query_parser.py`

### Addition 1: Import field registry (at top)
```python
from metadata.field_registry import FieldRegistry

def extract_field_request(query: str) -> str | None:
    """Extract specific field request from query"""
    return FieldRegistry.find_field(query)
```

### Addition 2: Modify extract_query_params()
Replace the existing intent-only logic with field-aware parsing:

```python
def extract_query_params(query: str) -> dict[str, Any]:
    q = query.lower().strip()
    parsed: dict[str, Any] = {
        "intent": "unknown",
        "field_request": None,  # NEW
        "month": None,
        "year": None,
        "compare_prev": False,
        "relative_time": None,
        "raw": query,
    }

    # === NEW: Try field extraction first ===
    field_request = extract_field_request(q)
    if field_request:
        parsed["field_request"] = field_request
        # Infer intent from field category
        field_meta = FieldRegistry.get_field(field_request)
        if field_meta["category"] == "earning":
            parsed["intent"] = "field_earning"
        elif field_meta["category"] == "deduction":
            parsed["intent"] = "field_deduction"
        elif field_meta["category"] == "tax":
            parsed["intent"] = "field_tax"
        else:
            parsed["intent"] = "field_total"
    else:
        # === EXISTING: Fallback to intent-only matching ===
        if any(token in q for token in ("salary", "net pay", "pay")) and any(
            token in q for token in ("why", "less", "decrease", "reduced", "drop", "dropped")
        ):
            parsed["intent"] = "salary_explanation"
        elif any(kw in q for kw in ["night shift", "overtime", "ot ", " ot"]):
            parsed["intent"] = "ot_query"
        # ... rest of existing logic ...

    # === Time extraction (EXISTING, keep as is) ===
    # Month/year extraction code...

    return parsed
```

### Addition 3: Add to normalize_time()
```python
def normalize_time(parsed: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    # ... existing code ...
    
    # Add field request to normalized output
    normalized["field_request"] = parsed.get("field_request")
    
    return normalized
```

---

## STEP 2: Create Field Registry (1-2 hours)

### What to Create
New file: `metadata/field_registry.py`

Use the template from FIELD_REGISTRY_TEMPLATE.py (already created).

### Copy the entire FieldRegistry class into this new file

This gives you:
- ✅ Complete mapping of 30+ fields
- ✅ Aliases for variations ("HRA" = "house rent allowance")
- ✅ Response templates per field
- ✅ Semantic descriptions

---

## STEP 3: Enhance Tool Planner (1-2 hours)

### What to Change
File: `tool_planner.py`

### Replace existing logic with field-aware routing:

```python
from metadata.field_registry import FieldRegistry

def plan_tool(parsed_query: dict, employee_id: int) -> dict:
    """Enhanced tool planner that handles field requests"""
    
    intent = parsed_query.get("intent")
    field_request = parsed_query.get("field_request")  # NEW
    month = parsed_query.get("month")
    year = parsed_query.get("year")

    base_params = {
        "employee_id": employee_id,
        "month": month,
        "year": year,
    }

    # === NEW: Field-specific routing ===
    if field_request:
        field_meta = FieldRegistry.get_field(field_request)
        if field_meta["table"] == "pay_register":
            return {
                "tool": "get_field_value",  # NEW generic tool
                "params": {
                    **base_params,
                    "field_key": field_request,
                    "table": "pay_register",
                    "column": field_meta["column"],
                }
            }
        elif field_meta["table"] == "tax_data":
            return {
                "tool": "get_field_value",  # Same generic tool
                "params": {
                    **base_params,
                    "field_key": field_request,
                    "table": "tax_data",
                    "column": field_meta["column"],
                }
            }
    
    # === EXISTING: Fallback to intent-based routing ===
    if intent == "salary_explanation":
        return {
            "tool": "analyze_salary",
            "params": {
                **base_params,
                "previous_month": parsed_query.get("previous_month"),
                "previous_year": parsed_query.get("previous_year"),
            },
        }
    # ... rest of existing logic ...


def validate_plan(plan: dict) -> bool:
    """Updated validation for new tool types"""
    tool = plan.get("tool")
    params = plan.get("params", {})
    
    if tool == "fallback":
        return True
    
    if not isinstance(params, dict):
        return False
    
    if params.get("employee_id") in (None, ""):
        return False
    
    # NEW: "get_field_value" doesn't require month/year
    if tool == "get_field_value":
        return params.get("field_key") and params.get("table") and params.get("column")
    
    # EXISTING: Other tools need month/year
    if tool == "analyze_salary":
        if params.get("previous_month") in (None, "") or params.get("previous_year") in (None, ""):
            return False
    else:
        if params.get("month") in (None, "") or params.get("year") in (None, ""):
            return False
    
    return True
```

---

## STEP 4: Add New Generic Tool (2-3 hours)

### What to Change
File: `tools.py`

### Addition: Add new generic field-value tool

```python
def get_field_value(
    employee_id: int, 
    field_key: str,
    table: str,
    column: str,
    month: str | None = None, 
    year: int | None = None
) -> dict[str, Any]:
    """
    Generic tool to fetch any field value from any table.
    Handles date fallback logic.
    """
    from metadata.field_registry import FieldRegistry
    
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_field_value", **validation_error}
    
    if not employee_exists(employee_id):
        return {
            "tool": "get_field_value",
            "status": "no_data",
            "message": "Employee not found",
            "data": None
        }
    
    # Try exact month/year first
    if month and year is not None:
        month_year = f"{month}-{year}"
        query = text(f"""
            SELECT {column} as value
            FROM {table}
            WHERE employee_id = :emp_id 
              AND month = :month_year
            LIMIT 1
        """)
        params = {"emp_id": employee_id, "month_year": month_year}
    else:
        # No date specified - get latest
        query = text(f"""
            SELECT {column} as value
            FROM {table}
            WHERE employee_id = :emp_id
            ORDER BY eyear DESC, month DESC
            LIMIT 1
        """)
        params = {"emp_id": employee_id}
    
    print(f"[QUERY] field_value -> field={field_key}, table={table}, emp={employee_id}, month={month}, year={year}")
    
    with engine.connect() as conn:
        row = conn.execute(query, params).fetchone()
    
    if not row:
        # === NEW: Date fallback logic ===
        if month and year:
            # Try latest available instead
            query_latest = text(f"""
                SELECT {column} as value, month, eyear
                FROM {table}
                WHERE employee_id = :emp_id
                ORDER BY eyear DESC, month DESC
                LIMIT 1
            """)
            with engine.connect() as conn:
                row = conn.execute(query_latest, {"emp_id": employee_id}).fetchone()
            
            if row:
                data = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
                return {
                    "tool": "get_field_value",
                    "status": "success_fallback",
                    "field_key": field_key,
                    "value": data.get("value"),
                    "fallback_to": f"{data.get('month')}-{data.get('eyear')}",
                    "original_request": f"{month}-{year}",
                }
        
        return {
            "tool": "get_field_value",
            "status": "no_data",
            "message": f"No data found for {field_key}",
            "data": None
        }
    
    data = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
    return {
        "tool": "get_field_value",
        "status": "success",
        "field_key": field_key,
        "value": data.get("value"),
        "month": month,
        "year": year,
    }
```

### Addition 2: Update execute_tool()
```python
def execute_tool(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
    tool = str(tool_name).strip().lower()
    
    if tool not in ALLOWED_TOOLS:
        # ADD THIS LINE:
        if tool != "get_field_value":  # Allow the new generic tool
            return {
                "tool": tool_name,
                "status": "error",
                "message": f"Unsupported tool '{tool_name}'",
                "data": [],
            }
    
    employee_id = params.get("employee_id")
    month = params.get("month")
    year = params.get("year")
    
    try:
        # === NEW: Handle field value requests ===
        if tool == "get_field_value":
            return get_field_value(
                employee_id=employee_id,
                field_key=params.get("field_key"),
                table=params.get("table"),
                column=params.get("column"),
                month=month,
                year=year,
            )
        
        # === EXISTING: Original tools ===
        if tool == "get_salary":
            return get_salary(employee_id=employee_id, month=month, year=year)
        # ... rest of existing logic ...
```

---

## STEP 5: Enhanced Formatting (2-3 hours)

### What to Change
File: `chat_service.py`

### Modification 1: Add field-aware formatting

```python
def _format_field_response(
    field_key: str,
    tool_data: dict[str, Any],
    month: str | None,
    year: int | None,
) -> str:
    """Format response based on field metadata"""
    from metadata.field_registry import FieldRegistry
    
    field_meta = FieldRegistry.get_field(field_key)
    if not field_meta:
        return FALLBACK_MSG
    
    value = tool_data.get("value")
    if value is None:
        return FALLBACK_MSG
    
    # Format value based on field type
    if field_meta["unit"] == "amount":
        formatted_value = f"₹{int(float(value)):,}" if value else "₹0"
    else:
        formatted_value = str(value)
    
    # Handle fallback month
    fallback_to = tool_data.get("fallback_to")
    if fallback_to:
        # "No data for Apr 2026, here's Jun 2025 data"
        fallback_month, fallback_year = fallback_to.split("-")
        prefix = f"I don't have payroll records for {month} {year} yet. Here is the data for the latest available month, {fallback_month} {fallback_year}. "
    else:
        prefix = ""
    
    # Use template from registry
    template = field_meta["response_template"]
    response = template.format(
        value=formatted_value,
        month=month or "the requested period",
        year=year or "",
    )
    
    return prefix + response
```

### Modification 2: Update _safe_format()

```python
def _safe_format(
    user_query: str,
    tool_name: str,
    tool_data: dict[str, Any],
    plan: dict[str, Any],
    context: str = "",
) -> str:
    
    # === NEW: Handle field value responses ===
    if tool_name == "get_field_value":
        field_key = plan.get("params", {}).get("field_key")
        month = plan.get("params", {}).get("month")
        year = plan.get("params", {}).get("year")
        
        deterministic_answer = _format_field_response(field_key, tool_data, month, year)
        if deterministic_answer == FALLBACK_MSG:
            return FALLBACK_MSG
        
        # Polish with LLM if needed
        try:
            polished = _format_with_llm(
                query=user_query,
                tool_data=tool_data,
                base_answer=deterministic_answer,
                context=context,
            )
            return polished or deterministic_answer
        except Exception as exc:
            print(f"LLM polish skipped: {exc}")
            return deterministic_answer
    
    # === EXISTING: Original formatting logic ===
    deterministic_answer = _deterministic_format(...)
    # ... rest of existing code ...
```

---

## STEP 6: Update ALLOWED_TOOLS

### What to Change
File: `tools.py`

```python
ALLOWED_TOOLS = {
    "get_salary",
    "get_lop",
    "get_tax",
    "get_ot",
    "analyze_salary",
    "get_full_salary_breakdown",
    "get_allowance_breakdown",
    "get_field_value",  # ADD THIS
}
```

---

## STEP 7: Test the Changes

### Quick Test File

```python
# test_field_registry.py

def test_field_extraction():
    from metadata.field_registry import FieldRegistry
    
    test_queries = [
        ("What is my net taxable income?", "net_taxable_income"),
        ("What is my HRA for June?", "hra"),
        ("What is my surcharge?", "surcharge"),
        ("Give me my tax regime", "tax_regime"),
    ]
    
    for query, expected_field in test_queries:
        field = FieldRegistry.find_field(query)
        print(f"Query: {query}")
        print(f"Expected: {expected_field}, Got: {field}")
        print(f"✓ PASS" if field == expected_field else "✗ FAIL")
        print()

def test_end_to_end():
    from query_parser import extract_query_params, normalize_time
    from tool_planner import plan_tool
    
    query = "What is my net taxable income for Jan 2026?"
    parsed = extract_query_params(query)
    normalized = normalize_time(parsed)
    plan = plan_tool(normalized, employee_id=1001452)
    
    print(f"Query: {query}")
    print(f"Parsed: {parsed}")
    print(f"Normalized: {normalized}")
    print(f"Plan: {plan}")
    
    # Should now plan to "get_field_value" instead of failing

if __name__ == "__main__":
    test_field_extraction()
    test_end_to_end()
```

---

## Summary: What Gets Fixed

With these 7 steps, you'll fix:

### Tests that currently FAIL → Will PASS:
- ✅ "What is my net taxable income?" 
- ✅ "What is my surcharge?"
- ✅ "What is my tax due?"
- ✅ "What is my tax regime?"
- ✅ "What is my HRA?"
- ✅ "What is my LTA?"
- ✅ "What is my PF deduction?"
- ✅ "What is my total gross salary?"
- ✅ Any future date → fallback to latest available month
- ✅ ~30-40 test cases total

### Tests that still need work:
- Reimbursement period extraction (requires OT-specific logic)
- Comparisons (Jan vs Feb)
- Year-aggregate queries

---

## Implementation Timeline

- Day 1 (4 hours):
  - Step 1: Enhance parser
  - Step 2: Create field registry
  - Test basic field extraction

- Day 2 (4 hours):
  - Step 3: Update tool planner
  - Step 4: Add generic tool
  - Test end-to-end

- Day 3 (3 hours):
  - Step 5: Enhanced formatting
  - Step 6: Update ALLOWED_TOOLS
  - Step 7: Full test suite

**Total: 11 hours → ~60% test case fixes**

Then, work on special cases (reimbursement, comparison) separately.

