const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8014";

export type RiskLevel = "GREEN" | "AMBER" | "RED";
export type DeploymentMode = "SHADOW" | "COPILOT" | "INTAKE" | "AUTONOMOUS";
export type MemoryStatus = "CANDIDATE" | "APPROVED" | "REJECTED";
export type MemoryType =
  | "preference"
  | "escalation_rule"
  | "communication_style"
  | "clinical_pattern"
  | "workflow_preference";

export interface Doctor {
  id: number;
  name: string;
  specialty: string;
  experience: string;
  communication_style: string;
  clinical_preferences: string;
  escalation_preferences: string;
  twin_version: string;
  default_deployment_mode: DeploymentMode;
}

export interface Patient {
  id: number;
  name: string;
  age: number;
  sex: string;
  chronic_conditions: string[];
  general_conditions: string[];
  medications: string[];
  allergies: string[];
  is_new_patient: boolean;
}

export interface ClinicalAssessment {
  symptoms: string[];
  missing_information: string[];
  risk_level: RiskLevel;
  escalation_required: boolean;
  escalation_reason: string | null;
  summary: string;
  recommended_action: string;
  confidence: number;
  fallback_used: boolean;
  recommended_tests: RecommendedDiagnosticTest[];
}

export interface RecommendedDiagnosticTest {
  catalog_code: string;
  clinical_indication: string;
  confidence: number;
  evidence_summary: string | null;
}

export interface DiagnosticTestCatalog {
  id: number;
  code: string;
  name: string;
  category: string;
  description: string | null;
  is_active: boolean;
  autonomous_eligible: boolean;
  created_at: string;
  updated_at: string;
}

export interface EncounterTestDecision {
  id: number;
  test_catalog_id: number;
  catalog_code: string;
  test_name: string;
  category: string;
  deployment_mode: DeploymentMode;
  origin: "DOCTOR_SELECTED" | "AGENT_RECOMMENDED";
  status: "PROPOSED" | "ORDERED" | "REJECTED";
  decided_by: "DOCTOR" | "SYSTEM";
  clinical_indication: string | null;
  model_confidence: number | null;
  evidence_snapshot: Record<string, unknown>;
  decided_at: string | null;
}

export interface DeploymentDecision {
  mode: DeploymentMode;
  allowed_actions: string[];
  autonomous_action_taken: boolean;
}

export interface AppointmentSlot {
  start: string;
  end: string;
}

export interface AppointmentRead {
  id: number;
  doctor_id: number;
  patient_id: number;
  encounter_id: number | null;
  slot_start: string;
  slot_end: string;
  status: string;
}

export interface ConversationTurn {
  role: string;
  content: string;
}

export interface ConsultationResponse {
  id: number;
  doctor_id: number;
  patient_id: number;
  deployment_mode: DeploymentMode;
  conversation: ConversationTurn[];
  assessment: ClinicalAssessment;
  risk_level: RiskLevel;
  escalation_required: boolean;
  escalation_reason: string | null;
  summary: string;
  appointment_id: number | null;
  deployment_decision: DeploymentDecision;
  available_slots: AppointmentSlot[];
  doctor_reviewed: boolean;
  doctor_review_action: "approve" | "modify" | null;
  closed_at: string | null;
  created_at: string;
  test_decisions: EncounterTestDecision[];
}

export interface MemoryRead {
  id: number;
  doctor_id: number;
  content: string;
  memory_type: MemoryType;
  source: string;
  confidence: number;
  status: MemoryStatus;
  created_at: string;
  approved_at: string | null;
}

export interface EvalCaseResult {
  case_id: string;
  expected_risk: RiskLevel;
  actual_risk: RiskLevel;
  expected_escalation: boolean;
  actual_escalation: boolean;
  structured_output_valid: boolean;
  red_flags_detected: string[];
  recommended_action: string;
  expected_action: string;
  required_questions: string[];
  missing_information: string[];
}

export interface EvaluationSummary {
  cases_evaluated: number;
  red_flag_recall: number;
  escalation_recall: number;
  required_question_coverage: number;
  structured_output_validity: number;
  doctor_preference_alignment: number;
  results: EvalCaseResult[];
  created_at: string;
}

export interface AdminDataCounts {
  encounters: number;
  appointments: number;
  audit_events: number;
  evaluation_runs: number;
  test_decisions: number;
  memories: number;
  doctors: number;
  patients: number;
}

export interface AdminDataSummary {
  resettable: AdminDataCounts;
  protected: Pick<AdminDataCounts, "doctors" | "patients" | "memories">;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${detail}`);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  listDoctors: () => request<Doctor[]>("/doctors"),
  getDoctor: (id: number) => request<Doctor>(`/doctors/${id}`),

  createDoctor: (body: {
    name: string;
    specialty: string;
    experience: string;
    communication_style: string;
    clinical_preferences: string;
    escalation_preferences: string;
  }) => request<Doctor>("/doctors", { method: "POST", body: JSON.stringify(body) }),

  updateDoctorMode: (doctorId: number, deployment_mode: DeploymentMode) =>
    request<Doctor>(`/doctors/${doctorId}/mode`, {
      method: "POST",
      body: JSON.stringify({ deployment_mode }),
    }),

  listPatients: () => request<Patient[]>("/patients"),
  getPatient: (id: number) => request<Patient>(`/patients/${id}`),

  createPatient: (body: { name: string; age: number; sex: string; chronic_conditions?: string[]; general_conditions?: string[] }) =>
    request<Patient>("/patients", { method: "POST", body: JSON.stringify(body) }),

  addPatientCondition: (patientId: number, category: "chronic" | "general", condition: string) =>
    request<Patient>(`/patients/${patientId}/conditions`, {
      method: "POST",
      body: JSON.stringify({ category, condition }),
    }),

  startConsultation: (body: { doctor_id: number; patient_id: number; message: string }) =>
    request<ConsultationResponse>("/consultations", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  addConsultationMessage: (consultationId: number, message: string) =>
    request<ConsultationResponse>(`/consultations/${consultationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  getConsultation: (id: number) => request<ConsultationResponse>(`/consultations/${id}`),

  listConsultations: (doctorId: number) =>
    request<ConsultationResponse[]>(`/consultations?doctor_id=${doctorId}`),

  listOpenPatientConsultations: (patientId: number) =>
    request<ConsultationResponse[]>(`/consultations/patient/${patientId}`),

  approveConsultation: (consultationId: number, selected_test_ids?: number[]) =>
    request<ConsultationResponse>(`/consultations/${consultationId}/review`, {
      method: "POST",
      body: JSON.stringify({ action: "approve", selected_test_ids }),
    }),

  modifyConsultation: (
    consultationId: number,
    overrides: {
      risk_level?: RiskLevel;
      escalation_required?: boolean;
      escalation_reason?: string | null;
      summary?: string;
      recommended_action?: string;
      selected_test_ids?: number[];
    }
  ) =>
    request<ConsultationResponse>(`/consultations/${consultationId}/review`, {
      method: "POST",
      body: JSON.stringify({ action: "modify", ...overrides }),
    }),

  closeConsultation: (consultationId: number) =>
    request<ConsultationResponse>(`/consultations/${consultationId}/close`, { method: "POST" }),

  listDiagnosticTests: () => request<DiagnosticTestCatalog[]>("/diagnostic-tests"),
  listAdminDiagnosticTests: () => request<DiagnosticTestCatalog[]>("/admin/diagnostic-tests"),
  createDiagnosticTest: (body: {
    code: string;
    name: string;
    category: string;
    description?: string;
    autonomous_eligible?: boolean;
  }) => request<DiagnosticTestCatalog>("/admin/diagnostic-tests", { method: "POST", body: JSON.stringify(body) }),
  updateDiagnosticTest: (
    id: number,
    body: Partial<Pick<DiagnosticTestCatalog, "name" | "category" | "description" | "is_active" | "autonomous_eligible">>
  ) => request<DiagnosticTestCatalog>(`/admin/diagnostic-tests/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  listMemories: (doctorId: number) => request<MemoryRead[]>(`/memories/${doctorId}`),

  createMemory: (body: { doctor_id: number; content: string; memory_type: MemoryType; source?: string }) =>
    request<MemoryRead>("/memories", { method: "POST", body: JSON.stringify(body) }),

  approveMemory: (id: number) => request<MemoryRead>(`/memories/${id}/approve`, { method: "POST" }),
  rejectMemory: (id: number) => request<MemoryRead>(`/memories/${id}/reject`, { method: "POST" }),

  createAppointment: (body: { doctor_id: number; patient_id: number; slot_start: string; encounter_id?: number | null }) =>
    request<AppointmentRead>("/appointments", { method: "POST", body: JSON.stringify(body) }),

  runEvaluations: () => request<EvaluationSummary>("/evaluations/run", { method: "POST" }),
  getEvaluationResults: () => request<EvaluationSummary>("/evaluations/results"),

  getAdminDataSummary: () => request<AdminDataSummary>("/admin/data-summary"),
  resetAdminData: () =>
    request<{ deleted: AdminDataCounts }>("/admin/reset-data", {
      method: "POST",
      body: JSON.stringify({ confirmation: "RESET ADDED DATA" }),
    }),
};
