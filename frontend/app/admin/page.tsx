"use client";

import { useEffect, useState } from "react";
import { AdminDataCounts, AdminDataSummary, api, DiagnosticTestCatalog, Doctor } from "@/lib/api";

const RESET_CONFIRMATION = "RESET ADDED DATA";

const DATA_LABELS: Record<keyof AdminDataCounts, string> = {
  encounters: "Cases / encounters",
  appointments: "Appointments",
  audit_events: "Audit events",
  evaluation_runs: "Evaluation runs",
  test_decisions: "Test decisions",
  memories: "Added memories",
  doctors: "Added doctors",
  patients: "Added patients",
};

export default function AdminPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [diagnosticTests, setDiagnosticTests] = useState<DiagnosticTestCatalog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [experience, setExperience] = useState("");
  const [communicationStyle, setCommunicationStyle] = useState("");
  const [clinicalPreferences, setClinicalPreferences] = useState("");
  const [escalationPreferences, setEscalationPreferences] = useState("");
  const [justCreated, setJustCreated] = useState<Doctor | null>(null);
  const [dataSummary, setDataSummary] = useState<AdminDataSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [showResetConfirmation, setShowResetConfirmation] = useState(false);
  const [resetConfirmation, setResetConfirmation] = useState("");
  const [resetting, setResetting] = useState(false);
  const [resetResult, setResetResult] = useState<AdminDataCounts | null>(null);
  const [testCode, setTestCode] = useState("");
  const [testName, setTestName] = useState("");
  const [testCategory, setTestCategory] = useState("Laboratory");
  const [testDescription, setTestDescription] = useState("");
  const [testAutonomousEligible, setTestAutonomousEligible] = useState(false);
  const [testSaving, setTestSaving] = useState(false);

  useEffect(() => {
    refreshDoctors();
    refreshDataSummary();
    refreshDiagnosticTests();
  }, []);

  function refreshDoctors() {
    api.listDoctors().then(setDoctors).catch((e) => setError(String(e)));
  }

  function refreshDataSummary() {
    setSummaryLoading(true);
    api
      .getAdminDataSummary()
      .then(setDataSummary)
      .catch((e) => setError(String(e)))
      .finally(() => setSummaryLoading(false));
  }

  function refreshDiagnosticTests() {
    api.listAdminDiagnosticTests().then(setDiagnosticTests).catch((e) => setError(String(e)));
  }

  async function handleCreateDiagnosticTest() {
    if (!testCode.trim() || !testName.trim() || !testCategory.trim()) return;
    setTestSaving(true);
    setError(null);
    try {
      await api.createDiagnosticTest({
        code: testCode,
        name: testName,
        category: testCategory,
        description: testDescription,
        autonomous_eligible: testAutonomousEligible,
      });
      setTestCode("");
      setTestName("");
      setTestDescription("");
      setTestAutonomousEligible(false);
      refreshDiagnosticTests();
    } catch (e) {
      setError(String(e));
    } finally {
      setTestSaving(false);
    }
  }

  async function updateDiagnosticTest(id: number, values: Parameters<typeof api.updateDiagnosticTest>[1]) {
    setTestSaving(true);
    setError(null);
    try {
      await api.updateDiagnosticTest(id, values);
      refreshDiagnosticTests();
    } catch (e) {
      setError(String(e));
    } finally {
      setTestSaving(false);
    }
  }

  async function handleCreate() {
    if (!name.trim() || !specialty.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const doctor = await api.createDoctor({
        name,
        specialty,
        experience,
        communication_style: communicationStyle,
        clinical_preferences: clinicalPreferences,
        escalation_preferences: escalationPreferences,
      });
      setJustCreated(doctor);
      setName("");
      setSpecialty("");
      setExperience("");
      setCommunicationStyle("");
      setClinicalPreferences("");
      setEscalationPreferences("");
      refreshDoctors();
    } catch (e) {
      setError(String(e));
    } finally {
      setCreating(false);
    }
  }

  async function handleResetData() {
    if (resetConfirmation !== RESET_CONFIRMATION) return;
    setResetting(true);
    setError(null);
    try {
      const result = await api.resetAdminData();
      setResetResult(result.deleted);
      setResetConfirmation("");
      setShowResetConfirmation(false);
      refreshDoctors();
      refreshDataSummary();
    } catch (e) {
      setError(String(e));
    } finally {
      setResetting(false);
    }
  }

  const totalResettable = dataSummary
    ? Object.values(dataSummary.resettable).reduce((total, count) => total + count, 0)
    : 0;

  return (
    <div>
      <div className="page-header">
        <h1>Admin</h1>
        <p>Manage doctor onboarding and maintain this prototype&apos;s synthetic data.</p>
      </div>
      {error && <div className="error-banner">{error}</div>}

      {justCreated && (
        <div className="card">
          <strong>{justCreated.name}</strong> was onboarded with deployment mode{" "}
          <strong>{justCreated.default_deployment_mode}</strong>.
        </div>
      )}

      {resetResult && (
        <div className="success-banner" role="status">
          Added data was reset successfully. {Object.values(resetResult).reduce((total, count) => total + count, 0)} records removed.
        </div>
      )}

      <section className="card admin-data-panel" aria-labelledby="data-maintenance-heading">
        <div className="card-row">
          <div>
            <span className="section-kicker">Database controls</span>
            <h2 id="data-maintenance-heading">Data maintenance</h2>
            <p className="muted">Clear activity added during testing without removing the default synthetic dataset.</p>
          </div>
          <button className="secondary small" onClick={refreshDataSummary} disabled={summaryLoading || resetting}>
            {summaryLoading ? "Refreshing..." : "Refresh counts"}
          </button>
        </div>

        {dataSummary && (
          <>
            <div className="admin-data-grid">
              {(Object.entries(dataSummary.resettable) as [keyof AdminDataCounts, number][]).map(([key, count]) => (
                <div className="admin-data-stat" key={key}>
                  <strong>{count}</strong>
                  <span>{DATA_LABELS[key]}</span>
                </div>
              ))}
            </div>

            <div className="protected-data-note">
              <strong>Always preserved</strong>
              <span>
                {dataSummary.protected.doctors} baseline doctors · {dataSummary.protected.patients} baseline patients · {dataSummary.protected.memories} baseline memories
              </span>
            </div>

            {!showResetConfirmation ? (
              <div className="danger-zone-row">
                <div>
                  <strong>Reset added data</strong>
                  <p>Deletes all cases, appointments, audits, evaluations, added profiles, and non-baseline memories.</p>
                </div>
                <button className="danger" onClick={() => setShowResetConfirmation(true)} disabled={totalResettable === 0}>
                  Reset {totalResettable} records
                </button>
              </div>
            ) : (
              <div className="reset-confirmation" role="alert">
                <strong>This cannot be undone</strong>
                <p>Type <code>{RESET_CONFIRMATION}</code> to confirm. Default synthetic records will remain available.</p>
                <div className="inline-field">
                  <input
                    type="text"
                    aria-label="Reset confirmation"
                    value={resetConfirmation}
                    onChange={(e) => setResetConfirmation(e.target.value)}
                    autoComplete="off"
                  />
                  <button className="danger" onClick={handleResetData} disabled={resetting || resetConfirmation !== RESET_CONFIRMATION}>
                    {resetting ? "Resetting..." : "Confirm reset"}
                  </button>
                  <button className="secondary" onClick={() => { setShowResetConfirmation(false); setResetConfirmation(""); }} disabled={resetting}>
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </section>

      <section className="card admin-catalog-panel" aria-labelledby="test-catalog-heading">
        <div className="card-row">
          <div>
            <span className="section-kicker">Hospital configuration</span>
            <h2 id="test-catalog-heading">Diagnostic test catalog</h2>
            <p className="muted">Maintain the approved tests doctors and the twin can select. Inactive tests remain in case history.</p>
          </div>
          <span className="catalog-count">{diagnosticTests.filter((item) => item.is_active).length} active</span>
        </div>

        <div className="catalog-create-grid">
          <div className="field">
            <label htmlFor="test-code">Code</label>
            <input id="test-code" type="text" value={testCode} onChange={(e) => setTestCode(e.target.value)} placeholder="TSH" />
          </div>
          <div className="field">
            <label htmlFor="test-name">Test name</label>
            <input id="test-name" type="text" value={testName} onChange={(e) => setTestName(e.target.value)} placeholder="Thyroid-stimulating hormone" />
          </div>
          <div className="field">
            <label htmlFor="test-category">Category</label>
            <select id="test-category" value={testCategory} onChange={(e) => setTestCategory(e.target.value)}>
              <option>Laboratory</option>
              <option>Imaging</option>
              <option>Cardiac</option>
              <option>Microbiology</option>
              <option>Other</option>
            </select>
          </div>
        </div>
        <div className="field">
          <label htmlFor="test-description">Description</label>
          <input id="test-description" type="text" value={testDescription} onChange={(e) => setTestDescription(e.target.value)} placeholder="Optional operational description" />
        </div>
        <label className="catalog-checkbox">
          <input type="checkbox" checked={testAutonomousEligible} onChange={(e) => setTestAutonomousEligible(e.target.checked)} />
          Eligible for evidence-gated autonomous ordering
        </label>
        <button onClick={handleCreateDiagnosticTest} disabled={testSaving || !testCode.trim() || !testName.trim() || !testCategory.trim()}>
          {testSaving ? "Saving..." : "Add diagnostic test"}
        </button>

        <div className="table-wrap catalog-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Test</th>
                <th>Category</th>
                <th>Availability</th>
                <th>Autonomous</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {diagnosticTests.map((item) => (
                <tr key={item.id}>
                  <td><strong>{item.code}</strong><span className="catalog-test-name">{item.name}</span></td>
                  <td>{item.category}</td>
                  <td><span className={`diagnostic-status ${item.is_active ? "ordered" : "rejected"}`}>{item.is_active ? "Active" : "Inactive"}</span></td>
                  <td>{item.autonomous_eligible ? "Eligible" : "Review only"}</td>
                  <td className="catalog-actions">
                    <button
                      className="secondary small"
                      disabled={testSaving}
                      onClick={() => updateDiagnosticTest(item.id, { autonomous_eligible: !item.autonomous_eligible })}
                    >
                      {item.autonomous_eligible ? "Require review" : "Allow autonomous"}
                    </button>
                    <button
                      className="secondary small"
                      disabled={testSaving}
                      onClick={() => updateDiagnosticTest(item.id, { is_active: !item.is_active })}
                    >
                      {item.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="card">
        <h2>Onboard a new doctor</h2>
        <div className="grid-2">
          <div className="field">
            <label htmlFor="name">Name</label>
            <input id="name" type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Dr. Jane Tan" />
          </div>
          <div className="field">
            <label htmlFor="specialty">Specialty</label>
            <input id="specialty" type="text" value={specialty} onChange={(e) => setSpecialty(e.target.value)} placeholder="General Medicine" />
          </div>
          <div className="field">
            <label htmlFor="experience">Experience</label>
            <input id="experience" type="text" value={experience} onChange={(e) => setExperience(e.target.value)} placeholder="8 years" />
          </div>
          <div className="field">
            <label htmlFor="communication-style">Communication style</label>
            <input
              id="communication-style"
              type="text"
              value={communicationStyle}
              onChange={(e) => setCommunicationStyle(e.target.value)}
              placeholder="Concise, empathetic"
            />
          </div>
        </div>
        <div className="field">
          <label htmlFor="clinical-preferences">Clinical preferences</label>
          <textarea
            id="clinical-preferences"
            rows={2}
            value={clinicalPreferences}
            onChange={(e) => setClinicalPreferences(e.target.value)}
            placeholder="Ask about symptom duration before assessing severity."
          />
        </div>
        <div className="field">
          <label htmlFor="escalation-preferences">Escalation preferences</label>
          <textarea
            id="escalation-preferences"
            rows={2}
            value={escalationPreferences}
            onChange={(e) => setEscalationPreferences(e.target.value)}
            placeholder="Escalate persistent or worsening symptoms."
          />
        </div>
        <button onClick={handleCreate} disabled={creating || !name.trim() || !specialty.trim()}>
          {creating ? "Onboarding..." : "Onboard doctor"}
        </button>
      </div>

      <div className="card">
        <h2>Existing doctors</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Specialty</th>
                <th>Twin mode</th>
              </tr>
            </thead>
            <tbody>
              {doctors.map((d) => (
                <tr key={d.id}>
                  <td>{d.name}</td>
                  <td>{d.specialty}</td>
                  <td>{d.default_deployment_mode}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
