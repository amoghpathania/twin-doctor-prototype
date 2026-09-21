"use client";

import { useEffect, useRef, useState } from "react";
import { api, ConsultationResponse, Doctor, Patient } from "@/lib/api";
import { RiskBadge } from "@/components/RiskBadge";

export default function IntakePage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [doctorId, setDoctorId] = useState<number | null>(null);
  const [patientId, setPatientId] = useState<number | null>(null);
  const [isNewPatient, setIsNewPatient] = useState(false);
  const [patientIdInput, setPatientIdInput] = useState("");
  const [lookedUpPatient, setLookedUpPatient] = useState<Patient | null>(null);
  const [lookingUp, setLookingUp] = useState(false);
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [newPatientName, setNewPatientName] = useState("");
  const [newPatientAge, setNewPatientAge] = useState("");
  const [newPatientSex, setNewPatientSex] = useState("female");
  const [newPatientChronicConditions, setNewPatientChronicConditions] = useState("");
  const [newPatientGeneralConditions, setNewPatientGeneralConditions] = useState("");
  const [registering, setRegistering] = useState(false);
  const [message, setMessage] = useState("");
  const [consultation, setConsultation] = useState<ConsultationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [optimisticPatientMessage, setOptimisticPatientMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openCases, setOpenCases] = useState<ConsultationResponse[]>([]);
  const [loadingCases, setLoadingCases] = useState(false);
  // The twin asks exactly one question per turn (server-enforced); holds it until the patient replies.
  const [pendingQueue, setPendingQueue] = useState<string[]>([]);
  // Guards against React StrictMode's dev-only double effect invocation firing this GET twice.
  const doctorsFetchedRef = useRef(false);
  const lookupInFlightRef = useRef(false);
  const registerInFlightRef = useRef(false);
  const composerInFlightRef = useRef(false);

  useEffect(() => {
    if (doctorsFetchedRef.current) return;
    doctorsFetchedRef.current = true;
    api
      .listDoctors()
      .then((list) => {
        setDoctors(list);
        if (list.length > 0) setDoctorId(list[0].id);
      })
      .catch((e) => setError(String(e)));
    api.listPatients().then(setPatients).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!patientId) {
      setOpenCases([]);
      return;
    }
    // Ignore this fetch's result if patientId changes again before it resolves (avoids a stale
    // response for a previous ID overwriting the list for the current one).
    let stale = false;
    setLoadingCases(true);
    api
      .listOpenPatientConsultations(patientId)
      .then((cases) => {
        if (!stale) setOpenCases(cases);
      })
      .catch((e) => {
        if (!stale) setError(String(e));
      })
      .finally(() => {
        if (!stale) setLoadingCases(false);
      });
    return () => {
      stale = true;
    };
  }, [patientId]);

  function splitConditions(value: string): string[] {
    return value
      .split(",")
      .map((c) => c.trim())
      .filter((c) => c.length > 0);
  }

  async function loadOpenCases(id: number) {
    setLoadingCases(true);
    try {
      const cases = await api.listOpenPatientConsultations(id);
      setOpenCases(cases);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoadingCases(false);
    }
  }

  async function handleLookupPatient() {
    if (!patientIdInput.trim() || lookupInFlightRef.current) return;
    lookupInFlightRef.current = true;
    setLookingUp(true);
    setLookupError(null);
    setLookedUpPatient(null);
    try {
      const patient = await api.getPatient(Number(patientIdInput));
      setLookedUpPatient(patient);
      setPatientId(patient.id);
    } catch (e) {
      setLookupError("No patient found with that ID.");
      setPatientId(null);
    } finally {
      setLookingUp(false);
      lookupInFlightRef.current = false;
    }
  }

  async function handleRegisterNewPatient() {
    if (!newPatientName.trim() || !newPatientAge || registerInFlightRef.current) return;
    registerInFlightRef.current = true;
    setRegistering(true);
    setError(null);
    try {
      const created = await api.createPatient({
        name: newPatientName,
        age: Number(newPatientAge),
        sex: newPatientSex,
        chronic_conditions: splitConditions(newPatientChronicConditions),
        general_conditions: splitConditions(newPatientGeneralConditions),
      });
      setPatientId(created.id);
      setIsNewPatient(false);
      setNewPatientName("");
      setNewPatientAge("");
      setNewPatientChronicConditions("");
      setNewPatientGeneralConditions("");
    } catch (e) {
      setError(String(e));
    } finally {
      setRegistering(false);
      registerInFlightRef.current = false;
    }
  }

  function applyConsultationResult(result: ConsultationResponse) {
    setConsultation(result);
    setPendingQueue(result.assessment.missing_information);
    if (patientId) loadOpenCases(patientId);
  }

  function handleResumeCase(caseToResume: ConsultationResponse) {
    setConsultation(caseToResume);
    setDoctorId(caseToResume.doctor_id);
    setPendingQueue(caseToResume.assessment.missing_information);
    setMessage("");
    setError(null);
  }

  async function handleComposerSubmit() {
    if (!doctorId || !patientId || !message.trim() || composerInFlightRef.current) return;
    composerInFlightRef.current = true;
    const text = message.trim();
    setLoading(true);
    setOptimisticPatientMessage(text);
    setMessage("");
    setError(null);
    try {
      if (!consultation) {
        const result = await api.startConsultation({ doctor_id: doctorId, patient_id: patientId, message: text });
        applyConsultationResult(result);
      } else {
        const result = await api.addConsultationMessage(consultation.id, text);
        applyConsultationResult(result);
      }
      setOptimisticPatientMessage(null);
    } catch (e) {
      setOptimisticPatientMessage(null);
      setMessage(text);
      setError(String(e));
    } finally {
      setLoading(false);
      composerInFlightRef.current = false;
    }
  }

  function resetConsultation() {
    setConsultation(null);
    setMessage("");
    setOptimisticPatientMessage(null);
    setPendingQueue([]);
    if (patientId) loadOpenCases(patientId);
  }

  function handlePatientSelect(id: number) {
    const patient = patients.find((item) => item.id === id) ?? null;
    setPatientId(patient?.id ?? null);
    setLookedUpPatient(patient);
    setPatientIdInput(patient ? String(patient.id) : "");
    setLookupError(null);
  }

  const isEmergency = consultation?.risk_level === "RED";
  const selectedDoctor = doctors.find((doctor) => doctor.id === doctorId) ?? null;
  const selectedPatient = lookedUpPatient ?? patients.find((patient) => patient.id === patientId) ?? null;
  const patientConditions = selectedPatient
    ? [...selectedPatient.chronic_conditions, ...selectedPatient.general_conditions]
    : [];

  const currentQuestion = pendingQueue[0] ?? null;
  const composerLabel = !consultation
    ? "Describe your symptoms"
    : currentQuestion
    ? "Your answer"
    : "Anything else the doctor should know?";
  const composerPlaceholder = !consultation
    ? "I have had a fever and cough for three days."
    : currentQuestion
    ? "Type your answer here..."
    : "Optional follow-up message";
  const sendButtonLabel = loading
    ? "Sending..."
    : !consultation
    ? "Start consultation"
    : currentQuestion
    ? "Send answer"
    : "Send follow-up";

  return (
    <div>
      <div className="page-header">
        <h1>Patient Intake</h1>
        <p>Describe symptoms to the doctor twin and answer its follow-up questions.</p>
      </div>
      {error && <div className="error-banner">{error}</div>}

      <div className="card intake-identity-panel">
        <div className="intake-panel-heading">
          <div>
            <span className="section-kicker">Before you begin</span>
            <h2>Choose your patient profile and doctor</h2>
          </div>
          <div className="patient-type-switch" aria-label="Patient type">
            <button
              type="button"
              className={!isNewPatient ? "active" : ""}
              disabled={!!consultation}
              onClick={() => setIsNewPatient(false)}
            >
              Existing patient
            </button>
            <button
              type="button"
              className={isNewPatient ? "active" : ""}
              disabled={!!consultation}
              onClick={() => setIsNewPatient(true)}
            >
              New patient
            </button>
          </div>
        </div>

        <div className="identity-grid">
          {!isNewPatient && (
            <div className="identity-field">
              <div className="identity-icon" aria-hidden="true">P</div>
              <div className="field">
                <label htmlFor="patient-profile">Patient profile</label>
                <select
                  id="patient-profile"
                  value={patientId ?? ""}
                  disabled={!!consultation}
                  onChange={(e) => handlePatientSelect(Number(e.target.value))}
                >
                  <option value="">Select a patient</option>
                  {patients.map((patient) => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name} ({patient.age}, {patient.sex})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <div className="identity-field">
            <div className="identity-icon doctor" aria-hidden="true">DT</div>
            <div className="field">
              <label htmlFor="doctor">Doctor&apos;s digital twin</label>
              <select
                id="doctor"
                value={doctorId ?? ""}
                disabled={!!consultation}
                onChange={(e) => setDoctorId(Number(e.target.value))}
              >
                {doctors.map((doctor) => (
                  <option key={doctor.id} value={doctor.id}>
                    {doctor.name} - {doctor.specialty}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {!isNewPatient && selectedPatient && (
          <div className="patient-profile-summary">
            <div>
              <span>Patient</span>
              <strong>{selectedPatient.name}, {selectedPatient.age}</strong>
            </div>
            <div>
              <span>Known conditions</span>
              <strong>{patientConditions.join(", ") || "None recorded"}</strong>
            </div>
            <div>
              <span>Allergies</span>
              <strong>{selectedPatient.allergies.join(", ") || "None recorded"}</strong>
            </div>
          </div>
        )}

        {!isNewPatient && patients.length === 0 && (
          <div className="field patient-id-fallback">
            <label htmlFor="patient-id">Patient ID</label>
            <div className="inline-field">
              <input
                id="patient-id"
                type="text"
                value={patientIdInput}
                disabled={!!consultation}
                onChange={(e) => {
                  setPatientIdInput(e.target.value);
                  setLookedUpPatient(null);
                  setPatientId(null);
                }}
              />
              <button type="button" onClick={handleLookupPatient} disabled={!!consultation || lookingUp || !patientIdInput.trim()}>
                {lookingUp ? "Looking up..." : "Look up"}
              </button>
            </div>
            {lookupError && <p className="error-banner">{lookupError}</p>}
          </div>
        )}

        {isNewPatient && !consultation && (
          <div className="grid-2">
            <div className="field">
              <label htmlFor="new-patient-name">Full name</label>
              <input id="new-patient-name" type="text" value={newPatientName} onChange={(e) => setNewPatientName(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="new-patient-age">Age</label>
              <input id="new-patient-age" type="text" value={newPatientAge} onChange={(e) => setNewPatientAge(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="new-patient-sex">Sex</label>
              <select id="new-patient-sex" value={newPatientSex} onChange={(e) => setNewPatientSex(e.target.value)}>
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="new-patient-chronic">Chronic conditions (comma separated)</label>
              <input
                id="new-patient-chronic"
                type="text"
                placeholder="e.g. diabetes, hypertension, asthma"
                value={newPatientChronicConditions}
                onChange={(e) => setNewPatientChronicConditions(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="new-patient-general">Recent/general conditions (comma separated)</label>
              <input
                id="new-patient-general"
                type="text"
                placeholder="e.g. recent surgery, physical therapy"
                value={newPatientGeneralConditions}
                onChange={(e) => setNewPatientGeneralConditions(e.target.value)}
              />
            </div>
            <div style={{ display: "flex", alignItems: "flex-end" }}>
              <button onClick={handleRegisterNewPatient} disabled={registering || !newPatientName.trim() || !newPatientAge}>
                {registering ? "Registering..." : "Register patient"}
              </button>
            </div>
          </div>
        )}

        {consultation && (
          <button className="secondary" onClick={resetConsultation}>
            Start a new case
          </button>
        )}
      </div>

      {!consultation && patientId && (
        <section className="card open-cases-panel" aria-labelledby="open-cases-heading">
          <div className="card-row">
            <div>
              <span className="section-kicker">Continue where you left off</span>
              <h2 id="open-cases-heading">Open cases</h2>
            </div>
            {!loadingCases && <span className="case-count">{openCases.length}</span>}
          </div>
          {loadingCases && <p className="muted">Loading your cases...</p>}
          {!loadingCases && openCases.length === 0 && <p className="muted">No open cases yet. Start a new one below.</p>}
          {!loadingCases && openCases.length > 0 && (
            <div className="case-list open-case-grid">
              {openCases.map((caseItem) => (
                <button key={caseItem.id} type="button" className="case-list-item" onClick={() => handleResumeCase(caseItem)}>
                  <div className="case-list-item-info">
                    <div className="case-list-item-title">Case #{caseItem.id} · {new Date(caseItem.created_at).toLocaleDateString()}</div>
                    <div className="case-list-item-preview">
                      {caseItem.conversation[caseItem.conversation.length - 1]?.content ?? "No messages yet"}
                    </div>
                  </div>
                  <RiskBadge risk={caseItem.risk_level} />
                </button>
              ))}
            </div>
          )}
        </section>
      )}

      {!consultation && patientId && selectedDoctor && (
        <div className="consultation-intro">
          <div>
            <span className="section-kicker">Active twin consultation</span>
            <h2>{selectedDoctor.name}&apos;s Digital Twin</h2>
            <p>{selectedDoctor.specialty} · Mode: {selectedDoctor.default_deployment_mode}</p>
          </div>
          <div className="quick-prompts" aria-label="Example symptom descriptions">
            <span>Quick fill</span>
            <button type="button" className="secondary small" onClick={() => setMessage("I have had a cold and sneezing since yesterday.")}>Cold and sneezing</button>
            <button type="button" className="secondary small" onClick={() => setMessage("I have had a persistent cough for three weeks.")}>Persistent cough</button>
            <button type="button" className="secondary small" onClick={() => setMessage("I have wheezing and shortness of breath.")}>Asthma symptoms</button>
          </div>
        </div>
      )}

      {(consultation || optimisticPatientMessage) && (
        <div className="card">
          <div className="card-row">
            <h2 style={{ marginBottom: 0 }}>{consultation ? `Case #${consultation.id}` : "Starting your case"}</h2>
          </div>

          {consultation && isEmergency && (
            <div className="error-banner">
              <strong>This may be a medical emergency.</strong>{" "}
              {consultation.escalation_reason ?? "Please seek immediate medical attention or contact emergency services."}{" "}
              A case has been created in your doctor's dashboard for immediate review.
            </div>
          )}

          {consultation?.assessment.fallback_used && (
            <div className="safety-banner" role="status">
              <strong>Your case has been created.</strong> {consultation.summary}
            </div>
          )}

          <h3>Conversation</h3>
          <div className="conversation" aria-live="polite">
            {consultation?.conversation.map((turn, i) => (
              <div key={`h-${i}`} className={`conversation-turn ${turn.role}`}>
                <span className="turn-role">{turn.role === "patient" ? "You" : "Doctor's twin"}</span>
                {turn.content}
              </div>
            ))}
            {currentQuestion && !isEmergency && (
              <div className="conversation-turn twin current">
                <span className="turn-role">Doctor's twin</span>
                {currentQuestion}
              </div>
            )}
            {optimisticPatientMessage && (
              <div className="conversation-turn patient optimistic">
                <span className="turn-role">You</span>
                {optimisticPatientMessage}
              </div>
            )}
            {loading && optimisticPatientMessage && (
              <div className="conversation-turn twin thinking" role="status">
                <span className="turn-role">Doctor&apos;s twin</span>
                Doctor&apos;s twin is reviewing your message<span className="thinking-dots" aria-hidden="true">...</span>
              </div>
            )}
          </div>

          {!isEmergency && !currentQuestion && !loading && (
            <p className="muted">Thanks for sharing these details. Your doctor will review your case and follow up if needed.</p>
          )}

          {consultation && consultation.available_slots.length > 0 && (
            <div>
              <h3>Available appointment slots</h3>
              <ul>
                {consultation.available_slots.map((slot) => (
                  <li key={slot.start}>{new Date(slot.start).toLocaleString()}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {isEmergency ? (
        <div className="card">
          <h3>Please show this to your doctor now</h3>
          <p>
            Chat has been stopped for this case because it may be a medical emergency. Show this screen to a doctor
            immediately, or seek in-person or emergency care right away - do not wait for a chat reply.
          </p>
        </div>
      ) : (
        <div className="card">
          <div className="field">
            <label htmlFor="message">{composerLabel}</label>
            <textarea
              id="message"
              rows={3}
              value={message}
              placeholder={composerPlaceholder}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>
          <button onClick={handleComposerSubmit} disabled={loading || !message.trim() || !doctorId || !patientId}>
            {sendButtonLabel}
          </button>
        </div>
      )}
    </div>
  );
}
