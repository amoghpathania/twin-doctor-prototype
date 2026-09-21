"use client";

import { useEffect, useId, useState } from "react";

import {
  DeploymentMode,
  DiagnosticTestCatalog,
  EncounterTestDecision,
  RecommendedDiagnosticTest,
} from "@/lib/api";

interface DiagnosticTestsPanelProps {
  mode: DeploymentMode;
  catalog: DiagnosticTestCatalog[];
  recommendations: RecommendedDiagnosticTest[];
  decisions: EncounterTestDecision[];
  editing: boolean;
  selectedTestIds: number[];
  onSelectedTestIdsChange: (ids: number[]) => void;
  canEdit: boolean;
  onStartEditing: () => void;
}

export function getInitialSelectedTestIds(
  catalog: DiagnosticTestCatalog[],
  recommendations: RecommendedDiagnosticTest[],
  decisions: EncounterTestDecision[]
): number[] {
  if (decisions.length > 0) {
    return decisions
      .filter((decision) => decision.status === "ORDERED")
      .map((decision) => decision.test_catalog_id);
  }

  return recommendations
    .map((recommendation) => catalog.find((item) => item.code === recommendation.catalog_code)?.id)
    .filter((id): id is number => id !== undefined);
}

function decisionLabel(decision: EncounterTestDecision): string {
  if (decision.status === "ORDERED" && decision.decided_by === "SYSTEM") return "Auto-ordered";
  if (decision.status === "ORDERED") return "Doctor selected";
  if (decision.status === "REJECTED") return "Not selected";
  return "Needs doctor review";
}

export function DiagnosticTestsPanel({
  mode,
  catalog,
  recommendations,
  decisions,
  editing,
  selectedTestIds,
  onSelectedTestIdsChange,
  canEdit,
  onStartEditing,
}: DiagnosticTestsPanelProps) {
  const available = catalog.filter((item) => !selectedTestIds.includes(item.id));
  const [testToAdd, setTestToAdd] = useState<number | "">(available[0]?.id ?? "");
  const selectId = useId();

  useEffect(() => {
    if (testToAdd !== "" && available.some((item) => item.id === testToAdd)) return;
    setTestToAdd(available[0]?.id ?? "");
  }, [available, testToAdd]);

  function addTest() {
    if (testToAdd === "" || selectedTestIds.includes(testToAdd)) return;
    onSelectedTestIdsChange([...selectedTestIds, testToAdd]);
    const next = available.find((item) => item.id !== testToAdd);
    setTestToAdd(next?.id ?? "");
  }

  return (
    <section className="diagnostic-tests" aria-labelledby="diagnostic-tests-heading">
      <div className="diagnostic-tests-heading">
        <div>
          <span className="section-kicker">Clinical investigation</span>
          <h3 id="diagnostic-tests-heading">Diagnostic tests</h3>
        </div>
        <span className="diagnostic-mode-label">{mode}</span>
      </div>

      {recommendations.length > 0 && decisions.length === 0 && (
        <div className="diagnostic-group">
          <strong>Recommended by twin</strong>
          <div className="diagnostic-test-list">
            {recommendations.map((recommendation) => {
              const item = catalog.find((candidate) => candidate.code === recommendation.catalog_code);
              return (
                <article className="diagnostic-test-row recommendation" key={recommendation.catalog_code}>
                  <div>
                    <strong>{item?.name ?? recommendation.catalog_code}</strong>
                    <span>{recommendation.clinical_indication}</span>
                    {recommendation.evidence_summary && <small>{recommendation.evidence_summary}</small>}
                  </div>
                  <span className="diagnostic-confidence">{Math.round(recommendation.confidence * 100)}% confidence</span>
                </article>
              );
            })}
          </div>
        </div>
      )}

      {decisions.length > 0 && (
        <div className="diagnostic-group">
          <strong>Recorded decisions</strong>
          <div className="diagnostic-test-list">
            {decisions.map((decision) => (
              <article className={`diagnostic-test-row ${decision.status.toLowerCase()}`} key={decision.id}>
                <div>
                  <strong>{decision.test_name}</strong>
                  <span>{decision.clinical_indication ?? decision.category}</span>
                  {typeof decision.evidence_snapshot.gate_reason === "string" && (
                    <small>Decision basis: {decision.evidence_snapshot.gate_reason.replaceAll("_", " ")}</small>
                  )}
                </div>
                <span className={`diagnostic-status ${decision.status.toLowerCase()}`}>{decisionLabel(decision)}</span>
              </article>
            ))}
          </div>
        </div>
      )}

      {editing && (
        <div className="diagnostic-editor">
          <label htmlFor={selectId}>Add a hospital test</label>
          <span className="field-hint">Select the tests clinically indicated for this case.</span>
          <div className="diagnostic-add-row">
            <select
              id={selectId}
              value={testToAdd}
              onChange={(event) => setTestToAdd(event.target.value ? Number(event.target.value) : "")}
            >
              <option value="">Select a test</option>
              {available.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.code} - {item.name}
                </option>
              ))}
            </select>
            <button type="button" className="secondary" onClick={addTest} disabled={testToAdd === ""}>
              Add test
            </button>
          </div>
          {selectedTestIds.length > 0 ? (
            <ul className="diagnostic-selected-list">
              {selectedTestIds.map((id) => {
                const item = catalog.find((candidate) => candidate.id === id);
                if (!item) return null;
                return (
                  <li key={id}>
                    <span><strong>{item.code}</strong> {item.name}</span>
                    <button
                      type="button"
                      className="secondary small"
                      aria-label={`Remove ${item.name}`}
                      onClick={() => onSelectedTestIdsChange(selectedTestIds.filter((selectedId) => selectedId !== id))}
                    >
                      Remove
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="muted diagnostic-empty">No tests selected.</p>
          )}
        </div>
      )}

      {canEdit && !editing && (
        <button type="button" className="secondary small diagnostic-edit-button" onClick={onStartEditing}>
          Add or edit tests
        </button>
      )}

      {!editing && recommendations.length === 0 && decisions.length === 0 && (
        <p className="muted diagnostic-empty">
          {mode === "SHADOW" ? "Awaiting the doctor's test selection." : "No diagnostic tests recorded."}
        </p>
      )}
    </section>
  );
}