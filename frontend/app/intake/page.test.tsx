import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import IntakePage from "./page";

const apiMocks = vi.hoisted(() => ({
  listDoctors: vi.fn(),
  listPatients: vi.fn(),
  listOpenPatientConsultations: vi.fn(),
  startConsultation: vi.fn(),
  addConsultationMessage: vi.fn(),
}));

vi.mock("@/lib/api", () => ({ api: apiMocks }));

describe("IntakePage", () => {
  it("shows the patient message and twin placeholder while awaiting the LLM", async () => {
    apiMocks.listDoctors.mockResolvedValue([
      {
        id: 1,
        name: "Dr. Sarah Lim",
        specialty: "General Medicine",
        default_deployment_mode: "INTAKE",
      },
    ]);
    apiMocks.listPatients.mockResolvedValue([
      {
        id: 2,
        name: "Tan Wei Ming",
        age: 45,
        sex: "male",
        chronic_conditions: [],
        general_conditions: [],
        medications: [],
        allergies: [],
      },
    ]);
    apiMocks.listOpenPatientConsultations.mockResolvedValue([]);
    apiMocks.startConsultation.mockReturnValue(new Promise(() => {}));

    render(<IntakePage />);

    fireEvent.change(await screen.findByLabelText("Patient profile"), { target: { value: "2" } });
    await waitFor(() => expect(screen.getByLabelText("Doctor's digital twin")).toHaveValue("1"));
    fireEvent.change(screen.getByLabelText("Describe your symptoms"), {
      target: { value: "I have had a cough for three days." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start consultation" }));

    expect(screen.getByText("I have had a cough for three days.")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Doctor's twin is reviewing your message");
    expect(screen.getByLabelText("Describe your symptoms")).toHaveValue("");
  });
});