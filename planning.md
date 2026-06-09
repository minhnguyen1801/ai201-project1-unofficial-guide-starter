# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

UIC (University of Illinois Chicago) CS core course and professor reviews.

This knowledge is valuable because official course descriptions don't reflect teaching style, exam difficulty, or workload. Students rely on scattered Rate My Professors (RMP) reviews that are hard to search systematically — there's no way to ask a question like "which CS 251 professor has the most manageable workload?" and get a synthesized answer across reviews. A RAG system over this corpus lets students query teaching style, grading, and difficulty across professors and courses in one place.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

12 documents total, all sourced from Rate My Professors via the RMP GraphQL API. Each professor-per-course pairing is one document. Professors who teach multiple courses get separate documents per course context (e.g., Mitch Theys has one document for CS 141 and a separate one for CS 362).

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | CS 141 — Zhaochen Gu | Programming Design II reviews | RMP GraphQL API |
| 2 | CS 141 — Hodges | Programming Design II reviews | RMP GraphQL API |
| 3 | CS 141 — Dale Reed | Programming Design II reviews | RMP GraphQL API |
| 4 | CS 141 — Mitch Theys | Programming Design II reviews | RMP GraphQL API |
| 5 | CS 211 — Scott Reckinger | Programming Practicum reviews | RMP GraphQL API |
| 6 | CS 211 — John Bell | Programming Practicum reviews | RMP GraphQL API |
| 7 | CS 211 — David Hayes | Programming Practicum reviews | RMP GraphQL API |
| 8 | CS 251 — Daniel Ayala | Data Structures reviews | RMP GraphQL API |
| 9 | CS 251 — Scott Reckinger | Data Structures reviews | RMP GraphQL API |
| 10 | CS 251 — Adam Koehler | Data Structures reviews | RMP GraphQL API |
| 11 | CS 362 — Mitchell Theys | Computer Design reviews | RMP GraphQL API |
| 12 | CS 362 — Patrick Troy | Computer Design reviews | RMP GraphQL API |
| 13 | CS 401 — Bhaskar DasGupta | Algorithms reviews | RMP GraphQL API |
| 14 | CS 401 — Xiaorui Sun | Algorithms reviews | RMP GraphQL API |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 500 characters

**Overlap:** 50 characters

**Strategy:** Split by individual review boundary first. If a single review exceeds 500 characters, split further with 50-character overlap.

**Reasoning:** RMP reviews are naturally short (2-5 sentences), each expressing one complete student opinion. Splitting by review boundary preserves semantic completeness. Overlap handles edge cases where a key point falls near a chunk boundary. Reviews shorter than 500 characters stay intact as single chunks.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** all-MiniLM-L6-v2 via sentence-transformers

**Top-k:** 5

**Production tradeoff reflection:** For a real deployment, weigh: (1) Cost — all-MiniLM-L6-v2 runs locally for free, while OpenAI's text-embedding-3-small costs per token but has higher accuracy; (2) Context length — MiniLM handles ~256 tokens, sufficient for short reviews, but longer documents would need a model with larger context windows; (3) Domain specificity — a general model may not capture academic slang like "curves hard" or "weed-out course"; a fine-tuned education-domain model could improve retrieval precision; (4) Latency — local inference adds startup time but avoids API round-trip; for a high-traffic deployment, a hosted embedding API would be more scalable.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about exam difficulty in CS 251 with Professor Daniel Ayala? | Exams are challenging and require strong grasp of data structures, but Ayala's lectures and exam reviews make them manageable. The bigger stress is heavy coding projects. |
| 2 | Is CS 401 with Professor DasGupta recommended, and what is the workload like? | Yes — recommended for easier grading. Tests are fair and don't heavily assess the hardest concepts. Tradeoff: students may not deeply learn complex algorithms needed for technical interviews. |
| 3 | How does Professor Dale Reed grade in CS 141? | Strict and demanding — tough grader with zero-tolerance for missed deadlines, though lectures are described as lively. |
| 4 | What do students say about the workload for CS 362 with Professor Patrick Troy? | Extremely heavy — students warn of 20+ hours of homework per week plus intensive labs. Tagged as "tough grader," "lots of homework," and "get ready to read." |
| 5 | What are the common complaints about Professor Scott Reckinger in CS 211? | Heavy homework volume, strict grading on labs/projects with little room for error, fast lecture pace, and can come across as sharp when answering basic questions. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Thin review coverage for some professors** — Professors like Xiaorui Sun or Hodges may have very few written reviews on RMP, producing documents too short to chunk meaningfully. This could cause retrieval to either miss relevant content or return low-quality fragments.

2. **Cross-course professor confusion** — Mitch Theys and Scott Reckinger both appear in multiple courses. If chunks aren't tagged with course metadata, the system might return CS 362 reviews when asked about CS 141, producing misleading answers.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
┌─────────────────────┐
│  RMP GraphQL API    │
│  (12 professor      │
│   review pages)     │
└────────┬────────────┘
         │ raw review text
         ▼
┌─────────────────────┐
│  Document Ingestion │
│  (Python requests + │
│   JSON parsing)     │
└────────┬────────────┘
         │ cleaned text
         ▼
┌─────────────────────┐
│  Chunking           │
│  500 char chunks,   │
│   50 char overlap,  │
│   by review boundary│
└────────┬────────────┘
         │ chunks + metadata
         ▼
┌─────────────────────┐
│  Embedding +        │
│  Vector Store       │
│  (all-MiniLM-L6-v2  │
│   + ChromaDB)       │
└────────┬────────────┘
         │ similarity search
         ▼
┌─────────────────────┐
│  Retrieval          │
│  (top-k=5 chunks    │
│   + source metadata)│
└────────┬────────────┘
         │ context + sources
         ▼
┌─────────────────────┐
│  Generation         │
│  (Groq llama-3.3-   │
│   70b-versatile +   │
│   Gradio UI)        │
└─────────────────────┘
```

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:** Give Claude the Documents section and Chunking Strategy section from planning.md. Ask it to implement a script that calls the RMP GraphQL API to fetch reviews per professor, cleans the text, and splits into 500-character chunks with 50-character overlap, tagging each chunk with professor name and course number.

**Milestone 4 — Embedding and retrieval:** Give Claude the Architecture diagram and Retrieval Approach section. Ask it to implement an embedding script using sentence-transformers (all-MiniLM-L6-v2), store chunks in ChromaDB with source metadata, and write a retrieval function returning top-5 chunks with source info.

**Milestone 5 — Generation and interface:** Give Claude the grounding requirement (answer from retrieved context only, with source attribution) and ask it to implement the Groq LLM connection, a prompt template enforcing grounding, and a Gradio interface with question input and answer + sources output fields.
