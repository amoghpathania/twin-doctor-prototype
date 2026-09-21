import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DiagnosticTestsPanel, getInitialSelectedTestIds } from "./DiagnosticTestsPanel";

const catalog = [
  { id: 1, code: "CBC", name: "Complete Blood Count", category: "Laboratory", description: null, is_active: true, autonomous_eligible: true, created_at: "", updated_at: "" },
  { id: 2, code: "CXR", name: "Chest X-Ray", category: "Imaging", description: null, is_active: true, autonomous_eligible: false, created_at: "", updated_at: "" },
];

describe("DiagnosticTestsPanel", () => {
  it("keeps twin recommendations visually and textually distinct", () => {
    render(
      <DiagnosticTestsPanel
        mode="COPILOT"
        catalog={catalog}
        recommendations={[{ catalog_code: "CXR", clinical_indication: "Persistent cough", confidence: 0.86, evidence_summary: "Accepted once in a similar case" }]}
        decisions={[]}
        editing={false}
        selectedTestIds={[]}
        onSelectedTestIdsChange={vi.fn()}
        canEdit
        onStartEditing={vi.fn()}
      />
    );

    expect(screen.getByRole("heading", { name: "Diagnostic tests" })).toBeInTheDocument();
    expect(screen.getByText("Recommended by twin")).toBeInTheDocument();
    expect(screen.getByText("Accepted once in a similar case")).toBeInTheDocument();
    expect(screen.getByText("86% confidence")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add or edit tests" })).toBeInTheDocument();
  });

  it("supports catalog selection during doctor review", () => {
    const onChange = vi.fn();
    render(
      <DiagnosticTestsPanel
        mode="SHADOW"
        catalog={catalog}
        recommendations={[]}
        decisions={[]}
        editing
        selectedTestIds={[]}
        onSelectedTestIdsChange={onChange}
        canEdit
        onStartEditing={vi.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText("Add a hospital test"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Add test" }));
    expect(onChange).toHaveBeenCalledWith([1]);
  });

  it("preselects Copilot recommendations until the doctor finalizes decisions", () => {
    const recommendations = [
      { catalog_code: "CBC", clinical_indication: "Baseline blood count", confidence: 0.82, evidence_summary: null },
      { catalog_code: "CXR", clinical_indication: "Persistent cough", confidence: 0.86, evidence_summary: null },
    ];

    expect(getInitialSelectedTestIds(catalog, recommendations, [])).toEqual([1, 2]);
    expect(
      getInitialSelectedTestIds(catalog, recommendations, [
        {
          id: 10,
          test_catalog_id: 2,
          catalog_code: "CXR",
          test_name: "Chest X-Ray",
          category: "Imaging",
          deployment_mode: "COPILOT",
          origin: "AGENT_RECOMMENDED",
          status: "REJECTED",
          decided_by: "DOCTOR",
          clinical_indication: "Persistent cough",
          model_confidence: 0.86,
          evidence_snapshot: {},
          decided_at: "",
        },
      ])
    ).toEqual([]);
  });
});