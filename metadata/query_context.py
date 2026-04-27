from enum import Enum
from typing import Dict, Any

class QueryType(Enum):
    FIELD_VALUE = "field_value"
    SINGLE_FIELD = "single_field"
    AGGREGATE = "aggregate"
    COMPARISON = "comparison"
    BREAKDOWN = "breakdown"
    FY_OVERVIEW = "fy_overview"
    OT_REIMBURSEMENT = "ot_reimbursement"

class QueryContext:
    """Manages the contextual routing and type matching for queries."""
    
    TOOL_ROUTING = {
        QueryType.BREAKDOWN: "get_full_salary_breakdown",
        QueryType.COMPARISON: "analyze_salary",
        QueryType.OT_REIMBURSEMENT: "get_ot_reimbursement", 
        QueryType.FY_OVERVIEW: "get_salary",
        QueryType.FIELD_VALUE: "get_field_value"
    }

    @staticmethod
    def determine_query_type(query: str, parsed_intent: str, field_request: str | None = None) -> QueryType:
        q = query.lower()
        if "compare" in q or "difference" in q or "why" in q or "less" in q or "increase" in q or "decrease" in q:
            return QueryType.COMPARISON
        if "financial year" in q or "fy" in q or "this year" in q or "last year" in q:
            return QueryType.FY_OVERVIEW
        if "reimbursement" in q or "overtime" in q or "ot" in q:
            return QueryType.OT_REIMBURSEMENT
        if "breakdown" in q or "all deductions" in q or "all earnings" in q:
            return QueryType.BREAKDOWN
        if field_request:
            return QueryType.FIELD_VALUE
        if parsed_intent in ["salary_explanation"]:
            return QueryType.COMPARISON
        if parsed_intent == "deduction_query" and "tax" not in q:
            return QueryType.BREAKDOWN
        return QueryType.SINGLE_FIELD
        
    @staticmethod
    def get_tool_for_type(query_type: QueryType) -> str | None:
        return QueryContext.TOOL_ROUTING.get(query_type)
