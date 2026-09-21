const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Doctor Digital Twin";
pptx.company = "SaxeCap FDE Take-Home";
pptx.subject = "AI transformation concept and working prototype";
pptx.title = "Doctor Digital Twin: Earning Clinical Trust Before Scaling Autonomy";
pptx.lang = "en-SG";
pptx.theme = { headFontFace: "Aptos Display", bodyFontFace: "Aptos", lang: "en-SG" };

const C = {
  ink: "132A2A", teal: "157A6E", mint: "D9EDE8", sea: "87C8BE",
  coral: "E46F51", amber: "E6A23C", green: "2B8A64", red: "C9463D",
  paper: "F5F2EB", white: "FFFFFF", muted: "657674", line: "CFD7D3",
  dark: "173C3D", pale: "E9EEEB", blue: "4776A8",
};
const S = pptx.ShapeType;

pptx.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.paper },
  objects: [
    { rect: { x: 0, y: 0, w: 0.16, h: 7.5, line: { transparency: 100 }, fill: { color: C.teal } } },
    { text: { text: "DOCTOR DIGITAL TWIN", options: { x: 0.55, y: 0.28, w: 3, h: 0.18, fontSize: 8.5, bold: true, color: C.muted, charSpacing: 1.5, margin: 0 } } },
    { text: { text: "SAXECAP FDE TAKE-HOME", options: { x: 10.2, y: 0.28, w: 2.5, h: 0.18, fontSize: 8.5, color: C.muted, align: "right", margin: 0 } } },
    { line: { x: 0.55, y: 7.12, w: 12.15, h: 0, line: { color: C.line, width: 0.8 } } },
  ],
  slideNumber: { x: 12.35, y: 7.18, w: 0.35, h: 0.16, fontSize: 8, color: C.muted, align: "right", margin: 0 },
});

function title(slide, text, kicker) {
  slide.addText(kicker.toUpperCase(), { x: 0.62, y: 0.68, w: 4.6, h: 0.22, fontSize: 10, bold: true, color: C.teal, charSpacing: 1.5, margin: 0 });
  slide.addText(text, { x: 0.6, y: 1.0, w: 12, h: 0.72, fontSize: 25, bold: true, color: C.ink, margin: 0, breakLine: false });
}
function footer(slide, text) {
  slide.addText(text, { x: 0.62, y: 6.79, w: 11.2, h: 0.18, fontSize: 8.5, color: C.muted, italic: true, margin: 0 });
}
function pill(slide, text, x, y, w, fill = C.mint, color = C.teal) {
  slide.addShape(S.roundRect, { x, y, w, h: 0.34, rectRadius: 0.04, line: { transparency: 100 }, fill: { color: fill } });
  slide.addText(text, { x: x + 0.07, y: y + 0.09, w: w - 0.14, h: 0.12, fontSize: 8.5, bold: true, color, align: "center", margin: 0 });
}
function card(slide, x, y, w, h, heading, body, accent = C.teal, number = "") {
  slide.addShape(S.roundRect, { x, y, w, h, rectRadius: 0.04, line: { color: C.line, width: 0.8 }, fill: { color: C.white } });
  slide.addShape(S.rect, { x, y, w: 0.08, h, line: { transparency: 100 }, fill: { color: accent } });
  if (number) slide.addText(number, { x: x + 0.24, y: y + 0.2, w: 0.42, h: 0.3, fontSize: 17, bold: true, color: accent, margin: 0 });
  slide.addText(heading, { x: x + (number ? 0.72 : 0.28), y: y + 0.2, w: w - (number ? 1.0 : 0.52), h: 0.34, fontSize: 14, bold: true, color: C.ink, margin: 0 });
  slide.addText(body, { x: x + 0.28, y: y + 0.72, w: w - 0.52, h: h - 0.92, fontSize: 10.3, color: C.muted, margin: 0, breakLine: false, paraSpaceAfterPt: 7 });
}
function arrow(slide, x, y, w, color = C.teal) {
  slide.addShape(S.line, { x, y, w, h: 0, line: { color, width: 2, endArrowType: "triangle" } });
}
function notes(slide, text) { slide.addNotes(text); }
function journeyStep(slide, number, heading, body, x, accent) {
  slide.addShape(S.ellipse, { x, y: 2.02, w: 0.54, h: 0.54, line: { color: accent, width: 1.3 }, fill: { color: C.white } });
  slide.addText(String(number), { x, y: 2.19, w: 0.54, h: 0.14, fontSize: 9.5, bold: true, color: accent, align: "center", margin: 0 });
  slide.addText(heading, { x: x - 0.3, y: 2.82, w: 1.14, h: 0.28, fontSize: 11.5, bold: true, color: C.ink, align: "center", margin: 0 });
  slide.addText(body, { x: x - 0.46, y: 3.25, w: 1.46, h: 0.86, fontSize: 9.2, color: C.muted, align: "center", margin: 0, breakLine: false });
}

// 1 — Cover
{
  const slide = pptx.addSlide();
  slide.background = { color: C.paper };
  slide.addShape(S.rect, { x: 9.45, y: 0, w: 3.88, h: 7.5, line: { transparency: 100 }, fill: { color: C.dark } });
  slide.addText("DOCTOR DIGITAL TWIN", { x: 0.75, y: 0.7, w: 4.3, h: 0.28, fontSize: 11, bold: true, color: C.teal, charSpacing: 2.2, margin: 0 });
  slide.addText("Earning clinical trust\nbefore scaling autonomy", { x: 0.75, y: 1.35, w: 7.95, h: 2.2, fontSize: 30, bold: true, color: C.ink, margin: 0, breakLine: false });
  slide.addText("A working prototype and AI transformation thesis for clinical workflows", { x: 0.78, y: 3.95, w: 7.15, h: 0.64, fontSize: 17, color: "415655", margin: 0 });
  [["OBSERVE", "01", C.sea], ["ASSIST", "02", C.white], ["EARN TRUST", "03", "F1C15D"]].forEach(([label, n, color], i) => {
    const y = 1.3 + i * 1.25;
    slide.addText(label, { x: 10.08, y, w: 2.2, h: 0.5, fontSize: 21, bold: true, color, margin: 0 });
    slide.addText(n, { x: 12.25, y, w: 0.4, h: 0.25, fontSize: 10, color, align: "right", margin: 0 });
    if (i < 2) slide.addShape(S.line, { x: 10.08, y: y + 0.68, w: 2.55, h: 0, line: { color: "527778" } });
  });
  slide.addText("FDE take-home | September 2026", { x: 0.78, y: 6.75, w: 4.4, h: 0.22, fontSize: 10, color: C.muted, margin: 0 });
  notes(slide, "Lead with the operating thesis, not the feature list. This is a working prototype used to test how clinical AI can earn trust progressively. It is not a claim of clinical validation, regulatory compliance or production readiness.");
}

// 2 — Business problem
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "The bottleneck is not intelligence. It is trusted workflow adoption.", "Business perspective");
  card(slide, 0.65, 2.0, 3.7, 3.55, "Today: fragmented work", "Repeated symptom collection\nContext rebuilt at review time\nManual test selection and documentation\nGeneric AI that does not reflect how a doctor works", C.coral, "01");
  card(slide, 4.8, 2.0, 3.7, 3.55, "Constraint: clinical trust", "A useful assistant must know when to stop\nDoctors need visibility and correction rights\nSafety cannot depend on one model response\nPractice differs by doctor and specialty", C.amber, "02");
  card(slide, 8.95, 2.0, 3.7, 3.55, "Opportunity: governed learning", "Structure cases before review\nLearn from accepted and rejected decisions\nTurn reviewed behavior into reusable capability\nScale one platform without flattening practice", C.teal, "03");
  slide.addText("Business hypothesis", { x: 0.68, y: 5.93, w: 1.55, h: 0.23, fontSize: 11, bold: true, color: C.teal, margin: 0 });
  slide.addText("Reduce repetitive work while increasing the evidence available to govern each next level of assistance.", { x: 2.25, y: 5.88, w: 9.65, h: 0.4, fontSize: 15, bold: true, color: C.ink, margin: 0 });
  footer(slide, "No ROI is assumed: Shadow mode establishes the operational baseline before value is claimed.");
  notes(slide, "For a PE transformation audience, the platform thesis is repeatability across provider groups. Doctor-specific configuration preserves local practice. Avoid invented savings; the pilot measures baseline and delta.");
}

// 3 — Singapore guidance
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Singapore guidance points to a lifecycle, not a launch checklist.", "Responsible AI context");
  const rows = [
    ["Human agency", "Appropriate human involvement and clear accountability", C.teal],
    ["Clinical safety", "Risk-based controls, validation and escalation", C.red],
    ["Transparency", "Explainable decisions and understandable communication", C.amber],
    ["Data governance", "Purpose, quality, access, privacy and traceability", C.blue],
    ["Lifecycle control", "Monitoring, robustness, change management and review", C.green],
  ];
  rows.forEach(([heading, body, color], i) => {
    const y = 1.82 + i * 0.86;
    slide.addShape(S.ellipse, { x: 0.78, y: y + 0.02, w: 0.36, h: 0.36, line: { color, width: 1.5 }, fill: { color: C.paper } });
    slide.addText(String(i + 1), { x: 0.78, y: y + 0.11, w: 0.36, h: 0.12, fontSize: 9, bold: true, color, align: "center", margin: 0 });
    slide.addText(heading, { x: 1.36, y, w: 2.0, h: 0.25, fontSize: 13, bold: true, color: C.ink, margin: 0 });
    slide.addText(body, { x: 3.4, y, w: 4.4, h: 0.38, fontSize: 10.5, color: C.muted, margin: 0 });
  });
  slide.addShape(S.roundRect, { x: 8.35, y: 1.75, w: 4.2, h: 4.35, rectRadius: 0.04, line: { transparency: 100 }, fill: { color: C.dark } });
  slide.addText("SOURCE HIERARCHY", { x: 8.75, y: 2.1, w: 2.8, h: 0.22, fontSize: 9.5, bold: true, color: C.sea, charSpacing: 1.5, margin: 0 });
  slide.addText("Healthcare-specific", { x: 8.75, y: 2.62, w: 2.7, h: 0.27, fontSize: 14, bold: true, color: C.white, margin: 0 });
  slide.addText("AIHGle (2021) as historical sector context; current HSA software medical-device lifecycle and SaMD-CDSS classification guidance where applicable.", { x: 8.75, y: 2.98, w: 3.35, h: 1.02, fontSize: 10.5, color: "D5E4E1", margin: 0 });
  slide.addText("Cross-sector governance", { x: 8.75, y: 4.28, w: 2.7, h: 0.27, fontSize: 14, bold: true, color: C.white, margin: 0 });
  slide.addText("PDPC Model AI Governance Framework: human-centric; explainable, transparent and fair.", { x: 8.75, y: 4.64, w: 3.35, h: 0.72, fontSize: 10.5, color: "D5E4E1", margin: 0 });
  pill(slide, "DESIGN ALIGNMENT, NOT COMPLIANCE", 8.75, 5.53, 3.15, "35595A", "F1C15D");
  footer(slide, "Sources: PDPC Model AI Governance Framework (2nd ed., 2020); HSA GL-04-R4 (Dec 2025); HSA GL-07-R2 (Jul 2025).");
  notes(slide, "Do not present these documents as certification. The architecture aligns to common governance expectations; intended-use classification and regulatory applicability remain formal production work. AI Verify is not proof for this system because PDPC states it cannot test GenAI or LLMs.");
}

// 4 — Controls traceability
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "The prototype turns principles into controls - and exposes what is still missing.", "Governance traceability");
  const xs = [0.66, 3.12, 6.14, 9.55], ws = [2.3, 2.84, 3.23, 3.05];
  ["Principle", "Product control", "Prototype evidence", "Production gap"].forEach((t, i) => {
    slide.addShape(S.rect, { x: xs[i], y: 1.72, w: ws[i], h: 0.5, line: { transparency: 100 }, fill: { color: C.dark } });
    slide.addText(t, { x: xs[i] + 0.14, y: 1.87, w: ws[i] - 0.28, h: 0.16, fontSize: 10, bold: true, color: C.white, margin: 0 });
  });
  const rows = [
    ["Human oversight", "Approve / modify; bounded modes", "Doctor review + audit events", "RBAC and governance board"],
    ["Clinical safety", "Deterministic override; fail-safe", "RED forced; failures become AMBER", "Clinical validation + hazard analysis"],
    ["Data governance", "Candidate approval; approved-only use", "Memory status and provenance", "Consent, retention, encryption"],
    ["Monitoring", "Evaluation suite; audit trail", "32 synthetic cases + metrics", "Drift, incidents, external validation"],
  ];
  rows.forEach((row, r) => row.forEach((text, c) => {
    const y = 2.25 + r * 0.93;
    slide.addShape(S.rect, { x: xs[c], y, w: ws[c], h: 0.86, line: { color: C.line, width: 0.7 }, fill: { color: r % 2 ? "EDF1EE" : C.white } });
    slide.addText(text, { x: xs[c] + 0.14, y: y + 0.16, w: ws[c] - 0.28, h: 0.48, fontSize: c === 0 ? 10.8 : 9.6, bold: c === 0, color: c === 3 ? "8A4A38" : C.ink, margin: 0, breakLine: false, valign: "mid" });
  }));
  pill(slide, "IMPLEMENTED", 0.72, 6.22, 1.5);
  pill(slide, "SYNTHETICALLY TESTED", 2.4, 6.22, 2.25, "E8E2CE", "745D1A");
  pill(slide, "PRODUCTION WORK", 4.83, 6.22, 1.85, "F3DDD6", "934530");
  slide.addText("Every claim uses one of these labels.", { x: 7.0, y: 6.27, w: 4.6, h: 0.2, fontSize: 10, color: C.muted, italic: true, margin: 0 });
  footer(slide, "Architecture alignment reduces risk; it does not replace clinical, privacy, security or regulatory review.");
  notes(slide, "Walk one row end to end. The FDE judgment is visible in exposing both evidence and gaps. Existing controls are meaningful, but identity, privacy engineering, monitoring and clinical validation are prerequisites for real deployment.");
}

// 5 — Workflow
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "One workflow connects patient context, doctor judgment and governed learning.", "Working product");
  const steps = [["P", "Patient", "Symptoms + one\nquestion at a time"], ["DT", "Doctor Twin", "Structured case +\nproposed next step"], ["!", "Safety + policy", "Override risk +\nbound action"], ["DR", "Doctor", "Approve, change\nor reject"], ["M", "Learning", "Promote only\nreviewed evidence"]];
  steps.forEach(([icon, heading, body], i) => {
    const x = 0.68 + i * 2.5;
    const accent = i === 2 ? C.red : C.teal;
    slide.addShape(S.ellipse, { x: x + 0.58, y: 2.0, w: 0.82, h: 0.82, line: { color: accent, width: 1.7 }, fill: { color: i === 2 ? "F7E3DF" : C.mint } });
    slide.addText(icon, { x: x + 0.58, y: 2.27, w: 0.82, h: 0.2, fontSize: icon.length > 1 ? 10 : 15, bold: true, color: accent, align: "center", margin: 0 });
    slide.addText(heading, { x, y: 3.08, w: 1.98, h: 0.3, fontSize: 13, bold: true, color: C.ink, align: "center", margin: 0 });
    slide.addText(body, { x, y: 3.52, w: 1.98, h: 0.7, fontSize: 9.8, color: C.muted, align: "center", margin: 0 });
    if (i < 4) arrow(slide, x + 1.88, 2.41, 0.66, C.sea);
  });
  slide.addShape(S.roundRect, { x: 1.08, y: 4.85, w: 11.15, h: 1.05, rectRadius: 0.04, line: { color: C.line }, fill: { color: C.white } });
  [["PATIENT INTAKE", "conversation", 2.1], ["DOCTOR DASHBOARD", "review + memory", 5.25], ["ADMIN + EVALUATION", "modes + catalog + metrics", 8.55]].forEach(([h, b, x]) => {
    slide.addText(h, { x, y: 5.15, w: 2.2, h: 0.22, fontSize: 10.5, bold: true, color: C.ink, align: "center", margin: 0 });
    slide.addText(b, { x, y: 5.48, w: 2.2, h: 0.18, fontSize: 9, color: C.muted, align: "center", margin: 0 });
  });
  footer(slide, "Implemented with synthetic patients and doctors; real clinical integrations are mocked.");
  notes(slide, "Learning occurs after doctor review, not directly from patient input or model output. The same system serves patient, doctor and administrator workflows.");
}

// 6 — Learning loop
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "The system learns two different things - and governs them differently.", "Doctor-specific learning");
  slide.addShape(S.roundRect, { x: 0.7, y: 1.75, w: 5.55, h: 4.55, rectRadius: 0.04, line: { color: C.line }, fill: { color: C.white } });
  slide.addText("1  EPISODIC MEMORY", { x: 1.05, y: 2.12, w: 2.45, h: 0.28, fontSize: 14, bold: true, color: C.teal, margin: 0 });
  slide.addText("What this doctor prefers", { x: 1.05, y: 2.58, w: 2.75, h: 0.28, fontSize: 17, bold: true, color: C.ink, margin: 0 });
  slide.addText("Communication style\nEscalation rules\nClinical patterns\nWorkflow preferences", { x: 1.05, y: 3.1, w: 2.25, h: 1.48, fontSize: 11, color: C.muted, margin: 0, paraSpaceAfterPt: 7 });
  [["EXTRACT", 3.0], ["CANDIDATE", 3.72], ["DOCTOR REVIEW", 4.44], ["APPROVED", 5.16]].forEach(([label, y], i) => {
    slide.addShape(S.roundRect, { x: 3.75, y, w: 1.72, h: 0.42, rectRadius: 0.04, line: { color: i === 3 ? C.green : C.line }, fill: { color: i === 3 ? "DCEFE5" : C.pale } });
    slide.addText(label, { x: 3.86, y: y + 0.13, w: 1.5, h: 0.13, fontSize: 8.5, bold: true, color: i === 3 ? C.green : C.ink, align: "center", margin: 0 });
    if (i < 3) slide.addShape(S.line, { x: 4.61, y: y + 0.43, w: 0, h: 0.29, line: { color: C.sea, width: 1.5, endArrowType: "triangle" } });
  });
  slide.addShape(S.roundRect, { x: 6.62, y: 1.75, w: 5.95, h: 4.55, rectRadius: 0.04, line: { transparency: 100 }, fill: { color: C.dark } });
  slide.addText("2  TEST-DECISION EVIDENCE", { x: 7.0, y: 2.12, w: 3.2, h: 0.28, fontSize: 14, bold: true, color: C.sea, margin: 0 });
  slide.addText("How this doctor acts in context", { x: 7.0, y: 2.58, w: 3.75, h: 0.28, fontSize: 17, bold: true, color: C.white, margin: 0 });
  pill(slide, "SHADOW: selected", 7.0, 3.2, 2.05, "35595A", "D5F1EC");
  pill(slide, "COPILOT: accepted", 7.0, 3.82, 2.05, "35595A", "D5F1EC");
  pill(slide, "COPILOT: rejected", 9.35, 3.2, 2.12, "613F37", "FFD9CF");
  pill(slide, "COPILOT: corrected", 9.35, 3.82, 2.12, "4D4930", "FFE9A8");
  slide.addText("Only finalized Shadow/Copilot decisions train future recommendations. Autonomous decisions never train themselves.", { x: 7.0, y: 4.7, w: 4.55, h: 0.82, fontSize: 11, color: "DDE8E5", bold: true, margin: 0 });
  slide.addText("Doctor benefit: learned assumptions remain visible and correctable.", { x: 7.0, y: 5.68, w: 4.6, h: 0.25, fontSize: 10, color: "F1C15D", margin: 0 });
  footer(slide, "Personalization is implemented; real-world improvement and confidence effects remain pilot hypotheses.");
  notes(slide, "Memory is extracted at closure but remains a candidate until approval. Test learning uses explicit doctor actions. The no-self-training invariant prevents autonomous decisions from manufacturing their own evidence.");
}

// 7 — Data management
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Shared foundation. Patient-bound context. Doctor-private learning.", "Data management");

  slide.addShape(S.roundRect, { x: 0.68, y: 1.78, w: 3.72, h: 4.45, rectRadius: 0.04, line: { color: C.teal, width: 1.2 }, fill: { color: C.white } });
  slide.addText("SHARED ACROSS DOCTORS", { x: 1.0, y: 2.12, w: 2.9, h: 0.25, fontSize: 11.5, bold: true, color: C.teal, charSpacing: 1.0, margin: 0 });
  slide.addText("Organization-governed reference layer", { x: 1.0, y: 2.55, w: 2.9, h: 0.28, fontSize: 15, bold: true, color: C.ink, margin: 0 });
  slide.addText("Diagnostic-test catalog\nSafety rules and escalation logic\nDeployment-policy definitions\nClinical output schemas and base prompts\nEvaluation cases and aggregate quality metrics", { x: 1.0, y: 3.08, w: 2.9, h: 2.1, fontSize: 10.5, color: C.muted, margin: 0, paraSpaceAfterPt: 7 });
  pill(slide, "CONSISTENT CONTROL PLANE", 1.0, 5.56, 2.35, C.mint, C.teal);

  slide.addShape(S.roundRect, { x: 4.8, y: 1.78, w: 3.72, h: 4.45, rectRadius: 0.04, line: { color: C.blue, width: 1.2 }, fill: { color: C.white } });
  slide.addText("PATIENT-SPECIFIC", { x: 5.12, y: 2.12, w: 2.9, h: 0.25, fontSize: 11.5, bold: true, color: C.blue, charSpacing: 1.0, margin: 0 });
  slide.addText("Available only for an authorized care relationship", { x: 5.12, y: 2.55, w: 2.9, h: 0.52, fontSize: 15, bold: true, color: C.ink, margin: 0 });
  slide.addText("Patient profile, conditions, medications and allergies\nEncounter conversation and assessment\nPrior visit summaries\nAppointments and encounter-linked audit history", { x: 5.12, y: 3.28, w: 2.9, h: 1.8, fontSize: 10.5, color: C.muted, margin: 0, paraSpaceAfterPt: 7 });
  pill(slide, "CARE-CONTEXT BOUNDARY", 5.12, 5.56, 2.35, "E4EBF5", C.blue);

  slide.addShape(S.roundRect, { x: 8.92, y: 1.78, w: 3.72, h: 4.45, rectRadius: 0.04, line: { color: C.amber, width: 1.2 }, fill: { color: C.dark } });
  slide.addText("DOCTOR-SPECIFIC", { x: 9.24, y: 2.12, w: 2.9, h: 0.25, fontSize: 11.5, bold: true, color: "F1C15D", charSpacing: 1.0, margin: 0 });
  slide.addText("Never pooled across doctors in the prototype", { x: 9.24, y: 2.55, w: 2.9, h: 0.52, fontSize: 15, bold: true, color: C.white, margin: 0 });
  slide.addText("Doctor profile and default mode\nApproved memories and preferences\nShadow selections and Copilot labels\nDoctor-specific test evidence and acceptance history\nDoctor case queue and scheduling", { x: 9.24, y: 3.28, w: 2.9, h: 2.0, fontSize: 10.5, color: "DDE8E5", margin: 0, paraSpaceAfterPt: 7 });
  pill(slide, "ISOLATED BY doctor_id", 9.24, 5.56, 2.35, "4D4930", "FFE9A8");

  footer(slide, "Prototype limitation: authentication, RBAC, consent and tenancy are not implemented; production must enforce these boundaries, not merely model them.");
  notes(slide, "Be explicit about the three data planes. Shared data is hospital-governed reference material and common control logic, not pooled doctor behavior. Patient information should follow an authorized care relationship rather than being visible to every doctor. Doctor memories and test-decision evidence are isolated by doctor_id, and the current recommendation query filters on that doctor. The prototype has no production authentication or authorization, so these are intended ownership boundaries that must be enforced before real data is used.");
}

// 8 — Scorecard
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Shadow mode creates the baseline; Copilot must earn the delta.", "Pilot economics");
  const groups = [
    ["EFFICIENCY", C.teal, [["Intake time", "Submission to review-ready"], ["Review time", "Open to approve / modify"], ["Throughput", "Cases per session"]]],
    ["ADOPTION", C.blue, [["Acceptance", "Recommendations retained"], ["Override rate", "Risk / action / test edits"], ["Active use", "Weekly participating doctors"]]],
    ["SAFETY + QUALITY", C.red, [["Red-flag recall", "Urgent cases detected"], ["Fallback rate", "Provider / output failures"], ["Disagreement", "Clinically significant variance"]]],
    ["BUSINESS", C.amber, [["Unit cost", "Cost per completed intake"], ["Capacity", "Review minutes released"], ["Patient flow", "Wait to next action"]]],
  ];
  groups.forEach(([name, color, metrics], i) => {
    const x = 0.7 + i * 3.12;
    slide.addShape(S.roundRect, { x, y: 1.78, w: 2.78, h: 4.45, rectRadius: 0.04, line: { color: C.line }, fill: { color: C.white } });
    slide.addText(name, { x: x + 0.25, y: 2.08, w: 2.15, h: 0.25, fontSize: 10, bold: true, color, charSpacing: 1.1, margin: 0 });
    metrics.forEach(([label, measure], m) => {
      const y = 2.75 + m * 1.05;
      slide.addShape(S.ellipse, { x: x + 0.28, y, w: 0.17, h: 0.17, line: { transparency: 100 }, fill: { color } });
      slide.addText(label, { x: x + 0.57, y: y - 0.03, w: 1.9, h: 0.22, fontSize: 11, bold: true, color: C.ink, margin: 0 });
      slide.addText(measure, { x: x + 0.57, y: y + 0.26, w: 1.9, h: 0.4, fontSize: 9.3, color: C.muted, margin: 0 });
    });
  });
  slide.addShape(S.roundRect, { x: 2.05, y: 6.4, w: 9.2, h: 0.38, rectRadius: 0.04, line: { transparency: 100 }, fill: { color: C.dark } });
  slide.addText("Expand only when workflow value improves without weakening predefined safety guardrails.", { x: 2.35, y: 6.51, w: 8.6, h: 0.15, fontSize: 9.5, bold: true, color: C.white, align: "center", margin: 0 });
  footer(slide, "Targets should be agreed with clinical and operational owners before the pilot starts.");
  notes(slide, "Do not invent targets. Shadow supplies the baseline. The value case includes inference cost, workflow cost and capacity released, not only model quality.");
}

// 9 — Trust ladder
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Trust is earned in stages - with a measurable exit gate at each step.", "Adoption strategy");
  const stages = [
    [0.78, 4.4, 3.25, 1.52, "SHADOW", "OBSERVE", "Collect facts only\nDoctor owns assessment\nCapture baseline behavior", "416E6B"],
    [4.32, 3.15, 3.75, 2.77, "COPILOT", "ASSIST", "Propose assessment and tests\nDoctor accepts, rejects or corrects\nMeasure usefulness and disagreement", C.teal],
    [8.38, 1.9, 4.15, 4.02, "BOUNDED AUTONOMY", "EARN", "Complete, non-fallback GREEN only\nAllowlisted actions\nEvidence-gated test decisions\nEverything else escalates", C.dark],
  ];
  stages.forEach(([x, y, w, h, name, tag, body, color], i) => {
    slide.addShape(S.roundRect, { x, y, w, h, rectRadius: 0.04, line: { transparency: 100 }, fill: { color } });
    slide.addText(tag, { x: x + 0.28, y: y + 0.25, w: 1.25, h: 0.2, fontSize: 9, bold: true, color: i === 2 ? C.sea : "D5F1EC", charSpacing: 1.3, margin: 0 });
    slide.addText(name, { x: x + 0.28, y: y + 0.62, w: w - 0.56, h: 0.34, fontSize: 16, bold: true, color: C.white, margin: 0 });
    slide.addText(body, { x: x + 0.28, y: y + 1.1, w: w - 0.56, h: h - 1.28, fontSize: 10, color: "E2ECE9", margin: 0, paraSpaceAfterPt: 6 });
  });
  arrow(slide, 3.75, 4.14, 0.78, C.amber); arrow(slide, 7.78, 2.9, 0.8, C.amber);
  slide.addText("EXIT GATE", { x: 3.55, y: 3.65, w: 1.1, h: 0.2, fontSize: 8.5, bold: true, color: C.amber, align: "center", margin: 0 });
  slide.addText("EXIT GATE", { x: 7.62, y: 2.4, w: 1.1, h: 0.2, fontSize: 8.5, bold: true, color: C.amber, align: "center", margin: 0 });
  slide.addText("INTAKE mode", { x: 0.82, y: 2.18, w: 1.25, h: 0.24, fontSize: 11, bold: true, color: C.ink, margin: 0 });
  slide.addText("A supporting structured-collection workflow, not a separate trust stage.", { x: 0.82, y: 2.56, w: 5.8, h: 0.36, fontSize: 10.5, color: C.muted, margin: 0 });
  footer(slide, "Mode graduation is a clinical governance decision based on evidence - never an automatic model choice.");
  notes(slide, "Shadow creates the baseline and doctor-specific evidence. Copilot creates positive and negative labels through review. Autonomy remains use-case-specific, bounded and reversible.");
}

// 10 — Architecture
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Probabilistic reasoning sits inside deterministic control boundaries.", "Technical perspective");
  const nodes = [
    [0.72, 2.2, 1.75, "NEXT.JS", "Patient | Doctor | Admin", C.white, C.teal],
    [2.95, 2.2, 1.65, "FASTAPI", "Typed API + services", C.white, C.teal],
    [5.08, 1.62, 1.78, "DOCTOR TWIN", "Profile + context", C.mint, C.teal],
    [5.08, 3.05, 1.78, "GEMINI", "Structured proposal", "E8E2CE", "745D1A"],
    [7.42, 1.62, 2.0, "SAFETY ENGINE", "Deterministic override", "F7E3DF", C.red],
    [7.42, 3.05, 2.0, "DEPLOYMENT POLICY", "Allowed actions", C.mint, C.teal],
    [10.0, 2.2, 2.35, "TOOLS + REPOS", "Mock EHR | SQLAlchemy", C.white, C.teal],
  ];
  nodes.forEach(([x, y, w, h1, h2, fill, accent]) => {
    slide.addShape(S.roundRect, { x, y, w, h: 0.86, rectRadius: 0.04, line: { color: accent, width: 1.3 }, fill: { color: fill } });
    slide.addText(h1, { x: x + 0.12, y: y + 0.18, w: w - 0.24, h: 0.2, fontSize: 10.5, bold: true, color: C.ink, align: "center", margin: 0 });
    slide.addText(h2, { x: x + 0.12, y: y + 0.5, w: w - 0.24, h: 0.16, fontSize: 8.3, color: C.muted, align: "center", margin: 0 });
  });
  arrow(slide, 2.45, 2.63, 0.5); arrow(slide, 4.58, 2.63, 0.46); arrow(slide, 6.88, 2.05, 0.54, C.red); arrow(slide, 6.88, 3.48, 0.54); arrow(slide, 9.42, 2.63, 0.58);
  slide.addShape(S.roundRect, { x: 1.2, y: 4.73, w: 10.9, h: 1.13, rectRadius: 0.04, line: { transparency: 100 }, fill: { color: C.dark } });
  [["APPROVED MEMORY", "Doctor-scoped", 1.55], ["DOCTOR EVIDENCE", "Finalized labels", 4.2], ["AUDIT EVENTS", "Append-only trail", 7.0], ["EVALUATION", "32 synthetic cases", 9.35]].forEach(([h, b, x]) => {
    slide.addText(h, { x, y: 5.05, w: 1.95, h: 0.22, fontSize: 9.5, bold: true, color: C.sea, align: "center", margin: 0 });
    slide.addText(b, { x, y: 5.42, w: 1.95, h: 0.18, fontSize: 8.5, color: C.white, align: "center", margin: 0 });
  });
  slide.addText("ONE REUSABLE TWIN", { x: 0.75, y: 6.22, w: 1.7, h: 0.22, fontSize: 9.5, bold: true, color: C.teal, margin: 0 });
  slide.addText("Personalized at runtime by doctor profile, approved memory and doctor-scoped evidence.", { x: 2.53, y: 6.19, w: 7.1, h: 0.27, fontSize: 11, color: C.ink, margin: 0 });
  footer(slide, "Prototype: SQLite, keyword retrieval and mocked clinic adapter. Production: identity, PostgreSQL, integrations and observability.");
  notes(slide, "The LLM proposes; deterministic code disposes. Structured output is validated, safety runs independently, and deployment policy decides permitted actions. One shared implementation centralizes controls.");
}

// 11 — Shadow journey
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Shadow mode: assist with intake, observe how the doctor decides.", "Mode 1 | Observe");
  pill(slide, "PATIENT JOURNEY", 8.55, 1.06, 1.42, C.mint, C.teal);
  pill(slide, "DASHBOARD OUTCOME", 10.12, 1.06, 1.72, "E4EBF5", C.blue);
  pill(slide, "LEARNING RULE", 11.99, 1.06, 1.12, "FFF6DE", "9A6A13");
  const steps = [
    ["Patient describes symptoms", "Patient context and one natural follow-up at a time"],
    ["Twin structures facts", "Factual summary only; no diagnosis, treatment or action recommendation"],
    ["Safety checks every turn", "Deterministic red flags can force RED escalation"],
    ["Case reaches dashboard", "Doctor sees the intake and creates the clinical assessment and next action"],
    ["Reviewed data is retained", "Doctor-selected tests become positive examples; closure proposes memory candidates"],
  ];
  steps.forEach(([heading, body], i) => {
    const x = 1.0 + i * 2.36;
    journeyStep(slide, i + 1, heading, body, x, "416E6B");
    if (i < steps.length - 1) arrow(slide, x + 0.62, 2.29, 1.18, C.sea);
  });
  slide.addShape(S.roundRect, { x: 0.78, y: 4.55, w: 5.75, h: 1.28, rectRadius: 0.04, line: { color: "416E6B", width: 1.1 }, fill: { color: C.white } });
  slide.addText("VALUE TODAY", { x: 1.08, y: 4.88, w: 1.25, h: 0.2, fontSize: 9.5, bold: true, color: "416E6B", charSpacing: 1.0, margin: 0 });
  slide.addText("Less clerical intake work and a review-ready case, while the doctor keeps all clinical judgment.", { x: 2.45, y: 4.82, w: 3.62, h: 0.48, fontSize: 11.5, bold: true, color: C.ink, margin: 0 });
  slide.addShape(S.roundRect, { x: 6.8, y: 4.55, w: 5.75, h: 1.28, rectRadius: 0.04, line: { color: C.amber, width: 1.1 }, fill: { color: "FFF6DE" } });
  slide.addText("LEARNING CREATED", { x: 7.1, y: 4.88, w: 1.52, h: 0.2, fontSize: 9.5, bold: true, color: "9A6A13", charSpacing: 0.8, margin: 0 });
  slide.addText("A baseline of doctor-authored decisions. Memory candidates remain inactive until the doctor approves them.", { x: 8.75, y: 4.82, w: 3.35, h: 0.5, fontSize: 11.2, bold: true, color: C.ink, margin: 0 });
  footer(slide, "Shadow does not train from raw model output: only reviewed doctor decisions and explicitly approved memories influence future behavior.");
  notes(slide, "Shadow is already an assistant: it performs conversational intake, creates a structured case and runs safety checks. The doctor authors the assessment and action. Finalized doctor-selected tests provide positive evidence; case closure may extract candidate memories, but only explicit approval makes a memory retrievable.");
}

// 12 — Copilot journey
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Copilot mode: recommend, review, and learn from the doctor's response.", "Mode 2 | Assist");
  pill(slide, "PATIENT JOURNEY", 8.55, 1.06, 1.42, C.mint, C.teal);
  pill(slide, "DOCTOR REVIEW", 10.12, 1.06, 1.42, "E4EBF5", C.blue);
  pill(slide, "LEARNING LOOP", 11.69, 1.06, 1.42, "FFF6DE", "9A6A13");
  const steps = [
    ["Patient completes intake", "Twin combines patient context, doctor profile and approved memory"],
    ["Twin proposes", "Structured assessment, risk, recommended action and catalog-constrained tests"],
    ["Safety + policy apply", "Red flags override the model; unsafe cases escalate"],
    ["Doctor reviews dashboard", "Approve as-is or edit risk, action, summary and test selection"],
    ["Feedback becomes evidence", "Accepted, rejected and replacement tests are stored as doctor-specific labels"],
  ];
  steps.forEach(([heading, body], i) => {
    const x = 1.0 + i * 2.36;
    journeyStep(slide, i + 1, heading, body, x, C.teal);
    if (i < steps.length - 1) arrow(slide, x + 0.62, 2.29, 1.18, C.teal);
  });
  slide.addShape(S.roundRect, { x: 0.78, y: 4.55, w: 3.72, h: 1.28, rectRadius: 0.04, line: { color: C.green, width: 1.1 }, fill: { color: "E5F2EB" } });
  slide.addText("APPROVED", { x: 1.08, y: 4.85, w: 1.0, h: 0.2, fontSize: 10, bold: true, color: C.green, margin: 0 });
  slide.addText("Proposal retained -> positive doctor-specific evidence", { x: 1.08, y: 5.18, w: 2.95, h: 0.36, fontSize: 10.5, color: C.ink, margin: 0 });
  slide.addShape(S.roundRect, { x: 4.82, y: 4.55, w: 3.72, h: 1.28, rectRadius: 0.04, line: { color: C.amber, width: 1.1 }, fill: { color: "FFF6DE" } });
  slide.addText("EDITED", { x: 5.12, y: 4.85, w: 1.0, h: 0.2, fontSize: 10, bold: true, color: "9A6A13", margin: 0 });
  slide.addText("Removal -> negative label; replacement -> positive correction", { x: 5.12, y: 5.18, w: 2.95, h: 0.36, fontSize: 10.5, color: C.ink, margin: 0 });
  slide.addShape(S.roundRect, { x: 8.86, y: 4.55, w: 3.72, h: 1.28, rectRadius: 0.04, line: { color: C.blue, width: 1.1 }, fill: { color: "E4EBF5" } });
  slide.addText("NEXT SIMILAR CASE", { x: 9.16, y: 4.85, w: 1.65, h: 0.2, fontSize: 10, bold: true, color: C.blue, margin: 0 });
  slide.addText("Recommendations receive transparent evidence from this doctor only", { x: 9.16, y: 5.18, w: 2.95, h: 0.36, fontSize: 10.5, color: C.ink, margin: 0 });
  footer(slide, "Copilot shortens the decision loop without removing it: every clinical proposal remains reviewable and correctable.");
  notes(slide, "Copilot begins to provide recommendations, but the doctor remains the decision maker. Acceptance and edits are both useful data. For diagnostic tests, accepted recommendations are positive examples, removed recommendations are negative examples, and doctor-added replacements are positive corrections. Evidence stays scoped to that doctor.");
}

// 13 — Autonomous journey
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Autonomous mode: act only inside a narrow, evidence-backed envelope.", "Mode 3 | Bounded autonomy");
  pill(slide, "PATIENT JOURNEY", 8.35, 1.06, 1.42, C.mint, C.teal);
  pill(slide, "SAFETY BOUNDARY", 9.92, 1.06, 1.52, "F3DDD6", C.red);
  pill(slide, "ACTION / ESCALATION", 11.59, 1.06, 1.52, "FFF6DE", "9A6A13");
  const steps = [
    ["Patient completes intake", "No missing information; structured assessment validates"],
    ["Safety classifies", "Any red flag, AMBER/RED risk or fallback routes to the doctor"],
    ["Policy checks action", "Only allowlisted low-risk actions are eligible"],
    ["Evidence gates tests", "Active eligible catalog item, confidence and matching doctor history must pass"],
    ["Act or escalate", "Pass all gates -> bounded action; fail any gate -> doctor review"],
  ];
  steps.forEach(([heading, body], i) => {
    const x = 1.0 + i * 2.36;
    journeyStep(slide, i + 1, heading, body, x, C.amber);
    if (i < steps.length - 1) arrow(slide, x + 0.62, 2.29, 1.18, C.amber);
  });
  slide.addShape(S.roundRect, { x: 0.78, y: 4.55, w: 5.75, h: 1.28, rectRadius: 0.04, line: { color: C.green, width: 1.1 }, fill: { color: "E5F2EB" } });
  slide.addText("ALL GATES PASS", { x: 1.08, y: 4.86, w: 1.45, h: 0.2, fontSize: 10, bold: true, color: C.green, margin: 0 });
  slide.addText("GREEN + complete + non-fallback + allowlisted + doctor-specific evidence -> bounded action is permitted and audited.", { x: 2.63, y: 4.79, w: 3.4, h: 0.52, fontSize: 10.7, bold: true, color: C.ink, margin: 0 });
  slide.addShape(S.roundRect, { x: 6.8, y: 4.55, w: 5.75, h: 1.28, rectRadius: 0.04, line: { color: C.red, width: 1.1 }, fill: { color: "F7E3DF" } });
  slide.addText("ANY GATE FAILS", { x: 7.1, y: 4.86, w: 1.5, h: 0.2, fontSize: 10, bold: true, color: C.red, margin: 0 });
  slide.addText("No autonomous action. The recommendation remains proposed for doctor review, with the evidence snapshot preserved.", { x: 8.7, y: 4.79, w: 3.35, h: 0.52, fontSize: 10.7, bold: true, color: C.ink, margin: 0 });
  slide.addText("LEARNING RULE", { x: 0.82, y: 6.11, w: 1.2, h: 0.18, fontSize: 9, bold: true, color: C.amber, margin: 0 });
  slide.addText("Autonomous actions do not create training evidence; future behavior changes only through reviewed Shadow/Copilot decisions.", { x: 2.08, y: 6.08, w: 9.85, h: 0.3, fontSize: 9.8, color: C.ink, margin: 0 });
  footer(slide, "Autonomous decisions never train themselves; only subsequent doctor-reviewed Shadow/Copilot evidence can change future recommendations.");
  notes(slide, "Autonomous means bounded, not general autonomy. The prototype permits only allowlisted GREEN workflows. Diagnostic-test automation additionally requires catalog eligibility, current confidence, matching Shadow selections and matching Copilot acceptance. AMBER, RED, fallback or insufficient evidence always returns control to the doctor. Autonomous decisions are excluded from training evidence.");
}

// 14 — Pilot roadmap
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "A 90-day pilot should buy evidence before it buys autonomy.", "Execution roadmap");
  const phases = [
    ["0", "READINESS", "Weeks 0-2", "Workflow discovery\nIntended-use assessment\nPrivacy + hazard analysis\nBaseline instrumentation", C.dark],
    ["1", "SHADOW", "Weeks 3-6", "No autonomous clinical action\nMeasure workflow baseline\nValidate data capture\nWeekly safety review", "416E6B"],
    ["2", "COPILOT", "Weeks 7-10", "Limited doctors + use cases\nMandatory review\nAcceptance + disagreement\nKill switch + rollback", C.teal],
    ["3", "DECIDE", "Weeks 11-13", "Compare with baseline\nReview safety + adoption gates\nSelect bounded next use case\nStop, iterate or expand", C.amber],
  ];
  phases.forEach(([n, h, period, body, color], i) => {
    const x = 0.68 + i * 3.13;
    slide.addShape(S.roundRect, { x, y: 1.82, w: 2.82, h: 3.92, rectRadius: 0.04, line: { color, width: 1.2 }, fill: { color: i === 3 ? "FFF6DE" : C.white } });
    slide.addShape(S.ellipse, { x: x + 0.28, y: 2.14, w: 0.54, h: 0.54, line: { transparency: 100 }, fill: { color } });
    slide.addText(n, { x: x + 0.28, y: 2.3, w: 0.54, h: 0.16, fontSize: 10, bold: true, color: C.white, align: "center", margin: 0 });
    slide.addText(h, { x: x + 1.02, y: 2.15, w: 1.45, h: 0.24, fontSize: 12, bold: true, color: C.ink, margin: 0 });
    slide.addText(period, { x: x + 1.02, y: 2.52, w: 1.45, h: 0.18, fontSize: 9, color, margin: 0 });
    slide.addText(body, { x: x + 0.3, y: 3.08, w: 2.18, h: 1.8, fontSize: 10, color: C.muted, margin: 0, paraSpaceAfterPt: 7 });
    if (i < 3) arrow(slide, x + 2.82, 3.76, 0.31, C.sea);
  });
  slide.addText("Production prerequisites", { x: 0.75, y: 6.08, w: 1.75, h: 0.23, fontSize: 10.5, bold: true, color: C.teal, margin: 0 });
  slide.addText("Identity + RBAC | privacy + consent | validated clinical rules | monitoring | PostgreSQL | real EHR/lab adapters", { x: 2.52, y: 6.05, w: 9.65, h: 0.35, fontSize: 10, color: C.ink, margin: 0 });
  footer(slide, "Pilot scope should be narrow enough that every disagreement can be reviewed and acted on.");
  notes(slide, "Phase 0 determines intended use, regulatory applicability and privacy requirements. Phase 3 produces a decision, not automatic expansion. This shows delivery discipline alongside product ambition.");
}

// 15 — Close
{
  const slide = pptx.addSlide();
  slide.background = { color: C.dark };
  slide.addText("THE END STATE", { x: 0.78, y: 0.72, w: 2.3, h: 0.24, fontSize: 10, bold: true, color: C.sea, charSpacing: 1.8, margin: 0 });
  slide.addText("A governed learning layer\naround clinical work.", { x: 0.78, y: 1.32, w: 7.2, h: 1.5, fontSize: 30, bold: true, color: C.white, margin: 0 });
  slide.addText("Not a digital replacement for a doctor. A system that makes reviewed clinical behavior reusable, measurable and auditable.", { x: 0.8, y: 3.18, w: 6.75, h: 0.82, fontSize: 16, color: "D5E4E1", margin: 0 });
  [["01", "BETTER PREPARATION", "More complete cases before review"], ["02", "LESS REPETITION", "Administrative and cognitive work reduced"], ["03", "EVIDENCE-LED TRUST", "Assistance expands only where outcomes support it"]].forEach(([n, h, b], i) => {
    const y = 1.18 + i * 1.55;
    slide.addText(n, { x: 8.35, y, w: 0.38, h: 0.24, fontSize: 10, bold: true, color: "F1C15D", margin: 0 });
    slide.addText(h, { x: 9.0, y, w: 3.2, h: 0.24, fontSize: 12, bold: true, color: C.white, margin: 0 });
    slide.addText(b, { x: 9.0, y: y + 0.42, w: 3.25, h: 0.42, fontSize: 10.5, color: "BFD2CE", margin: 0 });
  });
  slide.addShape(S.roundRect, { x: 0.8, y: 5.58, w: 11.75, h: 0.82, rectRadius: 0.04, line: { transparency: 100 }, fill: { color: C.teal } });
  slide.addText("Start narrow. Measure in Shadow. Earn Copilot trust. Scale only where evidence supports it.", { x: 1.18, y: 5.86, w: 10.95, h: 0.25, fontSize: 15, bold: true, color: C.white, align: "center", margin: 0 });
  slide.addText("Working prototype | Synthetic data | Not a medical device", { x: 0.8, y: 6.95, w: 4.5, h: 0.18, fontSize: 9, color: "8FB1AB", margin: 0 });
  notes(slide, "Close on the operating model. The long-term value is not an AI chat interface; it is governed conversion of reviewed behavior into organizational capability. The next step is a narrow evidence-building pilot, not production autonomy.");
}

// 16 — Appendix: sources
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Singapore guidance: sources and careful applicability.", "Appendix A");
  const sources = [
    ["PDPC Model AI Governance Framework, 2nd edition", "21 Jan 2020", "Human-centric; explainable, transparent and fair. Sector-agnostic implementation guidance.", "pdpc.gov.sg/.../singapores-approach-to-ai-governance"],
    ["HSA GL-04-R4: Software Medical Devices - A Life Cycle Approach", "Dec 2025", "Lifecycle guidance where intended use meets software medical-device definitions.", "hsa.gov.sg/medical-devices/guidance-documents"],
    ["HSA GL-07-R2: Risk Classification SaMD-CDSS", "Jul 2025", "Risk classification where intended use meets SaMD/CDSS definitions.", "hsa.gov.sg/medical-devices/guidance-documents"],
    ["Artificial Intelligence in Healthcare Guidelines (AIHGle)", "2021 context", "Historical healthcare-specific reference. Verify authoritative archived edition before external circulation.", "Authoritative archive verification pending"],
  ];
  sources.forEach(([h, date, body, url], i) => {
    const y = 1.68 + i * 1.2;
    slide.addText(String(i + 1), { x: 0.75, y: y + 0.05, w: 0.42, h: 0.3, fontSize: 16, bold: true, color: C.teal, margin: 0 });
    slide.addText(h, { x: 1.35, y, w: 5.1, h: 0.3, fontSize: 12, bold: true, color: C.ink, margin: 0 });
    slide.addText(date, { x: 6.6, y, w: 1.2, h: 0.23, fontSize: 9.5, bold: true, color: C.teal, margin: 0 });
    slide.addText(body, { x: 1.35, y: y + 0.4, w: 6.35, h: 0.48, fontSize: 9.5, color: C.muted, margin: 0 });
    slide.addText(url, { x: 8.0, y: y + 0.08, w: 4.3, h: 0.55, fontSize: 8.5, color: C.blue, margin: 0, breakLine: false });
  });
  footer(slide, "Source review date: 21 September 2026. This appendix is not legal or regulatory advice.");
  notes(slide, "The current HSA guidance matters more for a production classification discussion than relying only on the older AIHGle. Verify the archived AIHGle document before external circulation.");
}

// 17 — Appendix: control inventory
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Safety and governance controls implemented in the prototype.", "Appendix B");
  const controls = [
    ["Deterministic red flags", "Patient-authored statements are checked independently; red flags force RED and escalation."],
    ["Fail-safe handling", "Provider or validation failure becomes a persisted AMBER case for review."],
    ["Mode permissions", "Each deployment mode receives explicit allowed actions."],
    ["Human authority", "Doctors approve or modify assessment, tests and closure; actions are audited."],
    ["Approved-only memory", "Extracted memories remain candidates until explicit approval."],
    ["Evidence-gated tests", "Autonomy requires complete GREEN intake, eligibility, confidence and evidence."],
    ["No self-training", "Autonomous decisions are excluded from training evidence."],
    ["Synthetic evaluation", "32 cases measure red flags, escalation, output validity and question coverage."],
  ];
  controls.forEach(([h, b], i) => card(slide, 0.72 + (i % 2) * 6.08, 1.62 + Math.floor(i / 2) * 1.23, 5.72, 1.0, h, b, i < 2 ? C.red : C.teal));
  footer(slide, "Software controls demonstrated with synthetic data are not evidence of clinical validation.");
  notes(slide, "Use this for safety follow-up. The red-flag rules are synthetic demo rules and require clinician-led validation before real-world use.");
}

// 18 — Appendix: current vs future
{
  const slide = pptx.addSlide("CONTENT");
  title(slide, "Current capability versus production end state.", "Appendix C");
  const cols = [
    ["WORKING NOW", C.teal, "Patient / doctor / admin UI\nStructured intake\nDoctor review and closure\nDeterministic override\nGoverned memory\nDoctor-specific test evidence\nSynthetic evaluation"],
    ["PROTOTYPE LIMIT", C.amber, "Synthetic data only\nSQLite persistence\nKeyword retrieval\nMock EHR adapter\nHeuristic thresholds\nNo real laboratory\nNo clinical validation"],
    ["PRODUCTION WORK", C.red, "Authentication and RBAC\nConsent and retention\nEncryption and keys\nPostgreSQL and migrations\nObservability\nValidated clinical rules\nReal EHR / lab integration"],
  ];
  cols.forEach(([h, color, body], i) => {
    const x = 0.78 + i * 4.18;
    slide.addShape(S.roundRect, { x, y: 1.65, w: 3.78, h: 4.85, rectRadius: 0.04, line: { color, width: 1.3 }, fill: { color: C.white } });
    slide.addText(h, { x: x + 0.3, y: 2.0, w: 2.8, h: 0.28, fontSize: 12.5, bold: true, color, margin: 0 });
    slide.addText(body, { x: x + 0.3, y: 2.58, w: 3.0, h: 3.2, fontSize: 11, color: C.ink, margin: 0, paraSpaceAfterPt: 9 });
  });
  footer(slide, "Priority: identity/privacy and clinical safety validation before broader autonomous behavior.");
  notes(slide, "Semantic retrieval, production identity, real integrations and clinically calibrated thresholds are not implemented. The prototype demonstrates workflow and control concepts only.");
}

const outputFile = process.env.TWIN_DECK_OUTPUT || "presentation/Doctor_Digital_Twin_Deck.pptx";
pptx.writeFile({ fileName: outputFile });
