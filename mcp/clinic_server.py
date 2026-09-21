"""Mock Clinic MCP server.

This mirrors the tool interface a real MCP-based clinic integration would expose
(get_patient, get_previous_visits, get_available_slots, create_appointment,
create_clinical_note). It is an internal/mock adapter over the local database via
app.tools.clinic_tools - not a real MCP stdio/JSON-RPC server. Swap this module's
internals for a real MCP client later without changing the tool interface.
"""

import sys
from datetime import datetime
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.tools import clinic_tools  # noqa: E402


class ClinicMCPServer:
    def __init__(self, session) -> None:
        self.session = session

    def get_patient(self, patient_id: int):
        return clinic_tools.get_patient(self.session, patient_id)

    def get_previous_visits(self, patient_id: int):
        return clinic_tools.get_previous_visits(self.session, patient_id)

    def get_available_slots(self, doctor_id: int, day: datetime | None = None):
        return clinic_tools.get_available_slots(self.session, doctor_id, day)

    def create_appointment(self, doctor_id: int, patient_id: int, slot_start: datetime, encounter_id: int | None = None):
        return clinic_tools.create_appointment(self.session, doctor_id, patient_id, slot_start, encounter_id)

    def create_clinical_note(self, encounter_id: int, content: str) -> None:
        clinic_tools.create_clinical_note(self.session, encounter_id, content)
