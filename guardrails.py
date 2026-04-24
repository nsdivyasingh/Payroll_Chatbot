from __future__ import annotations

import re

BLOCK_PATTERNS = [
    r"\bother employee\b",
    r"\bsomeone else\b",
    r"\bcolleague\b",
    r"\bteam member\b",
    r"\bsalary of employee\s*\d+\b",
    r"\btax of employee\s*\d+\b",
    r"\blop of employee\s*\d+\b",
    r"\bcompare (my )?salary\b",
    r"\bwhose salary\b",
    r"\bemployee id\s*[:=]?\s*\d+\b",
]


def validate_query_scope(query: str) -> tuple[bool, str]:
    lowered = query.lower().strip()
    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, lowered):
            return (
                False,
                "I can only help with your own payroll details. "
                "Please contact the payroll team for any cross-employee request.",
            )
    return True, ""
