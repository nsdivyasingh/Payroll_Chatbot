from sentence_transformers import SentenceTransformer
import json
import numpy as np

with open('faq_all.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

model = SentenceTransformer('all-MiniLM-L6-v2')
texts = [f"Question: {item['question']} Answer: {item['answer']}" for item in data]

print("Generating embeddings... this may take a moment.")
embeddings = model.encode(texts, show_progress_bar=True)

print(f"Successfully vectorized {len(embeddings)} items.")

np.save("faq_embeddings.npy", embeddings)

with open("faq_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)