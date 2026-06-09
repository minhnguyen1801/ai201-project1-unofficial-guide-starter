"""
Retrieval for the Unofficial Guide RAG pipeline.

Loads the persistent ChromaDB collection built by embed.py and exposes a
retrieve() function that returns the top-k most similar review chunks for a
query, along with their source metadata and similarity distance.
"""

import chromadb
from sentence_transformers import SentenceTransformer

from embed import COLLECTION_NAME, EMBED_MODEL, PERSIST_DIR

# Load the embedding model and collection once at import time.
_model = SentenceTransformer(EMBED_MODEL)
_client = chromadb.PersistentClient(path=PERSIST_DIR)
_collection = _client.get_collection(COLLECTION_NAME)


def retrieve(query: str, k: int = 5) -> list[dict]:
    """Return the top-k chunks most similar to `query`.

    Each result dict has: text, source, professor, course, distance.
    """
    query_embedding = _model.encode([query]).tolist()
    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=k,
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    out = []
    for text, meta, distance in zip(documents, metadatas, distances):
        out.append(
            {
                "text": text,
                "source": meta.get("source"),
                "professor": meta.get("professor"),
                "course": meta.get("course"),
                "distance": distance,
            }
        )
    return out


def print_results(query: str, results: list[dict]) -> None:
    print(f"\n{'=' * 70}")
    print(f"QUERY: {query}")
    print("=" * 70)
    for rank, r in enumerate(results, 1):
        preview = r["text"][:200] + ("..." if len(r["text"]) > 200 else "")
        print(
            f"\n  [{rank}] distance={r['distance']:.4f} | "
            f"{r['professor']} | {r['course']} | {r['source']}"
        )
        print(f"      {preview}")


if __name__ == "__main__":
    test_queries = [
        "What do students say about exam difficulty in CS 251 with Daniel Ayala?",
        "Is CS 401 with DasGupta recommended and what is the workload like?",
        "What are common complaints about Scott Reckinger in CS 211?",
    ]
    for q in test_queries:
        print_results(q, retrieve(q, k=5))
