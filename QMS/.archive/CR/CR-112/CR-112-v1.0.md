---
title: ToolContext Migration Completion + Documentation Reconciliation
revision_summary: 'v0.3: Address QA second-cycle request-updates findings. (A) Sync
  §2.3 Files Affected with §7.1 — corrected tools.py count (~150 → 99), source_tool.py
  count (~28 → 25); §2.3 now lists property-accessor migration, BrushTool ParticleBrush
  replacement, _clear_constraint_ui body replacement, ctx.clear_constraint_ui fix,
  set_interaction_data signature extension, has_interaction_data addition. (B) Drop
  wrong dependency claim in §5.2 — SourceTool does not call clear_constraint_ui; clause
  removed from EI-5 description. (C) Address tu_ui finding #5 (cached-sub-object audit)
  — added §5.2 audit note documenting that grep finds only self.app cached in tools.py:87
  and source_tool.py:33; no self.session, self.layout, self.constraint_builder caches
  exist at the FLOW-STATE-1.0 baseline. v0.2 changes (subclass property migration,
  ctx.clear_constraint_ui fix, signature/call consistency) all preserved.'
---

# CR-112: ToolContext Migration Completion + Documentation Reconciliation

## 1. Purpose

Complete the ToolContext migration that CR-2026-004 (Phase J) left partially finished, and reconcile the CLAUDE.md technical guide with the current state of the `flow-state/` codebase. Together these close out the Air Gap as a fully-enforced architectural principle (no tool holds a direct app reference; no tool mutates `Sketch` state outside the ToolContext facade), fix a user-visible crash on the Source tool that surfaced on the first post-CR-111 attempt to use Flow State, and bring the project's authoritative architecture document back into alignment with the code reviewers will read during future CRs.

This is the first code CR against `flow-state/` after CR-111 closed it under SDLC governance. It will exercise the full code-CR machinery (execution branch, RS/RTM update cycles, qualified commit, merge gate, baseline tag advancement) for the first time on this system.

---

## 2. Scope

### 2.1 Context

Independent improvement identified during development. CR-111 closed on 2026-04-30 with `FLOW-STATE-1.0` as the qualified baseline. The first attempt to use Flow State after closure (creating a Source via the Source tool in the Simulation viewport) crashed:

```
AttributeError: 'ToolContext' object has no attribute 'scene'
  at ui/source_tool.py:201 in _get_snapped: self.app.scene.sketch.entities
```

Diagnosis: `SourceTool` was never migrated to the ToolContext-receiving signature established by CR-2026-004 Phase J. It uses `__init__(self, app)` and treats the parameter as the app reference. But `FlowStateApp.init_tools` at `flow-state/app/flow_state_app.py:217` passes a `ToolContext`, not the app — so every `self.app.scene.X` reach in `SourceTool` is unreachable.

CR-111's Execution Summary (§11) listed three queued follow-ups in this same architectural area: (1) the SourceTool fix would be one of them in spirit, though not yet known as a crash at that time, (2) Tool base-class `self.app = ctx._app` backward-compat passthrough cleanup, and (3) `ctx.set_interaction_data` adoption-or-removal. CR-111 also surfaced three CLAUDE.md narrative drift items during qualitative-proof RTM authoring: §2.3 (interaction_data ownership), §6.2 (input layer order), §7 (orchestration loop step count). All five concerns are bundled here because they are thematically the same work: finishing the ToolContext migration and aligning the architecture document with reality.

- **Parent Document:** None

### 2.2 Changes Summary

1. Migrate `SourceTool` to inherit from `Tool` and use only `self.ctx`; replace all `self.app.X` reaches.
2. Migrate every other tool in `ui/tools.py` (BrushTool, SelectTool, LineTool, RectTool, CircleTool, PointTool) off `self.app`; all direct reaches and the two `@property sketch` / `@property scene` accessor bodies go through `self.ctx`. Replace BrushTool's cached `ParticleBrush(self.app.sim)` with direct `ctx.paint_particles()` / `ctx.erase_particles()` calls.
3. Retire the `self.app = ctx._app` backward-compat passthrough at `ui/tools.py:87`. Tools have only `self.ctx` after this CR.
4. Adopt `ctx.set_interaction_data` / `update_interaction_target` / `clear_interaction_data` at the four direct `sketch.interaction_data` mutation sites in `ui/tools.py`.
5. ToolContext API changes: add `add_process_object(obj)` (used by SourceTool); add `has_interaction_data()` query; extend `set_interaction_data` signature with keyword-only `point_idx`; **fix existing `clear_constraint_ui()`** to call `builder.reset()` and use `btn.active` (previously partial manual sets and `btn.is_active` — the latter would silently fail because the actual button attribute is `active`).
6. Update stale module docstrings: `ui/input_handler.py:4-9` (claims 5-layer protocol; actual is 4) and `engine/compiler.py:7` ("Data flow is ONE-WAY" wording predates tethered atoms / two-way coupling).
7. Update CLAUDE.md §2.3, §6.2, §7 to match current code; targeted audit pass for any other drift surfaced while editing those sections.
8. Update SDLC-FLOW-RS to reflect that `interaction_data` mutations route through the facade (was previously documented as the acknowledged exception).
9. Update SDLC-FLOW-RTM with new qualitative-proof rows for the affected REQs at the new qualified commit.
10. Apply annotated git tag `FLOW-STATE-1.1` to the merge commit on `flow-state/main`; advance the qualified baseline.

### 2.3 Files Affected

- `flow-state/ui/source_tool.py` — Inherit from `Tool`; replace 25 `self.app.X` reaches with `self.ctx.X` equivalents; use `ctx.create_coincident_command()` and `ctx.add_process_object()`; remove unused `AddConstraintCommand` and `Coincident` imports.
- `flow-state/ui/tools.py` — Replace 99 `self.app.X` reaches with `self.ctx.X` equivalents; rewrite `@property sketch` and `@property scene` bodies (at lines 277-283 and 741-747) to delegate through `ctx._get_sketch()` / `ctx._get_scene()`; replace `BrushTool`'s cached `ParticleBrush` with direct `ctx.paint_particles()` / `ctx.erase_particles()` calls; migrate 4 `sketch.interaction_data = X` sites to `ctx.set_interaction_data` / `update_interaction_target` / `clear_interaction_data`; replace `_clear_constraint_ui` body with `ctx.clear_constraint_ui()` plus separate selection clearing; remove `self.app = ctx._app` line at 87.
- `flow-state/core/tool_context.py` — Add `add_process_object(obj)` method; add `has_interaction_data()` query; extend `set_interaction_data` signature with keyword-only `point_idx`; **fix existing `clear_constraint_ui()`** to call `builder.reset()` (was partial manual sets) and use `btn.active` (was `btn.is_active`).
- `flow-state/ui/input_handler.py` — Replace stale 5-layer protocol docstring (lines 4-9) with accurate 4-layer description and rationale (Modals before Global so dialogs capture keys before hotkeys trigger).
- `flow-state/engine/compiler.py` — Replace "Data flow is ONE-WAY: Sketch → Simulation (never reverse)" wording (lines 7) with accurate description acknowledging tethered atoms and two-way coupling.
- `CLAUDE.md` — §2.3 (move `interaction_data` callout out of Session); §6.2 (reorder input layers to System → Modals → Global → HUD); §7 (replace 5-step list with 8-phase actual order); targeted audit for additional drift in §5.4 and §5.5.
- `QMS/SDLC-FLOW/SDLC-FLOW-RS.md` — New revision touching the REQ(s) related to ToolContext / interaction_data routing.
- `QMS/SDLC-FLOW/SDLC-FLOW-RTM.md` — New revision with re-anchored qualitative-proof rows at the new qualified commit.
- `flow-state` (submodule) — execution branch `cr-112-toolcontext-completion` for the code work; merge commit on `main` after RS/RTM EFFECTIVE; annotated tag `FLOW-STATE-1.1` at the merge commit.
- `.claude/PROJECT_STATE.md` — Update SDLC-FLOW-RS / SDLC-FLOW-RTM rows to v2.0; advance Qualified Baselines row to `CLI-18.0 + FLOW-STATE-1.1`; remove CR-112 from Open QMS Documents on closure.

---

## 3. Current State

`flow-state` is under formal SDLC governance as of CR-111 (CLOSED 2026-04-30). The qualified baseline is `FLOW-STATE-1.0` at `flow-state/main@a26f7fb`. SDLC-FLOW-RS v1.0 and SDLC-FLOW-RTM v1.0 are EFFECTIVE.

The ToolContext facade exists at `flow-state/core/tool_context.py` and exposes the methods most tools need (command execution, view-state queries, interaction-state management, snap detection, brush operations, coincident-constraint factory, and an unused `set_interaction_data` / `update_interaction_target` / `clear_interaction_data` family). The `Tool` base class at `flow-state/ui/tools.py:73` accepts a `ctx` parameter and stores both `self.ctx` and `self.app = ctx._app` (the latter as backward-compat during CR-2026-004 Phase J migration).

In practice, most tools still reach through `self.app.X` for the bulk of their state queries (camera, mode, selection, status, sound). `SourceTool` was never migrated at all — it does not inherit from `Tool`, does not capture the ctx, and treats the constructor's `ctx` argument as the app, causing a crash on first event (mouse motion or click) inside the Source tool. `SelectTool` and others mutate `sketch.interaction_data` directly via `self.app.scene.sketch.interaction_data = X` (or `self.sketch.interaction_data = X` where `self.sketch` is cached) at four sites in `ui/tools.py`, leaving the existing `ctx.set_interaction_data` facade unused.

CLAUDE.md §2.3 lists `interaction_data` under the Session's transient state, but `interaction_data` actually lives on the Sketch (`flow-state/model/sketch.py:33`). §6.2 documents the input chain as `System → Global → Modal → HUD`, but the actual chain at `flow-state/ui/input_handler.py:108-129` is `System → Modals → Global → HUD`. §7 lists the orchestration loop as 5 phases, but `Scene.update` at `flow-state/core/scene.py:265-345` runs 8 distinct phases. Module docstrings in `ui/input_handler.py:4-9` (claims 5-layer protocol) and `engine/compiler.py:7-8` ("Data flow is ONE-WAY") are similarly out of date.

### 3.1 Audit table — `self.app.X` reaches in tools (target categories)

Static audit across `ui/tools.py`, `ui/source_tool.py`. Counts are exact unless prefixed with `~`.

| Target | Reaches | Notes |
|--------|---------|-------|
| `self.app.session.X` (camera, selection, status, mode, state, auto_atomize, constraint_builder, focused_element) | ~85 in tools.py + ~14 in source_tool.py | All have `ctx.X` equivalents already exposed (zoom, pan, mode, set_status, selection, snap_target, interaction_state, etc.). |
| `self.app.scene.X` (sketch, execute, add_process_object) | ~6 in tools.py + ~5 in source_tool.py | `ctx.execute(cmd)`, `ctx._get_sketch()` exist; `add_process_object` is one new method (see §5.4). |
| `self.app.sim.X` (world_size, snapshot, **constructor argument** — see below) | ~14 in tools.py + ~5 in source_tool.py | `ctx.world_size` exposed; `ctx.snapshot_particles()` exposed. **Special case:** `BrushTool` at `tools.py:153` constructs `ParticleBrush(self.app.sim)` — passing the full Simulation as a constructor argument, not a property reach. Cleaner path: use existing `ctx.paint_particles()` / `ctx.erase_particles()` directly rather than caching a local `ParticleBrush`. |
| `self.app.sound_manager.play_sound(...)` | 2 | `ctx.play_sound(sound_id)` already exists at `tool_context.py:193-195`. |
| `self.app.input_handler.constraint_btn_map` | 1 | `ctx.clear_constraint_ui()` exists at `tool_context.py:474-486` but **needs a fix** (see §5.4) — current implementation uses `btn.is_active` instead of `btn.active`, and manually clears `pending_type`/`snap_target` instead of calling `builder.reset()`. |
| `self.app.layout` | 2 | `ctx.layout` already exposed at `tool_context.py:118-120`. |
| `self.app.scene.sketch.interaction_data` (mutation, in tools.py) | 4 | Four sites; migrate to `ctx.set_interaction_data` / `update_interaction_target` / `clear_interaction_data`. |
| `self.app.X` total (direct reaches) | 99 in tools.py + 25 in source_tool.py | Verified via grep at the FLOW-STATE-1.0 baseline. |

**Hidden coupling — subclass property accessors.** Beyond the direct `self.app.X` reaches above, `tools.py` defines two `@property` accessors that read through `self.app` and are used as `self.sketch` / `self.scene` throughout subclass methods:

| Location | Property bodies | Callsites that read through them |
|----------|-----------------|----------------------------------|
| `tools.py:277-283` (in geometry-creation tool intermediate base, used by LineTool/RectTool/CircleTool/PointTool) | `@property sketch: return self.app.scene.sketch` and `@property scene: return self.app.scene` | ~22 secondary callsites of `self.sketch.*` / `self.scene.*` across the geometry-creation subclasses |
| `tools.py:741-747` (in `SelectTool`) | Same two properties duplicated | ~18 secondary callsites in `SelectTool` |

After EI-7 deletes the `self.app = ctx._app` passthrough, both property bodies break (they read `self.app.scene.X`), and every secondary callsite throws `AttributeError`. EI-6 must therefore migrate the property bodies as well — the cleanest path is to rewrite the property bodies to delegate through `self.ctx._get_sketch()` / `self.ctx._get_scene()` (preserves callsite syntax; no callsite changes needed). See §5.2 for the migration step.

**Key takeaway:** With `ctx.add_process_object` added (§5.4), `ctx.clear_constraint_ui` fixed (§5.4), the `set_interaction_data` signature extended (§5.3.1), and the two property accessors migrated to delegate through ctx, ToolContext exposes everything tools need without expanding scope further.

---

## 4. Proposed State

After execution, no tool in `flow-state/ui/` holds a direct app reference; every tool uses only its `self.ctx` (a `ToolContext`). Tools route every state mutation — including `sketch.interaction_data` writes — through the `ctx` facade. The `Tool` base class no longer carries the `self.app = ctx._app` passthrough. `SourceTool` inherits from `Tool` and works correctly when a Source is created in either Simulation or Builder mode.

Module docstrings in `ui/input_handler.py` and `engine/compiler.py` describe the actual current behavior. CLAUDE.md §§2.3, 6.2, 7 — and any other sections surfaced during a targeted drift audit — match the code reviewers will read during future CRs.

`SDLC-FLOW-RS v2.0` is EFFECTIVE, with the REQ(s) related to ToolContext / interaction_data updated to reflect the closed Air Gap. `SDLC-FLOW-RTM v2.0` is EFFECTIVE with re-anchored qualitative-proof rows at the new qualified commit on `flow-state/main`. `FLOW-STATE-1.1` is the qualified baseline.

---

## 5. Change Description

### 5.1 SourceTool migration to ToolContext

`SourceTool` is rewritten to inherit from `Tool` and use `self.ctx` exclusively. The class signature changes from `def __init__(self, app)` to `def __init__(self, ctx)`, and the constructor calls `super().__init__(ctx, name="Source")` so the base class sets `self.ctx`. All 25 `self.app.X` reaches are replaced with their `self.ctx.X` equivalents per the audit table in §3.1.

Two specific substitutions:

- `self.app.scene.add_process_object(source)` → `self.ctx.add_process_object(source)` (uses the new ctx method added in this CR).
- `Coincident(center_idx, 0, snap_entity, snap_pt)` constructed inline at lines 173-179 is replaced by `self.ctx.create_coincident_command(center_idx, 0, snap_entity, snap_pt)` and the resulting command is dispatched via `self.ctx.execute(cmd)` if non-None.

The `Source.get_handle_indices(sketch)` call needs the sketch reference; the simplest path is `self.ctx._get_sketch()` (the marked-for-internal-use accessor at `tool_context.py:559-569`). This is the same pattern other tools use for command construction.

After the migration, `from core.commands import AddConstraintCommand` and `from model.constraints import Coincident` at the top of `source_tool.py` become unused (the `Coincident` factory + AddConstraintCommand wrapping is encapsulated by `ctx.create_coincident_command()`). Remove the unused imports as part of EI-5 to avoid scar tissue.

### 5.2 tools.py migration to `self.ctx`

Every `self.app.X` reach across the seven tools in `ui/tools.py` (Tool base + SelectTool, BrushTool, LineTool, RectTool, CircleTool, PointTool) is replaced with the corresponding `self.ctx.X` form. The substitutions are mechanical for the direct reaches because every category in the audit table has a ctx equivalent already exposed.

**Subclass property accessor migration (per §3.1).** The two `@property` accessors at `tools.py:277-283` and `tools.py:741-747` are rewritten so their bodies delegate through ctx rather than reading `self.app`:

```python
@property
def sketch(self):
    return self.ctx._get_sketch()

@property
def scene(self):
    return self.ctx._get_scene()
```

This preserves the existing `self.sketch.*` / `self.scene.*` callsite syntax across ~40 subclass callsites — no callsite-by-callsite migration of those is needed. The properties become thin wrappers over the ctx accessors that exist for command instantiation.

**BrushTool's ParticleBrush instantiation (per §3.1).** `BrushTool.__init__` at `tools.py:153` currently constructs `self._brush = ParticleBrush(self.app.sim)` and uses `self._brush.paint(...)` / `self._brush.erase(...)` in its mouse handlers. The migration replaces this caching pattern with direct calls to `self.ctx.paint_particles(...)` / `self.ctx.erase_particles(...)`, which already delegate to the Scene's owned `ParticleBrush`. This removes the local `_brush` attribute and the `from engine.particle_brush import ParticleBrush` import from `tools.py`. End behavior is unchanged because both paths route through the same Scene-owned brush.

**`ctx.clear_constraint_ui` callsite (per §3.1).** The body of `_clear_constraint_ui` at `tools.py:1378-1384` is reduced to a `self.ctx.clear_constraint_ui()` call (after the fix in §5.4) plus the separate `selection.walls.clear()` / `selection.points.clear()` calls. The selection-clearing stays inline because selection is a separable concern from constraint-UI state.

After all the above, the `self.app = ctx._app` line at `ui/tools.py:87` is deleted.

**Pre-deletion audit for cached app sub-objects.** A grep over the FLOW-STATE-1.0 baseline for `self.<X> = ` in `flow-state/ui/tools.py` and `flow-state/ui/source_tool.py` (where `<X>` covers `session`, `layout`, `constraint_builder`, `sound_manager`, `input_handler`, `sim`, `scene`, `sketch`, `app`) returns exactly two matches: `tools.py:87` (`self.app = ctx._app`) and `source_tool.py:33` (`self.app = app`). Both are explicitly retired by this CR. There are **no** cached `self.session`, `self.layout`, `self.constraint_builder`, etc. sub-objects that would silently break after the passthrough is removed. The migration scope enumerated in §3.1 is therefore complete.

The migration is staged in three EIs (see §10):

1. **EI-5** migrates SourceTool to depend on the `ctx.add_process_object()` method that EI-4 adds. (SourceTool does not consume `clear_constraint_ui`; that method is consumed only by `tools.py` in EI-6.) This pulls SourceTool's fix forward independent of the rest of `tools.py`.
2. **EI-6** migrates the remaining tools in `tools.py` — direct `self.app.X` reaches, the two property-accessor bodies, the BrushTool ParticleBrush pattern, the `_clear_constraint_ui` callsite, and the four `interaction_data` mutation sites (per §5.3).
3. **EI-7** deletes the `self.app = ctx._app` line. Smoke-test confirms no remaining reach hits the deleted attribute.

Order matters: deleting the passthrough before completing the per-tool migration would crash any unmigrated tool on first event.

### 5.3 Adoption of `ctx.set_interaction_data`

The four direct mutation sites in `ui/tools.py` are migrated to the existing facade:

- `tools.py:788` (clear on cancel) → `self.ctx.clear_interaction_data()`
- `tools.py:950` (clear on release) → `self.ctx.clear_interaction_data()`
- `tools.py:978` (set on point edit drag start) → `self.ctx.set_interaction_data(target_pos, entity_idx, point_idx=point_idx)` *(keyword args per §5.3.1)*
- `tools.py:1061` (set on entity body drag start) → `self.ctx.set_interaction_data(target_pos, entity_idx, handle_t=t)` *(keyword args per §5.3.1)*

The one read site at `tools.py:928` (`if self.sketch.interaction_data is not None:`) becomes `if self.ctx.has_interaction_data():` — a new query method to keep the call site readable.

**Deliberate non-policed exception:** `Scene.update` at `scene.py:324` continues to read `sketch.interaction_data` directly. This is intentional and **not** policed by this CR — Scene is not a tool, it owns the model, and the Air Gap principle is about UI-layer mutation of model state, not about Scene's internal model orchestration. The post-CR architecture is: tools mutate `interaction_data` only through the ctx facade; Scene/solver read it directly as a transient solver-input field.

#### 5.3.1 Note on `set_interaction_data` signature

The current `ToolContext.set_interaction_data(target_pos, entity_idx, handle_t)` at `tool_context.py:427-444` does not accept `point_idx`, but tools at `tools.py:978` set `point_idx` (for the EDIT-mode single-endpoint drag). The signature is therefore extended to:

```python
def set_interaction_data(self, target_pos, entity_idx, *, handle_t=None, point_idx=None):
```

The two new arguments are **keyword-only** (after `*`). The two `set` callsites in §5.3 above use keyword form for both `point_idx` and `handle_t` accordingly:

```python
# Point-edit drag start
self.ctx.set_interaction_data(target_pos, entity_idx, point_idx=point_idx)

# Entity-body drag start
self.ctx.set_interaction_data(target_pos, entity_idx, handle_t=t)
```

The underlying dict is assembled to match the shape that the solver already consumes at `model/solver.py:223-248`. This is a backward-compatible signature extension (no existing callers; the method is currently unused).

### 5.4 ToolContext API changes

**New methods:**

```python
def add_process_object(self, obj) -> None:
    """Add a ProcessObject (Source, Sink, etc.) to the scene."""
    self._app.scene.add_process_object(obj)

def has_interaction_data(self) -> bool:
    """True if a drag interaction is currently active."""
    return self._app.scene.sketch.interaction_data is not None
```

**Fix to existing `clear_constraint_ui()`** (per tu_ui v0.1 finding). The current implementation at `tool_context.py:474-486` has two defects:

1. It manually sets `builder.pending_type = None` and `builder.snap_target = None` — but `ConstraintBuilder.reset()` clears more state than this (target_walls, target_points, etc.). The current ctx implementation is incomplete.
2. It uses `btn.is_active = False` — but the actual button attribute is `btn.active` (verified against existing `tools.py:1383-1384`, `input_handler.py`).

The fix replaces the body with:

```python
def clear_constraint_ui(self):
    """Clear the constraint-builder pending state and the constraint-button visual state."""
    self._app.session.constraint_builder.reset()
    if hasattr(self._app, 'input_handler') and self._app.input_handler:
        for btn in self._app.input_handler.constraint_btn_map.keys():
            btn.active = False
```

After the fix, the `_clear_constraint_ui` method body in `tools.py:1378-1384` is replaced by `self.ctx.clear_constraint_ui()` plus the separate `selection.walls.clear()` / `selection.points.clear()` calls (per §5.2).

**Signature extension** (per §5.3.1): `set_interaction_data` gains keyword-only `point_idx=None` parameter.

No other API expansion is permitted by this CR (out of scope per §2).

### 5.5 Stale module docstrings

`flow-state/ui/input_handler.py` lines 4-9 currently read:

```
Handles all keyboard and mouse input using a 5-layer protocol:
1. System (Quit, Resize)
2. Global (Hotkeys)
3. Modals (Context Menu, Dialogs)
4. HUD (Panel Tree - NOW INCLUDES SCENE)
```

The implementation is 4 layers in the order System → Modals → Global → HUD (verified in `_attempt_handle_*` calls at lines 113-129). The docstring is rewritten to match the code, with the rationale for Modals-before-Global preserved (so dialogs capture keys before global hotkeys trigger; the inline comment at lines 117-119 carries this reasoning today).

`flow-state/engine/compiler.py` lines 7-8 currently read:

```
Data flow is ONE-WAY: Sketch → Simulation (never reverse)
```

Tethered atoms (`is_static=3`) introduced by the dynamic-entity feature establish a two-way coupling: the compiler still writes to the simulation (no reverse data flow at the *Compiler* level), but particles and entities exert mutual force on each other during the physics step (the physics layer establishes the two-way coupling that the compiler enables). The docstring is rewritten to clarify: the *Compiler* itself is one-way (CAD → atom arrays), but the system as a whole becomes two-way once tethered atoms participate in physics. This preserves the original architectural claim while removing the misleading absolute "never reverse" wording.

### 5.6 CLAUDE.md updates

#### 5.6.1 §2.3 The Session

The Session bullet list currently includes:

> * **Interaction Data:** Live data for the constraint solver regarding mouse drag targets.

This is incorrect — `interaction_data` is a field on `Sketch` (`flow-state/model/sketch.py:33`), not on `Session`. The bullet is removed from §2.3 and a corrected statement is added to §5.1 (The Sketch & Solver) noting that the Sketch holds a transient `interaction_data` field used by the solver as the "User Servo" for mouse-driven dragging.

#### 5.6.2 §6.2 Input Chain of Responsibility

The current numbering reads:

> 1. **System Layer**
> 2. **Global Layer**
> 3. **Modal Layer (Blocking)**
> 4. **HUD Layer (Generic Focus)**

The actual order in `input_handler.py:113-129` is **System → Modals → Global → HUD**. The numbering is corrected and a brief rationale added: dialogs need to capture keyboard input before global hotkeys trigger, which is why Modals precede Global.

#### 5.6.3 §7 The Orchestration Loop

The current 5-step list is replaced with the 8-phase order from `scene.py:265-345`:

1. Topology check (full rebuild if `_topology_dirty`)
2. Driver update (animate constraint values)
3. Sync entity arrays (fast path) and sync static atoms to geometry
4. Physics coupling sub-loop (clear forces, apply tether forces, integrate dynamic entities)
5. Constraint solve (PBD; runs if constraints exist OR `interaction_data` is set)
6. Post-constraint sync (re-sync entity arrays and static atoms after solver moved geometry)
7. Process objects (Sources emit, Sinks absorb, etc.)
8. Physics step (Numba `integrate_n_steps` over particle arrays)

Phases 3, 4, 6, 7 are new since the original 5-step description was written; phases 1 and 8 are renamed/reordered.

#### 5.6.4 Targeted audit pass

While editing §§2.3, 6.2, 7, the entire CLAUDE.md technical guide (§§1–9) is read against current code state. Any additional drift surfaced is fixed in the same pass. Likely candidates already noted: §5.4 Compiler should mention static-vs-tethered atom split (rather than describing only static particles); §5.5 ToolContext should drop the `self.app = ctx._app` reference once that line is removed in this CR. The audit is bounded by "anything else discovered while doing §§2.3, 6.2, 7" rather than open-ended.

### 5.7 SDLC-FLOW-RS revision

Touched requirements (exact set determined at execution time):

- **REQ-FS-ARCH-004 (ToolContext Facade):** Strengthened to explicitly state that tools shall not hold a direct app reference, and that `interaction_data` mutations shall flow through the facade.
- **REQ-FS-CAD-003 (Interaction Servo):** May need a wording adjustment to reflect that the injection path is `ctx.set_interaction_data` (was previously documented as direct mutation, an acknowledged exception in CR-111's RTM).

The exact wording is determined at execution time after reading the current REQ text. Document version advances v1.0 → v2.0.

### 5.8 SDLC-FLOW-RTM revision

Qualitative-proof rows whose cited file:line ranges shift are re-anchored to the new qualified commit (the merge commit on `flow-state/main` after the execution branch merges). Rows for the affected REQs are updated to describe the new behavior (closed Air Gap; facade-routed interaction_data). The Qualified Baseline section is updated to record the new commit hash, and `System Release: FLOW-STATE-1.1`. Document version advances v1.0 → v2.0.

---

## 6. Justification

The Lead has just shifted active focus to Flow State for an upcoming working vacation. The first interaction with the application after CR-111's closure produced a hard crash (SourceTool), which would block any meaningful Flow State session until fixed. The crash is also a governance signal: it demonstrates that ToolContext migration scope was incomplete in CR-2026-004 — a finding worth resolving structurally rather than patching one tool at a time.

- **Bundling makes architectural sense.** All five concerns (SourceTool fix, tools.py migration, `self.app` retirement, interaction_data facade adoption, and the related CLAUDE.md drift) are different projections of the same underlying work: finishing the Air Gap as a fully-enforced principle. Splitting into five small CRs would multiply review overhead without improving comprehension.
- **The Air Gap is structurally important.** Per CLAUDE.md §3.1, the Air Gap is the architectural commitment that allows the Command Pattern to be the single source of truth for state mutation — which in turn enables reliable undo/redo and replay. Letting tools mutate `Sketch.interaction_data` directly leaves a hole that would gradually widen if more tools learned the same pattern.
- **CLAUDE.md is the document agents and reviewers read.** Each CR-111 review cycle surfaced a piece of CLAUDE.md drift that had to be corrected for the RTM to be accurate. Letting the drift persist guarantees the same correction work happens on every future CR — a tax that compounds.
- **Doing this first is the right ordering.** With the Air Gap closed and CLAUDE.md aligned, every subsequent Flow State CR (gameplay, CAD, sim) starts from a clean architectural baseline rather than dragging accumulated migration debt forward.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `flow-state/ui/source_tool.py` | Modify | Inherit from `Tool`; replace 25 `self.app.X` reaches with `self.ctx.X`; use `ctx.create_coincident_command()` and `ctx.add_process_object()`; remove unused `AddConstraintCommand` / `Coincident` imports after substitution. |
| `flow-state/ui/tools.py` | Modify | Replace 99 `self.app.X` reaches with `self.ctx.X`; rewrite `@property sketch` and `@property scene` bodies (at lines 277-283 and 741-747) to delegate through `ctx._get_sketch()` / `ctx._get_scene()`; replace `BrushTool`'s cached `ParticleBrush` with direct `ctx.paint_particles()` / `ctx.erase_particles()` calls; migrate 4 `interaction_data` mutation sites to facade; replace `_clear_constraint_ui` body with `ctx.clear_constraint_ui()` + separate selection clearing; delete `self.app = ctx._app` line at 87. |
| `flow-state/core/tool_context.py` | Modify | Add `add_process_object(obj)` method; add `has_interaction_data()` query; extend `set_interaction_data` signature with keyword-only `point_idx`; **fix existing `clear_constraint_ui()`** to call `builder.reset()` and use `btn.active` (was using partial manual sets and `btn.is_active`). |
| `flow-state/ui/input_handler.py` | Modify | Replace 5-layer-protocol module docstring with accurate 4-layer description. |
| `flow-state/engine/compiler.py` | Modify | Replace "Data flow is ONE-WAY" wording with accurate two-way-via-tether description. |
| `CLAUDE.md` | Modify | §2.3 (move interaction_data callout out of Session); §6.2 (reorder input layers); §7 (replace 5-step list with 8-phase list); targeted audit pass. |
| `QMS/SDLC-FLOW/SDLC-FLOW-RS.md` | Modify | Revision v1.0 → v2.0 touching REQ-FS-ARCH-004 and possibly REQ-FS-CAD-003. |
| `QMS/SDLC-FLOW/SDLC-FLOW-RTM.md` | Modify | Revision v1.0 → v2.0 with re-anchored rows; new qualified commit; System Release `FLOW-STATE-1.1`. |
| `.claude/PROJECT_STATE.md` | Modify | Update SDLC-FLOW-RS / RTM to v2.0; advance Qualified Baselines row to `CLI-18.0 + FLOW-STATE-1.1`; remove CR-112 from Open QMS Documents on closure. |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-FLOW-RS | Modify | New revision v2.0; touches ToolContext-related REQs. |
| SDLC-FLOW-RTM | Modify | New revision v2.0; re-anchored rows; new qualified commit. |
| CLAUDE.md | Modify | §§2.3, 6.2, 7 narrative drift correction + targeted audit. |
| PROJECT_STATE.md | Modify | SDLC table version bump; Qualified Baselines advance; Open QMS Documents update on closure. |

### 7.3 Other Impacts

- **`flow-state` submodule:** New execution branch `cr-112-toolcontext-completion`, merged to `main` via regular merge commit (no squash). Annotated tag `FLOW-STATE-1.1` applied to the merge commit. Submodule pointer in `pipe-dream` advances to the new merge commit.
- **`pipe-dream` repo:** Pre-execution baseline commit, post-execution baseline commit, closure commit (consistent with CR-111 pattern).
- **Future CRs:** Standard execution-branch workflow per SOP-005 §7.1, now with a cleaner architectural baseline (no `self.app` in tools, facade-routed interaction_data).
- **No external systems, interfaces, or dependencies are affected.**
- **CR-110 (Razem engine work) is unaffected** — paused, no overlap.

### 7.4 Development Controls

This CR implements changes to `flow-state`, a controlled submodule under SOP-005 governance. Development follows established controls:

1. **Test environment isolation:** Development in `.test-env/` (local) or `/projects/` (containerized agents). The `flow-state/` submodule mounted under `pipe-dream/` is not a permitted edit location for this code work; the executor checks out the submodule's `cr-112-toolcontext-completion` branch in a permitted location and edits there.
2. **Branch isolation:** All development on branch `cr-112-toolcontext-completion`.
3. **Write protection:** `.claude/settings.local.json` blocks direct writes to `flow-state/` source code from the agent environment; QMS document edits happen via qms-cli, code edits happen on the branched copy.
4. **Qualification required:** Changes verified via integration verification (see §8) before merge.
5. **CI verification:** No CI exists on `flow-state/` at the time of this CR (acknowledged gap; a CR to add tests is queued for later). Until CI exists, the qualified commit is the post-integration-verification commit on the execution branch, evidenced by the smoke-test VR and the executor's recorded observation.
6. **PR gate:** Changes merge to `main` via PR after RS/RTM EFFECTIVE.
7. **Submodule update:** Parent repo `pipe-dream` updates the `flow-state` pointer only after merge.

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | `flow-state/main@a26f7fb` | EFFECTIVE v1.0 | FLOW-STATE-1.0 |
| During execution | Unchanged | DRAFT (RS / RTM checked out) | FLOW-STATE-1.0 (unchanged) |
| Post-merge | Merged from `cr-112-toolcontext-completion` | EFFECTIVE v2.0 | FLOW-STATE-1.1 |

Per SOP-006 §7.4, RS and RTM must both be EFFECTIVE before merging the execution branch to `main`.

---

## 8. Testing Summary

For code CRs without an automated test suite (Flow State has no `tests/` directory at the time of this CR), integration verification through user-facing levers carries the burden of demonstrating effectiveness. Flow State has no automated test infrastructure; introducing it is out of scope for this CR.

### Automated Verification

Not applicable. No automated tests exist; none are added in this CR.

### Integration Verification

Each VR-flagged EI (see §10) records a smoke-test session exercising specific functionality through the running app. The combined smoke coverage across EIs 5, 6, 7, 9 is:

- **Source tool smoke (EI-5 VR):** Launch `python flow-state/main.py --mode builder`. Press `Shift+S` to switch to Source tool. Hover canvas (snap indicator updates without crash). Click to set center; click again to set radius. Source appears with rendered handles and dashed preview. Status bar reads "Source created (r=X.X)". With `Ctrl` held during snap, a Coincident constraint is created between the Source center and the snapped point.
- **All-tools smoke (EI-6 VR):** In both `--mode sim` and `--mode builder`, exercise each tool — Brush (paint particles in sim mode), Select (click an entity, drag it, observe responsive feedback and final commit), Line (draw a line with live-preview supersede; ESC mid-draw discards), Rect (draw a rect), Circle (draw a circle), Point (place a point). No crashes; geometry created via commands; undo / redo (`Ctrl+Z` / `Ctrl+Y`) walks the history correctly.
- **Interaction data smoke (EI-7 VR):** In builder mode, drag a line by its midpoint — line translates. Drag a line endpoint — line rotates around its other point if the other end is anchored, otherwise both endpoints move. Press ESC mid-drag — line returns to its pre-drag position. Apply a LENGTH constraint to a line; drag — line preserves length. Press F9 to toggle Numba; repeat the same drag gestures — same observed behavior on both backends.
- **Consolidated full smoke (EI-9 VR):** In a single session, exercise the union of EI-5/6/7 plus: F9 / F10 / F11 solver controls (Numba toggle, iteration count adjust); `Ctrl+/-` UI scale; mode switch sim ↔ builder via menu; save / load scene (`.scn`); save / load model (`.mdl`); particle paint / erase / clear in sim mode; `Make Dynamic` / `Make Static` toggle on an entity (verify two-way coupling kicks in for dynamic); right-click context menus on entity / point / constraint produce expected actions. No crashes throughout the full session.

Each VR records the actions taken, the observed behavior, and Pass / Fail with prose evidence anchored to the running session.

---

## 9. Implementation Plan

### 9.1 Phase 1: Test Environment Setup

1. Verify the development directory `.test-env/flow-state/` exists; if not, clone `whharris917/flow-state` there.
2. Update `.test-env/flow-state/` to current `origin/main` (commit `a26f7fb`).
3. Create and check out branch `cr-112-toolcontext-completion`.
4. Verify clean test environment: `git status` shows clean working tree.

### 9.2 Phase 2: Requirements (RS Update)

1. Checkout `SDLC-FLOW-RS` in production QMS (`qms checkout SDLC-FLOW-RS`).
2. Modify REQ-FS-ARCH-004 (and REQ-FS-CAD-003 if needed) per §5.7.
3. Checkin RS, route for review and approval.
4. **Verify RS reaches EFFECTIVE before proceeding to Phase 3.**

### 9.3 Phase 3: Implementation

1. **Add ToolContext methods** (`add_process_object`, `has_interaction_data`, extend `set_interaction_data` signature) per §5.4 and §5.3.1.
2. **Migrate SourceTool** to inherit from `Tool` and use `self.ctx` per §5.1.
3. **Migrate `tools.py`** — replace all `self.app.X` reaches with `self.ctx.X` per §5.2 and migrate `interaction_data` mutation sites to the facade per §5.3.
4. **Delete** the `self.app = ctx._app` line at `ui/tools.py:87` per §5.2.
5. **Update stale module docstrings** in `ui/input_handler.py` and `engine/compiler.py` per §5.5.
6. Commit changes to `cr-112-toolcontext-completion`.

### 9.4 Phase 4: Qualification

1. Flow State has no automated test suite; this phase reduces to "verify the application launches and runs without errors at the import / startup level":
   - `python main.py --mode dashboard` — dashboard launches without crash.
   - `python main.py --mode sim` — simulation viewport launches; default Brush tool is selected; window appears.
   - `python main.py --mode builder` — builder viewport launches; default Select tool is selected; window appears.
2. Push to `cr-112-toolcontext-completion` branch on remote.
3. Document the head-of-branch commit hash as a candidate qualified commit (will be re-confirmed after Phase 5 integration verification).

### 9.5 Phase 5: Integration Verification

1. Launch the application from the execution branch.
2. Exercise the smoke-test scope described in §8 through user-facing levers (EI-5, EI-6, EI-7, EI-9 VRs).
3. Confirm no crashes; confirm primary functionality of each tool; confirm undo/redo walks correctly; confirm dragging respects constraints; confirm Numba toggle preserves behavior.
4. Record observations in each VR document.
5. The commit at this point becomes the qualified commit — record its hash.

### 9.6 Phase 6: RTM Update and Approval

1. Checkout `SDLC-FLOW-RTM` in production QMS.
2. Re-anchor qualitative-proof rows for affected REQs to the qualified commit; update Qualified Baseline section to record the new commit, repo, branch, and `System Release: FLOW-STATE-1.1`.
3. Checkin RTM, route for review and approval.
4. **Verify RTM reaches EFFECTIVE before proceeding to Phase 7.**

### 9.7 Phase 7: Merge and Submodule Update

**Prerequisite:** RS and RTM must both be EFFECTIVE before proceeding (per SOP-006 §7.4).

1. Verify RS is EFFECTIVE (`qms status SDLC-FLOW-RS` returns `EFFECTIVE, Version: 2.0`).
2. Verify RTM is EFFECTIVE (`qms status SDLC-FLOW-RTM` returns `EFFECTIVE, Version: 2.0`).
3. Open PR on GitHub from `cr-112-toolcontext-completion` to `main`. (No CI configured; merge gate is the manual EFFECTIVE/RTM check above.)
4. Merge using regular merge commit (`--no-ff`); not squash (per SOP-005 §7.1.3).
5. Verify the qualified commit is reachable on `main` via the merge commit.
6. Apply annotated tag `FLOW-STATE-1.1` to the merge commit; push tag to remote.
7. In `pipe-dream`, update the `flow-state` submodule pointer to the new merge commit; commit and push.
8. Verify functionality once more in the production-context (submodule-pointer-advanced) tree.

### 9.8 Phase 8: Documentation

1. Update CLAUDE.md §§2.3, 6.2, 7 per §5.6; targeted audit pass for additional drift.
2. Update `.claude/PROJECT_STATE.md` SDLC table to v2.0; advance Qualified Baselines to `CLI-18.0 + FLOW-STATE-1.1`.

---

## 10. Execution

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution baseline: commit and push `pipe-dream` (including all submodules) per SOP-004 §5. Record the commit hash. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Phase 1 (Test Environment Setup): clone/update `flow-state` in `.test-env/`; create branch `cr-112-toolcontext-completion`. Record starting commit hash on branch. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Phase 2 (RS Update): checkout SDLC-FLOW-RS; modify REQ-FS-ARCH-004 (and REQ-FS-CAD-003 if needed) per §5.7; checkin; route for review and approval. RS reaches EFFECTIVE v2.0. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Phase 3.1: ToolContext API changes per §5.4 — add `add_process_object`, `has_interaction_data`; extend `set_interaction_data` with keyword-only `point_idx`; fix existing `clear_constraint_ui()` to call `builder.reset()` and use `btn.active`. Commit to execution branch. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Phase 3.2: migrate SourceTool to inherit from `Tool` and use `self.ctx` per §5.1. Remove unused imports (`AddConstraintCommand`, `Coincident`). Commit to execution branch. **VR scope:** open builder mode; switch to Source tool (Shift+S); hover (snap indicator updates without crash); click center; click radius; verify Source created with status update; **with Ctrl held during snap, verify Coincident constraint is created end-to-end** (since `ctx.create_coincident_command()` adds validation that the prior direct `Coincident(...)` constructor lacked). | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Phase 3.3: migrate `tools.py` per §5.2 — direct `self.app.X` reaches → `self.ctx.X`; rewrite `@property sketch` and `@property scene` bodies to delegate through ctx; replace BrushTool's cached `ParticleBrush` with direct `ctx.paint_particles()` / `ctx.erase_particles()`; migrate 4 `interaction_data` mutation sites to facade per §5.3; replace `_clear_constraint_ui` body with `ctx.clear_constraint_ui()` + separate selection clearing. Commit to execution branch. | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | Phase 3.4: delete `self.app = ctx._app` line at `ui/tools.py:87`. Smoke-test that all tools still function (no remaining `self.app` reaches). Commit to execution branch. | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-8 | Phase 3.5: update stale module docstrings in `ui/input_handler.py` (4-layer correction) and `engine/compiler.py` (two-way-via-tether) per §5.5. Commit to execution branch. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-9 | Phases 4 + 5 (Qualification + Integration Verification): full app smoke test per §8 across sim and builder modes; consolidated smoke session covering tools, interaction data, mode switches, save/load, undo/redo, Numba toggle, dynamic-entity toggle, context menus. Push branch; record the qualified commit hash. | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-10 | Phase 6 (RTM Update): checkout SDLC-FLOW-RTM; re-anchor qualitative-proof rows for affected REQs at the qualified commit; update Qualified Baseline section (System Release `FLOW-STATE-1.1`); checkin; route for review and approval. RTM reaches EFFECTIVE v2.0. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-11 | Phase 7 (Merge and Submodule Update): verify RS + RTM EFFECTIVE; open PR `cr-112-toolcontext-completion` → `main`; merge with regular merge commit (no squash); apply tag `FLOW-STATE-1.1` at the merge commit; push tag; advance `flow-state` submodule pointer in `pipe-dream`; commit submodule pointer update. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-12 | Phase 8 (Documentation): update CLAUDE.md §§2.3, 6.2, 7 per §5.6; targeted audit pass for additional drift; update `.claude/PROJECT_STATE.md` SDLC table to v2.0 and advance Qualified Baselines to `CLI-18.0 + FLOW-STATE-1.1`. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-13 | Post-execution baseline: commit and push `pipe-dream` (including the advanced flow-state submodule pointer) per SOP-004 §5. Record the commit hash. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

---

## 11. Execution Summary

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-004:** Document Execution (pre-execution / post-execution baseline; EI conventions)
- **SOP-005:** System Lifecycle (execution branch workflow §7.1; merge gate §7.1.3; System Release versioning §9)
- **SOP-006:** SDLC (RS/RTM coordination; merge prerequisites §7.4)
- **CR-111:** Adopt Flow State into QMS Governance (CLOSED 2026-04-30 — establishes `FLOW-STATE-1.0` qualified baseline; Execution Summary §11 lists this CR's queued follow-ups).
- **CR-2026-004:** ToolContext migration (Phase J) — partial migration whose completion this CR addresses.
- **SDLC-FLOW-RS v1.0:** Flow State Requirements Specification (current EFFECTIVE; this CR advances to v2.0).
- **SDLC-FLOW-RTM v1.0:** Flow State Requirements Traceability Matrix (current EFFECTIVE; this CR advances to v2.0).
- **CLAUDE.md:** Pipe Dream technical architecture guide (§§2.3, 6.2, 7 corrected by this CR).
- **PROJECT_STATE.md §6.1:** Records the queued follow-ups from CR-111 that this CR consolidates.
- **`flow-state/ui/source_tool.py`:** The crash site that prompted this CR.
- **`flow-state/core/tool_context.py`:** The facade whose API this CR modestly extends.

---

**END OF DOCUMENT**
