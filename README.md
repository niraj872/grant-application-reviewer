# Grant Application Reviewer
Evidence-review and completeness-assistance tool: compares a draft grant application with a guideline. **AI output is advisory only; the tool makes no legal, compliance or funding-eligibility decision.**

## Architecture
`backend/` FastAPI + SQLAlchemy (SQLite; set `DATABASE_URL` for PostgreSQL) · `backend/app/ai/` LLM client, prompts, offline demo provider · `backend/app/services.py` parsing, AI orchestration, deterministic logic · `frontend/` React + Vite + TS.

## Setup
```
cp .env.example .env
# backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
# frontend (new shell)
cd frontend && npm install && npm run dev      # http://localhost:5173
# docker
docker compose up --build                       # http://localhost:8080
```
Env vars: `AI_PROVIDER` (`demo` offline heuristics | `anthropic`), `ANTHROPIC_API_KEY`, `AI_MODEL`, `DATABASE_URL`. Keys are never hardcoded.
Click **Load demo assessment** on the dashboard (5 satisfied / 2 missing / 1 weak mandatory) to see the full workflow.

## API
`POST /api/guidelines`, `POST /api/applications` (multipart; optional `guideline_id`/`application_id` creates a new version; `supporting_documents` JSON list) · `POST /api/assessments` · `GET /api/assessments[/{id}[/requirements|/summary]]` · `PATCH /api/mappings/{id}` · `PATCH /api/supporting-documents/{id}` · `POST /api/demo` · `GET /api/health`.

## AI workflow
Extract requirements (with source citation) → map application evidence → detect unsupported claims → generate traceable questions. Every LLM response is JSON-validated with Pydantic (fence-stripping/brace recovery, then a clear 502 error). Guard: evidence not found verbatim in the application is downgraded to `missing`. Wording is "not supported by supplied evidence", never "false".

## Versioning / staleness
Each upload stores a SHA-256 hash and increments the version. An assessment pins exact guideline/application versions; if a newer version (or hash) exists it is reported `stale`, review is blocked (409), and nothing is silently updated.

## Deterministic completion (backend code, no LLM)
Mandatory completion = mandatory requirements whose **reviewed** status is `satisfied` ÷ total mandatory. Confirmed/corrected decisions count as reviewed; rejected, pending, weak, missing, ambiguous, unsupported are incomplete. Recommended items are reported separately. Example: 7 satisfied, 2 missing, 1 weak of 10 → 70%.

## Human review
Each mapping starts "AI Suggested"; reviewer can Confirm, Correct (new status/evidence) or Reject; decisions are stored in `reviewer_decisions` and drive the summary. Lifecycle: draft → in review → reviewed → stale.

## Limitations
No OCR (scanned PDFs fail); page numbers for DOCX/TXT are approximate (TXT uses form feeds); very long documents are not chunked; supporting-doc *content* is not analyzed (metadata only); no auth; schema created via `create_all` (no migrations); demo provider is keyword-based.

## Testing
`cd backend && pytest` (upload, hashing, versioning, mappings, review, 70% calculation, staleness, supporting docs). Screenshots: _placeholder_.
