"""
Evaluation harness for the Unofficial Guide RAG pipeline.

Runs the 5 test questions from planning.md through ask() and prints each
answer with its retrieved sources, so the results can be compared against the
expected answers recorded in planning.md / README.md.
"""

from query import ask

# The 5 evaluation questions from planning.md (with their expected answers,
# kept here for side-by-side comparison while reviewing output).
EVAL_QUESTIONS = [
    {
        "q": "What do students say about exam difficulty in CS 251 with Professor Daniel Ayala?",
        "expected": "Exams are challenging but manageable thanks to lectures and exam "
        "reviews; the bigger stress is heavy coding projects.",
    },
    {
        "q": "Is CS 401 with Professor DasGupta recommended, and what is the workload like?",
        "expected": "Recommended for easier grading; tests are fair. Tradeoff: may not "
        "deeply learn complex algorithms for interviews.",
    },
    {
        "q": "How does Professor Dale Reed grade in CS 141?",
        "expected": "Strict, tough grader with zero tolerance for missed deadlines; "
        "lectures described as lively.",
    },
    {
        "q": "What do students say about the workload for CS 362 with Professor Patrick Troy?",
        "expected": "Extremely heavy — 20+ hours of homework per week plus intensive "
        "labs; tough grader, lots of reading.",
    },
    {
        "q": "What are the common complaints about Professor Scott Reckinger in CS 211?",
        "expected": "Heavy homework, strict grading with little room for error, fast "
        "lecture pace, can come across as sharp.",
    },
]


def main() -> None:
    for i, item in enumerate(EVAL_QUESTIONS, 1):
        print("=" * 78)
        print(f"Q{i}: {item['q']}")
        print("-" * 78)
        print(f"Expected: {item['expected']}\n")

        result = ask(item["q"])
        print(f"Answer:\n{result['answer']}\n")
        print("Retrieved sources:")
        for s in result["sources"]:
            print(f"  - {s}")
        print()


if __name__ == "__main__":
    main()
