---
title: Software Development Life Cycle (SDLC) Governance
revision_summary: 'CR-089: Add Verification Record (VR) as third verification type
  in Sections 3, 6.2, 6.3, 7.3, 9'
---

# SOP-006: Software Development Life Cycle (SDLC) Governance

## 1. Purpose

This procedure establishes the minimum documentation framework required for a software system to reach a qualified state within the QMS. The goal is **streamlined rigor**: formal traceability without documentation proliferation.

---

## 2. Scope

This SOP applies to all software systems governed under the QMS, including:

- Application code (e.g., Flow State)
- QMS infrastructure code (e.g., QMS CLI)

**Out of Scope:**

- Personal notes, scratch files, workshop drafts
- Genesis Sandbox work (per SOP-005 Section 7.2)

---

## 3. Definitions

| Term | Definition |
|------|------------|
| **RS** | Requirements Specification - defines what the system shall do |
| **RTM** | Requirements Traceability Matrix - maps requirements to code and verification evidence |
| **Unit Test** | Automated, deterministic verification script |
| **Qualitative Proof** | Verification requiring intelligent judgment, documented as prose with code references |
| **Verification Record (VR)** | Structured behavioral verification evidence documenting observable system behavior (see SOP-004 Section 9C) |
| **Qualified State** | A system with approved RS, verified RTM, and code at a documented commit |

---

## 4. SDLC Document Types

A system requires exactly **two** controlled documents to reach a qualified state:

| Document | Purpose | Content |
|----------|---------|---------|
| **RS** | What the system shall do | Requirements only |
| **RTM** | Proof that requirements are met | Verification evidence (test refs or qualitative proofs) |

No Design Specification, Configuration Specification, or Operational Qualification documents are required. The code is the design; verification evidence lives in the RTM.

### 4.1 Document Location

For a system named `{system-name}` with code in `{system-name}/`, SDLC documents are located in:

```
QMS/SDLC-{SYS-NAME}/
├── SDLC-{SYS-NAME}-RS.md
└── SDLC-{SYS-NAME}-RTM.md
```

**Example:** For Flow State with code in `flow-state/`:

```
QMS/SDLC-FLOW/
├── SDLC-FLOW-RS.md
└── SDLC-FLOW-RTM.md
```

---

## 5. Requirements Specification (RS)

### 5.1 Purpose

The RS defines **what** the system shall do. It contains requirements and nothing else.

### 5.2 Requirement Format

Each requirement shall be:

- **Uniquely identified** by type prefix: `REQ-{TYPE}-{NNN}`
- **Verifiable:** Can be confirmed through test or analysis

Requirements may group closely-related items if they can be readily verified together. For example, a requirement specifying a template format may include a bulleted list of format rules.

**Requirement ID Examples:**

| Prefix | Domain |
|--------|--------|
| REQ-SIM | Simulation / Physics |
| REQ-SKETCH | Sketch / Geometry / Solver |
| REQ-UI | User Interface / Tools |
| REQ-SCENE | Scene / Commands / Orchestration |
| REQ-ARCH | Architecture / Cross-cutting |

Types emerge organically based on the system's domains.

**Example Requirement:**

```markdown
### REQ-SIM-001: Verlet Integration

Particle positions shall be integrated using Verlet integration.
```

### 5.3 RS Structure

The RS may be organized in whatever structure aids readability (e.g., grouped by type prefix, by subsystem, or by feature area). The structure itself is not governed; what matters is that each requirement has a unique ID that the RTM can reference.

### 5.4 Lifecycle

RS changes after initial approval require a CR per SOP-002.

---

## 6. Requirements Traceability Matrix (RTM)

### 6.1 Purpose

The RTM provides **proof** that each requirement is implemented and verified. It maps requirements to code locations and contains verification evidence.

### 6.2 Three Verification Types

All verification falls into one of three categories:

| Type | Nature | Evidence in RTM |
|------|--------|-----------------|
| **Unit Test** | Automated script | Test file reference + pass status + commit |
| **Qualitative Proof** | Intelligent analysis | Prose argument + code references (inline) |
| **Verification Record** | Structured behavioral observation | VR document reference + outcome |

**Rationale:** If verification can be scripted, it's a unit test. If it requires judgment about code structure or design, it's a qualitative proof. If it requires observable behavioral evidence from a running system, it's a verification record.

### 6.3 RTM Structure

#### 6.3.1 Unit Test Entries

For requirements verified by automated tests:

| Requirement | Verification | Evidence |
|-------------|--------------|----------|
| REQ-SIM-001 | Unit Test | `tests/test_simulation.py::test_verlet_integration` @ `a1b2c3d` PASS |
| REQ-UI-003 | Unit Test | `tests/test_ui.py::test_toolbar_rendering` @ `a1b2c3d` PASS |

Test files may use markers (e.g., `@verifies("REQ-SIM-001")`) to link tests to requirements, enabling partial automation of RTM maintenance.

#### 6.3.2 Qualitative Proof Entries

For requirements requiring intelligent judgment, the RTM contains the proof inline:

```markdown
### REQ-ARCH-001: Separation of Concerns (Sketch/Simulation)

**Verification Type:** Qualitative Proof

**Proof:**

The Sketch and Simulation domains are decoupled via the Compiler bridge:

- `model/sketch.py` has no imports from `engine/`
- `engine/simulation.py` has no imports from `model/`
- `engine/compiler.py` is the sole translation layer

Code references:
- `model/sketch.py:1-50` @ `a1b2c3d` - no engine imports
- `engine/simulation.py:1-50` @ `a1b2c3d` - no model imports
- `engine/compiler.py:23` @ `a1b2c3d` - imports both, performs translation

**Verified by:** Reviewer agent
```

Qualitative proofs may be authored by AI agents, humans, or collaboratively.

#### 6.3.3 Verification Record Entries

For requirements verified by structured behavioral testing:

| Requirement | Verification | Evidence |
|-------------|--------------|----------|
| REQ-MCP-015 | Verification Record | `CR-088-VR-001` PASS |

The VR document contains the full procedure, observations, and outcome. The RTM references the VR by ID; the VR itself contains the detailed evidence per SOP-004 Section 9C.

### 6.4 Human-in-the-Loop Verification

Some requirements require human judgment - cases that are both hard to automate and hard for AI to assess:

- Visual/aesthetic verification
- Complex interactive workflows
- Subjective quality assessment

These are documented as qualitative proofs with explicit human verification noted:

```markdown
### REQ-UI-042: Particle Flow Visual Quality

**Verification Type:** Qualitative Proof (Human-in-the-Loop)

**Proof:**

Visual inspection confirms particles flow smoothly around obstacles without
stuttering, clipping, or unnatural behavior.

**Verified by:** Human reviewer (visual inspection, 2026-01-15)
```

### 6.5 RTM Maintenance

| Event | RTM Action |
|-------|------------|
| New requirement in RS | Add entry, verification pending |
| Test created/linked | Update with test reference |
| Test passes | Update with commit hash + PASS |
| Qualitative proof authored | Add inline proof |
| Requirement changed | Re-verify, update evidence |

### 6.6 Lifecycle

RTM changes require a CR per SOP-002.

---

## 7. Qualification

### 7.1 Qualified State

A system is in a **qualified state** when:

1. RS is EFFECTIVE (approved per SOP-001)
2. RTM is EFFECTIVE with all requirements showing verification evidence
3. Code state is documented (System Release version + qualified commit per SOP-005)

### 7.2 Single Commit Requirement

The qualified state must be demonstrable at a **single git commit**. This means:

- All unit tests referenced in the RTM passed at that commit
- All qualitative proofs reference code at that commit
- The RTM references this single commit as the **qualified commit**

The qualified commit shall be a commit on the execution branch (per SOP-005 Section 7.1) where all tests passed as verified by CI. This commit is preserved on main via merge commit (`--no-ff`). The RTM shall reference this execution branch commit hash -- not the merge commit hash and not a commit that exists only on main.

A range of commits where different tests passed at different times does not constitute a qualified state. An auditor must be able to ask: "At commit `X`, did the system meet all requirements simultaneously?" The answer must be yes.

**Rationale:** If there is no evidence that the system met all requirements at the same point in time, there is no evidence that it was ever fully qualified.

### 7.3 Qualification is Not a Document

There is no Operational Qualification (OQ) document. Qualification is an **event**: the point at which RS and RTM are approved and all verification evidence is complete.

The evidence is:

- Test suite output (for unit tests)
- Qualitative proofs in RTM (for judgment-based verification)
- Verification Records (for behavioral verification)
- The RTM itself as the master record

### 7.4 CR Closure Prerequisite

For any CR that modifies an SDLC-governed system:

1. The system's RS must be EFFECTIVE before the CR can be routed for post-review
2. The system's RTM must be EFFECTIVE before the CR can be routed for post-review
3. Code changes shall not be merged to the main branch until both the RS and RTM are EFFECTIVE

**Rationale:** A CR claiming to qualify a system is not complete until the qualification evidence (RTM) is formally approved. Closing a CR before RTM approval creates a window where the system is claimed qualified but lacks approved verification evidence. Merging code before RS/RTM approval is equally problematic -- it places unqualified code on the main branch.

The merge gate (requirement 3) is distinct from the post-review gate (requirements 1-2). The merge must happen after RS/RTM approval but before post-review routing, so that post-reviewers can verify the code exists on main. See SOP-005 Section 7.1.3 for merge type requirements.

This requirement applies regardless of whether the CR modifies RS/RTM content. If the CR touches code in an SDLC-governed system, the RTM must reflect the qualified state.

---

## 8. Relationship to Other SOPs

| SOP | Relationship |
|-----|--------------|
| SOP-001 | RS and RTM follow document control lifecycle |
| SOP-002 | Changes to RS, RTM, or code require a CR |
| SOP-005 | Code governance, System Release versioning, commit references |

---

## 9. Summary

| What | Where |
|------|-------|
| What the system shall do | RS |
| How the system does it | Code (not a document) |
| Proof requirements are met | RTM (tests + qualitative proofs + verification records) |
| Qualification evidence | RTM + test output + VRs (not an OQ document) |

**Streamlined rigor:** Two documents (RS, RTM) plus the code itself. Nothing more.

---

**END OF DOCUMENT**
