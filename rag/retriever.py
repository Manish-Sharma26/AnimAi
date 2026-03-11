"""
RAG Retriever — searches Manim docs for relevant patterns
given a user query.
"""

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Load once globally so we don't reload every request
_model = None
_index = None
_chunks = None


def load_rag():
    """Load the FAISS index and chunks into memory."""
    global _model, _index, _chunks

    if _model is not None:
        return  # already loaded

    print("[RAG] Loading search index...")

    _model = SentenceTransformer('all-MiniLM-L6-v2')

    with open("rag/manim_chunks.json", "r") as f:
        _chunks = json.load(f)

    _index = faiss.read_index("rag/manim_docs.index")

    print(f"[RAG] Loaded {len(_chunks)} chunks ready to search")


def retrieve(query: str, k: int = 4) -> str:
    """
    Searches the Manim docs index for chunks relevant to the query.
    Returns a formatted string of the top-k results to inject into prompt.
    """
    load_rag()

    # Embed the query
    query_embedding = _model.encode([query], convert_to_numpy=True).astype(np.float32)

    # Search FAISS
    distances, indices = _index.search(query_embedding, k)

    # Format results for prompt injection
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(_chunks):
            chunk = _chunks[idx]
            results.append(f"# Relevant Manim pattern {i+1} (from {chunk['source']}):\n{chunk['content']}")

    return "\n\n---\n\n".join(results)


if __name__ == "__main__":
    # Quick test
    result = retrieve("animate binary search tree nodes")
    print("Search results:")
    print(result[:500])