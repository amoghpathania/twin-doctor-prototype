# mcp/ context

Mock Clinic MCP server - demonstrates how the Doctor Twin would integrate with a real clinic/EHR system via MCP, without implementing a real MCP stdio/JSON-RPC protocol server (explicitly out of scope per user instruction: "mock it up for the time being").

## Files
- `clinic_server.py` - `ClinicMCPServer(session)` class exposing `get_patient`, `get_previous_visits`, `get_available_slots`, `create_appointment`, `create_clinical_note` - same signatures as `backend/app/tools/clinic_tools.py`, and delegates directly to those functions. Inserts `backend/` onto `sys.path` at import time (it's a repo-root sibling of `backend/`, not a subpackage).

## Future work (not implemented)
Replace the internals of `ClinicMCPServer` with a real MCP client/server (stdio or JSON-RPC transport) talking to an actual EHR/scheduling/billing system, without changing the public method signatures - callers (Doctor Twin workflows) shouldn't need to change.

## Tests
Covered by `backend/tests/test_clinic_tools.py::test_mock_mcp_clinic_server_delegates_to_clinic_tools`, which inserts the repo root onto `sys.path` itself before importing `mcp.clinic_server`.
