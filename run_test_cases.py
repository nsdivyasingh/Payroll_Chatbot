from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from chat_service import process_user_query


def _normalize_colnames(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def run_test_cases(test_file: str, employee_id: int, limit: int | None = None) -> pd.DataFrame:
    xls = pd.ExcelFile(test_file)
    rows = []
    count = 0
    for sheet in xls.sheet_names:
        df = pd.read_excel(test_file, sheet_name=sheet)
        df = _normalize_colnames(df)
        if "query" not in df.columns:
            continue
        expected_col = "answer" if "answer" in df.columns else "response" if "response" in df.columns else None

        for _, row in df.iterrows():
            query = str(row.get("query", "")).strip()
            if not query or query.lower() == "nan":
                continue
            expected = str(row.get(expected_col, "")).strip() if expected_col else ""
            result = process_user_query(query, employee_id=employee_id)
            rows.append(
                {
                    "sheet": sheet,
                    "query": query,
                    "expected": expected,
                    "actual": result.get("answer", ""),
                    "status": result.get("status"),
                    "source": result.get("source"),
                    "tool": (result.get("tool_call") or {}).get("tool"),
                    "tool_month": (result.get("tool_call") or {}).get("month"),
                }
            )
            count += 1
            if limit is not None and count >= limit:
                return pd.DataFrame(rows)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run chatbot against Excel test cases.")
    parser.add_argument("--test-file", default="Ascendion_test_cases.xlsx")
    parser.add_argument("--employee-id", type=int, required=True)
    parser.add_argument("--out", default="logs/test_results.xlsx")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    results_df = run_test_cases(args.test_file, employee_id=args.employee_id, limit=args.limit)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_excel(out_path, index=False)
    print(f"Saved {len(results_df)} test results to {out_path}")


if __name__ == "__main__":
    main()
