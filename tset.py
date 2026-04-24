from chat_service import process_user_query

employee_id = 3

queries = [
    "salary in Jan",
    "salary last month",
    "salary this month",
    "salary for february",
    "salary for 2026 jan",
    "why is my salary less",
    "why is my salary less in jan",
    "tax in feb",
    "lop in nov",
    "salary in 2030",
    "salary of employee 5",
]

for q in queries:
    print("\nQUERY:", q)
    response = process_user_query(q, employee_id)
    print("RESPONSE:", response)