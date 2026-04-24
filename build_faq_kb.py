from __future__ import annotations

import json
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


def extract_faq_pairs_from_excel(path: str) -> list[dict[str, str]]:
    xls = pd.ExcelFile(path)
    faq_pairs: list[dict[str, str]] = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        # Each FAQ is often laid out as alternating question row and answer row.
        values = [str(v).strip() for v in df.stack().tolist() if str(v).strip() and str(v) != "nan"]
        for i in range(len(values) - 1):
            q = values[i]
            a = values[i + 1]
            if q.endswith("?") and not a.endswith("?"):
                faq_pairs.append(
                    {
                        "question": q,
                        "answer": a,
                        "source_sheet": sheet,
                    }
                )
    # De-duplicate by question text.
    seen = set()
    unique = []
    for item in faq_pairs:
        key = item["question"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def main() -> None:
    faq_pairs = extract_faq_pairs_from_excel("FAQ_data.xlsx")
    if not faq_pairs:
        raise RuntimeError("No FAQ pairs extracted from FAQ_data.xlsx")

    out_json = Path("faq_all.json")
    out_json.write_text(json.dumps(faq_pairs, ensure_ascii=False, indent=2), encoding="utf-8")

    texts = [f["question"] for f in faq_pairs]
    backend = "sentence_transformers"
    embeddings = None

    try:
        from sentence_transformers import SentenceTransformer  # pylint: disable=import-outside-toplevel

        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(texts, show_progress_bar=True)
    except Exception as exc:  # noqa: BLE001
        # Safe fallback when transformer/tensorflow/protobuf deps are broken.
        backend = "tfidf"
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
        embeddings = vectorizer.fit_transform(texts).toarray()
        with open("faq_vectorizer.pkl", "wb") as fp:
            pickle.dump(vectorizer, fp)
        print(f"[WARN] sentence-transformers unavailable, using TF-IDF fallback: {exc}")

    np.save("faq_embeddings.npy", embeddings)
    Path("faq_index_meta.json").write_text(
        json.dumps({"backend": backend}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Built FAQ KB with {len(faq_pairs)} Q/A pairs")
    print(f"Saved faq_all.json, faq_embeddings.npy using backend: {backend}")


if __name__ == "__main__":
    main()
