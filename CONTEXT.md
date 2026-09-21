# Repo context index

Doctor Digital Twin prototype (synthetic data only, not a real medical device). See root [README.md](README.md) for setup/run/test instructions and the safety position.

Each folder below has its own `CONTEXT.md` with what lives there, key conventions, and gotchas. Read the relevant one(s) before making changes.

- [backend/CONTEXT.md](backend/CONTEXT.md) - FastAPI app, phases 1-7 implemented (domain/repos/APIs, Doctor Twin, safety engine, deployment modes, clinic tools, memory approval loop, evaluation suite).
- [backend/app/CONTEXT.md](backend/app/CONTEXT.md) - app package layout.
- [backend/app/api/CONTEXT.md](backend/app/api/CONTEXT.md)
- [backend/app/agents/CONTEXT.md](backend/app/agents/CONTEXT.md)
- [backend/app/safety/CONTEXT.md](backend/app/safety/CONTEXT.md)
- [backend/app/memory/CONTEXT.md](backend/app/memory/CONTEXT.md)
- [backend/app/models/CONTEXT.md](backend/app/models/CONTEXT.md)
- [backend/app/repositories/CONTEXT.md](backend/app/repositories/CONTEXT.md)
- [backend/app/services/CONTEXT.md](backend/app/services/CONTEXT.md)
- [backend/app/tools/CONTEXT.md](backend/app/tools/CONTEXT.md)
- [backend/tests/CONTEXT.md](backend/tests/CONTEXT.md)
- [evals/CONTEXT.md](evals/CONTEXT.md)
- [mcp/CONTEXT.md](mcp/CONTEXT.md)
- [frontend/CONTEXT.md](frontend/CONTEXT.md) - Next.js app (phase 8): Patient Intake, Doctor Dashboard, Twin Memory screens.

## Status (as of this writing)
Implemented: phases 1-7 (domain/repos/read APIs, Doctor Twin + structured output, deterministic safety engine, deployment modes, mocked clinic tools/MCP, memory candidate/approve/reject loop, evaluation suite). 57/57 backend tests passing.

Not yet implemented: pgvector semantic memory retrieval (currently naive keyword overlap), Next.js frontend, seed datasets, Docker/docker-compose, production deployment.

Not in this repo yet: `src/twin_api` (an earlier flat FastAPI boilerplate) was removed and replaced by `backend/app/...` early on - don't recreate it.
