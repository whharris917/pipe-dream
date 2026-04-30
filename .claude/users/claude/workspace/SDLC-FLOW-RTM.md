---
title: Flow State Requirements Traceability Matrix
revision_summary: 'CR-111: Initial Adoption RTM. Qualitative-proof verification (inspection-based)
  for each of the 12 requirements in SDLC-FLOW-RS v1.0. Qualified baseline established
  at flow-state/main@a26f7fb as System Release FLOW-STATE-1.0.'
---

# SDLC-FLOW-RTM: Flow State Requirements Traceability Matrix

## 1. Purpose

This document provides traceability between the requirements specified in SDLC-FLOW-RS v1.0 and their verification evidence. Since `flow-state` has no automated test suite at the time of this adoption, verification is by **qualitative-proof inspection** (prose narratives anchored to specific files and line ranges) rather than by automated tests. This mirrors the pattern established by SDLC-CQ-RTM for `claude-qms`.

This is the inaugural RTM for Flow State, authored as part of CR-111 (Adopt Flow State into QMS Governance) which brings the system from the Genesis Sandbox into formal SDLC governance and establishes the qualified baseline `FLOW-STATE-1.0`.

---

## 2. Scope

This RTM covers all 12 requirements defined in SDLC-FLOW-RS v1.0 across the following domain groups:

- **REQ-FS-ARCH** (Architecture): 4 requirements
- **REQ-FS-CAD** (Sketch and Solver): 3 requirements
- **REQ-FS-SIM** (Simulation): 2 requirements
- **REQ-FS-UI** (User Interface): 2 requirements
- **REQ-FS-APP** (Application Shell): 1 requirement

---

## 3. Traceability Summary

| Requirement | Short Name | Verification Method | Result |
|-------------|------------|---------------------|--------|
| REQ-FS-ARCH-001 | Air Gap | Qualitative Proof | PASS |
| REQ-FS-ARCH-002 | Command Pattern | Qualitative Proof | PASS |
| REQ-FS-ARCH-003 | Scene/Session Split | Qualitative Proof | PASS |
| REQ-FS-ARCH-004 | ToolContext Facade | Qualitative Proof | PASS |
| REQ-FS-CAD-001 | Geometric Entities and Constraints | Qualitative Proof | PASS |
| REQ-FS-CAD-002 | PBD Solver with Hybrid Backend | Qualitative Proof | PASS |
| REQ-FS-CAD-003 | Interaction Servo | Qualitative Proof | PASS |
| REQ-FS-SIM-001 | Particle Engine | Qualitative Proof | PASS |
| REQ-FS-SIM-002 | Compiler Bridge | Qualitative Proof | PASS |
| REQ-FS-UI-001 | Hierarchical UI Tree with Overlays | Qualitative Proof | PASS |
| REQ-FS-UI-002 | Input Chain of Responsibility | Qualitative Proof | PASS |
| REQ-FS-APP-001 | Execution Modes | Qualitative Proof | PASS |

---

## 4. Verification Evidence

### 4.1 Architecture (REQ-FS-ARCH)

#### REQ-FS-ARCH-001: Air Gap

**Requirement:** UI components shall not mutate the Sketch or Simulation directly. All mutations of persistent state shall flow through `Command` objects submitted via `scene.execute()`.

**Evidence:** The `Scene` class at `flow-state/core/scene.py` exposes `execute(command)` (line 184) as the sole authorized mutation gateway for persistent state. The method delegates through `CommandQueue`, which records the command in history if `historize` is true. Tools never receive a direct reference to `Sketch` or `Simulation`; they receive a `ToolContext` (see REQ-FS-ARCH-004) whose `execute(command)` method is the only state-mutation channel exposed to UI code. Cascade effects of commands (e.g., `MaterialManager.on_rebuild`, `Simulation.sync_entity_arrays`) are downstream consequences of authorized commands, not separate state-mutation channels. The Air Gap is the architectural property that makes command-history replay correct: if state changed without a command, the history would be incomplete.

---

#### REQ-FS-ARCH-002: Command Pattern

**Requirement:** Every `Command` shall implement `execute()` and `undo()`, and shall carry a `historize` flag controlling whether the command is pushed onto the history stack.

**Evidence:** The abstract base class `Command` at `flow-state/core/command_base.py` declares `execute()` and `undo()` as abstract methods that all subclasses must implement, and carries `historize` as an instance attribute (defaulting to `True`) controlling history-stack insertion. Concrete commands at `flow-state/core/commands.py` (e.g., `AddLineCommand`, `SetEntityGeometryCommand`, `DeleteEntityCommand`) follow this contract. The `CommandQueue` in `core/scene.py` consults `command.historize` when deciding whether to push to the undo stack, so transient/preview commands can be applied without polluting history. Geometric commands store absolute state snapshots (not deltas) so the solver-influenced rotation/constraint outcomes are preserved exactly under undo.

---

#### REQ-FS-ARCH-003: Scene/Session Split

**Requirement:** The `Scene` shall hold persistent document state (Sketch, Simulation, ProcessObjects, CommandQueue). The `Session` shall hold transient application state (camera, selection, focused element, current tool, mode).

**Evidence:** `flow-state/core/scene.py` defines the `Scene` class as the owner of `sketch`, `simulation`, `process_objects`, and `command_queue` — the four persistent-state containers that constitute the document. `flow-state/core/session.py` defines the `Session` class as the owner of camera (pan/zoom), selection state, focused UI element, current tool, and mode/view options — all transient state describing how the user is *looking at* the document, not the document itself. The split underlies the file-I/O contract (Scene serializes; Session is reconstructed per launch) and the UI contract (Session-owned state never enters command history). Note: `interaction_data` (the solver's mouse-target buffer) is held on `Sketch.interaction_data` rather than on Session — this is acknowledged as a known asymmetry of the codebase and is not part of this requirement's scope; future granular CRs may revisit the placement.

---

#### REQ-FS-ARCH-004: ToolContext Facade

**Requirement:** Tools shall receive a `ToolContext` exposing only command execution, view/geometry queries, and transient interaction state — never the full application reference.

**Evidence:** `flow-state/core/tool_context.py` defines the `ToolContext` class as the facade interface for tools. It exposes:
- **Command execution:** `execute(command)` — the only authorized mutation channel.
- **View queries:** `zoom`, `pan`, `mode` — read-only access to camera and mode state.
- **Geometry queries:** `find_entity_at(...)`, `get_entity_type(...)` — read-only geometry helpers.
- **Transient interaction state:** `selection`, `interaction_state`, plus `set_interaction_data` / `clear_interaction_data` (which route to `sketch.interaction_data`).

The full application reference is held privately as `self._app`; the `Tool` base class in `flow-state/ui/tools.py` extracts `self.app = ctx._app` for backward compatibility during migration, but new tool code is expected to use only the facade interface. The leading-underscore convention marks `_app`, `_get_sketch`, and `_get_scene` as internal-only.

---

### 4.2 Sketch and Solver (REQ-FS-CAD)

#### REQ-FS-CAD-001: Geometric Entities and Constraints

**Requirement:** The `Sketch` shall support lines and circles as primary geometric entities, and shall support constraints (e.g., parallel, perpendicular, equal, fixed) operating over those entities.

**Evidence:** `flow-state/model/sketch.py` defines the `Sketch` class as the container for entities (lines, circles), constraints, drivers, and materials. `flow-state/model/geometry.py` defines the entity primitive classes (`Line`, `Circle`, plus `Point` as an internal entity type used by ProcessObject handle registration and `.mdl` import — not exposed as a primary user-facing entity in v1.0). `flow-state/model/constraints.py` defines the constraint type classes (parallel, perpendicular, equal-length, equal-radius, anchored/fixed flags on entities, plus length, radius, angle, distance, etc.). The constraint factory at `flow-state/model/constraint_factory.py` is the construction surface for tools. "Lines and circles as primary" is a high-level invariant; granular per-entity-type and per-constraint-type requirements are deferred to subsequent CRs.

---

#### REQ-FS-CAD-002: PBD Solver with Hybrid Backend

**Requirement:** The geometric constraint solver shall enforce constraints using Position-Based Dynamics. It shall provide both a Python (legacy, OOP) backend and a Numba-compiled (kernel) backend, switchable at runtime.

**Evidence:** `flow-state/model/solver.py` defines the constraint-enforcement engine. It exposes both `solve()` (the legacy Python/OOP backend that walks constraint objects and applies PBD corrections per object) and `solve_numba()` (the kernel backend that flattens constraint state to numpy arrays and dispatches to JIT functions). The runtime toggle is exposed via the `F9` global hotkey (handler in `flow-state/ui/input_handler.py` global-hotkey layer), letting users benchmark both backends live. The kernel implementations live at `flow-state/model/solver_kernels.py` as `@njit` (Numba JIT) functions implementing the PBD math (constraint projection, length preservation, anchor enforcement, etc.). Both backends operate on the same constraint set and produce equivalent results for static cases; the Numba path is faster for large constraint counts.

---

#### REQ-FS-CAD-003: Interaction Servo

**Requirement:** The mouse cursor shall be modeled as a temporary infinite-mass constraint target injected into the solver each frame, so that interactive dragging respects all other geometric constraints (length preservation, anchors, rotation about pivots).

**Evidence:** `flow-state/ui/tools.py` (Select tool) injects mouse drag state into `sketch.interaction_data` via `ctx.set_interaction_data(...)` each frame. The solver at `flow-state/model/solver.py` reads this interaction data each iteration and treats the mouse target as a constraint with effectively infinite mass — the cursor position is applied as a hard constraint, and other geometric constraints (length, parallel, anchored, etc.) negotiate around it via PBD. This produces emergent physical behaviors: dragging an end of an anchored line causes the line to *rotate about its anchor* rather than translate; dragging a midpoint of a line with two anchored endpoints causes the line to *deform within length-preservation limits*. The solver runs every frame as long as either constraints exist OR the user is interacting (per the orchestration loop in `core/scene.py` `update()`).

---

### 4.3 Simulation (REQ-FS-SIM)

#### REQ-FS-SIM-001: Particle Engine

**Requirement:** The `Simulation` shall represent particles as flat NumPy arrays following Data-Oriented Design and shall integrate motion via Verlet integration with spatial hashing.

**Evidence:** `flow-state/engine/simulation.py` (lines 51–69) defines the particle state as a Structure-of-Arrays layout: `pos_x`, `pos_y`, `vel_x`, `vel_y`, `force_x`, `force_y`, `is_static`, `atom_sigma`, `atom_eps_sqrt`, plus tether arrays (see REQ-FS-SIM-002). All are 1-D NumPy arrays preallocated to `MAX_ATOMS`. There are no per-particle Python objects in the hot path — this is Data-Oriented Design. `flow-state/engine/physics_core.py` `integrate_n_steps()` (lines 100–180) implements velocity Verlet integration in the kick-drift-kick form. `build_neighbor_list()` (lines 49–97) and `spatial_sort()` provide a uniform-grid cell-list spatial hash, drastically reducing pair-collision search cost from O(N²) to O(N).

---

#### REQ-FS-SIM-002: Compiler Bridge

**Requirement:** The `Compiler` shall translate Sketch geometry into Simulation atoms — static atoms (`is_static=1`) for non-dynamic entities, and tethered atoms (`is_static=3`) for dynamic entities (the mechanism by which the Compiler enables two-way CAD↔Physics coupling). The Compiler shall rebuild these atoms when the Scene reports that geometry has changed.

**Evidence:** `flow-state/engine/compiler.py` defines the `Compiler` class with a `rebuild()` entrypoint that walks Sketch entities and discretizes them into Simulation atoms. Static atoms (`is_static=1`, written at line 266) are immobile particles representing walls and other non-dynamic geometry — they participate in collisions but never move. Tethered atoms (`is_static=3`, written at line 236) are particles bound to dynamic entities via `tether_entity_idx`, `tether_local_pos`, and `tether_stiffness` arrays in `simulation.py`; they are the mechanism by which the Compiler enables two-way CAD↔Physics coupling (entity geometry drives tether positions, and tether forces influence entity dynamics). `Scene.rebuild()` at `flow-state/core/scene.py` (line 421) triggers `compiler.rebuild()` when the orchestration loop detects topology changes; geometry-only changes use a faster `sync_entity_arrays`/`sync_static_atoms_to_geometry` path (`simulation.py` lines 358–508) without full recompilation.

---

### 4.4 User Interface (REQ-FS-UI)

#### REQ-FS-UI-001: Hierarchical UI Tree with Overlays

**Requirement:** The `UIManager` shall maintain a retained widget tree rooted at a single root container. Widgets that produce floating elements (dropdowns, tooltips) shall implement an `OverlayProvider` protocol so the manager can render overlays after the main tree for correct Z-ordering.

**Evidence:** `flow-state/ui/ui_manager.py` defines the `UIManager` class as the root of the retained widget tree. The tree is rendered by recursive traversal from the root container. `flow-state/ui/ui_widgets.py` defines the `OverlayProvider` protocol (line 31), implemented by widgets that need to spawn floating elements outside their normal Z-order — `Dropdown` is a concrete implementer (line 712). `UIManager` exposes `register_overlay`/`unregister_overlay` for managing the overlay set, and `_draw_overlays` runs after the main tree pass so overlays render on top regardless of their owning widget's depth. This protocol-based design means future floating-element widgets (e.g., context menus, tooltips with rich content) need only implement the protocol — no `UIManager` changes required.

---

#### REQ-FS-UI-002: Input Chain of Responsibility

**Requirement:** Input events shall be processed in a strict 4-layer order: System → Modal → Global → HUD. (Modal precedes Global so dialogs capture keyboard input before global hotkeys trigger.) When the modal stack changes (push or pop), interaction state shall be reset across the widget tree to prevent ghost inputs.

**Evidence:** `flow-state/ui/input_handler.py` (lines 113–129) implements `handle_input()` with the four layers in order: (1) **System** — quit, video resize; (2) **Modal** — checks the central modal stack in `AppController` and routes events to the topmost modal if any; (3) **Global** — hotkeys (Ctrl+Z undo, B brush, F9 backend toggle, etc.); (4) **HUD** — passes events to the UI tree, manages generic focus via `wants_focus()` / `on_focus_lost()`. An explicit comment at lines 117–118 documents the deliberate Modal-before-Global ordering: "Modals BEFORE global hotkeys! Dialogs need to capture keyboard input before hotkeys trigger." Modal-stack reset is implemented at `flow-state/app/app_controller.py` lines 59 and 75 (`push_modal` and `pop_modal`), both of which call `self.app.ui.root.reset_interaction_state()` to clear `is_hovered` / `is_clicked` / `hot` flags across the widget tree, preventing the click-through-modal-close ghost-input class of bug. (Note: the module docstring at `input_handler.py:4–9` and `CLAUDE.md` Section 6.2 contain an outdated layer-ordering comment; the runtime dispatch order is the authoritative truth and matches this requirement. A follow-up CR is queued to correct the stale narrative.)

---

### 4.5 Application Shell (REQ-FS-APP)

#### REQ-FS-APP-001: Execution Modes

**Requirement:** The application entry point (`main.py`) shall support three execution modes selectable via CLI: a Dashboard mode (launcher GUI), a Simulation mode (active physics), and a Builder mode (CAD editor without active physics). The specific flag values are an implementation detail of `main.py`'s argparse configuration and may evolve under change control.

**Evidence:** `flow-state/main.py` (line 20) declares `argparse` with `choices=["dashboard", "sim", "builder"]` for the `--mode` argument. The three modes are dispatched to distinct entry-point flows: dashboard launches a launcher GUI for selecting projects; `sim` launches the main simulation mode with active physics integration; and `builder` launches a CAD-only editor (geometry creation and constraint editing) without the physics step running. The mode determines which subset of subsystems are instantiated and whether the physics integration step in `Scene.update()` is invoked. The current flag spelling `"sim"` is the implementation choice; the requirement is satisfied by the existence of the three conceptual modes with CLI selection, not by any specific flag string.

---

## 5. Qualified Baseline

| Attribute | Value |
|-----------|-------|
| Requirements Spec | SDLC-FLOW-RS v1.0 |
| Repository | whharris917/flow-state |
| Branch | main |
| Commit | a26f7fb |
| Commit message | "Remove personal note from README" |
| System Release | FLOW-STATE-1.0 |
| Verification method | Qualitative-proof inspection (no automated test suite at v1.0) |

The qualified-baseline commit `a26f7fb` is the inaugural qualified state of `flow-state`. All twelve requirements in SDLC-FLOW-RS v1.0 are verified by inspection against the source at this commit. Future CRs that modify `flow-state` code will follow the standard execution-branch workflow (SOP-005 §7.1) and will update this RTM with the new qualified baseline at merge time.

---

## 6. References

- **CR-111:** Adopt Flow State into QMS Governance — the authorizing change record for this RTM.
- **SDLC-FLOW-RS:** Flow State Requirements Specification v1.0 — the requirements verified here.
- **SDLC-CQ-RTM:** claude-qms Requirements Traceability Matrix — pattern reference for inspection-only verification.
- **Quality-Manual/10-SDLC.md:** Verification types (Unit Test, Qualitative Proof, Verification Record) and qualification semantics.
- **Quality-Manual/09-Code-Governance.md:** Qualified-commit and System-Release mechanics.

---

**END OF DOCUMENT**
