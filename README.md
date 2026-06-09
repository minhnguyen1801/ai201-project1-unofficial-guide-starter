# The Unofficial Guide — Project 1

A retrieval-augmented generation (RAG) system that answers questions about UIC
CS core courses and professors, grounded in Rate My Professors reviews.

---

## Domain

UIC (University of Illinois Chicago) CS core course and professor reviews —
covering CS 141, CS 211, CS 251, CS 362, and CS 401. This knowledge is valuable
because official course descriptions don't reflect teaching style, exam
difficulty, or workload. Students rely on scattered Rate My Professors reviews
that are hard to search systematically. This system lets a student ask a natural
question — "which CS 251 professor has the most manageable workload?" — and get a
synthesized, source-attributed answer across many reviews at once.

---

## Document Sources

All 14 documents are sourced from Rate My Professors (RMP) via its GraphQL API.
Each professor-per-course pairing is one document, so professors who teach more
than one course (Scott Reckinger, Mitchell Theys) get a separate document per
course context.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | CS141 — Zhaochen Gu | RMP professor page | https://www.ratemyprofessors.com |
| 2 | CS141 — Mark Hodges | RMP professor page | https://www.ratemyprofessors.com |
| 3 | CS141 — Dale Reed | RMP professor page | https://www.ratemyprofessors.com |
| 4 | CS141 — Mitchell Theys | RMP professor page | https://www.ratemyprofessors.com |
| 5 | CS211 — Scott Reckinger | RMP professor page | https://www.ratemyprofessors.com |
| 6 | CS211 — John Bell | RMP professor page | https://www.ratemyprofessors.com |
| 7 | CS211 — David Hayes | RMP professor page | https://www.ratemyprofessors.com |
| 8 | CS251 — Daniel Ayala | RMP professor page | https://www.ratemyprofessors.com |
| 9 | CS251 — Scott Reckinger | RMP professor page | https://www.ratemyprofessors.com |
| 10 | CS251 — Adam Koehler | RMP professor page | https://www.ratemyprofessors.com |
| 11 | CS362 — Mitchell Theys | RMP professor page | https://www.ratemyprofessors.com |
| 12 | CS362 — Pat Troy | RMP professor page | https://www.ratemyprofessors.com |
| 13 | CS401 — Bhaskar Dasgupta | RMP professor page | https://www.ratemyprofessors.com |
| 14 | CS401 — Xiaorui Sun | RMP professor page | https://www.ratemyprofessors.com |

---

## Chunking Strategy

**Chunk size:** 500 characters

**Overlap:** 50 characters

**Why these choices fit your documents:** The pipeline splits by individual
review boundary first — each RMP review is one natural chunk. If a single review
exceeds 500 characters, it is split further with 50 characters of overlap. Empty
chunks are filtered out. RMP reviews are naturally short (2–5 sentences), each
expressing one complete student opinion, so splitting by review boundary
preserves semantic completeness. The 50-character overlap handles edge cases
where a key point falls near a chunk boundary, and reviews shorter than 500
characters stay intact as single chunks.

**Final chunk count:** 901 chunks across 14 documents.

---

## Sample Chunks

**Sample 1 — `CS251_Koehler.txt` (Adam Koehler, CS251):**
> [REVIEW] He is great I don't know why people don't like him, the class is
> fairly easy, and he gives plenty of help and there's only a lecture once a
> week, there is a good amount of hw but its all fairly simple and can be done
> in hour the only really involved parts are the projects but you have a week to
> do them and only the 5th one is very difficult | Quality: 5.0 | Difficulty: 2

**Sample 2 — `CS211_Bell.txt` (John Bell, CS211):**
> [REVIEW] All lectures were recorded and posted on Blackboard. Dr. Bell also
> uploads the notes taken in class to Blackboard and the class site which
> contains all relevant information for the course. Dr. Bell is very passionate
> about Computer Science which makes the lectures go by a little quicker. |
> Quality: 4.0 | Difficulty: 2

**Sample 3 — `CS211_Reckinger.txt` (Scott Reckinger, CS211):**
> [REVIEW] Very hard class, and the professor did not make it any easier. Have
> fun reading and googling every question you have. | Quality: 1.0 | Difficulty: 4

**Sample 4 — `CS211_Reckinger.txt` (Scott Reckinger, CS211):**
> [REVIEW] He's a good prof but the material is just hard. The first half of the
> course is insanely easy but randomly midway through it skyrockets in
> difficulty. The projects are insanely hard to the point where half the class
> doesn't do them. Tests are okay at least. | Quality: 3.0 | Difficulty: 4

**Sample 5 — `CS401_Dasgupta.txt` (Bhaskar Dasgupta, CS401):**
> [REVIEW] This class was quite easy. You would be fine if you study the
> powerpoints. Homework is not bad at all. You get plenty of time to do it.
> Overall exams were easy. He curves grades. A very good prof. | Quality: 5.0 |
> Difficulty: 2

---

## Embedding Model

**Model used:** all-MiniLM-L6-v2 via sentence-transformers (runs locally, no API
key required).

**Production tradeoff reflection:** For a real deployment, the tradeoffs include:
(1) **Cost** — all-MiniLM-L6-v2 is free and runs locally; OpenAI's
text-embedding-3-small costs per token but offers higher accuracy. (2) **Context
length** — MiniLM handles ~256 tokens, which is sufficient for short reviews, but
longer documents would need a model with a larger context window. (3) **Domain
specificity** — a general model may not capture academic slang like "curves hard"
or "weed-out course"; a fine-tuned education-domain model could improve retrieval
precision. (4) **Latency** — local inference avoids API round-trips but adds
startup time; a hosted embedding API would scale better for high-traffic
production use.

---

## Retrieval Test Results

**Query 1:** "What do students say about exam difficulty in CS 251 with Daniel Ayala?"

Top chunks returned:
- **[1] Daniel Ayala (CS251) — distance=0.34:** "251 was a challenging class, but
  it never was an unfair class. Lecturers were so huge, yet Ayala was able to
  condense and make all the information so easy to digest."
- **[2] Mark Hodges (CS141) — distance=0.36:** "this is for CS341. the second test
  was quite difficult, but he is a really nice guy and caring."
- **[3] Mitchell Theys (CS141) — distance=0.38:** "CS261 is a difficult course,
  the material is very dense and a change of pace from normal programming."

*Relevance explanation:* The top result directly matches — it's a CS251 Ayala
review describing the class as challenging but fair. Results 2–3 matched on
"difficult/exam" semantics but are from different professors, showing the system
correctly ranks the most relevant chunk first.

**Query 2:** "Is CS 401 with DasGupta recommended and what is the workload like?"

Top chunks returned:
- **[1] Bhaskar Dasgupta (CS401) — distance=0.54:** "401 is known as one of the
  hardest CS classes at UIC, but with this professor, it is easy to get an A."
- **[2] Bhaskar Dasgupta (CS401) — distance=0.56:** "Dasgupta is awesome."
- **[3] John Bell (CS211) — distance=0.56:** "If you are completely free in life
  and feel like wasting your time then take it."

*Relevance explanation:* Results 1 and 2 are directly relevant — both are
Dasgupta CS401 reviews. Result 3 is a false positive; the word "workload"
semantically pulled in an unrelated Bell review. Distance scores around 0.54–0.56
indicate weaker signal, likely because Dasgupta only has 31 reviews — a thin
document.

**Query 3:** "What are common complaints about Scott Reckinger in CS 211?"

Top chunks returned:
- **[1] Adam Koehler (CS251) — distance=0.47:** "people really hate on him, not
  sure why. no one attended class or started their programs early, so they like
  to complain."
- **[2] Scott Reckinger (CS211) — distance=0.51:** "Why was he even added to the
  cs department?"
- **[3] Scott Reckinger (CS251) — distance=0.51:** "Why was he even added to the
  cs department?"

*Relevance explanation:* The two Reckinger reviews surface complaints directly,
though the top-ranked Koehler chunk is a near-miss that matched on "hate
on him / complain" sentiment rather than the named professor — another example of
semantic-similarity bleed across professors.

---

## Grounded Generation

**System prompt grounding instruction:** Grounding is enforced in the system
prompt passed to the Groq LLM:

> "You are a helpful guide for UIC CS students. Answer questions using ONLY the
> information provided in the documents below. If the documents do not contain
> enough information to answer the question, respond with exactly: 'I don't have
> enough information on that topic in my documents.'"

The word **ONLY** constrains the model to the retrieved context, and the exact
refusal string gives a deterministic fallback when the documents lack an answer.

**How source attribution is surfaced in the response:** Source attribution is
added programmatically — the retrieved chunk metadata (professor, course, source
filename) is appended to every response regardless of what the LLM generates,
ensuring attribution is never hallucinated.

---

## Example Responses

**Example 1 — Grounded response with source attribution:**

- *Query:* "Is CS 401 with Professor DasGupta recommended, and what is the workload like?"
- *Answer:* "CS 401 with Professor DasGupta is highly recommended, with a perfect
  quality rating of 5.0 in both reviews. The workload is considered manageable,
  with few homework assignments, 2 midterms, and a final exam. The exams are
  described as fair with few questions. The lectures are not extremely
  fast-paced, although they are proof-heavy. Overall, Professor DasGupta's
  section of CS 401 is a great option for students. Sources: [1] Professor:
  Bhaskar Dasgupta | Course: CS401"
- *Retrieved from:* Bhaskar Dasgupta (CS401) — CS401_Dasgupta.txt

**Example 2 — Grounded response with source attribution:**

- *Query:* "What are the common complaints about Professor Scott Reckinger in CS 211?"
- *Answer:* "The common complaints about Professor Scott Reckinger in CS 211
  include tough projects, lectures, labs, and homework, with one reviewer feeling
  that he made it seem like CS 211 was the only class they were taking at UIC.
  Another complaint is that he can be inconsiderate. However, not all reviews are
  negative — some reviewers find him to be a great professor who helps students
  succeed. Sources: [2] Professor: Scott Reckinger | Course: CS211"
- *Retrieved from:* Scott Reckinger (CS211) — CS211_Reckinger.txt

**Out-of-scope example:**

- *Query:* "What is the best pizza place near UIC?"
- *Answer:* "I don't have enough information on that topic in my documents."
- *Retrieved from:* (sources listed, but the answer correctly refused)

---

## Query Interface

Built with Gradio. Run with `python app.py` — it opens at http://localhost:7860.

- **Input field:** "Ask a question about UIC CS professors and courses" (single
  text box; submits on the **Ask** button or the Enter key)
- **Output fields:** "Answer" (10-line text box) and "Sources" (5-line text box
  showing retrieved document names with professor and course labels)

**Sample interaction transcript:**

- *Query:* "How does Professor Dale Reed grade in CS 141?"
- *Answer:* "The reviews provide varying opinions on Professor Dale Reed's grading
  in CS 141. One review mentions that despite almost failing every exam, they
  still received a B, suggesting a potentially lenient grading curve. However,
  other reviews mention that the projects and tests are difficult and demand a
  lot of effort to get above a C. Difficulty ratings vary from 1 to 5 across
  reviewers, while quality ratings are generally positive (4.0–5.0)."
- *Sources:*
  - Dale Reed (CS141) — CS141_Reed.txt

---

## Evaluation Report

| # | Question | Expected Answer | System Response | Accuracy |
|---|----------|-----------------|-----------------|----------|
| 1 | What do students say about exam difficulty in CS 251 with Professor Daniel Ayala? | Exams are challenging but manageable; bigger stress is heavy coding projects | System noted class was challenging but not unfair; could not find specific exam difficulty details due to thin review coverage (only 10 reviews) | Partially accurate |
| 2 | Is CS 401 with Professor DasGupta recommended, and what is the workload like? | Recommended for easier grading; fair tests; tradeoff is less depth for interviews | Correctly identified as highly recommended, manageable workload, few HW assignments, fair exams, proof-heavy lectures | Accurate |
| 3 | How does Professor Dale Reed grade in CS 141? | Strict, tough grader with zero tolerance for missed deadlines; lively lectures | Captured varying difficulty perceptions and positive quality ratings but missed the zero-tolerance deadline policy | Partially accurate |
| 4 | What do students say about the workload for CS 362 with Professor Patrick Troy? | Extremely heavy — 20+ hours/week, intensive labs, tough grader | Described workload as mixed/moderate; missed the extreme workload characterization from less-retrieved reviews | Partially accurate |
| 5 | What are the common complaints about Professor Scott Reckinger in CS 211? | Heavy homework, strict grading, fast pace, sharp demeanor | Correctly identified tough projects/homework and inconsiderate behavior; missed fast pace and strict grading specifics | Partially accurate |

---

## Failure Case Analysis

**Question that failed:** "What do students say about exam difficulty in CS 251
with Professor Daniel Ayala?" (Q1) is the clearest failure case.

**What the system returned:** The system noted the class was challenging but not
unfair, but it could not surface explicit exam-difficulty commentary, producing
only a partially accurate answer.

**Root cause (tied to a specific pipeline stage):** Daniel Ayala has only 10
reviews in the dataset — the thinnest coverage of any professor. With top-k=5,
the retrieved chunks represented nearly half of all available Ayala reviews, yet
none contained explicit exam-difficulty commentary. This is a document-coverage
gap at the retrieval/ingestion stage: the pipeline worked correctly, but the
source documents simply lacked the specific information the question asked for.

**What you would change to fix it:** A system with richer per-professor data
would produce a more accurate answer — e.g., supplementing RMP with additional
sources (Reddit, course forums) for thinly-reviewed professors. This highlights a
fundamental RAG limitation: retrieval quality is bounded by document quality.

---

## Spec Reflection

**One way the spec helped you during implementation:** The planning.md AI Tool
Plan sections gave us clear inputs to prompt Claude Code at each milestone.
Handing the Chunking Strategy section directly to Claude Code produced code that
matched the 500-char / 50-overlap spec without needing to re-explain
requirements, which kept the generated implementation tightly aligned with the
plan.

**One way your implementation diverged from the spec, and why:** The spec assumed
the RMP school lookup would work dynamically by searching for the school name. In
practice, the GraphQL API returned the wrong school (School-1113 instead of
School-1111 for UIC), so we hardcoded the correct UIC school ID. This was a
real-world API reliability issue the spec did not anticipate.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Documents section and Chunking Strategy from
  planning.md, with a request to implement `ingest.py`.
- *What it produced:* The RMP GraphQL queries, pagination logic, and file-saving
  structure.
- *What I changed or overrode:* We reviewed the output and identified that the
  professor name matching was too loose — it was matching wrong professors from
  other schools. We diagnosed the root cause (wrong school ID returned by the
  dynamic lookup), directed Claude to fix the `find_teacher` function to filter
  by school ID, and then hardcoded the correct UIC school ID after verifying it
  manually.

**Instance 2**

- *What I gave the AI:* A spec for `query.py` with a specific grounding
  requirement — the system prompt must use the word "ONLY" and include an exact
  refusal string.
- *What it produced:* The Groq integration and prompt template.
- *What I changed or overrode:* We reviewed and confirmed the system prompt
  enforced grounding correctly. We also noted the LLM was appending its own
  "Sources: [1], [2]..." text inside the answer box — a minor formatting overlap
  with the programmatic source attribution. We kept the programmatic attribution
  as the canonical source display and noted this as a known quirk.
