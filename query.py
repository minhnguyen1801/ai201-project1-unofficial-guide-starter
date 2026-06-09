"""
Grounded generation for the Unofficial Guide RAG pipeline.

Connects the retriever (retrieve.py) to the Groq LLM. Retrieved review chunks
are formatted into a numbered context block and passed to the model with a
strict grounding instruction. Sources are derived from the retrieved chunks'
metadata, not parsed from the model's output.
"""

import os

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "You are a helpful guide for UIC CS students. Answer questions using ONLY "
    "the information provided in the documents below. If the documents do not "
    "contain enough information to answer the question, respond with exactly: "
    "'I don't have enough information on that topic in my documents.'\n"
    "Always end your answer with a Sources section listing which documents "
    "you drew from."
)

_api_key = os.getenv("GROQ_API_KEY")
if not _api_key or _api_key == "your_key_here":
    raise RuntimeError(
        "GROQ_API_KEY is not set. Copy .env.example to .env and add your Groq "
        "API key (get one free at https://console.groq.com)."
    )

_client = Groq(api_key=_api_key)


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered, attributed context block."""
    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(
            f"[{i}] Professor: {c['professor']} | Course: {c['course']}\n"
            f"Review: {c['text']}"
        )
    return "\n\n".join(lines)


def _build_sources(chunks: list[dict]) -> list[str]:
    """Derive deduplicated source strings from chunk metadata (order preserved)."""
    sources: list[str] = []
    seen: set[str] = set()
    for c in chunks:
        label = f"{c['professor']} ({c['course']}) — {c['source']}"
        if label not in seen:
            seen.add(label)
            sources.append(label)
    return sources


def ask(question: str) -> dict:
    """Answer `question` from retrieved UIC CS reviews.

    Returns {answer, sources} where sources is a list of strings like
    "Scott Reckinger (CS211) — CS211_Reckinger.txt".
    """
    chunks = retrieve(question, k=5)
    context = _build_context(chunks)
    sources = _build_sources(chunks)

    user_message = (
        f"Documents:\n{context}\n\n"
        f"Question: {question}"
    )

    completion = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )
    answer = completion.choices[0].message.content

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    result = ask("What do students say about exam difficulty in CS 251 with Daniel Ayala?")
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  - {s}")
