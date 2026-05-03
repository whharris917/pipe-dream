---
title: Flow State Requirements Traceability Matrix
revision_summary: 'CR-114 (v2.1 → v3.0, cycle 3 corrections per tu_sim and tu_scene
  findings on cycle 2). REQ-FS-SIM-002 evidence had three line-citation drifts at
  f69455f: (a) sync_*/teleport block end shifted from 508 to 520 — my cycle 1 update
  fixed the 358→370 start anchor but failed to apply the same +12 shift to the end
  of the range; (b) compiler.py tethered atom write cited as line 236, actual line
  245 (pre-existing drift in v2.0 EFFECTIVE, carried forward unchanged into v2.1,
  not caught by my "unchanged file = unchanged citation" heuristic on cycle 1); (c)
  compiler.py static atom write cited as line 266, actual line 275 (same pre-existing
  v2.0 drift). All three corrected. tu_ui RECOMMEND on cycle 2; tu_sim and tu_scene
  REQUEST_UPDATES with the same findings independently. Cycle 1 substantive content
  otherwise preserved. Re-pin Qualified Baseline to flow-state@f69455f (System Release
  FLOW-STATE-1.2). Body changes are minimal because no requirements were added or
  modified; CR-114 is bug fixes within the existing requirement surface (Resize World
  UX — input field visibility + confirmation dialog + full physics reset on confirm;
  plus ui/brush_tool.py orphan deletion). Re-anchored citations: REQ-FS-SIM-002 simulation.py
  sync_* block 358–508 → 370–520; REQ-FS-SIM-002 compiler.py tethered 236 → 245, static
  266 → 275. Other line citations independently re-verified via `git show f69455f:`
  against the new commit and confirmed unchanged: REQ-FS-UI-002 (input_handler.py
  115-136, 124-125, 1-16, app_controller.py push_modal/pop_modal at 48/63 with reset
  calls at 59/75); REQ-FS-UI-001 (ui_widgets.py 31, 712); REQ-FS-SIM-001 (simulation.py
  51-69, physics_core.py 100-251, 49-97, 254); REQ-FS-SIM-002 (scene.py 421 only —
  compiler.py 245/275 are corrections in this cycle, not unchanged); REQ-FS-ARCH and
  REQ-FS-CAD bodies (tools.py and tool_context.py untouched in CR-114). References
  updated to add CR-114.'
---

# SDLC-FLOW-RTM: Flow State Requirements Traceability Matrix

## 1. Purpose

This document provides traceability between the requirements specified in SDLC-FLOW-RS v3.0 and their verification evidence. Since `flow-state` has no automated test suite at the time of this revision, verification is by **qualitative-proof inspection** (prose narratives anchored to specific files and line ranges) rather than by automated tests. This mirrors the pattern established by SDLC-CQ-RTM for `claude-qms`.

The inaugural RTM (v1.0) was authored as part of CR-111 (Adopt Flow State into QMS Governance), which brought the system from the Genesis Sandbox into formal SDLC governance and established the qualified baseline `FLOW-STATE-1.0` at flow-state@a26f7fb. CR-112 (ToolContext Migration Completion + Documentation Reconciliation) strengthens REQ-FS-ARCH-004 (no `self.app` passthrough; interaction_data routes through the facade) and REQ-FS-CAD-003 (facade-routed Servo injection), and advances the qualified baseline to `FLOW-STATE-1.1` at flow-state@ec450e2.

---

## 2. Scope

This RTM covers all 12 requirements defined in SDLC-FLOW-RS v3.0 across the following domain groups:

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

**Evidence:** The `Scene` class at `flow-state/core/scene.py` exposes `execute(command)` (line 184) as the principal authorized mutation gateway for persistent state. The method delegates through `CommandQueue`, which records the command in history if `historize` is true. Tools never receive a direct reference to `Sketch` or `Simulation`; they receive a `ToolContext` (see REQ-FS-ARCH-004) whose `execute(command)` method is the primary state-mutation channel exposed to UI code. Cascade effects of commands (e.g., `MaterialManager.on_rebuild`, `Simulation.sync_entity_arrays`) are downstream consequences of authorized commands, not separate state-mutation channels.

**Documented authorized exception — brush operations.** `Scene.paint_particles()` and `Scene.erase_particles()` (`flow-state/core/scene.py:452-491`) mutate `Simulation` state directly *without* going through `Command` objects. This is a deliberate exception: per CLAUDE.md §3.3, fluid dynamics are irreversible, so commands that alter physics state rely on full state snapshots (the **time-travel snapshot pattern**) rather than per-command undo. The brush operations are deliberately exposed on the `ToolContext` at lines 383-413 (with a companion `snapshot_particles()` at line 415-421 that captures state for snapshot-based undo before the brush mutates). Architecturally, this means: (a) **geometric** persistent state (Sketch entities, constraints) flows exclusively through `Command` objects with per-command undo; (b) **physics** persistent state (particle arrays in Simulation) is mutated by Commands for structural changes (Compiler rebuild, etc.) but by direct `paint`/`erase` for brush operations, with snapshot-based undo. The Air Gap invariant is preserved in spirit — UI code does not mutate the model directly; it routes through Scene methods exposed via ToolContext — but the per-mutation Command requirement holds for sketch state, not for the physics brush.

---

#### REQ-FS-ARCH-002: Command Pattern

**Requirement:** Every `Command` shall implement `execute()` and `undo()`, and shall carry a `historize` flag controlling whether the command is pushed onto the history stack.

**Evidence:** The abstract base class `Command` at `flow-state/core/command_base.py` declares `execute()` and `undo()` as abstract methods that all subclasses must implement, and carries `historize` as an instance attribute (defaulting to `True`) controlling history-stack insertion. Concrete commands follow this contract — for example, `RemoveEntityCommand` at `flow-state/model/commands/geometry.py:77` (a topology-changing entity deletion that stores the entity's serialized form on `execute` for restoration on `undo`), plus the geometric mutation commands at `flow-state/core/commands.py` (`SetEntityGeometryCommand` and similar). The `CommandQueue` in `core/scene.py` consults `command.historize` when deciding whether to push to the undo stack, so transient/preview commands can be applied without polluting history. Geometric commands store absolute state snapshots (not deltas) so the solver-influenced rotation/constraint outcomes are preserved exactly under undo.

---

#### REQ-FS-ARCH-003: Scene/Session Split

**Requirement:** The `Scene` shall hold persistent document state (Sketch, Simulation, ProcessObjects, CommandQueue). The `Session` shall hold transient application state (camera, selection, focused element, current tool, mode).

**Evidence:** `flow-state/core/scene.py` defines the `Scene` class as the owner of `sketch`, `simulation`, `process_objects`, and `command_queue` — the four persistent-state containers that constitute the document. `flow-state/core/session.py` defines the `Session` class as the owner of camera (pan/zoom), selection state, focused UI element, current tool, and mode/view options — all transient state describing how the user is *looking at* the document, not the document itself. The split underlies the file-I/O contract (Scene serializes; Session is reconstructed per launch) and the UI contract (Session-owned state never enters command history). Note: `interaction_data` (the solver's mouse-target buffer) is held on `Sketch.interaction_data` rather than on Session — this is acknowledged as a known asymmetry of the codebase and is not part of this requirement's scope; future granular CRs may revisit the placement.

---

#### REQ-FS-ARCH-004: ToolContext Facade

**Requirement (RS v3.0):** Tools shall interact with the application exclusively through a `ToolContext` instance and shall not hold a direct application reference (no `self.app` or equivalent passthrough). The facade exposes command execution, view and geometry queries, transient interaction-state management (selection, snap target, status, sound, drag-target injection via `set_interaction_data` / `update_interaction_target` / `clear_interaction_data`), and ProcessObject registration. Tools shall not mutate persistent model state — including the Sketch's `interaction_data` field — outside this facade.

**Evidence:** `flow-state/core/tool_context.py` defines the `ToolContext` class as the facade interface for tools. At qualified commit `ec450e2` it exposes:
- **Command execution:** `execute(command)` — the only authorized mutation channel; plus `discard()` for cancel paths and `create_coincident_command(...)` as a constraint-command factory that preserves the Air Gap.
- **View queries:** `zoom`, `pan`, `world_size`, `layout`, `mode`, `auto_atomize` — read-only access to camera and mode state.
- **Geometry queries:** `find_entity_at(...)`, `get_entity_type(...)`, `get_entity_render_data(...)`, `get_entity_point(...)`, `iter_entities()`, `find_snap(...)`, `get_active_material()` — read-only geometry helpers.
- **Transient interaction state:** `interaction_state`, `selection`, `snap_target`, `set_status(...)`, `play_sound(...)`, plus the drag-target facade `set_interaction_data(target_pos, entity_idx, *, handle_t=None, point_idx=None)` / `update_interaction_target(target_pos)` / `clear_interaction_data()` / `has_interaction_data()` (the writes route to `Sketch.interaction_data`; the data residence on Sketch is the REQ-FS-ARCH-003 known asymmetry).
- **ProcessObject registration:** `add_process_object(obj)` — registers Source/Sink and similar handles with the Sketch via Scene.
- **Constraint-builder access:** `constraint_builder` (read-only), `clear_constraint_ui()` (resets the builder via `reset()` and deactivates each constraint button).
- **Brush operations (BrushTool only):** `paint_particles(...)`, `erase_particles(...)`, `snapshot_particles()` (per REQ-FS-ARCH-001 documented exception).

The `Tool` base class in `flow-state/ui/tools.py` (lines 83-120) stores only `self.ctx` and `self.name` — there is no public `self.app` attribute. The module docstring at lines 12-58 explicitly documents the contract — "Tools receive a ToolContext (self.ctx). They have no direct application reference (CR-112)." (lines 13-14) — and the Tool class docstring at lines 84-89 points back to the module docstring as the authoritative access-contract reference. Subclass property accessors that previously reached through `self.app.scene.sketch` / `self.app.scene` now delegate through the facade via `self.ctx._get_sketch()` / `self.ctx._get_scene()`: the `GeometryTool` base class at lines 263-269 (whose `LineTool` / `CircleTool` / `RectTool` / `PointTool` subclasses inherit the property pair), and `SelectTool` at lines 727-733. The leading-underscore convention marks `_app`, `_get_sketch`, and `_get_scene` as internal-only — they are reserved for the facade's own delegation and for advanced operations such as command instantiation that need a sketch reference; tools are expected to confine their use of `_get_sketch` to those constrained sites and not introduce new direct uses.

---

### 4.2 Sketch and Solver (REQ-FS-CAD)

#### REQ-FS-CAD-001: Geometric Entities and Constraints

**Requirement:** The `Sketch` shall support lines and circles as primary geometric entities, and shall support constraints (e.g., parallel, perpendicular, equal, fixed) operating over those entities.

**Evidence:** `flow-state/model/sketch.py` defines the `Sketch` class as the container for entities (lines, circles), constraints, drivers, and materials. `flow-state/model/geometry.py` defines the entity primitive classes (`Line`, `Circle`, plus `Point` as an internal entity type used by ProcessObject handle registration and `.mdl` import — not exposed as a primary user-facing entity at this baseline). `flow-state/model/constraints.py` defines the concrete constraint classes (verified examples: `Coincident`, `Collinear`, `Midpoint`, `Length`, `Radius`, `EqualLength`, `Angle`, `FixedAngle`), with additional `HORIZONTAL` / `VERTICAL` constraint variants categorized by string type (see `Solver` unary-type set at `flow-state/model/solver.py:35`). Anchored/fixed semantics are carried as flags on entities themselves rather than as a standalone constraint class. The constraint factory at `flow-state/model/constraint_factory.py` is the construction surface for tools. "Lines and circles as primary" is a high-level invariant; granular per-entity-type and per-constraint-type requirements are deferred to subsequent CRs.

---

#### REQ-FS-CAD-002: PBD Solver with Hybrid Backend

**Requirement:** The geometric constraint solver shall enforce constraints using Position-Based Dynamics. It shall provide both a Python (legacy, OOP) backend and a Numba-compiled (kernel) backend, switchable at runtime.

**Evidence:** `flow-state/model/solver.py` defines the constraint-enforcement engine. The public entrypoint is `Solver.solve(constraints, entities, iterations, use_numba, interaction_data)` (line 18), which acts as a **dispatcher**: when `use_numba=True` it delegates to `Solver.solve_numba(...)` (line 55) — the kernel backend that flattens constraint state to numpy arrays and dispatches to JIT functions; when `use_numba=False` it executes an inline legacy OOP path that walks constraint objects in two phases (unary establish-truth constraints first, then binary propagate-between-entities constraints) and applies PBD corrections per object (lines 32-52). The runtime toggle is exposed via the `F9` global hotkey (handler in `flow-state/ui/input_handler.py` global-hotkey layer), letting users benchmark both backends live by flipping the `use_numba` argument. The kernel implementations live at `flow-state/model/solver_kernels.py` as `@njit` (Numba JIT) functions implementing the PBD math (constraint projection, length preservation, anchor enforcement, etc.). Both backends operate on the same constraint set and produce equivalent results for static cases; the Numba path is faster for large constraint counts.

---

#### REQ-FS-CAD-003: Interaction Servo

**Requirement (RS v3.0):** The mouse cursor shall be modeled as a temporary infinite-mass constraint target injected into the solver each frame, so that interactive dragging respects all other geometric constraints (length preservation, anchors, rotation about pivots). Tools shall route this injection through the `ToolContext` facade (`ctx.set_interaction_data` / `update_interaction_target` / `clear_interaction_data`) rather than mutating `Sketch.interaction_data` directly.

**Evidence:** At qualified commit `ec450e2`, tools route all interaction-data updates through the `ToolContext` facade. In `flow-state/ui/tools.py`:
- **Set sites:** Two call sites invoke `ctx.set_interaction_data(target_pos, entity_idx, ...)` to publish the drag target — at line 963 in EDIT-mode endpoint dragging (`point_idx=...` keyword form) and at line 1041 in body-drag-along-line (`handle_t=...` keyword form). The `handle_t` and `point_idx` parameters are keyword-only in the facade signature (`tool_context.py` `set_interaction_data` definition).
- **Update site:** One call site invokes `ctx.update_interaction_target(curr_sim)` at line 914 to update the target position during an active drag without re-publishing the entity index or handle parameter.
- **Clear sites:** Two call sites invoke `ctx.clear_interaction_data()` — at line 774 on tool-discard / cancel and at line 935 on drag end.
- **Read site:** One call site reads `ctx.has_interaction_data()` at line 913 to gate the drag-update branch.

The facade pair is defined on `flow-state/core/tool_context.py` and ultimately writes to `Sketch.interaction_data`, which remains the storage location (per the REQ-FS-ARCH-003 known-asymmetry note — `interaction_data` is a transient solver-target buffer held on Sketch). Routing through the facade satisfies the Air Gap principle as strengthened by REQ-FS-ARCH-004 in RS v3.0 (no direct `self.app` or `self.sketch` mutation by tools); the data residence on Sketch is the residual asymmetry. (Scene's own read of `interaction_data` at `core/scene.py` is a deliberate non-policed exception — Scene owns Sketch and is the orchestrator, not a tool.)

The solver at `flow-state/model/solver.py` reads `interaction_data` each iteration (`Solver._solve_interaction` at line 42) and treats the mouse target as a constraint with effectively infinite mass — the cursor position is applied as a hard constraint, and other geometric constraints (length, parallel, anchored, etc.) negotiate around it via PBD. This produces emergent physical behaviors: dragging an end of an anchored line causes the line to *rotate about its anchor* rather than translate; dragging a midpoint of a line with two anchored endpoints causes the line to *deform within length-preservation limits*. The solver runs every frame as long as either constraints exist OR the user is interacting (per the orchestration loop in `core/scene.py` `update()`).

---

### 4.3 Simulation (REQ-FS-SIM)

#### REQ-FS-SIM-001: Particle Engine

**Requirement:** The `Simulation` shall represent particles as flat NumPy arrays following Data-Oriented Design and shall integrate motion via Verlet integration with spatial hashing.

**Evidence:** `flow-state/engine/simulation.py` (lines 51–69) defines the particle state as a Structure-of-Arrays layout: `pos_x`, `pos_y`, `vel_x`, `vel_y`, `force_x`, `force_y`, `is_static`, `atom_sigma`, `atom_eps_sqrt`, plus tether arrays (see REQ-FS-SIM-002). The scalar arrays are 1-D NumPy arrays of length `self.capacity` (default 5000); `atom_color` is a `(capacity, 3)` 2-D RGB array. There are no per-particle Python objects in the hot path — this is Data-Oriented Design. `flow-state/engine/physics_core.py` `integrate_n_steps()` (lines 100–251) implements velocity Verlet integration in the kick-drift-kick form, including the LJ pair-force loop and second half-kick. `build_neighbor_list()` (lines 49–97) and `spatial_sort()` (line 254) provide a uniform-grid cell-list spatial hash, drastically reducing pair-collision search cost from O(N²) to O(N).

---

#### REQ-FS-SIM-002: Compiler Bridge

**Requirement:** The `Compiler` shall translate Sketch geometry into Simulation atoms — static atoms (`is_static=1`) for non-dynamic entities, and tethered atoms (`is_static=3`) for dynamic entities (the mechanism by which the Compiler enables two-way CAD↔Physics coupling). The Compiler shall rebuild these atoms when the Scene reports that geometry has changed.

**Evidence:** `flow-state/engine/compiler.py` defines the `Compiler` class with a `rebuild()` entrypoint that walks Sketch entities and discretizes them into Simulation atoms. Static atoms (`is_static=1`, written at line 275) are immobile particles representing walls and other non-dynamic geometry — they participate in collisions but never move. Tethered atoms (`is_static=3`, written at line 245) are particles bound to dynamic entities via `tether_entity_idx`, `tether_local_pos`, and `tether_stiffness` arrays in `simulation.py`; they are the mechanism by which the Compiler enables two-way CAD↔Physics coupling (entity geometry drives tether positions, and tether forces influence entity dynamics). `Scene.rebuild()` at `flow-state/core/scene.py` (line 421) triggers `compiler.rebuild()` when the orchestration loop detects topology changes; geometry-only changes use a faster `sync_entity_arrays`/`sync_static_atoms_to_geometry` path (`simulation.py` lines 370–520) without full recompilation.

---

### 4.4 User Interface (REQ-FS-UI)

#### REQ-FS-UI-001: Hierarchical UI Tree with Overlays

**Requirement:** The `UIManager` shall maintain a retained widget tree rooted at a single root container. Widgets that produce floating elements (dropdowns, tooltips) shall implement an `OverlayProvider` protocol so the manager can render overlays after the main tree for correct Z-ordering.

**Evidence:** `flow-state/ui/ui_manager.py` defines the `UIManager` class as the root of the retained widget tree. The tree is rendered by recursive traversal from the root container. `flow-state/ui/ui_widgets.py` defines the `OverlayProvider` protocol (line 31), implemented by widgets that need to spawn floating elements outside their normal Z-order — `Dropdown` is a concrete implementer (line 712). `UIManager` exposes `register_overlay`/`unregister_overlay` for managing the overlay set, and `_draw_overlays` runs after the main tree pass so overlays render on top regardless of their owning widget's depth. This protocol-based design means future floating-element widgets (e.g., context menus, tooltips with rich content) need only implement the protocol — no `UIManager` changes required.

---

#### REQ-FS-UI-002: Input Chain of Responsibility

**Requirement:** Input events shall be processed in a strict 4-layer order: System → Modal → Global → HUD. (Modal precedes Global so dialogs capture keyboard input before global hotkeys trigger.) When the modal stack changes (push or pop), interaction state shall be reset across the widget tree to prevent ghost inputs.

**Evidence:** `flow-state/ui/input_handler.py` (lines 115–136) implements `handle_input()` with the four layers in order: (1) **System** — quit, video resize; (2) **Modal** — checks the central modal stack in `AppController` and routes events to the topmost modal if any; (3) **Global** — hotkeys (Ctrl+Z undo, B brush, F9 backend toggle, etc.); (4) **HUD** — passes events to the UI tree, manages generic focus via `wants_focus()` / `on_focus_lost()`. An explicit comment at lines 124–125 documents the deliberate Modal-before-Global ordering: "Modals BEFORE global hotkeys! Dialogs need to capture keyboard input before hotkeys trigger." The `input_handler.py` module docstring at lines 1-16 (with the numbered protocol at lines 4-11) was corrected in CR-112 EI-8 (qualified at flow-state@`ec450e2`) to reflect this ordering; the corresponding correction to `CLAUDE.md` §6.2 is in scope of CR-112 EI-12. Modal-stack reset is implemented at `flow-state/app/app_controller.py` lines 59 and 75 (`push_modal` and `pop_modal`), both of which call `self.app.ui.root.reset_interaction_state()` to clear `is_hovered` / `is_clicked` / `hot` flags across the widget tree, preventing the click-through-modal-close ghost-input class of bug.

---

### 4.5 Application Shell (REQ-FS-APP)

#### REQ-FS-APP-001: Execution Modes

**Requirement:** The application entry point (`main.py`) shall support three execution modes selectable via CLI: a Dashboard mode (launcher GUI), a Simulation mode (active physics), and a Builder mode (CAD editor without active physics). The specific flag values are an implementation detail of `main.py`'s argparse configuration and may evolve under change control.

**Evidence:** `flow-state/main.py` (line 20) declares `argparse` with `choices=["dashboard", "sim", "builder"]` for the `--mode` argument. The three modes are dispatched to distinct entry-point flows: dashboard launches a launcher GUI for selecting projects; `sim` launches the main simulation mode with active physics integration; and `builder` launches a CAD-only editor (geometry creation and constraint editing) without the physics step running. The mode determines which subset of subsystems are instantiated and whether the physics integration step in `Scene.update()` is invoked. The current flag spelling `"sim"` is the implementation choice; the requirement is satisfied by the existence of the three conceptual modes with CLI selection, not by any specific flag string.

---

## 5. Qualified Baseline

| Attribute | Value |
|-----------|-------|
| Requirements Spec | SDLC-FLOW-RS v3.0 |
| Repository | whharris917/flow-state |
| Branch | main (at merge of `cr-114-resize-world-ux`) |
| Commit | f69455f |
| Commit message | "CR-114 EI-9 fix: Restore input field on resize cancel" |
| System Release | FLOW-STATE-1.2 |
| Verification method | Qualitative-proof inspection (no automated test suite at v1.2) |

The qualified-baseline commit `f69455f` is the qualified state of `flow-state` after CR-114 (Resize World UX fixes and brush_tool orphan deletion). All twelve requirements in SDLC-FLOW-RS v3.0 are verified by inspection against the source at this commit; CR-114 added no requirements and modified no verified surfaces beyond the single REQ-FS-SIM-002 line-citation re-anchor (sync_* methods shifted from line 358 to line 370 due to the resize_world body expansion). The strengthened REQ-FS-ARCH-004 and REQ-FS-CAD-003 from CR-112 remain satisfied unchanged at this commit (Tool subclass property accessors and ToolContext facade surface untouched in CR-114). The prior qualified baselines `FLOW-STATE-1.0` at flow-state@a26f7fb (under RS v1.0 / RTM v1.0) and `FLOW-STATE-1.1` at flow-state@ec450e2 (under RS v3.0 / RTM v2.0) are retained as historical record. Future CRs that modify `flow-state` code will follow the standard execution-branch workflow (SOP-005 §7.1) and will update this RTM with the new qualified baseline at merge time.

---

## 6. References

- **CR-111:** Adopt Flow State into QMS Governance — the authorizing change record for the inaugural RTM v1.0 and the FLOW-STATE-1.0 qualified baseline.
- **CR-112:** ToolContext Migration Completion + Documentation Reconciliation — the authorizing change record for RTM revision v2.0 and the FLOW-STATE-1.1 qualified baseline; strengthened REQ-FS-ARCH-004 and REQ-FS-CAD-003.
- **CR-114:** Resize World UX fixes and brush_tool orphan deletion — the authorizing change record for this RTM revision (v3.0) and the FLOW-STATE-1.2 qualified baseline. No requirements added or modified; the only RTM body change is the REQ-FS-SIM-002 line-citation re-anchor (sync_* methods 358 → 370 due to resize_world body expansion).
- **SDLC-FLOW-RS:** Flow State Requirements Specification v3.0 — the requirements verified here.
- **SDLC-CQ-RTM:** claude-qms Requirements Traceability Matrix — pattern reference for inspection-only verification.
- **Quality-Manual/10-SDLC.md:** Verification types (Unit Test, Qualitative Proof, Verification Record) and qualification semantics.
- **Quality-Manual/09-Code-Governance.md:** Qualified-commit and System-Release mechanics.

---

**END OF DOCUMENT**
