"""
Embedding + vector store for the Unofficial Guide RAG pipeline.

Loads all chunks (via chunk.load_chunks), embeds them with all-MiniLM-L6-v2,
and stores them in a persistent ChromaDB collection. The collection is rebuilt
from scratch on every run so re-ingested documents stay in sync.
"""

import chromadb
from sentence_transformers import SentenceTransformer

from chunk import load_chunks

EMBED_MODEL = "all-MiniLM-L6-v2"
PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "uic_cs_reviews"
BATCH_SIZE = 100


def build_collection():
    """Embed all chunks and (re)create the ChromaDB collection from scratch."""
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from documents/.")

    print(f"Loading embedding model: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)

    client = chromadb.PersistentClient(path=PERSIST_DIR)

    # Fresh rebuild: drop the collection if it already exists.
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        print(f"Collection '{COLLECTION_NAME}' exists — deleting for fresh rebuild.")
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    total = len(chunks)
    stored = 0
    for start in range(0, total, BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        documents = [c.text for c in batch]
        metadatas = [c.metadata for c in batch]
        ids = [
            f"{c.metadata['source']}_{c.metadata['chunk_index']}" for c in batch
        ]
        embeddings = model.encode(documents, show_progress_bar=False).tolist()

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        stored += len(batch)
        print(f"  embedded & stored {stored}/{total} chunks")

    print(f"\nDone. {stored} chunks embedded and stored in '{COLLECTION_NAME}'.")
    print(f"Persisted to {PERSIST_DIR}")
    return collection


if __name__ == "__main__":
    build_collection()
