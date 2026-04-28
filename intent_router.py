def classify_intent(query: str) -> str:
    q = query.lower()

    # FAQ type
    faq_keywords = ["policy", "leave policy", "benefits", "rules"]
    if any(k in q for k in faq_keywords):
        return "faq"

    # Data queries
    data_keywords = [
        "salary", "tax", "lop", "deduction",
        "allowance", "bonus", "pf", "income"
    ]
    if any(k in q for k in data_keywords):
        return "data"

    return "unknown"