# backend/app/tools/ context

The tool/service layer the AI (and doctor-facing workflows) use to interact with the clinic. **The AI must never touch the database directly** - only through these functions.

## Files
- `clinic_tools.py`:
  - `get_patient(session, patient_id)` / `get_previous_visits(session, patient_id)` - thin repository reads.
  - `get_available_slots(session, doctor_id, day=None) -> list[AppointmentSlot]` - synthetic clinic hours (9am-5pm hourly, `_SLOT_HOURS` / `_SLOT_DURATION`), excludes already-booked slots for that doctor/day. Uses **naive** datetimes deliberately (see [../models/CONTEXT.md](../models/CONTEXT.md) gotcha).
  - `create_appointment(session, doctor_id, patient_id, slot_start, encounter_id=None) -> Appointment` - persists, links `Encounter.appointment_id` if an encounter is given, records an `appointment_created` audit event.
  - `create_clinical_note(session, encounter_id, content) -> None` - synthetic demo note capture, recorded as a `clinical_note` audit event (no dedicated notes table exists yet - deliberate simplification).

## Relationship to mcp/
[../../../mcp/CONTEXT.md](../../../mcp/CONTEXT.md) (`mcp/clinic_server.py`, repo root) is a mock adapter that mirrors this exact function interface, standing in for a real MCP-based clinic/EHR integration. It delegates directly to these functions - no real MCP stdio/JSON-RPC protocol is implemented (explicitly deferred, per user instruction to "mock it up for the time being").
