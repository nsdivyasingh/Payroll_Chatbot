import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
model = SentenceTransformer('all-MiniLM-L6-v2')

embeddings = np.load("faq_embeddings.npy")
with open("faq_all.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def retrieve_one(query, threshold=0.5):
    query_embedding = model.encode([query])
    similarities = cosine_similarity(query_embedding, embeddings)[0]

    best_idx = similarities.argmax()
    best_score = similarities[best_idx]

    if best_score < threshold:
        return None

    return data[best_idx]

print("FAQ Bot — type 'exit' to quit\n")

while True:
    query = input("You: ")

    if query.lower() in ["exit", "quit"]:
        print("Bot: Have a Good Day!")
        break

    result = retrieve_one(query)

    if result:
        print("\nBot:", result["answer"], "\n")
    else:
        print("\nBot: Sorry, I couldn't find a relevant answer for your query. Please contact the PayRoll team\n")