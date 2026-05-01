---
title: Flow State Requirements Specification
revision_summary: 'CR-112 (cosmetic v2.1 → v3.0 cycle): Correct prior revision_summary
  wording. The substantive change in this document remains the v1.0 → v2.0 strengthening
  of REQ-FS-ARCH-004 (ToolContext Facade — forbids direct application references in
  tools and requires Sketch.interaction_data mutations through the facade) and REQ-FS-CAD-003
  (Interaction Servo — facade-routed injection clause). All other 10 requirements
  unchanged from v1.0. The v1.1 → v2.0 cycle was approved with a revision_summary
  that misread the engine''s versioning behavior (drafts increment minor; approvals
  bump major). This v2.1 → v3.0 cycle replaces that wording with correct version-numbering.
  Substantive RS content (REQ-FS-ARCH-004 and REQ-FS-CAD-003 strengthening) unchanged
  from v2.0.'
---

# SDLC-FLOW-RS: Flow State Requirements Specification

## 1. Purpose

This document defines the requirements for `flow-state` — the Flow State application, a hybrid interactive Python program combining a CAD geometric constraint solver with a particle-based physics engine. It is the inaugural Requirements Specification for the `flow-state` system, authored as part of CR-111 (Adopt Flow State into QMS Governance) which brings the system from the Genesis Sandbox into formal SDLC governance.

These v1.0 requirements are intentionally high-level: they capture the architectural and behavioral invariants that *make Flow State Flow State* — the Air Gap, the Command Pattern, the PBD constraint solver, the particle engine, the UI input chain — rather than enumerating every entity, tool, constraint, or UI affordance. Granular feature-level requirements will be added in subsequent CRs as the system stabilizes.

---

## 2. Scope

This RS covers 12 requirements across 5 domain groups:

- **REQ-FS-ARCH** (Architecture): 4 requirements
- **REQ-FS-CAD** (Sketch and Solver): 3 requirements
- **REQ-FS-SIM** (Simulation): 2 requirements
- **REQ-FS-UI** (User Interface): 2 requirements
- **REQ-FS-APP** (Application Shell): 1 requirement

These requirements govern the contents of `whharris917/flow-state` on GitHub.

---

## 3. Requirements

### 3.1 Architecture (REQ-FS-ARCH)

| ID | Requirement |
|----|-------------|
| REQ-FS-ARCH-001 | **Air Gap.** UI components shall not mutate the Sketch or Simulation directly. All mutations of persistent state shall flow through `Command` objects submitted via `scene.execute()`. |
| REQ-FS-ARCH-002 | **Command Pattern.** Every `Command` shall implement `execute()` and `undo()`, and shall carry a `historize` flag controlling whether the command is pushed onto the history stack. |
| REQ-FS-ARCH-003 | **Scene/Session Split.** The `Scene` shall hold persistent document state (Sketch, Simulation, ProcessObjects, CommandQueue). The `Session` shall hold transient application state (camera, selection, focused element, current tool, mode). |
| REQ-FS-ARCH-004 | **ToolContext Facade.** Tools shall interact with the application exclusively through a `ToolContext` instance and shall not hold a direct application reference (no `self.app` or equivalent passthrough). The facade exposes command execution, view and geometry queries, transient interaction-state management (selection, snap target, status, sound, drag-target injection via `set_interaction_data` / `update_interaction_target` / `clear_interaction_data`), and ProcessObject registration. Tools shall not mutate persistent model state — including the Sketch's `interaction_data` field — outside this facade. |

---

### 3.2 Sketch and Solver (REQ-FS-CAD)

| ID | Requirement |
|----|-------------|
| REQ-FS-CAD-001 | **Geometric Entities and Constraints.** The `Sketch` shall support lines and circles as primary geometric entities, and shall support constraints (e.g., parallel, perpendicular, equal, fixed) operating over those entities. |
| REQ-FS-CAD-002 | **PBD Solver with Hybrid Backend.** The geometric constraint solver shall enforce constraints using Position-Based Dynamics. It shall provide both a Python (legacy, OOP) backend and a Numba-compiled (kernel) backend, switchable at runtime. |
| REQ-FS-CAD-003 | **Interaction Servo.** The mouse cursor shall be modeled as a temporary infinite-mass constraint target injected into the solver each frame, so that interactive dragging respects all other geometric constraints (length preservation, anchors, rotation about pivots). Tools shall route this injection through the `ToolContext` facade (`ctx.set_interaction_data` / `update_interaction_target` / `clear_interaction_data`) rather than mutating `Sketch.interaction_data` directly. |

---

### 3.3 Simulation (REQ-FS-SIM)

| ID | Requirement |
|----|-------------|
| REQ-FS-SIM-001 | **Particle Engine.** The `Simulation` shall represent particles as flat NumPy arrays following Data-Oriented Design and shall integrate motion via Verlet integration with spatial hashing. |
| REQ-FS-SIM-002 | **Compiler Bridge.** The `Compiler` shall translate Sketch geometry into Simulation atoms — **static atoms** (`is_static=1`) for non-dynamic entities, and **tethered atoms** (`is_static=3`) for dynamic entities (the mechanism by which the Compiler enables two-way CAD↔Physics coupling). The Compiler shall rebuild these atoms when the Scene reports that geometry has changed. |

---

### 3.4 User Interface (REQ-FS-UI)

| ID | Requirement |
|----|-------------|
| REQ-FS-UI-001 | **Hierarchical UI Tree with Overlays.** The `UIManager` shall maintain a retained widget tree rooted at a single root container. Widgets that produce floating elements (dropdowns, tooltips) shall implement an `OverlayProvider` protocol so the manager can render overlays after the main tree for correct Z-ordering. |
| REQ-FS-UI-002 | **Input Chain of Responsibility.** Input events shall be processed in a strict 4-layer order: System → Modal → Global → HUD. (Modal precedes Global so dialogs capture keyboard input before global hotkeys trigger.) When the modal stack changes (push or pop), interaction state shall be reset across the widget tree to prevent ghost inputs. |

---

### 3.5 Application Shell (REQ-FS-APP)

| ID | Requirement |
|----|-------------|
| REQ-FS-APP-001 | **Execution Modes.** The application entry point (`main.py`) shall support three execution modes selectable via CLI: a Dashboard mode (launcher GUI), a Simulation mode (active physics), and a Builder mode (CAD editor without active physics). The specific flag values are an implementation detail of `main.py`'s argparse configuration and may evolve under change control. |

---

## 4. References

- **CR-111:** Adopt Flow State into QMS Governance — the authorizing change record for the v1.0 baseline.
- **CR-112:** ToolContext Migration Completion + Documentation Reconciliation — the authorizing change record for the strengthened REQ-FS-ARCH-004 and REQ-FS-CAD-003 (v1.0 → v2.0 substantive revision; subsequent v2.0 → v3.0 cycle was a revision_summary cosmetic correction with no substantive RS content change).
- **SDLC-FLOW-RTM:** Flow State Requirements Traceability Matrix — provides verification evidence for these requirements.
- **SDLC-CQ-RS:** claude-qms Requirements Specification — pattern reference for lightweight, inspection-only RS.
- **Quality-Manual/10-SDLC.md:** The two-document SDLC framework and "the code is the design" principle.
- **Quality-Manual/09-Code-Governance.md:** Adoption CRs and qualified-baseline mechanics.

---

**END OF DOCUMENT**
