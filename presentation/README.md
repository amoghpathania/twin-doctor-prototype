# Doctor Digital Twin Presentation

## Build

From the repository root:

```powershell
npm run deck:build
```

This creates `presentation/Doctor_Digital_Twin_Deck.pptx` from
`presentation/generate-deck.js`. The deck uses a 16:9 layout and includes speaker
notes on every slide.

## Email Review Structure

- Slides 1-4: business problem and responsible-AI framing
- Slides 5-10: product, doctor-specific learning, data management, value,
  adoption and technical architecture
- Slide 11: Shadow mode end-to-end journey
- Slide 12: Copilot mode end-to-end journey
- Slide 13: bounded Autonomous mode end-to-end journey
- Slides 14-15: pilot roadmap and end state
- Slides 16-18: supporting sources, control inventory and capability boundaries

The deck is designed to stand alone when shared by email. Each mode slide shows
the patient journey, dashboard or action outcome, learning behavior and safety
boundary without requiring a live demonstration or speaker narration.

The data-management slide distinguishes organization-wide reference data,
patient-bound care context and doctor-specific learning. In the prototype,
memories and test-decision evidence are filtered by `doctor_id` and are not
pooled across doctors. Production authentication, authorization, consent and
tenancy controls remain required to enforce the intended boundaries.

## Mode Journey Interpretation

- **Shadow:** the Twin gathers and structures facts, creates a dashboard case,
  and observes doctor-authored decisions. Finalized test selections and
  explicitly approved memories become future evidence.
- **Copilot:** the Twin proposes an assessment, action and diagnostic tests.
  Doctor approvals, removals and replacements become doctor-specific labels.
- **Autonomous:** only complete, non-fallback GREEN cases inside allowlisted and
  evidence-backed boundaries may proceed. Every failed gate returns the case to
  doctor review. Autonomous decisions never train themselves.

## Claim Discipline

Use these terms consistently:

- **Implemented:** available in the current synthetic prototype.
- **Synthetically tested:** exercised through automated tests or the 32-case
  synthetic evaluation suite.
- **Production work:** required before any real clinical deployment.

Do not claim regulatory compliance, clinical validation, production security,
real-world ROI or autonomous diagnosis. The current autonomous thresholds are
engineering defaults, not clinically calibrated constants.

## Source Note

Before distributing the deck externally, verify an authoritative archived copy
of Singapore's 2021 Artificial Intelligence in Healthcare Guidelines (AIHGle).
The current HSA software medical-device lifecycle and SaMD-CDSS guidance and the
PDPC Model AI Governance Framework are linked in the appendix.