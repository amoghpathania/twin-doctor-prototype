"""Idempotent synthetic baseline data for local development and demos."""

from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models.domain import DiagnosticTestCatalog, Doctor, Memory, Patient
from app.models.schemas import MemoryStatus, MemoryType


DOCTOR_SEEDS = [
    {
        "name": "Dr. Sarah Lim",
        "specialty": "General Medicine",
        "experience": "10 years",
        "communication_style": "Concise, empathetic, asks structured follow-up questions.",
        "clinical_preferences": "Ask symptom duration before assessing severity; ask about relevant medication use.",
        "escalation_preferences": "Escalate persistent or worsening symptoms.",
    },
    {
        "name": "Dr. Arjun Mehta",
        "specialty": "Neurology",
        "experience": "14 years",
        "communication_style": "Calm and systematic; explains neurological questions in plain language.",
        "clinical_preferences": "Establish onset, progression, laterality, triggers, and associated neurological symptoms.",
        "escalation_preferences": "Urgently escalate sudden focal deficits, thunderclap headache, seizure, or altered consciousness.",
    },
    {
        "name": "Dr. Mei Lin Tan",
        "specialty": "Otolaryngology (ENT)",
        "experience": "11 years",
        "communication_style": "Practical and reassuring; uses short, specific symptom questions.",
        "clinical_preferences": "Clarify laterality, duration, hearing change, discharge, vertigo, and recent infection or exposure.",
        "escalation_preferences": "Escalate airway symptoms, sudden hearing loss, severe vertigo with neurological signs, or uncontrolled bleeding.",
    },
    {
        "name": "Dr. Noor Aziz",
        "specialty": "Family Medicine",
        "experience": "12 years",
        "communication_style": "Warm, holistic, and action-oriented with clear safety-netting.",
        "clinical_preferences": "Consider chronic conditions, medications, lifestyle, and continuity of care in every assessment.",
        "escalation_preferences": "Escalate unstable vital symptoms, significant deterioration, or concerns requiring same-day examination.",
    },
]

PATIENT_SEEDS = [
    {
        "name": "Tan Wei Ming",
        "age": 45,
        "sex": "male",
        "chronic_conditions": ["asthma"],
        "general_conditions": [],
        "medications": ["salbutamol inhaler"],
        "allergies": [],
    },
    {
        "name": "Lim Hui Ying",
        "age": 29,
        "sex": "female",
        "chronic_conditions": [],
        "general_conditions": [],
        "medications": [],
        "allergies": ["penicillin"],
    },
    {
        "name": "Ahmad Ismail",
        "age": 62,
        "sex": "male",
        "chronic_conditions": ["type 2 diabetes", "hypertension"],
        "general_conditions": [],
        "medications": ["metformin", "amlodipine"],
        "allergies": [],
    },
    {
        "name": "Priya Nair",
        "age": 34,
        "sex": "female",
        "chronic_conditions": [],
        "general_conditions": [],
        "medications": [],
        "allergies": [],
    },
    {
        "name": "Goh Zhi Hao",
        "age": 8,
        "sex": "male",
        "chronic_conditions": ["eczema"],
        "general_conditions": [],
        "medications": [],
        "allergies": ["shellfish"],
    },
    {
        "name": "Daniel Koh",
        "age": 38,
        "sex": "male",
        "chronic_conditions": ["migraine with aura"],
        "general_conditions": [],
        "medications": ["sumatriptan as needed"],
        "allergies": [],
    },
    {
        "name": "Nur Aisyah",
        "age": 31,
        "sex": "female",
        "chronic_conditions": ["allergic rhinitis"],
        "general_conditions": ["recurrent sinusitis"],
        "medications": ["intranasal corticosteroid"],
        "allergies": [],
    },
    {
        "name": "Mdm Wong Siew Lan",
        "age": 68,
        "sex": "female",
        "chronic_conditions": ["hypertension", "hyperlipidemia"],
        "general_conditions": ["intermittent dizziness"],
        "medications": ["losartan", "atorvastatin"],
        "allergies": ["sulfonamides"],
    },
]

DIAGNOSTIC_TEST_SEEDS = [
    {"code": "CBC", "name": "Complete Blood Count", "category": "Laboratory", "description": "Measures blood cell counts."},
    {"code": "CMP", "name": "Comprehensive Metabolic Panel", "category": "Laboratory", "description": "Measures metabolic and organ-function markers."},
    {"code": "CRP", "name": "C-Reactive Protein", "category": "Laboratory", "description": "Measures an inflammatory marker."},
    {"code": "UA", "name": "Urinalysis", "category": "Laboratory", "description": "Screens urine for common abnormalities."},
    {"code": "CXR", "name": "Chest X-Ray", "category": "Imaging", "description": "Plain radiograph of the chest."},
    {"code": "US-ABD", "name": "Abdominal Ultrasound", "category": "Imaging", "description": "Ultrasound imaging of the abdomen."},
    {"code": "ECG", "name": "Electrocardiogram", "category": "Cardiac", "description": "Records cardiac electrical activity."},
    {"code": "BCX", "name": "Blood Culture", "category": "Microbiology", "description": "Checks blood for microbial growth."},
]

MEMORY_SEEDS = {
    "Dr. Sarah Lim": [
        ("For persistent cough, ask about inhaler usage.", MemoryType.CLINICAL_PATTERN, 0.9, MemoryStatus.APPROVED),
        ("Ask about symptom duration before assessing severity.", MemoryType.PREFERENCE, 0.9, MemoryStatus.APPROVED),
        ("Escalate persistent or worsening symptoms rather than reassuring the patient.", MemoryType.ESCALATION_RULE, 0.9, MemoryStatus.APPROVED),
        ("Keep explanations concise; patients prefer short, clear guidance.", MemoryType.COMMUNICATION_STYLE, 0.85, MemoryStatus.APPROVED),
        ("Ask about relevant medication use before recommending over-the-counter remedies.", MemoryType.WORKFLOW_PREFERENCE, 0.85, MemoryStatus.APPROVED),
        ("For wheezing, also ask about recent exposure to allergens.", MemoryType.CLINICAL_PATTERN, 0.6, MemoryStatus.CANDIDATE),
        ("Always recommend the patient stop all medication immediately.", MemoryType.PREFERENCE, 0.4, MemoryStatus.CANDIDATE),
    ],
    "Dr. Arjun Mehta": [
        ("For headache, establish whether onset was sudden or gradual before discussing severity.", MemoryType.CLINICAL_PATTERN, 0.92, MemoryStatus.APPROVED),
        ("Ask about weakness, numbness, speech change, vision change, and loss of awareness one topic at a time.", MemoryType.WORKFLOW_PREFERENCE, 0.9, MemoryStatus.APPROVED),
        ("Escalate any new focal neurological deficit or thunderclap headache immediately.", MemoryType.ESCALATION_RULE, 0.98, MemoryStatus.APPROVED),
        ("Use concrete descriptions such as side, duration, and functional impact instead of neurological jargon.", MemoryType.COMMUNICATION_STYLE, 0.86, MemoryStatus.APPROVED),
        ("For recurrent migraine, ask how the current episode differs from the patient's usual pattern.", MemoryType.PREFERENCE, 0.88, MemoryStatus.APPROVED),
    ],
    "Dr. Mei Lin Tan": [
        ("For ear symptoms, establish which ear is affected and whether hearing changed suddenly.", MemoryType.CLINICAL_PATTERN, 0.92, MemoryStatus.APPROVED),
        ("Ask about discharge, fever, recent swimming, air travel, and instrument use when relevant.", MemoryType.WORKFLOW_PREFERENCE, 0.84, MemoryStatus.APPROVED),
        ("Escalate sudden hearing loss or breathing and swallowing difficulty for urgent assessment.", MemoryType.ESCALATION_RULE, 0.98, MemoryStatus.APPROVED),
        ("Describe ENT follow-up questions in familiar language and avoid unexplained anatomical terms.", MemoryType.COMMUNICATION_STYLE, 0.86, MemoryStatus.APPROVED),
        ("For dizziness, distinguish spinning sensation from light-headedness before asking about triggers.", MemoryType.PREFERENCE, 0.9, MemoryStatus.APPROVED),
    ],
    "Dr. Noor Aziz": [
        ("Review chronic conditions and current medicines before forming a general-care summary.", MemoryType.WORKFLOW_PREFERENCE, 0.9, MemoryStatus.APPROVED),
        ("For fever, ask about duration, hydration, breathing symptoms, and relevant exposure history.", MemoryType.CLINICAL_PATTERN, 0.88, MemoryStatus.APPROVED),
        ("Escalate significant deterioration or symptoms requiring same-day physical examination.", MemoryType.ESCALATION_RULE, 0.92, MemoryStatus.APPROVED),
        ("End summaries with concise safety-net information for the reviewing doctor.", MemoryType.COMMUNICATION_STYLE, 0.84, MemoryStatus.APPROVED),
        ("Consider preventive care and continuity needs when they are relevant to the presenting concern.", MemoryType.PREFERENCE, 0.82, MemoryStatus.APPROVED),
    ],
}

SEED_DOCTOR_NAMES = frozenset(item["name"] for item in DOCTOR_SEEDS)
SEED_PATIENT_NAMES = frozenset(item["name"] for item in PATIENT_SEEDS)
SEED_MEMORY_KEYS = frozenset(
    (doctor_name, content)
    for doctor_name, memories in MEMORY_SEEDS.items()
    for content, _memory_type, _confidence, _status in memories
)


def seed_session(session: Session) -> dict[str, int]:
    created = {"doctors": 0, "patients": 0, "memories": 0}
    doctors_by_name = {doctor.name: doctor for doctor in session.query(Doctor).all()}

    for values in DOCTOR_SEEDS:
        if values["name"] in doctors_by_name:
            continue
        doctor = Doctor(**values, twin_version="v1")
        session.add(doctor)
        session.flush()
        doctors_by_name[doctor.name] = doctor
        created["doctors"] += 1

    existing_patient_names = {patient.name for patient in session.query(Patient).all()}
    for values in PATIENT_SEEDS:
        if values["name"] in existing_patient_names:
            continue
        session.add(Patient(**values, previous_visits=[]))
        existing_patient_names.add(values["name"])
        created["patients"] += 1

    existing_test_codes = {item.code for item in session.query(DiagnosticTestCatalog).all()}
    for values in DIAGNOSTIC_TEST_SEEDS:
        if values["code"] in existing_test_codes:
            continue
        session.add(DiagnosticTestCatalog(**values))
        existing_test_codes.add(values["code"])

    existing_memory_keys = {(memory.doctor_id, memory.content) for memory in session.query(Memory).all()}
    for doctor_name, memories in MEMORY_SEEDS.items():
        doctor = doctors_by_name[doctor_name]
        for content, memory_type, confidence, status in memories:
            if (doctor.id, content) in existing_memory_keys:
                continue
            session.add(
                Memory(
                    doctor_id=doctor.id,
                    content=content,
                    memory_type=memory_type.value,
                    source="doctor_feedback",
                    confidence=confidence,
                    status=status.value,
                )
            )
            existing_memory_keys.add((doctor.id, content))
            created["memories"] += 1

    session.commit()
    return created


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        created = seed_session(session)
        print(
            "Seeded "
            f"{created['doctors']} doctors, {created['patients']} patients, and {created['memories']} memories."
        )
    finally:
        session.close()


if __name__ == "__main__":
    seed()