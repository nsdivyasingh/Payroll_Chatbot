import pandas as pd
from chat_service import process_user_query

# -------------------------------
# CONFIG
# -------------------------------
FILE_PATH = "Ascendion_test_cases.xlsx"
EMPLOYEE_ID = 15  # test user aligned with payroll samples


# -------------------------------
# HELPER: safe console output on Windows cp1252
# -------------------------------
def safe_text(value):
    text = str(value)
    try:
        text.encode("cp1252")
        return text 
    except UnicodeEncodeError:
        return text.encode("cp1252", errors="replace").decode("cp1252")


# -------------------------------
# HELPER: resolve expected columns
# -------------------------------
def resolve_column(df, candidates):
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in normalized:
            return normalized[key]
    raise KeyError(
        f"Could not find any of these columns: {candidates}. "
        f"Available columns: {list(df.columns)}"
    )


# -------------------------------
# HELPER: simple match logic
# -------------------------------
def is_match(actual, expected):
    if pd.isna(actual) or pd.isna(expected):
        return True
    if not actual or not expected:
        return False

    actual = str(actual).lower()
    expected = str(expected).lower()

    return actual == expected


# -------------------------------
# MAIN EVALUATION
# -------------------------------
def run_evaluation():
    df = pd.read_excel(FILE_PATH)
    query_col = resolve_column(df, ["query", "question", "prompt"])
    expected_col = resolve_column(
        df,
        ["expected response", "expected answer", "response", "answer", "expected", "expected_response"],
    )

    results = []

    correct = 0
    total = len(df)

    for idx, row in df.iterrows():
        query = str(row[query_col])
        expected = row[expected_col]

        print(f"\n[Query] {safe_text(query)}")

        try:
            result = process_user_query(query, EMPLOYEE_ID)
            actual = result.get("answer") if isinstance(result, dict) else str(result)
        except Exception as e:
            actual = f"ERROR: {str(e)}"

        match = is_match(actual, expected)
        contains_match = (
            True if pd.isna(expected) else str(expected).lower() in str(actual).lower()
        )

        if match:
            correct += 1

        results.append({
            "query": query,
            "expected": "" if pd.isna(expected) else str(expected),
            "actual": actual,
            "match": match,
            "contains_match": contains_match,
        })

        print(f"Expected: {safe_text(expected)}")
        print(f"Actual: {safe_text(actual)}")
        print(f"Exact Match: {match} | Contains Match: {contains_match}")

    accuracy = (correct / total) * 100

    print("\n" + "="*50)
    print(f"Accuracy: {accuracy:.2f}% ({correct}/{total})")

    return pd.DataFrame(results)


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    df_results = run_evaluation()

    df_results.to_csv("evaluation_report.csv", index=False)
    print("\nReport saved as evaluation_report.csv")