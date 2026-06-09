"""
Chunking for the Unofficial Guide RAG pipeline.

Loads every .txt document from documents/, splits it into chunks, attaches
metadata to each chunk, and prints 5 random samples for inspection.

Chunking strategy (see planning.md):
  - Each `[REVIEW]` line is one natural chunk (review-boundary splitting).
  - If a review exceeds CHUNK_SIZE characters, it is split further with
    OVERLAP characters of overlap between consecutive sub-chunks.
  - Empty chunks are discarded.

Each chunk carries metadata:
  {source, professor, course, chunk_index}
"""

import random
from dataclasses import dataclass, field
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).parent / "documents"

CHUNK_SIZE = 500   # characters
OVERLAP = 50       # characters

# Maps a (course, lastname) filename back to the professor's full name.
# Falls back to the lastname token if a file isn't listed here.
FULL_NAMES = {
    ("CS141", "Gu"): "Zhaochen Gu",
    ("CS141", "Hodges"): "Mark Hodges",
    ("CS141", "Reed"): "Dale Reed",
    ("CS141", "Theys"): "Mitchell Theys",
    ("CS211", "Reckinger"): "Scott Reckinger",
    ("CS211", "Bell"): "John Bell",
    ("CS211", "Hayes"): "David Hayes",
    ("CS251", "Ayala"): "Daniel Ayala",
    ("CS251", "Reckinger"): "Scott Reckinger",
    ("CS251", "Koehler"): "Adam Koehler",
    ("CS362", "Theys"): "Mitchell Theys",
    ("CS362", "Troy"): "Pat Troy",
    ("CS401", "Dasgupta"): "Bhaskar Dasgupta",
    ("CS401", "Sun"): "Xiaorui Sun",
}


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def parse_filename(path: Path) -> tuple[str, str]:
    """Return (course, professor_name) inferred from a `<course>_<last>.txt` name."""
    stem = path.stem
    course, _, last = stem.partition("_")
    professor = FULL_NAMES.get((course, last), last or stem)
    return course, professor


def split_long(text: str, size: int, overlap: int) -> list[str]:
    """Split text longer than `size` into windows with `overlap` chars shared."""
    if len(text) <= size:
        return [text]
    step = size - overlap
    if step <= 0:
        raise ValueError("OVERLAP must be smaller than CHUNK_SIZE")
    pieces = []
    start = 0
    while start < len(text):
        pieces.append(text[start : start + size])
        start += step
    return pieces


def chunk_file(path: Path) -> list[Chunk]:
    """Chunk a single document by review boundary, then by length."""
    course, professor = parse_filename(path)
    chunks: list[Chunk] = []
    index = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        review = line.strip()
        if not review:
            continue
        for piece in split_long(review, CHUNK_SIZE, OVERLAP):
            piece = piece.strip()
            if not piece:  # filter out empty chunks
                continue
            chunks.append(
                Chunk(
                    text=piece,
                    metadata={
                        "source": path.name,
                        "professor": professor,
                        "course": course,
                        "chunk_index": index,
                    },
                )
            )
            index += 1
    return chunks


def load_chunks() -> list[Chunk]:
    files = sorted(DOCUMENTS_DIR.glob("*.txt"))
    if not files:
        raise SystemExit(
            f"No .txt documents found in {DOCUMENTS_DIR}. Run ingest.py first."
        )
    all_chunks: list[Chunk] = []
    for path in files:
        all_chunks.extend(chunk_file(path))
    return all_chunks


def main() -> None:
    chunks = load_chunks()
    print(f"Total chunks: {len(chunks)}\n")

    if not chunks:
        print("No non-empty chunks produced.")
        return

    print("=== 5 random sample chunks ===")
    samples = random.sample(chunks, min(5, len(chunks)))
    for i, chunk in enumerate(samples, 1):
        print(f"\n--- Sample {i} ---")
        print(f"metadata: {chunk.metadata}")
        print(f"text: {chunk.text}")


if __name__ == "__main__":
    main()
