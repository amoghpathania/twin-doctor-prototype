# frontend/ context

Next.js (App Router, TypeScript, no CSS framework) frontend for the Doctor Digital Twin prototype. Hand-rolled clinical design system in `app/globals.css` (teal/mist palette, CSS variables, sidebar app shell, cards, badges, tables, stat grids) - no component library, but deliberately more polished than a bare unstyled page after an initial pass looked too bare-bones for real usability.

## Stack
Next.js 16.3.5 + React 19 (deliberately upgraded from the initial 14.x scaffold to resolve `npm audit` high/critical vulnerabilities - 0 vulnerabilities as of last check). Plain `fetch` for API calls, no data-fetching library.

## Visual structure
- `app/globals.css` - design tokens (`--color-*`, `--radius-*`, `--shadow-*`) plus reusable classes: `.app-shell`/`.sidebar`/`.content` (layout), `.card`, `.page-header`, `.stat-grid`/`.stat-card` (eval metrics), `.home-grid`/`.home-card` (landing page), `.badge` (+ `.GREEN`/`.AMBER`/`.RED`/`.CANDIDATE`/`.APPROVED`/`.REJECTED` modifiers), `.conversation`/`.conversation-turn`, `.table-wrap` (scrollable table container), `.error-banner`/`.safety-banner`/`.empty-state`, button variants (`.secondary`, `.small`).
- `components/SidebarNav.tsx` - client component (`usePathname`) rendering the left sidebar nav with active-link highlighting and a persona label (Patient/Doctor/Admin) per screen.
- `app/layout.tsx` - renders the `.app-shell`: fixed sidebar (brand + nav + safety footer) + scrollable `.content` area wrapping every page.
- Each page uses a `.page-header` (`<h1>` + description) at the top, then `.card`-wrapped sections.

## Layout
- `lib/api.ts` - single typed API client (`api.listDoctors()`, `api.startConsultation()`, etc.) mirroring the backend's Pydantic schemas. Reads `NEXT_PUBLIC_API_BASE_URL` (default `http://127.0.0.1:8014`). All screens import from here - don't call `fetch` directly in page components.
- `components/RiskBadge.tsx` - colored GREEN/AMBER/RED badge (uses `.badge` classes from globals.css).
- `components/DeploymentModeSelector.tsx` - shared SHADOW/COPILOT/INTAKE/AUTONOMOUS dropdown.
- `app/intake/page.tsx` - **Screen 1: Patient Intake**. An identity-first panel selects a synthetic patient profile and doctor twin, summarizes known conditions/allergies, and retains a new-patient registration path. After selection, compact resumable-case cards and quick symptom prompts lead into the consultation composer. The conversation renders as a chatbot-style thread with live risk/escalation state and available slots. After patient selection/registration, `GET /consultations/patient/{patient_id}` loads that patient's open (not yet doctor-reviewed) cases. The server returns at most one `assessment.missing_information` question per turn; each answer calls `POST /consultations/{id}/messages`. Patient messages render optimistically and the thread shows an accessible twin loading placeholder until the LLM response arrives. The first message of a new case calls `POST /consultations`.
- `app/dashboard/page.tsx` - **Screen 2: Doctor Dashboard**. Select doctor and deployment mode once, then switch between top-level Patient Cases, Memory Management, and Evaluation tabs. Patient Cases supports review, explicit closure, and optional closed history. Pending SHADOW cases show only the factual patient intake summary (never an agent diagnosis/action); the doctor records their assessment and next action, then closes the case to generate pending memory candidates from that response. Memory Management has five doctor-scoped category tabs; the active category filters responsive CANDIDATE/APPROVED/REJECTED review lists and the manual candidate form. Evaluation runs `POST /evaluations/run` and shows the resulting metrics as a stat grid.
- `app/admin/page.tsx` - **Screen 3: Admin**. Shows live resettable row counts and protected baseline counts, provides a typed-confirmation data reset, and retains doctor onboarding and the existing-doctor table. Reset clears encounters, appointments, audits, evaluations, added profiles, and non-baseline memories without deleting deterministic seed records.
- `app/memory/page.tsx` - **Screen 3: Twin Memory**. Select doctor, view CANDIDATE/APPROVED/REJECTED memories in separate lists, approve/reject candidates, and a form to record new doctor feedback as a CANDIDATE memory.

## What's connected vs. not
The dashboard's approve/modify actions call the backend's `POST /consultations/{id}/review` endpoint (doctor is always the final authority - modify does **not** re-run the safety engine). There is still no "doctor manually escalates" endpoint beyond what happens automatically from risk level - the dashboard doesn't add a separate escalate button since none exists on the backend.

## Backend changes made to support the frontend (additive only)
- `GET /doctors`, `GET /patients` (list-all, previously only get-by-id existed).
- `GET /consultations?doctor_id=` (list, for the dashboard).
- `GET /consultations/patient/{patient_id}` (list, for the patient's resumable open cases - excludes `doctor_reviewed` cases; no auth layer yet, see Further Considerations below).
- CORS middleware (`TWIN_CORS_ALLOW_ORIGINS` setting, default `http://localhost:3000`).
- `backend/app/seed_data.py` - per-record idempotent baseline seeder with General Medicine, Neurology, ENT, and Family Medicine doctors; eight matching synthetic patients; and doctor-specific approved/candidate memories. Re-running it fills missing baseline records without replacing existing data.

## Known prototype limitation
`GET /consultations/patient/{patient_id}` is scoped by the ID the caller supplies with no authentication - acceptable for this synthetic prototype, but must be replaced with an authenticated patient identity before any real deployment.

## Run
```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```
Requires the backend running first (`uvicorn app.main:app --reload` from `backend/`) and seeded (`python -m app.seed_data`).
