"""
Document ingestion for the Unofficial Guide RAG pipeline.

Fetches professor reviews from the Rate My Professors (RMP) GraphQL API and
saves them as plain-text documents in documents/, one review per line:

    [REVIEW] <review text> | Quality: <quality_score> | Difficulty: <difficulty_score>

One document is produced per (course, professor) pairing, so professors who
teach multiple courses (e.g. Mitch Theys, Scott Reckinger) get separate files
tagged with the course prefix.
"""

import re
import sys
import time
from pathlib import Path

import requests

# --- Configuration ----------------------------------------------------------

RMP_ENDPOINT = "https://www.ratemyprofessors.com/graphql"
# Public anonymous token RMP's own frontend ships with ("test:test").
AUTH_HEADER = "Basic dGVzdDp0ZXN0"
SCHOOL_NAME = "University of Illinois at Chicago"

DOCUMENTS_DIR = Path(__file__).parent / "documents"

# course -> list of professor names to fetch for that course.
# A professor listed under two courses is fetched (and saved) once per course.
PROFESSORS = {
    "CS141": ["Zhaochen Gu", "Mark Hodges", "Dale Reed", "Mitchell Theys"],
    "CS211": ["Scott Reckinger", "John Bell", "David Hayes"],
    "CS251": ["Daniel Ayala", "Scott Reckinger", "Adam Koehler"],
    "CS362": ["Mitchell Theys", "Pat Troy"],
    "CS401": ["Bhaskar Dasgupta", "Xiaorui Sun"],
}

PAGE_SIZE = 20  # ratings per GraphQL page

HEADERS = {
    "Authorization": AUTH_HEADER,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; UnofficialGuideBot/1.0)",
}


# --- GraphQL helpers ---------------------------------------------------------

def graphql(query: str, variables: dict) -> dict:
    """Run a GraphQL query against RMP and return the `data` object."""
    resp = requests.post(
        RMP_ENDPOINT,
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


SCHOOL_QUERY = """
query SearchSchool($text: String!) {
  newSearch {
    schools(query: {text: $text}) {
      edges {
        node { id name city state }
      }
    }
  }
}
"""

TEACHER_QUERY = """
query SearchTeacher($text: String!, $schoolID: ID!) {
  newSearch {
    teachers(query: {text: $text, schoolID: $schoolID}) {
      edges {
        node {
          id
          firstName
          lastName
          numRatings
          avgRating
          avgDifficulty
        }
      }
    }
  }
}
"""

RATINGS_QUERY = """
query TeacherRatings($id: ID!, $cursor: String, $count: Int!) {
  node(id: $id) {
    ... on Teacher {
      firstName
      lastName
      numRatings
      ratings(first: $count, after: $cursor) {
        edges {
          node {
            comment
            qualityRating
            clarityRating
            helpfulRating
            difficultyRating
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
"""


def find_school_id(name: str) -> str:
    """Return the RMP node id for the school matching `name`."""
    data = graphql(SCHOOL_QUERY, {"text": name})
    edges = data["newSearch"]["schools"]["edges"]
    if not edges:
        raise RuntimeError(f"No school found for {name!r}")
    # Prefer an exact (case-insensitive) name match, else the first result.
    for edge in edges:
        if edge["node"]["name"].lower() == name.lower():
            return edge["node"]["id"]
    return edges[0]["node"]["id"]


def find_teacher(name: str, school_id: str) -> dict | None:
    """Search for a teacher by name within a school; return the best match."""
    data = graphql(TEACHER_QUERY, {"text": name, "schoolID": school_id})
    edges = [e["node"] for e in data["newSearch"]["teachers"]["edges"]]
    if not edges:
        return None

    target_last = name.split()[-1].lower()
    target_first = name.split()[0].lower() if len(name.split()) > 1 else None

    # Rank candidates: last-name match required; first-name match preferred;
    # tie-break on review count.
    def score(node: dict) -> tuple:
        last_ok = node["lastName"].lower() == target_last
        first_ok = (
            target_first is not None
            and node["firstName"].lower().startswith(target_first)
        )
        return (last_ok, first_ok, node["numRatings"])

    candidates = [n for n in edges if n["lastName"].lower() == target_last]
    pool = candidates or edges
    return max(pool, key=score)


def fetch_all_ratings(teacher_id: str) -> list[dict]:
    """Fetch every rating for a teacher, paginating through the connection."""
    ratings: list[dict] = []
    cursor = None
    while True:
        data = graphql(
            RATINGS_QUERY,
            {"id": teacher_id, "cursor": cursor, "count": PAGE_SIZE},
        )
        node = data["node"]
        if not node:
            break
        conn = node["ratings"]
        ratings.extend(edge["node"] for edge in conn["edges"])
        page = conn["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]
        time.sleep(0.2)  # be polite to the API
    return ratings


# --- Formatting / output -----------------------------------------------------

def clean_text(text: str) -> str:
    """Collapse whitespace so each review fits on a single line."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def quality_score(rating: dict) -> float:
    """RMP per-review quality = average of clarity and helpfulness ratings.

    Falls back to qualityRating if the components aren't present.
    """
    clarity = rating.get("clarityRating")
    helpful = rating.get("helpfulRating")
    if clarity is not None and helpful is not None:
        return round((clarity + helpful) / 2, 1)
    return round(rating.get("qualityRating") or 0.0, 1)


def lastname(name: str) -> str:
    return name.split()[-1]


def format_review(rating: dict) -> str | None:
    comment = clean_text(rating.get("comment", ""))
    if not comment:
        return None
    quality = quality_score(rating)
    difficulty = rating.get("difficultyRating")
    difficulty = round(difficulty, 1) if difficulty is not None else "N/A"
    return f"[REVIEW] {comment} | Quality: {quality} | Difficulty: {difficulty}"


def save_reviews(course: str, name: str, ratings: list[dict]) -> tuple[Path, int]:
    DOCUMENTS_DIR.mkdir(exist_ok=True)
    path = DOCUMENTS_DIR / f"{course}_{lastname(name)}.txt"
    lines = [line for r in ratings if (line := format_review(r))]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path, len(lines)


# --- Main --------------------------------------------------------------------

def main() -> None:
    print(f"Looking up school: {SCHOOL_NAME}")
    try:
        school_id = "U2Nob29sLTExMTE="
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not resolve school: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"  -> school id: {school_id}\n")

    summary: list[tuple[str, int]] = []
    for course, names in PROFESSORS.items():
        for name in names:
            label = f"{course} / {name}"
            try:
                teacher = find_teacher(name, school_id)
                if teacher is None:
                    print(f"  [skip] {label}: no teacher found")
                    summary.append((f"{course}_{lastname(name)}.txt", 0))
                    continue
                ratings = fetch_all_ratings(teacher["id"])
                path, count = save_reviews(course, name, ratings)
                print(
                    f"  [ok]   {label}: matched "
                    f"{teacher['firstName']} {teacher['lastName']} "
                    f"({teacher['numRatings']} ratings on RMP) "
                    f"-> {count} saved"
                )
                summary.append((path.name, count))
            except Exception as exc:  # noqa: BLE001
                print(f"  [err]  {label}: {exc}", file=sys.stderr)
                summary.append((f"{course}_{lastname(name)}.txt", 0))

    print("\n=== Summary ===")
    for filename, count in summary:
        print(f"  {filename:<28} {count} reviews")
    total = sum(c for _, c in summary)
    print(f"  {'TOTAL':<28} {total} reviews across {len(summary)} files")


if __name__ == "__main__":
    main()
