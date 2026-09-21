# Doctor Digital Twin (Prototype)

A prototype "Digital Twin of a Doctor" for a synthetic Singapore clinic network. It includes structured consultations, deterministic safety checks, configurable deployment modes, mocked clinic tools, governed episodic memory, a synthetic evaluation suite, an admin-managed hospital diagnostic-test catalog, doctor-specific test-decision learning, and a Next.js frontend.

For the complete architecture, workflows, data model, API reference, safety analysis, testing evidence, and presentation diagrams, see [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md).

## Safety position

- **Synthetic data only.** No real patients, doctors, or clinical records are used.
- **Prototype only** — this is not a medical device or diagnostic system.
- The system does **not** perform autonomous diagnosis. AMBER/RED cases always escalate to a human doctor; AUTONOMOUS mode only permits explicitly allowlisted low-risk (GREEN) workflows.
- If Gemini is unavailable, rate-limited, misconfigured, or returns invalid output, the API persists an AMBER case for doctor review and returns a stable patient-facing message instead of a provider error.
- Clinical validation, regulatory review, privacy, and security assessment are required before any real deployment. No claims are made about Singapore healthcare regulatory compliance.

## Prerequisites

- Python 3.11+
- Node.js 22.12+

## Setup

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Copy `.env.example` to `.env` in the repo root and set:

| Variable | Default | Description |
| --- | --- | --- |
| `TWIN_DATABASE_URL` | `sqlite:///./twin.db` | SQLAlchemy connection string (SQLite locally; swap for Postgres later). |
| `TWIN_GEMINI_API_KEY` | _(none)_ | Gemini API key, required only to run the app with a real LLM. Not needed to run tests. |
| `TWIN_GEMINI_MODEL` | `gemini-3.1-flash-lite` | Gemini model name. |
| `TWIN_AUTONOMOUS_TEST_MIN_CONFIDENCE` | `0.8` | Minimum current recommendation confidence for autonomous ordering. |
| `TWIN_AUTONOMOUS_TEST_MIN_SHADOW_ORDERS` | `2` | Required matching Shadow selections by this doctor. |
| `TWIN_AUTONOMOUS_TEST_MIN_COPILOT_DECISIONS` | `2` | Required matching Copilot decisions by this doctor. |
| `TWIN_AUTONOMOUS_TEST_MIN_COPILOT_ACCEPTANCE` | `0.75` | Required acceptance rate for matching Copilot recommendations. |

## Run locally

```powershell
npm run dev:backend
```

The API is available at `http://127.0.0.1:8014`; interactive docs at `/docs`. Uvicorn watches `backend/app/**/*.py` and reloads after each saved source change.

To discard local SQLite data, recreate the schema, load deterministic seed data, and then start the reloading backend:

```powershell
npm run dev:backend:fresh
```

The fresh command checks that port 8014 is free before deleting anything. `npm run db:reset` is destructive and intended only for local synthetic development data.

For a non-destructive baseline reset while the app is running, use **Admin > Data maintenance**. It clears cases/encounters, diagnostic-test decisions, appointments, audit events, evaluation runs, user-added doctors/patients, and non-baseline memories. The hospital test catalog and deterministic baseline profiles/memories are preserved. The action requires typing `RESET ADDED DATA` before submission.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -v
```

All automated tests run against an in-memory SQLite database and a fake LLM client — no network calls or real Gemini API key required.

Frontend component tests and the production build run with:

```powershell
cd frontend
npm test
npm run build
```

## Seed data + frontend

Seed four doctors across General Medicine, Neurology, ENT, and Family Medicine; eight synthetic patients; doctor-specific memories; and an active hospital diagnostic-test catalog (idempotent and safe to re-run):

```powershell
cd backend
..\.venv\Scripts\python.exe -m app.seed_data
```

The baseline doctors are Dr. Sarah Lim (General Medicine), Dr. Arjun Mehta (Neurology), Dr. Mei Lin Tan (Otolaryngology/ENT), and Dr. Noor Aziz (Family Medicine). Their approved memories cover domain-specific intake questions, communication preferences, workflows, and escalation rules.

Then run the frontend:

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

The frontend is available at `http://localhost:3000` with three screens: **Patient Intake** (`/intake`), **Doctor Dashboard** (`/dashboard`), and **Twin Memory** (`/memory`). Intake begins with a synthetic patient-profile and doctor-twin selector, shows relevant conditions/allergies and resumable cases, then opens the consultation composer. It talks to the backend via `NEXT_PUBLIC_API_BASE_URL` (default `http://127.0.0.1:8014`) - make sure the backend is running first, and that `TWIN_CORS_ALLOW_ORIGINS` on the backend includes the frontend's origin (default already includes `http://localhost:3000`).

## Free prototype deployment

The recommended prototype setup is **Vercel** for the Next.js frontend, **Render** for the FastAPI backend, and **Neon** for persistent Postgres. Keep using synthetic data only. Free services can sleep when idle, so the first request after a quiet period can be slow.

1. Push this repository to GitHub.
2. Create a free Neon project and copy its pooled connection string.
3. In Render, create a Blueprint from the repository. Render reads [`render.yaml`](render.yaml). Supply these secret environment values when prompted:

  | Variable | Value |
  | --- | --- |
  | `TWIN_DATABASE_URL` | Neon connection string (`postgresql://...`; the app selects Psycopg 3 automatically). |
  | `TWIN_GEMINI_API_KEY` | Gemini API key. |
  | `TWIN_CORS_ALLOW_ORIGINS` | Temporary frontend origin, then the exact Vercel production URL after step 4. |

  The Render start command creates missing tables and idempotently loads the synthetic baseline before starting the API. Verify `https://<render-service>.onrender.com/health` returns `{"status":"ok"}`.

4. In Vercel, import the same repository, set **Root Directory** to `frontend`, and add:

  | Variable | Value |
  | --- | --- |
  | `NEXT_PUBLIC_API_BASE_URL` | Render API URL without a trailing slash. |

5. Deploy the frontend, copy its production origin (for example, `https://example.vercel.app`), set Render's `TWIN_CORS_ALLOW_ORIGINS` to that origin, and redeploy the backend.
6. Open the Vercel `/intake` route and confirm that the seeded doctors and patients load.

Do not commit `.env`, `frontend/.env.local`, the Neon connection string, or the Gemini key. Vercel Hobby is intended for personal, non-commercial projects; use an organization-approved plan if this prototype is being distributed commercially.

## Architecture

```
backend/app/
  api/          FastAPI routers, including public/admin diagnostic-test catalog APIs
  agents/       DoctorTwin orchestration, prompt building, LLM client, deployment policy
  safety/       Deterministic red-flag detection + override policy (independent of the LLM)
  memory/       Read-only retrieval of APPROVED memories + candidate/approve/reject lifecycle
  tools/        Clinic tools + doctor-scoped test recommendation context retrieval
  models/       Pydantic schemas (incl. ClinicalAssessment, EvalCase) + SQLAlchemy ORM models
  services/     Consultation orchestration, audit logging, evaluation, test decisions and learning
  repositories/ SQLAlchemy-backed CRUD per entity
mcp/clinic_server.py   Mock Clinic MCP adapter mirroring the clinic tool interface (not a real MCP protocol server)
evals/                 cases.json (synthetic eval cases), run_evals.py (CLI), metrics.py (thin re-export)
frontend/              Next.js app (App Router, TypeScript): /intake, /dashboard, /memory
```

Workflow: `POST /consultations` → `DoctorTwin` retrieves doctor profile, approved memories, patient info, and prior encounters → calls the LLM for a structured `ClinicalAssessment` → the deterministic safety engine evaluates patient-authored statements and contextual answers, then can override the risk level (e.g. LLM says GREEN, the patient reports or affirms a red flag → final RED) → the deployment-mode policy determines what actions are permitted → the encounter and any safety-override/escalation audit events are persisted. Twin-authored questions do not themselves trigger red flags; a short "yes" confirms one unambiguous preceding safety question, while "no" or "none" does not. Intake responses contain at most one follow-up question. Appointment slots are shown only after question collection is complete and an AMBER case genuinely requires escalation. A doctor can then `POST /consultations/{id}/review` to **approve** the assessment as-is or **modify** specific fields (risk level, escalation, summary, recommended action) - the doctor is always the final authority and this is recorded as a `doctor_approved_assessment`/`doctor_modified_assessment` audit event. Sending a new patient message after a review resets `doctor_reviewed` since the assessment changes. A reviewed case is explicitly finalized with `POST /consultations/{id}/close`; closed cases reject further messages and review changes.

In **SHADOW** mode, the agent is restricted to collecting patient information and producing a factual intake summary for the doctor's dashboard. Its prompt prohibits diagnosis, treatment advice, and action recommendations, and the stored internal action is forced to `await_doctor_review`. Deterministic red-flag safety checks still run. The doctor records the clinical assessment and next action; closing the reviewed case uses that doctor-authored response to propose pending memory candidates.

### Diagnostic-test learning loop

The hospital catalog is stored in `diagnostic_test_catalog`. Doctors select active catalog entries instead of typing test names. `GET /diagnostic-tests` returns active entries; admins use `GET/POST /admin/diagnostic-tests` and `PATCH /admin/diagnostic-tests/{id}` to create, edit, activate/deactivate, and control autonomous eligibility. Catalog items are soft-deactivated, never hard-deleted from history.

Finalized test decisions are stored separately from episodic memory. In **SHADOW**, doctor-selected tests become positive examples. In **COPILOT**, accepted recommendations are positive examples, removed recommendations are negative examples, and doctor-added replacements are positive corrections. Open cases, patient intake, and autonomous decisions do not train the system.

For a completed COPILOT or AUTONOMOUS intake, the twin first creates the clinical assessment. The deterministic `get_test_recommendation_context` tool then retrieves only that doctor's similar finalized Shadow/Copilot decisions using de-identified symptoms, risk, age band, sex, and relevant conditions. A second catalog-constrained LLM call receives this transparent evidence and produces structured recommendations. Evidence snapshots are persisted with decisions so later history cannot rewrite why a recommendation was made.

AUTONOMOUS mode auto-orders a test only for a complete, non-fallback GREEN case when the catalog item is active and autonomous-eligible, current confidence passes its threshold, and matching Shadow/Copilot evidence passes the configured counts and acceptance rate. Otherwise the test remains `PROPOSED` for review. Test completion, specimens, results, reference ranges, billing, and external laboratory integration are outside the current scope.

### Memory learning loop
Doctor feedback/corrections are submitted as `CANDIDATE` memories (`POST /memories`). They are **never auto-promoted** - only `POST /memories/{id}/approve` makes a memory `APPROVED` and eligible for future retrieval; `POST /memories/{id}/reject` discards it. `GET /memories/{doctor_id}` lists all memories regardless of status.

Closing a reviewed case makes one best-effort structured Gemini call to extract zero or one candidate in each supported category: preference, escalation rule, communication style, clinical pattern, and workflow preference. Extracted items use source `case_closure`, skip normalized exact duplicates, and always remain `CANDIDATE` until explicitly approved. Provider or validation failures are audited but do not block closure. Memory governance lives in a dedicated dashboard tab with five doctor-scoped category tabs; each category contains separate Pending, Approved, and Rejected sections.

The local development database has no migration runner. After pulling a schema change such as the encounter `closed_at` field, recreate and reseed the disposable synthetic database with `npm run db:reset` followed by `npm run seed`.

### Evaluation suite
`evals/cases.json` has 32 synthetic cases (GREEN/AMBER/RED/ambiguous). `POST /evaluations/run` executes them all through the Doctor Twin + safety engine and computes real metrics (red flag recall, escalation recall, required-question coverage, structured output validity, doctor-preference alignment) - metrics are always computed from the actual run, never hard-coded. `GET /evaluations/results` returns the latest persisted run. The standalone CLI (`python evals/run_evals.py`, run from the repo root with the backend on `PYTHONPATH` and `TWIN_GEMINI_API_KEY` set) prints the same summary.

### Mocked MCP / clinic tools
`app/tools/clinic_tools.py` implements `get_patient`, `get_previous_visits`, `get_available_slots`, `create_appointment`, `create_clinical_note` against the local database - the twin never touches the database directly. `mcp/clinic_server.py` is a thin mock adapter mirroring the same interface (not a real MCP stdio/JSON-RPC server); it can be swapped for a real MCP-based EHR/scheduling integration later without changing the tool interface.

## Not yet implemented (future phases)

- pgvector-backed semantic memory retrieval (current retrieval is a naive keyword-overlap fallback).
- Full seed/ JSON datasets (a minimal idempotent `backend/app/seed_data.py` script exists instead).
- Docker/docker-compose, production deployment configuration.

## Frontend/backend integration notes (additive, not a backend redesign)

To support the frontend, a few minimal read/list endpoints were added on top of the existing API: `GET /doctors`, `GET /patients` (list all), and `GET /consultations?doctor_id=` (list a doctor's cases for the dashboard). CORS middleware was added (`TWIN_CORS_ALLOW_ORIGINS`, comma-separated, default `http://localhost:3000`). No existing endpoint behavior was changed.
