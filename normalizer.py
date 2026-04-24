from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

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


@dataclass
class NormalizedQuery:
    query: str
    target_month: str | None
    comparison_month: str | None
    relative_month_keyword: str | None


def _format_month_year(year: int, month: int) -> str:
    return datetime(year, month, 1).strftime("%b-%Y")


def _previous_month(ref: datetime) -> tuple[int, int]:
    if ref.month == 1:
        return ref.year - 1, 12
    return ref.year, ref.month - 1


def normalize_query_dates(query: str, now: datetime | None = None) -> NormalizedQuery:
    now = now or datetime.now()
    q = query.lower().strip()
    target_month = None
    comparison_month = None
    relative_keyword = None

    # Special comparative phrase: current month vs previous month.
    if "less than last month" in q or "less than previous month" in q:
        target_month = _format_month_year(now.year, now.month)
        y, m = _previous_month(now)
        comparison_month = _format_month_year(y, m)
        relative_keyword = "current_vs_previous"
    # Relative month keywords.
    elif "this month" in q or "current month" in q:
        target_month = _format_month_year(now.year, now.month)
        relative_keyword = "this_month"
    elif "previous month" in q or "last month" in q:
        y, m = _previous_month(now)
        target_month = _format_month_year(y, m)
        relative_keyword = "previous_month"

    # Explicit month + year (e.g. Sep 2025, september 2025).
    month_year_match = re.search(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)\s*,?\s*(20\d{2})\b",
        q,
    )
    if month_year_match:
        month_text = month_year_match.group(1).lower()
        year = int(month_year_match.group(2))
        month = MONTH_ALIASES[month_text]
        target_month = f"{month}-{year}"
        relative_keyword = "explicit_month"

    # If no explicit month and user asks less than previous/last month, compare with previous month.
    comparison_cues = [
        "less than last month",
        "less than previous month",
        "reduced compared to last month",
        "salary got reduced",
        "why is my salary less",
    ]
    if target_month is None and any(cue in q for cue in comparison_cues):
        y, m = _previous_month(now)
        comparison_month = _format_month_year(y, m)
        relative_keyword = relative_keyword or "comparison_previous_month"

    return NormalizedQuery(
        query=query,
        target_month=target_month,
        comparison_month=comparison_month,
        relative_month_keyword=relative_keyword,
    )
