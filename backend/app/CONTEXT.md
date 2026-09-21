# backend/app/ context

FastAPI application package. Entry point: `main.py` (creates tables on startup via lifespan, mounts all routers, `/health`).

## Sub-packages
- `api/` - FastAPI routers (thin - delegate to services/repositories). See [api/CONTEXT.md](api/CONTEXT.md).
- `agents/` - Doctor Twin orchestration, prompt building, LLM client abstraction, deployment-mode policy. See [agents/CONTEXT.md](agents/CONTEXT.md).
- `safety/` - deterministic red-flag detection + override policy, independent of the LLM. See [safety/CONTEXT.md](safety/CONTEXT.md).
- `memory/` - approved-memory retrieval + candidate/approve/reject lifecycle. See [memory/CONTEXT.md](memory/CONTEXT.md).
- `tools/` - clinic tools plus deterministic doctor-specific test-decision context retrieval. See [tools/CONTEXT.md](tools/CONTEXT.md).
- `models/` - Pydantic schemas + SQLAlchemy ORM models. See [models/CONTEXT.md](models/CONTEXT.md).
- `services/` - orchestration: consultation flow, audit logging, evaluation runner, diagnostic-test decisions, and scenario-matched learning. See [services/CONTEXT.md](services/CONTEXT.md).
- `repositories/` - SQLAlchemy CRUD per entity, all extend a generic `Repository[ModelT]` base. See [repositories/CONTEXT.md](repositories/CONTEXT.md).

## Top-level files
- `config.py` - `Settings` (pydantic-settings, env prefix `TWIN_`): `database_url`, `gemini_api_key`, `gemini_model`, `eval_cases_path`, `app_name`, `environment`.
- `db.py` - SQLAlchemy `Base`, `engine`, `SessionLocal`, `get_db` FastAPI dependency. Uses `check_same_thread=False` for SQLite.
- `main.py` - app factory + router mounting + `/health`.

## Conventions
- The AI (Doctor Twin) never touches the database directly - it only calls `app/tools/clinic_tools.py` functions, which use repositories.
- Routers that need an LLM client depend on `app.api.deps.get_llm_client` (shared, overridable in tests via `app.dependency_overrides`).
- Workflow order is always: `DoctorTwin` (LLM) -> `safety.policy.apply_safety_policy` (can override risk to RED) -> `agents.deployment_policy.evaluate_deployment_policy` (decides allowed actions per mode) -> persist + audit.
