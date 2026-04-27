from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from metadata.field_registry import FieldRegistry

MONTH_ALIASES = {
    "jan": "Jan",
    "january": "Jan",
    "feb": "Feb",
    "february": "Feb",
    "mar": "Mar",
    "march": "Mar",
    "apr": "Apr",
    "april": "Apr",
    "may": "May",
    "jun": "Jun",
    "june": "Jun",
    "jul": "Jul",
    "july": "Jul",
    "aug": "Aug",
    "august": "Aug",
    "sep": "Sep",
    "sept": "Sep",
    "september": "Sep",
    "oct": "Oct",
    "october": "Oct",
    "nov": "Nov",
    "november": "Nov",
    "dec": "Dec",
    "december": "Dec",
}

MONTH_TO_NUMBER = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def extract_query_params(query: str) -> dict[str, Any]:
    q = query.lower().strip()
    parsed: dict[str, Any] = {
        "intent": "unknown",
        "field_request": None,
        "month": None,
        "year": None,
        "compare_prev": False,
        "relative_time": None,
        "fy_start": None,
        "query_type": None,
        "raw": query,
    }

    field_request = FieldRegistry.find_field(q)
    if field_request:
        parsed["field_request"] = field_request
        field_meta = FieldRegistry.get_field(field_request) or {}
        category = field_meta.get("category")
        if category == "tax":
            parsed["intent"] = "field_tax"
        elif category == "deduction":
            parsed["intent"] = "field_deduction"
        elif category == "earning":
            parsed["intent"] = "field_earning"
        else:
            parsed["intent"] = "field_total"

    if "salary" in q and any(word in q for word in ["why", "less", "reduced", "decrease", "deduction"]):
        parsed["intent"] = "salary_explanation"
    elif parsed["field_request"] is None and any(kw in q for kw in ["night shift", "overtime", "ot ", " ot", "saot"]):
        parsed["intent"] = "ot_query"
    elif parsed["field_request"] is None and any(kw in q for kw in ["allowance", "reimbursement"]):
        parsed["intent"] = "allowance_query"
    elif parsed["field_request"] is None and any(
        kw in q
        for kw in [
            "deduction",
            "deductions",
            "pf",
            "pt",
            "tax deduction",
            "earning",
            "earnings",
            "basic",
            "hra",
            "lta",
            "gratuity",
            "gross salary",
            "non tax",
            "non-tax",
        ]
    ):
        parsed["intent"] = "deduction_query"
    elif parsed["field_request"] is None and any(kw in q for kw in ["lop", "loss of pay"]):
        parsed["intent"] = "lop"
    elif parsed["field_request"] is None and any(kw in q for kw in ["tax", "tds", "regime"]):
        parsed["intent"] = "tax"
    elif parsed["field_request"] is None and any(kw in q for kw in ["salary", "net pay", "gross", "payroll", "payslip"]):
        parsed["intent"] = "salary"
        # Extract field specifically
    if "net taxable" in q or "taxable income" in q:
        parsed["field_request"] = "net_taxable_income"

    if any(
        kw in q
        for kw in [
            "less than last month",
            "less than previous month",
            "why salary less",
            "why is my salary less",
            "salary less than",
            "my salary is less",
            "salary decreased",
            "salary dropped",
            "salary reduced",
        ]
    ):
        parsed["compare_prev"] = True

    if "last month" in q or "previous month" in q:
        parsed["relative_time"] = "last_month"
    elif "this month" in q or "current month" in q:
        parsed["relative_time"] = "this_month"
    elif "last year" in q or "previous year" in q:
        parsed["relative_time"] = "last_year"
    elif "this year" in q or "current year" in q:
        parsed["relative_time"] = "this_year"

    fy_match = re.search(r"\bfy\s*(20\d{2})(?:-(20\d{2}|\d{2}))?\b", q)
    if fy_match:
        parsed["fy_start"] = int(fy_match.group(1))

    # Explicit formats: "Jan 2026", "January, 2026"
    month_year_match = re.search(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)\s*,?\s*(20\d{2})\b",
        q,
    )
    # Explicit formats: "2026 Jan", "2026 January"
    year_month_match = re.search(
        r"\b(20\d{2})\s*,?\s*(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
        r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)\b",
        q,
    )
    if month_year_match:
        parsed["month"] = MONTH_ALIASES[month_year_match.group(1).lower()]
        parsed["year"] = int(month_year_match.group(2))
    elif year_month_match:
        parsed["month"] = MONTH_ALIASES[year_month_match.group(2).lower()]
        parsed["year"] = int(year_month_match.group(1))
    else:
        year_match = re.search(r"\b(20\d{2})\b", q)
        if year_match:
            parsed["year"] = int(year_match.group(1))
        month_match = re.search(
            r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
            r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|"
            r"dec(?:ember)?)\b",
            q,
        )
        if month_match:
            parsed["month"] = MONTH_ALIASES[month_match.group(1).lower()]

    return parsed


def normalize_time(parsed: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now()
    normalized = dict(parsed)
    normalized["time_valid"] = True
    normalized["time_error"] = None

    month = normalized.get("month")
    year = normalized.get("year")
    relative_time = normalized.get("relative_time")

    if relative_time == "this_month":
        normalized["month"] = now.strftime("%b")
        normalized["year"] = now.year
    elif relative_time == "last_month":
        if now.month == 1:
            normalized["month"] = "Dec"
            normalized["year"] = now.year - 1
        else:
            prev_date = datetime(now.year, now.month - 1, 1)
            normalized["month"] = prev_date.strftime("%b")
            normalized["year"] = prev_date.year
    elif relative_time == "this_year":
        normalized["fy_start"] = now.year if now.month >= 4 else now.year - 1
    elif relative_time == "last_year":
        normalized["fy_start"] = now.year - 1 if now.month >= 4 else now.year - 2
    else:
        normalized["fy_start"] = parsed.get("fy_start")
        
        if month and year is None and not normalized.get("fy_start"):
            normalized["year"] = now.year
        elif normalized.get("compare_prev") and not month and not year:
            normalized["month"] = now.strftime("%b")
            normalized["year"] = now.year

    from metadata.query_context import QueryContext
    normalized["query_type"] = QueryContext.determine_query_type(
        query=parsed["raw"], 
        parsed_intent=parsed["intent"], 
        field_request=parsed.get("field_request")
    ).value

    if normalized.get("month") and normalized.get("year"):
        normalized["month_year"] = f"{normalized['month']}-{normalized['year']}"
    else:
        normalized["month_year"] = None

    # Future-period rejection to avoid impossible payroll lookups.
    if normalized.get("month") and normalized.get("year"):
        query_month_num = MONTH_TO_NUMBER[normalized["month"]]
        if normalized["year"] > now.year or (
            normalized["year"] == now.year and query_month_num > now.month
        ):
            normalized["time_valid"] = False
            normalized["time_error"] = (
                f"Salary data is not available for future dates ({normalized['month']}-{normalized['year']})."
            )
    elif normalized.get("year") and normalized["year"] > now.year:
        normalized["time_valid"] = False
        normalized["time_error"] = (
            f"Salary data is not available for future dates ({normalized['year']})."
        )

    if normalized.get("compare_prev") and normalized.get("month") and normalized.get("year"):
        month_num = MONTH_TO_NUMBER[normalized["month"]]
        if month_num == 1:
            normalized["previous_month"] = "Dec"
            normalized["previous_year"] = normalized["year"] - 1
        else:
            prev = datetime(normalized["year"], month_num - 1, 1)
            normalized["previous_month"] = prev.strftime("%b")
            normalized["previous_year"] = prev.year
    else:
        normalized["previous_month"] = None
        normalized["previous_year"] = None

    normalized["field_request"] = parsed.get("field_request")

    return normalized

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