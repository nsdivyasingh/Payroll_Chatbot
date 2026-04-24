from __future__ import annotations

import json
import os
import pickle

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

from build_faq_kb import main as build_faq_kb

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

_model = None
_embeddings = None
_faq_data = None
_faq_init_error = None
_backend = None
_vectorizer = None


def _ensure_faq_resources():
    global _model, _embeddings, _faq_data, _faq_init_error, _backend, _vectorizer
    if _model is not None and _embeddings is not None and _faq_data is not None:
        return True
    try:
        if not Path("faq_all.json").exists() or not Path("faq_embeddings.npy").exists():
            build_faq_kb()
        meta_path = Path("faq_index_meta.json")
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            _backend = meta.get("backend", "sentence_transformers")
        else:
            _backend = "sentence_transformers"

        _embeddings = np.load("faq_embeddings.npy")
        with open("faq_all.json", "r", encoding="utf-8") as f:
            _faq_data = json.load(f)

        if _backend == "sentence_transformers":
            # Local import to avoid startup crashes if transformer deps are broken.
            from sentence_transformers import SentenceTransformer  # pylint: disable=import-outside-toplevel

            _model = SentenceTransformer("all-MiniLM-L6-v2")
        elif _backend == "tfidf":
            with open("faq_vectorizer.pkl", "rb") as fp:
                _vectorizer = pickle.load(fp)
            _model = "tfidf"
        else:
            raise RuntimeError(f"Unsupported FAQ backend: {_backend}")

        return True
    except Exception as exc:  # noqa: BLE001
        _faq_init_error = str(exc)
        return False


def retrieve_faq(query: str, threshold: float = 0.5) -> dict | None:
    if not _ensure_faq_resources():
        return None

    if _backend == "sentence_transformers":
        query_embedding = _model.encode([query])
    else:
        query_embedding = _vectorizer.transform([query]).toarray()

    similarities = cosine_similarity(query_embedding, _embeddings)[0]
    best_idx = int(similarities.argmax())
    best_score = float(similarities[best_idx])
    if best_score < threshold:
        return None
    result = _faq_data[best_idx]
    return {"answer": result.get("answer", ""), "score": best_score}
