# backend/ context

FastAPI backend for the Doctor Digital Twin prototype. Deployable standalone (target: Railway) - the API only reaches outside `backend/` to read `evals/cases.json` for `/evaluations/run`.

## Layout
- `app/` - the application package (see [app/CONTEXT.md](app/CONTEXT.md)).
- `tests/` - pytest suite, fully hermetic (see [tests/CONTEXT.md](tests/CONTEXT.md)).
- `requirements.txt` - pinned deps (fastapi, uvicorn, pydantic, pydantic-settings, sqlalchemy, google-generativeai, pytest, httpx).
- `pytest.ini` - sets `pythonpath = .` and `testpaths = tests` so `app` imports resolve without installing the package.

## Run / test
```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pytest backend\tests -v
cd backend; ..\.venv\Scripts\uvicorn.exe app.main:app --reload
```

## Key decisions
- DB: SQLite via SQLAlchemy repository abstraction (`TWIN_DATABASE_URL`, default `sqlite:///./twin.db`). Designed so swapping to Postgres/pgvector later is a config change, not a rewrite.
- LLM: **Gemini** (`google-generativeai`), not OpenAI - user preference, deviates from the original take-home spec. Configured via `TWIN_GEMINI_API_KEY` / `TWIN_GEMINI_MODEL`.
- All automated tests use a `FakeLLMClient`/`ScriptedLLMClient` test double - no real Gemini calls in CI.
- Gemini quota, network, authentication, and malformed-output failures produce a persisted AMBER case with `fallback_used=true`; the patient sees a stable message while the doctor receives the case for review.
- Settings are in `app/config.py` (pydantic-settings, env prefix `TWIN_`, reads root `.env`).
