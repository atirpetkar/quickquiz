QuickQuiz‑GPT — Product Requirements Document (PRD)

1. Purpose

Build a stand‑alone, open‑source micro‑service that turns any instructional text (PDFs, URLs, markdown, lecture notes) into high‑quality, difficulty‑ranked quiz items, evaluates its own output for clarity & correctness, and stores everything behind a clean REST and WebSocket API.
The MVP is intentionally scoped to 2–3 weeks so you can ship fast, showcase applied GenAI expertise on LinkedIn, and later plug the service directly into a larger EdTech platform without re‑work.

2. Problem Statement

Educators & course creators spend hours crafting practice questions that (a) truly test concept mastery, (b) come with crisp explanations, and (c) sit inside a searchable store for re‑use. Existing automatic generators either ignore factual accuracy or lack an API‑first design that other apps can reuse.

3. Goals & Success Metrics

Goal	KPI / Metric
Ship an MVP in ≤ 21 days	Working demo & public repo ✅
Produce quizzes with ≥ 90 % self‑evaluation score	LLM‑as‑judge rubric
Provide < 1 s latency for cached generation	Benchmarked on 1‑page input
Showcase resume‑worthy tech	> 3 LinkedIn reactions & 1 share

4. Personas
	•	Content Author – uploads notes / syllabus and pulls ready‑made quizzes.
	•	Developer – integrates the API into LMS or study app.
	•	Learner (future) – receives adaptive quizzes (out of MVP scope).

5. User Stories (MVP)
	1.	As a Content Author I can POST /ingest a PDF URL so the service extracts clean text & stores embeddings.
	2.	As a Developer I can POST /generate with {topic: "Kinematics", difficulty:"medium", count:10} to receive MCQs with answers & explanations.
	3.	As a Developer I can GET /questions/{id} to retrieve any item, including metadata tags.
	4.	As a Developer I can POST /evaluate on custom items to get an LLM rubric score & suggestions.

6. Functional Requirements
	•	Ingestion Pipeline – PDF/Docx/URL → text chunks → embeddings in pgvector.
	•	Question Generation – Prompt chain that creates MCQ stem, 4 options, correct key, explanation, Bloom level, difficulty index.
	•	Self‑Eval Loop – Secondary model uses rubric prompt → accepts/flags/amends.
	•	How it works: Generation → Rubric prompt → JSON score → threshold check (default accept ≥ 90 %).
	•	Rubric fields: quality_score, issues, suggested_fix.
	•	API exposure: POST /evaluate accepts custom MCQs for scoring.
	•	Metadata Store – Postgres tables: documents, chunks, questions.
	•	REST & WS API – FastAPI; OpenAPI spec auto‑generated.
	•	Auth (optional) – API‑key header (self‑managed secret).
	•	Caching – Fingerprint input; Redis‑lite (sqlite fallback) to avoid repeats.

7. Non‑Functional Requirements
	•	Containerised (Docker) and deployable on Render/Replit.
	•	90 % test coverage on pure‑python logic via pytest.
	•	CI via GitHub Actions → lint, test, build.

8. Architecture Overview

+---------------+       +-----------+      +----------------+
| PDF / URL API |  -->  |  Ingestor | -->  |  pgvector DB   |
+---------------+       +-----------+      +----------------+
                                 ^                |
                                 |                v
   +---------+    prompt chain  +-----------+  +----------+
   | OpenAI  |<----------------->| Generator |->|  Redis   |
   +---------+                   +-----------+  +----------+
                                        |
                                        v
                                 +--------------+
                                 |  FastAPI     |
                                 +--------------+

9. Tech Stack
	•	Python 3.10
	•	FastAPI + Uvicorn
	•	LangChain 0.2 (LCEL)
	•	OpenAI GPT‑4o (or local Llama‑3‑instruct via Ollama)
	•	Postgres 15 + pgvector
	•	pdfplumber / trafilatura for extraction
	•	pytest, ruff, pre‑commit
	•	docker‑compose
	•	TruLens (self‑eval)
	•	Github Actions / Codespaces

10. API Sketch

POST /ingest
  body: { "source_url": "https://.../chapter1.pdf" }
  returns: { document_id }
POST /generate
  body: {
    "document_id": "...",
    "topic": "Kinematics",
    "difficulty": "medium",
    "count": 5
  }
  returns: [ { id, stem, options[], answer, explanation, tags[] } ]
GET /questions/{id}
POST /evaluate  # optional self‑service eval

11. Data Model (DDL excerpt)

CREATE TABLE documents (
  id UUID PRIMARY KEY,
  title TEXT,
  source_url TEXT,
  created_at TIMESTAMP DEFAULT now()
);
CREATE TABLE chunks (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(id),
  content TEXT,
  embedding VECTOR(1536)
);
CREATE TABLE questions (
  id UUID PRIMARY KEY,
  chunk_id UUID REFERENCES chunks(id),
  stem TEXT,
  options JSONB,
  answer TEXT,
  explanation TEXT,
  bloom_level TEXT,
  difficulty TEXT,
  quality_score FLOAT,
  created_at TIMESTAMP DEFAULT now()
);

12. Timeline & Milestones (21 days)

Day Range	Milestone
1‑2	Finalise PRD, repo skeleton, CI
3‑5	Ingestion & embedding pipeline
6‑9	Question generation chain & tests
10‑12	Self‑evaluation loop & caching
13‑15	REST endpoints & OpenAPI docs
16‑18	Containerisation & deployment demo
19‑20	Polish, write README & badges
21	Launch on LinkedIn / HackerNews

13. Deliverables
	•	Public GitHub repo quickquiz-gpt
	•	Docker image & one‑click deploy guide (Render)
	•	Sample notebook + cURL examples
	•	1‑min Loom demo video
	•	Blog/LinkedIn post template (see Appendix A)

14. Success Checklist
	•	All core endpoints live
	•	20 sample quizzes generated
	•	CI passing & code‑cov badge ≥ 90 %
	•	Deployed URL shared on LinkedIn post

⸻

Appendix A — LinkedIn Post Template

Excited to open‑source QuickQuiz‑GPT, a micro‑service that converts any learning material into high‑quality quiz questions with built‑in AI self‑evaluation. Built in three weeks with FastAPI + Postgres + GPT‑4o. Check the repo & tell me how you’d use it!

Appendix B — Future Extensions (post‑MVP)
	•	Adaptive difficulty based on learner profile.
	•	xAPI events + Learning Locker integration.
	•	Hybrid search (keyword + semantic) endpoint.
	•	UI widget (React) for embedding quizzes.

Appendix C — Risk & Mitigations

Risk	Impact	Mitigation
Hallucinated answers	High	Self‑eval + holdout manual review
OpenAI cost spikes	Medium	Switch to local Llama3 for bulk
PDF parsing errors	Medium	Fallback library + manual override

Appendix D — Prompt Snippet (Generation)

You are an expert pedagogy designer… [prompt omitted for brevity]

⸻

End of PRD