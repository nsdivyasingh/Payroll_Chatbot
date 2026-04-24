from query_engine import get_salary
from llm_handler import ask_llm

def chatbot(user_query):
    
    # Step 1: ask LLM to extract info
    prompt = f"""
    Extract employee_id and month from this query.
    If not present, return null.

    Query: {user_query}

    Output JSON:
    {{
        "employee_id": int,
        "month": string or null
    }}
    """

    extraction = ask_llm(prompt)
    print("LLM extraction:", extraction)

    # ⚠️ for now manually parse (we'll improve later)
    if "3" in extraction:
        employee_id = 3
    else:
        employee_id = 1

    month = None

    # Step 2: fetch from DB
    data = get_salary(employee_id, month)

    # Step 3: generate final answer
    answer_prompt = f"""
    User asked: {user_query}

    Data:
    {data}

    Explain clearly in a professional way.
    """

    answer = ask_llm(answer_prompt)

    return answer


# test
print(chatbot("What is my salary?"))