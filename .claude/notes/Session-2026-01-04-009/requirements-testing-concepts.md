# Requirements, Testing, and Traceability Concepts

**Date:** 2026-01-04
**Session:** 009
**Status:** Discussion notes (not implemented)

---

## Overview

Discussion of a formal validation framework for Flow State, adapted for an AI-driven development environment with modern automation.

---

## Document Structure: One of Each Per System

Flow State will have:

- **RS-001** — Requirements Specification (single document)
- **RTM-001** — Requirements Traceability Matrix (single document)
- **OQ-001** — Operational Qualification (potentially retired or repurposed)

This keeps relationships visible and avoids reconciliation across fragmented domain-specific documents.

---

## Requirements Specification (RS)

### Structure

Requirements are categorized by domain:

```
RS-001
├── REQ-UI-001, REQ-UI-002, ...
├── REQ-SIM-001, REQ-SIM-002, ...
├── REQ-PHYS-001, ...
├── REQ-MATH-001, ...
├── REQ-SKETCH-001, ...
├── REQ-SCENE-001, ...
├── REQ-ARCH-001, ...
└── ...
```

### TU Ownership

More REQ categories than TU agents; TUs cover multiple categories:

| TU Agent | REQ Categories |
|----------|----------------|
| TU-UI | REQ-UI |
| TU-SIM | REQ-SIM, REQ-PHYS, REQ-MATH |
| TU-SKETCH | REQ-SKETCH |
| TU-SCENE | REQ-SCENE, REQ-ARCH (possibly) |

### RS as Authoritative Driver

Each requirement specifies its verification type:

```markdown
## REQ-SIM-001: Particle Integration Accuracy

Particle positions shall be integrated using Verlet integration
with error < 1e-6 per timestep.

| Attribute | Value |
|-----------|-------|
| Category | REQ-SIM |
| Verification Type | Unit Test |
```

---

## Two-Category Verification Model

**Key simplification:** Eliminate "TC Execution" as a category. All verification is either automated or requires intelligent judgment.

| Type | Nature | Evidence | Reproducibility |
|------|--------|----------|-----------------|
| **Unit Test** | Automated script | Commit + pass/fail + logs | Run anytime, deterministic |
| **Qualitative Proof** | Intelligent analysis (AI, human, or both) | Prose + code refs | Re-verifiable by reading |

### Rationale

If a test can be scripted, it's a unit test. If it requires judgment, it's a qualitative proof. The middle category ("manual execution of predefined steps") is just an unautomated unit test waiting to be scripted.

Qualitative proofs can be authored by AI agents, humans, or collaboratively — as long as there's intelligence behind the judgment that a requirement is met. Humans are particularly useful for verifications that are both hard to automate and hard for AI to assess, such as multi-step interactive workflows or visual/aesthetic judgments.

Traditional TCs/OQs/TPs become reproducible scripts. The "protocol" is the test script; the "execution record" is the run output.

---

## Requirements Traceability Matrix (RTM)

### Evolution from Manual to Automated

Traditional RTMs are manually maintained — error-prone and drift-prone.

**New model:** RTM is partially generated, partially authored.

### RTM Structure by Verification Type

| Requirement | Type | Verification Reference | Evidence |
|-------------|------|----------------------|----------|
| REQ-SIM-001 | Unit Test | `test_integration.py::test_verlet_accuracy` | Commit `a1b2c3d`, PASS |
| REQ-UI-003 | Unit Test | `test_ui.py::test_toolbar_rendering` | Commit `a1b2c3d`, PASS |
| REQ-ARCH-001 | Qualitative | — | [Proof documented inline] |

### Unit Test Entries (Generated)

Automation flow:
1. Parse RS for requirements with `verification_type: unit_test`
2. Scan test files for markers linking tests to REQ IDs (e.g., `@verifies("REQ-SIM-001")`)
3. Run tests, capture commit hash and pass/fail
4. Generate RTM entries automatically

### Qualitative Proof Entries (Authored)

For requirements requiring intelligent judgment, the RTM contains the actual proof:

```markdown
### REQ-ARCH-001: Separation of Concerns (Sketch/Simulation)

**Proof:**

The Sketch and Simulation domains are decoupled via the Compiler bridge.
- Sketch (`model/sketch.py`) has no imports from `engine/`
- Simulation (`engine/simulation.py`) has no imports from `model/`
- The Compiler (`engine/compiler.py`) is the sole translation layer

Code references:
- `model/sketch.py:1-50` — no engine imports
- `engine/simulation.py:1-50` — no model imports
- `engine/compiler.py:23` — imports both, performs translation

**Verified by:** TU-SIM
**Approved by:** QA
```

### Potential New Role: Code Architecture Auditor

For qualitative proofs, especially architectural requirements:
- Traces code and constructs the argument
- TU provides domain expertise on what the requirement means
- QA validates the argument is sound

---

## Fate of OQ and Test Protocols

### OQ: Potentially Retired or Repurposed

With the two-category model:
- Tests live with code (same repo, same commits)
- RTM maps requirements to tests and contains qualitative proofs
- Test results are artifacts (logs, reports), not controlled documents

The "OQ" becomes an *event* — running the full test suite at a qualification milestone — not a document with manual steps. Evidence is the test run output.

### TPs: Retained as Concept

Test Protocols remain conceptually valuable:
- AI executing a protocol is interesting and worth preserving
- Human-in-the-loop scripts: automated steps with prompts for human confirmation
- The script is the protocol; the human step is just an input

---

## What Gets Versioned Where

| Artifact | Location | Version Control |
|----------|----------|-----------------|
| Test scripts | Code repo | Git commits |
| RS | QMS | Controlled document |
| RTM | QMS | Controlled document (partially generated) |
| Qualitative proofs | RTM | Part of controlled document |
| Test results | CI/artifacts | Timestamped, linked to commit |

---

## Human-in-the-Loop Testing

Some tests specifically require human participation — cases that are both hard to automate and hard for AI to verify:
- Complex visual/aesthetic verification
- Hardware interaction
- Multi-step interactive workflows
- Subjective assessment

Model: Script with human-in-the-loop steps

```python
def test_visual_rendering():
    app.render_scene()
    screenshot = capture_screenshot()

    # Human-in-the-loop step
    confirmed = prompt_human(
        "Does the rendering look correct?",
        image=screenshot,
        expected="Particles should flow smoothly around obstacles"
    )

    assert confirmed, "Human verification failed"
```

The script is still the protocol. The human provides input at defined points.

---

## Open Items

- RS-001 drafting process (convene all agents)
- Test marker convention for linking tests to REQs
- RTM generation tooling
- Qualification milestone process (what triggers a "qualification event")
- Code Architecture Auditor role definition
- Human-in-the-loop test framework

---

**End of Notes**
