"use client";

import { Fragment, useEffect, useState } from "react";
import {
  api,
  ConsultationResponse,
  DiagnosticTestCatalog,
  Doctor,
  DeploymentMode,
  MemoryRead,
  MemoryType,
  Patient,
  RiskLevel,
} from "@/lib/api";
import { RiskBadge } from "@/components/RiskBadge";
import { DiagnosticTestsPanel, getInitialSelectedTestIds } from "@/components/DiagnosticTestsPanel";

const MODES: DeploymentMode[] = ["SHADOW", "COPILOT", "INTAKE", "AUTONOMOUS"];
const MEMORY_TYPES: MemoryType[] = [
  "preference",
  "escalation_rule",
  "communication_style",
  "clinical_pattern",
  "workflow_preference",
];
const MEMORY_TYPE_LABELS: Record<MemoryType, string> = {
  preference: "Preference",
  escalation_rule: "Escalation Rule",
  communication_style: "Communication Style",
  clinical_pattern: "Clinical Pattern",
  workflow_preference: "Workflow Preference",
};
// Lower rank surfaces first - emergencies must never be buried below older, lower-risk cases.
const RISK_RANK: Record<RiskLevel, number> = { RED: 0, AMBER: 1, GREEN: 2 };

interface AssessmentDraft {
  risk_level: RiskLevel;
  escalation_required: boolean;
  escalation_reason: string;
  summary: string;
  recommended_action: string;
  selected_test_ids: number[];
}

type DashboardView = "cases" | "memory" | "evaluation";

export default function DashboardPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [diagnosticTests, setDiagnosticTests] = useState<DiagnosticTestCatalog[]>([]);
  const [doctorId, setDoctorId] = useState<number | null>(null);
  const [cases, setCases] = useState<ConsultationResponse[]>([]);
  const [showClosed, setShowClosed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busyCaseId, setBusyCaseId] = useState<number | null>(null);

  const [editingCaseId, setEditingCaseId] = useState<number | null>(null);
  const [draft, setDraft] = useState<AssessmentDraft | null>(null);

  const [modeSaving, setModeSaving] = useState(false);
  const [activeView, setActiveView] = useState<DashboardView>("cases");

  const [memoryCaseId, setMemoryCaseId] = useState<number | null>(null);
  const [memoryDraft, setMemoryDraft] = useState("");

  const [memories, setMemories] = useState<MemoryRead[]>([]);
  const [memoryBusyId, setMemoryBusyId] = useState<number | null>(null);
  const [newMemoryContent, setNewMemoryContent] = useState("");
  const [activeMemoryType, setActiveMemoryType] = useState<MemoryType>("preference");
  const [memoryCreating, setMemoryCreating] = useState(false);

  const [evalSummary, setEvalSummary] = useState<Awaited<ReturnType<typeof api.runEvaluations>> | null>(null);
  const [evalRunning, setEvalRunning] = useState(false);

  const selectedDoctor = doctors.find((d) => d.id === doctorId) ?? null;

  useEffect(() => {
    api
      .listDoctors()
      .then((list) => {
        setDoctors(list);
        if (list.length > 0) setDoctorId(list[0].id);
      })
      .catch((e) => setError(String(e)));
    api.listPatients().then(setPatients).catch((e) => setError(String(e)));
    api.listDiagnosticTests().then(setDiagnosticTests).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (doctorId === null) return;
    let stale = false;
    setCases([]);
    setMemories([]);
    api
      .listConsultations(doctorId)
      .then((items) => {
        if (!stale) setCases(items);
      })
      .catch((e) => {
        if (!stale) setError(String(e));
      });
    api
      .listMemories(doctorId)
      .then((items) => {
        if (!stale) setMemories(items);
      })
      .catch((e) => {
        if (!stale) setError(String(e));
      });
    return () => {
      stale = true;
    };
  }, [doctorId]);

  function refreshCases(id: number) {
    api
      .listConsultations(id)
      .then(setCases)
      .catch((e) => setError(String(e)));
  }

  function refreshMemories(id: number) {
    api
      .listMemories(id)
      .then(setMemories)
      .catch((e) => setError(String(e)));
  }

  function patientName(patientId: number): string {
    return patients.find((p) => p.id === patientId)?.name ?? `Patient #${patientId}`;
  }

  function isExistingPatient(patientId: number): boolean {
    const patient = patients.find((p) => p.id === patientId);
    return patient ? !patient.is_new_patient : false;
  }

  async function handleModeChange(mode: DeploymentMode) {
    if (!doctorId) return;
    setModeSaving(true);
    setError(null);
    try {
      const updated = await api.updateDoctorMode(doctorId, mode);
      setDoctors((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
    } catch (e) {
      setError(String(e));
    } finally {
      setModeSaving(false);
    }
  }

  async function handleCreateAppointment(caseItem: ConsultationResponse) {
    if (caseItem.available_slots.length === 0) return;
    setBusyCaseId(caseItem.id);
    setError(null);
    try {
      await api.createAppointment({
        doctor_id: caseItem.doctor_id,
        patient_id: caseItem.patient_id,
        slot_start: caseItem.available_slots[0].start,
        encounter_id: caseItem.id,
      });
      if (doctorId) refreshCases(doctorId);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusyCaseId(null);
    }
  }

  function startEditingAssessment(caseItem: ConsultationResponse) {
    setEditingCaseId(caseItem.id);
    setDraft({
      risk_level: caseItem.risk_level,
      escalation_required: caseItem.escalation_required,
      escalation_reason: caseItem.escalation_reason ?? "",
      summary: caseItem.summary,
      recommended_action: caseItem.assessment.recommended_action,
      selected_test_ids: getInitialSelectedTestIds(
        diagnosticTests,
        caseItem.assessment.recommended_tests,
        caseItem.test_decisions
      ),
    });
  }

  function cancelEditingAssessment() {
    setEditingCaseId(null);
    setDraft(null);
  }

  async function handleApprove(caseItem: ConsultationResponse) {
    setBusyCaseId(caseItem.id);
    setError(null);
    try {
      await api.approveConsultation(caseItem.id);
      if (doctorId) refreshCases(doctorId);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusyCaseId(null);
    }
  }

  async function handleSaveAssessment(caseId: number) {
    if (!draft) return;
    setBusyCaseId(caseId);
    setError(null);
    try {
      await api.modifyConsultation(caseId, {
        risk_level: draft.risk_level,
        escalation_required: draft.escalation_required,
        escalation_reason: draft.escalation_reason || null,
        summary: draft.summary,
        recommended_action: draft.recommended_action,
        selected_test_ids: draft.selected_test_ids,
      });
      cancelEditingAssessment();
      if (doctorId) refreshCases(doctorId);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusyCaseId(null);
    }
  }

  async function handleCloseCase(caseId: number) {
    setBusyCaseId(caseId);
    setError(null);
    try {
      await api.closeConsultation(caseId);
      if (doctorId) {
        refreshCases(doctorId);
        refreshMemories(doctorId);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setBusyCaseId(null);
    }
  }

  function startRecordingMemory(caseItem: ConsultationResponse) {
    setMemoryCaseId(caseItem.id);
    setMemoryDraft("");
  }

  async function handleSaveCaseMemory(caseItem: ConsultationResponse) {
    if (!doctorId || !memoryDraft.trim()) return;
    setBusyCaseId(caseItem.id);
    setError(null);
    try {
      await api.createMemory({ doctor_id: doctorId, content: memoryDraft, memory_type: "clinical_pattern" });
      setMemoryCaseId(null);
      setMemoryDraft("");
      refreshMemories(doctorId);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusyCaseId(null);
    }
  }

  async function handleApproveMemory(id: number) {
    setMemoryBusyId(id);
    setError(null);
    try {
      await api.approveMemory(id);
      if (doctorId) refreshMemories(doctorId);
    } catch (e) {
      setError(String(e));
    } finally {
      setMemoryBusyId(null);
    }
  }

  async function handleRejectMemory(id: number) {
    setMemoryBusyId(id);
    setError(null);
    try {
      await api.rejectMemory(id);
      if (doctorId) refreshMemories(doctorId);
    } catch (e) {
      setError(String(e));
    } finally {
      setMemoryBusyId(null);
    }
  }

  async function handleCreateMemory() {
    if (!doctorId || !newMemoryContent.trim()) return;
    setMemoryCreating(true);
    setError(null);
    try {
      await api.createMemory({ doctor_id: doctorId, content: newMemoryContent, memory_type: activeMemoryType });
      setNewMemoryContent("");
      refreshMemories(doctorId);
    } catch (e) {
      setError(String(e));
    } finally {
      setMemoryCreating(false);
    }
  }

  async function handleRunEvaluations() {
    setEvalRunning(true);
    setError(null);
    try {
      const summary = await api.runEvaluations();
      setEvalSummary(summary);
    } catch (e) {
      setError(String(e));
    } finally {
      setEvalRunning(false);
    }
  }

  const visibleCases = (showClosed ? cases : cases.filter((c) => c.closed_at === null))
    .slice()
    .sort((a, b) => RISK_RANK[a.risk_level] - RISK_RANK[b.risk_level]);
  const categoryMemories = memories.filter((memory) => memory.memory_type === activeMemoryType);
  const approvedMemories = categoryMemories.filter((memory) => memory.status === "APPROVED");
  const candidateMemories = categoryMemories.filter((memory) => memory.status === "CANDIDATE");
  const rejectedMemories = categoryMemories.filter((memory) => memory.status === "REJECTED");
  const openCaseCount = cases.filter((caseItem) => caseItem.closed_at === null).length;
  const pendingMemoryCount = memories.filter((memory) => memory.status === "CANDIDATE").length;

  function CaseCard({ caseItem }: { caseItem: ConsultationResponse }) {
    const history = cases.filter((c) => c.patient_id === caseItem.patient_id && c.id !== caseItem.id);
    const isShadow = caseItem.deployment_mode === "SHADOW";
    const isEditing = editingCaseId === caseItem.id;
    const isRecordingMemory = memoryCaseId === caseItem.id;
    const isClosed = caseItem.closed_at !== null;

    return (
      <div className="card">
        <div className="card-row">
          <div>
            <h3 style={{ marginBottom: "0.15rem" }}>{patientName(caseItem.patient_id)}</h3>
            <span className="muted">
              {caseItem.deployment_mode} - case #{caseItem.id}
            </span>
          </div>
          <RiskBadge risk={caseItem.risk_level} />
        </div>

        {caseItem.closed_at && (
          <p className="case-closed-label">Closed {new Date(caseItem.closed_at).toLocaleString()}</p>
        )}

        {caseItem.escalation_required && (
          <div className="error-banner">
            Escalation required{caseItem.escalation_reason ? `: ${caseItem.escalation_reason}` : "."}
          </div>
        )}

        {isShadow && !caseItem.doctor_reviewed && (
          <div className="shadow-mode-note">
            <strong>Shadow intake only</strong>
            <span>The twin collected and summarized patient information. Diagnosis and next actions are for doctor review.</span>
          </div>
        )}

        <p>
          <strong>Initial condition mentioned:</strong> {caseItem.conversation[0]?.content ?? "(none recorded)"}
        </p>
        <p>
          <strong>Symptoms collected by agent:</strong>{" "}
          {caseItem.assessment.symptoms.join(", ") || "none recorded yet"}
        </p>

        {!isEditing && (isShadow || caseItem.doctor_reviewed) && (
          <div className="stat-grid" style={{ marginBottom: "0.75rem" }}>
            <div className="stat-card">
              <div className="stat-label">
                {isShadow && !caseItem.doctor_reviewed ? "Patient intake summary" : "Doctor-reviewed assessment"}
              </div>
              <div style={{ marginTop: "0.35rem" }}>{caseItem.summary}</div>
              {(!isShadow || caseItem.doctor_reviewed) && (
                <div className="muted" style={{ marginTop: "0.25rem" }}>
                  Next action: {caseItem.assessment.recommended_action}
                </div>
              )}
            </div>
          </div>
        )}

        <DiagnosticTestsPanel
          mode={caseItem.deployment_mode}
          catalog={diagnosticTests}
          recommendations={caseItem.assessment.recommended_tests}
          decisions={caseItem.test_decisions}
          editing={isEditing}
          selectedTestIds={isEditing && draft ? draft.selected_test_ids : []}
          onSelectedTestIdsChange={(selected_test_ids) => {
            if (draft) setDraft({ ...draft, selected_test_ids });
          }}
          canEdit={!isClosed}
          onStartEditing={() => startEditingAssessment(caseItem)}
        />

        {!isEditing && !isClosed && (
          <div style={{ marginBottom: "0.75rem" }}>
            {!caseItem.doctor_reviewed && !isShadow && (
              <button className="small" onClick={() => handleApprove(caseItem)} disabled={busyCaseId === caseItem.id}>
                Approve
              </button>
            )}{" "}
            <button
              className="secondary small"
              onClick={() => startEditingAssessment(caseItem)}
              disabled={busyCaseId === caseItem.id}
            >
              {isShadow ? "Record doctor response" : "Modify"}
            </button>{" "}
            {!caseItem.appointment_id && caseItem.available_slots.length > 0 && (
              <button className="small" onClick={() => handleCreateAppointment(caseItem)} disabled={busyCaseId === caseItem.id}>
                {busyCaseId === caseItem.id ? "Booking..." : "Create appointment"}
              </button>
            )}{" "}
            {!isShadow && isExistingPatient(caseItem.patient_id) && !isRecordingMemory && (
              <button className="secondary small" onClick={() => startRecordingMemory(caseItem)}>
                Record as memory
              </button>
            )}
            {caseItem.doctor_reviewed && (
              <button className="small" onClick={() => handleCloseCase(caseItem.id)} disabled={busyCaseId === caseItem.id}>
                {busyCaseId === caseItem.id
                  ? "Closing..."
                  : isShadow
                  ? "Close and generate memory candidates"
                  : "Close case"}
              </button>
            )}
          </div>
        )}

        {isRecordingMemory && (
          <div className="field">
            <label htmlFor={`memory-${caseItem.id}`}>Record doctor feedback as a candidate memory</label>
            <textarea
              id={`memory-${caseItem.id}`}
              rows={2}
              value={memoryDraft}
              onChange={(e) => setMemoryDraft(e.target.value)}
              placeholder="For persistent cough, also ask about inhaler usage."
            />
            <div>
              <button className="small" onClick={() => handleSaveCaseMemory(caseItem)} disabled={busyCaseId === caseItem.id}>
                Save
              </button>{" "}
              <button className="secondary small" onClick={() => setMemoryCaseId(null)}>
                Cancel
              </button>
            </div>
          </div>
        )}

        {isEditing && draft && (
          <div className="field-group">
            <div className="field">
              <label htmlFor={`risk-${caseItem.id}`}>Risk level</label>
              <select
                id={`risk-${caseItem.id}`}
                value={draft.risk_level}
                onChange={(e) => setDraft({ ...draft, risk_level: e.target.value as RiskLevel })}
              >
                <option value="GREEN">GREEN</option>
                <option value="AMBER">AMBER</option>
                <option value="RED">RED</option>
              </select>
            </div>
            <div className="field field-checkbox">
              <input
                id={`escalation-${caseItem.id}`}
                type="checkbox"
                checked={draft.escalation_required}
                onChange={(e) => setDraft({ ...draft, escalation_required: e.target.checked })}
                style={{ width: "auto" }}
              />
              <label htmlFor={`escalation-${caseItem.id}`} style={{ margin: 0 }}>
                Escalation required
              </label>
            </div>
            <div className="field">
              <label htmlFor={`reason-${caseItem.id}`}>Escalation reason</label>
              <input
                id={`reason-${caseItem.id}`}
                type="text"
                value={draft.escalation_reason}
                onChange={(e) => setDraft({ ...draft, escalation_reason: e.target.value })}
              />
            </div>
            <div className="field">
              <label htmlFor={`summary-${caseItem.id}`}>{isShadow ? "Doctor assessment / response" : "Summary"}</label>
              <textarea
                id={`summary-${caseItem.id}`}
                rows={2}
                value={draft.summary}
                onChange={(e) => setDraft({ ...draft, summary: e.target.value })}
              />
            </div>
            <div className="field">
              <label htmlFor={`action-${caseItem.id}`}>{isShadow ? "Doctor's next action" : "Recommended action"}</label>
              <input
                id={`action-${caseItem.id}`}
                type="text"
                value={draft.recommended_action}
                onChange={(e) => setDraft({ ...draft, recommended_action: e.target.value })}
              />
            </div>
            <button onClick={() => handleSaveAssessment(caseItem.id)} disabled={busyCaseId === caseItem.id}>
              {busyCaseId === caseItem.id ? "Saving..." : isShadow ? "Save doctor response" : "Save"}
            </button>{" "}
            <button className="secondary" onClick={cancelEditingAssessment}>
              Cancel
            </button>
          </div>
        )}

        {history.length > 0 && (
          <details style={{ marginTop: "0.75rem" }}>
            <summary className="muted">History for this patient ({history.length})</summary>
            <div className="table-wrap" style={{ marginTop: "0.5rem" }}>
              <table>
                <thead>
                  <tr>
                    <th>Initial condition</th>
                    <th>Symptoms</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.id}>
                      <td>{h.conversation[0]?.content ?? "-"}</td>
                      <td>{h.assessment.symptoms.join(", ") || "-"}</td>
                      <td>
                        <RiskBadge risk={h.risk_level} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        )}
      </div>
    );
  }

  function MemoryTable({ items, showActions }: { items: MemoryRead[]; showActions: boolean }) {
    if (items.length === 0) return <p className="empty-state">None.</p>;
    return (
      <div className="memory-list">
        {items.map((memory) => (
          <article className="memory-item" key={memory.id}>
            <p>{memory.content}</p>
            <div className="memory-item-footer">
              <div className="memory-meta">
                <span>{memory.source.replaceAll("_", " ")}</span>
                <span>{Math.round(memory.confidence * 100)}% confidence</span>
              </div>
              {showActions && (
                <div className="memory-actions">
                  <button className="small" onClick={() => handleApproveMemory(memory.id)} disabled={memoryBusyId === memory.id}>
                    Approve
                  </button>
                  <button className="secondary small" onClick={() => handleRejectMemory(memory.id)} disabled={memoryBusyId === memory.id}>
                    Reject
                  </button>
                </div>
              )}
            </div>
          </article>
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Doctor Dashboard</h1>
        <p>Review patient cases, govern the twin&apos;s memory, and monitor evaluation quality.</p>
      </div>
      {error && <div className="error-banner">{error}</div>}

      <div className="card dashboard-settings">
        <div className="field">
          <label htmlFor="doctor">Doctor</label>
          <select id="doctor" value={doctorId ?? ""} onChange={(e) => setDoctorId(Number(e.target.value))}>
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.specialty})
              </option>
            ))}
          </select>
        </div>

        {selectedDoctor && (
          <div className="field">
            <label htmlFor="mode">Twin deployment mode</label>
            <select
              id="mode"
              value={selectedDoctor.default_deployment_mode}
              disabled={modeSaving}
              onChange={(e) => handleModeChange(e.target.value as DeploymentMode)}
            >
              {MODES.map((mode) => (
                <option key={mode} value={mode}>
                  {mode}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="dashboard-tabs" role="tablist" aria-label="Doctor workspace">
        <button
          type="button"
          role="tab"
          id="cases-tab"
          aria-selected={activeView === "cases"}
          aria-controls="cases-panel"
          className={`dashboard-tab${activeView === "cases" ? " active" : ""}`}
          onClick={() => setActiveView("cases")}
        >
          Patient cases <span>{openCaseCount}</span>
        </button>
        <button
          type="button"
          role="tab"
          id="memory-tab"
          aria-selected={activeView === "memory"}
          aria-controls="memory-panel"
          className={`dashboard-tab${activeView === "memory" ? " active" : ""}`}
          onClick={() => setActiveView("memory")}
        >
          Memory management <span>{pendingMemoryCount}</span>
        </button>
        <button
          type="button"
          role="tab"
          id="evaluation-tab"
          aria-selected={activeView === "evaluation"}
          aria-controls="evaluation-panel"
          className={`dashboard-tab${activeView === "evaluation" ? " active" : ""}`}
          onClick={() => setActiveView("evaluation")}
        >
          Evaluation
        </button>
      </div>

      {activeView === "cases" && (
        <section id="cases-panel" role="tabpanel" aria-labelledby="cases-tab">
          <div className="section-heading">
            <div>
              <h2>Patient cases</h2>
              <p className="muted">Review urgent cases first, then record the doctor&apos;s assessment and next action.</p>
            </div>
            <label className="muted section-control">
              <input type="checkbox" checked={showClosed} onChange={(e) => setShowClosed(e.target.checked)} />
              Show closed cases
            </label>
          </div>
          {visibleCases.length === 0 && <div className="card empty-state">No open cases right now.</div>}
          {visibleCases.map((caseItem) => (
            <Fragment key={caseItem.id}>
              <CaseCard caseItem={caseItem} />
            </Fragment>
          ))}
        </section>
      )}

      {activeView === "memory" && (
        <section id="memory-panel" role="tabpanel" aria-labelledby="memory-tab">
          <div className="section-heading">
            <div>
              <h2>Memory management</h2>
              <p className="muted">Approve only durable guidance that should shape future consultations.</p>
            </div>
          </div>

          <div className="memory-tabs" role="tablist" aria-label="Memory category">
            {MEMORY_TYPES.map((memoryType) => {
              const count = memories.filter((memory) => memory.memory_type === memoryType).length;
              const selected = activeMemoryType === memoryType;
              return (
                <button
                  key={memoryType}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  aria-controls="memory-category-panel"
                  className={`memory-tab${selected ? " active" : ""}`}
                  onClick={() => setActiveMemoryType(memoryType)}
                >
                  {MEMORY_TYPE_LABELS[memoryType]} <span>{count}</span>
                </button>
              );
            })}
          </div>

          <div id="memory-category-panel" role="tabpanel">
            <div className="card memory-section memory-section-priority">
              <h3>
                Pending review <span className="badge CANDIDATE">{candidateMemories.length}</span>
              </h3>
              <p className="muted">Candidates do not influence the twin until you approve them.</p>
              <MemoryTable items={candidateMemories} showActions />
            </div>

            <div className="memory-grid">
              <div className="card memory-section">
                <h3>
                  Approved <span className="badge APPROVED">{approvedMemories.length}</span>
                </h3>
                <p className="muted">Active guidance used by the Doctor Twin.</p>
                <MemoryTable items={approvedMemories} showActions={false} />
              </div>

              <div className="card memory-section">
                <h3>
                  Rejected <span className="badge REJECTED">{rejectedMemories.length}</span>
                </h3>
                <p className="muted">Retained for governance history only.</p>
                <MemoryTable items={rejectedMemories} showActions={false} />
              </div>
            </div>

            <div className="card memory-create">
              <h3>Add candidate memory</h3>
              <p className="muted">New feedback will be filed under {MEMORY_TYPE_LABELS[activeMemoryType]}.</p>
              <div className="field">
                <label htmlFor="memory-content">Doctor guidance</label>
                <textarea
                  id="memory-content"
                  rows={3}
                  value={newMemoryContent}
                  placeholder="For persistent cough, also ask about inhaler usage."
                  onChange={(e) => setNewMemoryContent(e.target.value)}
                />
              </div>
              <button onClick={handleCreateMemory} disabled={memoryCreating || !newMemoryContent.trim()}>
                {memoryCreating ? "Saving..." : "Save as candidate"}
              </button>
            </div>
          </div>
        </section>
      )}

      {activeView === "evaluation" && (
        <section id="evaluation-panel" role="tabpanel" aria-labelledby="evaluation-tab">
          <div className="card">
            <h2>Evaluation suite</h2>
            <p className="muted">
              Runs all synthetic cases (evals/cases.json) through this Doctor Twin and the safety engine.
              Requires a configured LLM key on the backend.
            </p>
            <button onClick={handleRunEvaluations} disabled={evalRunning}>
              {evalRunning ? "Running..." : "Run evaluations"}
            </button>
            {evalSummary && (
              <div className="stat-grid">
                <div className="stat-card">
                  <div className="stat-value">{evalSummary.cases_evaluated}</div>
                  <div className="stat-label">Cases evaluated</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{(evalSummary.red_flag_recall * 100).toFixed(0)}%</div>
                  <div className="stat-label">Red flag recall</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{(evalSummary.escalation_recall * 100).toFixed(0)}%</div>
                  <div className="stat-label">Escalation recall</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{(evalSummary.required_question_coverage * 100).toFixed(0)}%</div>
                  <div className="stat-label">Required question coverage</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{(evalSummary.structured_output_validity * 100).toFixed(0)}%</div>
                  <div className="stat-label">Structured output validity</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{(evalSummary.doctor_preference_alignment * 100).toFixed(0)}%</div>
                  <div className="stat-label">Doctor preference alignment</div>
                </div>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
