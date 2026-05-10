# Session-2026-05-10-001

## Current State (last updated: Sink + ProcessObject resize + handle cascade-delete done)
- **Active document:** CR-116 (IN_EXECUTION v1.2) — Exploration CR umbrella for beach-trip Flow State work
- **Current EI:** EI-3 (free-form exploration)
- **Blocking on:** Nothing — ready for Lead in-GUI re-validation
- **Next:** Lead validates resize (drag a Source/Sink edge) and cascade-delete (select handle Point + DEL) in
  the GUI; if both work, commit the session's work
- **Subagent IDs:** none active
- **Branch state:**
  - `.test-env/flow-state/` on `cr-116-beach-trip-exploration` upstream @ `9358631`
  - **Uncommitted local changes** across 13 files now (Sink + resize + cascade-delete)
  - Suite at **564 passing + 1 skipped** (was 523 + 1 → **+41 new tests this session**)

## Session-start checklist
- New day (2026-05-10); first session of the day → Session-2026-05-10-001
- CURRENT_SESSION updated; session folder created
- Read SELF.md, previous session notes (Session-2026-05-08-001), QMS-Policy / START_HERE / QMS-Glossary, PROJECT_STATE
- Inbox: empty
- No compaction-log → genuine new session

## Direction picked (2026-05-10)
Lead chose "Continue CR-116, different direction" — pivoting away from raw physics perf where last session
concluded the classic kernel is at the atom-centric parallelization limit. The natural next-feature is the
**Sink ProcessObject** — particle absorber, complement to Source. The base-class doc string in
`model/process_objects.py` already lists `Sink` / `Heater` / `Sensor` as "future" placeholders; Sink is the
most-bounded of the three, has zero physics-perf risk, and is purely additive. Auto mode active.

## Plan: Sink ProcessObject

**Scope.** Add a Sink (particle drain / absorber) as a peer to Source. Mirrors Source's plumbing wherever
possible. No filtering by particle type/material yet (Sink absorbs all dynamic particles inside its radius);
filtering is a clean extension when it's wanted.

**Why this is in-bounds for CR-116.** EI-3 is free-form exploration of the `flow-state/` submodule; CR-116
§2.4 sets target submodule = `flow-state/`, execution branch = `cr-116-beach-trip-exploration`,
RS-immutability declaration (no REQ changes — additive feature within existing process-object surface). No
anti-scope violation.

**Files to create / modify (in `.test-env/flow-state/`):**
1. `model/process_objects.py` — add `SinkProperties` dataclass, `Sink(ProcessObject)` class, register
   `'sink'` in `create_process_object` factory.
2. `core/sink_commands.py` — NEW. Mirror `core/source_commands.py`: `AddSinkCommand`,
   `DeleteSinkCommand`, `SetSinkRadiusCommand`, `ToggleSinkEnabledCommand`.
3. `ui/sink_tool.py` — NEW. Mirror `ui/source_tool.py`: two-click center+radius placement, snap support,
   ESC cancel, preview rendering with sink-distinct color.
4. `ui/process_object_renderer.py` — extend to render `'dashed_circle'` geom with per-object color, OR add
   a new geom type `'sink_circle'`. Pick the smaller surface change.
5. `ui/icons.py` — add procedural `draw_icon_sink` (inverse motif of `draw_icon_source`: particles
   converging inward).
6. `shared/config.py` — add `TOOL_SINK = 8`.
7. `ui/ui_manager.py` — add a Sink button to the right-panel toolbar.
8. `ui/input_handler.py` — register Sink button mapping; add Shift+D hotkey (S already taken by Source
   via Shift+S).
9. `app/flow_state_app.py` — import & register `SinkTool` in `init_tools`.
10. `tests/test_process_objects.py` — add `TestSinkProperties`, `TestSinkConstruction`,
    `TestSinkHandleLifecycle`, `TestSinkHitTesting`, `TestSinkAbsorption`, `TestSinkSerialization`.

**Absorption mechanics.** Mirror `ParticleBrush.erase`:
- Iterate dynamic particles (`is_static[i] == 0`); skip static and tethered.
- Distance check against sink center; collect indices inside `radius`.
- Build `keep_indices`; call `sim.compact_arrays(keep_indices)`; set `sim.rebuild_next = True`.
- Track `absorbed_count` (cumulative) and `last_frame_absorbed` (per-frame; useful for HUD/diagnostics).

**Visual.** Dashed red circle (200, 90, 90) with optional faint inward-radial fill. Distinguishable from
Source's blue (100, 180, 255) at a glance.

**Hotkey.** Shift+D ("D" for Drain since S=Source, K not memorable, X destructive-feeling).

**Execution order in Scene.update step 7.** Sources and Sinks both call `obj.execute(simulation, dt)` in
list order. If a Source feeds particles into a Sink that overlaps it, the Sink absorbs them on the same
frame — natural behavior, matches intent.

## Progress Log

### [start] Context loaded; Sink design fixed
- Session-start checklist complete; PROJECT_STATE read
- Surveyed Source plumbing end-to-end (process_objects.py, source_commands.py, source_tool.py,
  process_object_renderer.py, icons.py, ui_manager.py, input_handler.py, flow_state_app.py)
- Confirmed `ParticleBrush.erase` is the absorption template; `Simulation.compact_arrays(keep_indices)` is
  the existing public API for particle removal
- Confirmed Scene step 7 (PROCESS OBJECTS) calls `obj.execute(simulation, dt)` for all enabled objects in
  list order — Sink slots into the same lifecycle as Source

### Sink implementation (under CR-116 EI-3)

**Files created:**
- `core/sink_commands.py` — `AddSinkCommand` / `DeleteSinkCommand` / `SetSinkRadiusCommand` /
  `ToggleSinkEnabledCommand`. Mirror of `core/source_commands.py`.
- `ui/sink_tool.py` — `SinkTool` (two-click center+radius placement, dashed-red preview, snap support, ESC
  cancel, Ctrl+click for coincident constraint). Mirror of `ui/source_tool.py`. Visual palette uses
  `SINK_COLOR = (220, 80, 80)` (red) — visually distinct from Source's `(100, 180, 255)` (blue).

**Files modified:**
- `model/process_objects.py` — added `SinkProperties` dataclass and `Sink(ProcessObject)` class. Sink
  absorbs `is_static==0` (dynamic) particles only — static and tethered survive. Stats tracked:
  `absorbed_count` (cumulative) + `last_frame_absorbed` (per-frame). `to_dict`/`from_dict` round-trip;
  `max_sigma` uses `None` as JSON sentinel for `inf`. `create_process_object` factory now routes `'sink'`
  alongside `'source'`. Sink's render descriptor carries `kind='sink'` so the renderer can pick the red
  palette without sniffing types.
- `ui/process_object_renderer.py` — `_draw_dashed_circle` gained a `kind='source'` param (default keeps
  the existing Source rendering identical, no caller-site changes for Source); `kind='sink'` selects
  the red palette. Disabled-state grey unchanged for both.
- `ui/icons.py` — added `draw_icon_sink` (procedural fallback): same dashed circle as Source but with
  inward arrows on the diagonals (mirror motif of Source's emanating-particle dots). Registered as
  `'sink'` in `PROCEDURAL_ICONS`.
- `shared/config.py` — `TOOL_SINK = 8` (was 7=TOOL_SOURCE). All TOOL_* constants now sequential 0-8.
- `ui/ui_manager.py` — added a single-button `row_sink` after the existing Ref/Source row, registered as
  `self.tools['sink']` with the procedural sink icon and tooltip "Sink (Drain)". Sink stands alone
  rather than sharing a row, since pairing it arbitrarily would obscure the Source-Sink direct
  counterpart relationship.
- `ui/input_handler.py` — added `'sink': config.TOOL_SINK` to the tool-button map; added Shift+D global
  hotkey (mirrors existing Shift+S for Source).
- `app/flow_state_app.py` — added optional `SinkTool` import (`HAS_SINK_TOOL` flag) and the corresponding
  registry entry in `init_tools()`.

**Tests added (34 total, all green):**
- `tests/test_process_objects.py` (+28 in 6 new classes): `TestSinkProperties` (3 incl. inf-sentinel
  round-trip), `TestSinkConstruction` (4), `TestSinkHandleLifecycle` (3), `TestSinkHitTesting` (3),
  `TestSinkAbsorption` (8 — disabled, in/out of radius, static/tethered preserved, multi-absorb,
  per-frame counter reset, empty-sim safety), `TestSinkSerialization` (5 incl. factory routing of
  Source vs Sink), `TestSinkRendering` (2 — kind='sink' descriptor on Sink, defaults to 'source' on
  Source).
- `tests/test_scene.py` (+6 in `TestSinkIntegration`): Scene plumbing (add/remove sink registers/
  unregisters handle), `find_process_object_at` resolves Sink, `AddSinkCommand` undo/redo round-trip,
  `DeleteSinkCommand` round-trip via to_dict reconstruction, Source+Sink coexistence.

**Suite:** 523+1 → **557 passing + 1 skipped**.

**Smoke checks (headless):**
- All new imports succeed (`SinkTool`, `SINK_COLOR`, all command classes, `Sink`, `SinkProperties`,
  `create_process_object` factory)
- `config.TOOL_SINK == 8` ✓
- Factory dispatches `{'type': 'sink', ...}` → `Sink` instance ✓
- `icons.get_icon('sink')` returns the procedural callable ✓
- `HAS_SINK_TOOL is True` in `flow_state_app` ✓
- `_draw_dashed_circle` signature is backwards-compatible (`kind='source'` default) ✓

**Architectural notes:**
- Sink absorbs *all* dynamic particles in radius — no rate limit, no rolling window, no Maxwell sampling
  needed (it removes, doesn't create). Properties dataclass exists with `enabled_filter` /
  `min_sigma` / `max_sigma` reserved for future material-selective filtering, but those fields are
  unused by `execute()` at this stage; documented as forward-compatible placeholders.
- Same `process_objects` list as Source. Order matters: if a Source is added before a Sink that
  overlaps it, the Source's emit fires first within Scene step 7, then the Sink absorbs same-frame —
  which is the intended behaviour for collocated source/sink pairs ("recycler").
- Scene's `find_process_object_at` already iterates all `ProcessObject` instances and dispatches via
  `obj.hit_test`, so Sink works with the existing right-click-context-menu plumbing without any change
  on the Scene side.

**Awaiting Lead in-GUI validation** before any commit.

### Round 2: post-validation bug fixes (still under CR-116 EI-3)

Lead validated Sink works in the GUI but reported two real bugs that affect Source as well:

1. **Sources/Sinks aren't resizable.** Once placed, no UI affordance to change radius. The
   `SetSourceRadiusCommand` / `SetSinkRadiusCommand` classes existed but weren't wired to any drag
   path.
2. **Deleting the central handle Point doesn't delete the owning ProcessObject.** The doc string in
   `process_objects.py` claimed "When a handle Point is deleted via normal entity deletion, the owning
   ProcessObject should also be deleted — This is handled by DeleteEntityCommand checking for
   is_handle flag" — but `RemoveEntityCommand` had no such check, so the cascade was aspirational.

Both fixes land within CR-116 EI-3 (no RS changes — bug fixes within the existing process-object
requirement surface).

**Resize fix (`ui/tools.py`):**
- Added `RESIZE_PROCESS_OBJECT` mode to SelectTool, mirroring the `RESIZE_CIRCLE` pattern
- New `target_obj` field in `_reset_drag_state` — stores the Source/Sink reference directly
  (ProcessObjects aren't in `sketch.entities`, so we keep an instance ref rather than an index)
- `_hit_test_process_object_resize(mx, my, layout)` mirrors `_hit_test_circle_resize`: iterate
  `scene.process_objects`, transform world (center, radius) → screen, return the obj if mouse is
  within 8 px of the screen circumference
- Inserted into `_handle_click` priority order at step 2b (between sketch-circle resize and
  entity-body hit) — runs only when Shift is not held, same gate as circle resize
- `_start_resize_process_object_drag(obj, mouse_pos)` captures `original_radius`, executes initial
  supersede=False command via `_build_set_radius_command(obj, ...)` (helper that does an
  `isinstance` dispatch to pick `SetSourceRadiusCommand` or `SetSinkRadiusCommand`)
- `_handle_resize_process_object_drag(curr_sim)` computes new radius (clamped to 0.5 floor matching
  placement floor), executes supersede=True command per frame
- `_commit_resize_process_object()` is a pass — supersede pattern leaves the final command on the stack

**Cascade-delete fix (`app/app_controller.py:action_delete_selection`):**
- Per-index dispatch: for each selected entity, check `scene.get_process_object_for_handle(entity)`;
  if it returns an owner, build `DeleteSourceCommand` (for `Source`) or `DeleteSinkCommand` (for
  `Sink`) instead of `RemoveEntityCommand`. Otherwise `RemoveEntityCommand` as before.
- Single command path stays single; multi-command path uses the existing `CompositeCommand`
- The owner-instance cascade naturally undoes via `DeleteSourceCommand.undo()` /
  `DeleteSinkCommand.undo()` (which round-trip through `to_dict`/`from_dict`)
- The model layer dependency stays clean (`model/commands/geometry.py` does **not** depend on
  source/sink commands) — the dispatch happens at the action layer where the orchestration is

**Tests added (round 2 — +7, all green):**
- `tests/test_scene.py::TestSinkIntegration::test_set_sink_radius_undo_redo` (single-step round-trip)
- `tests/test_scene.py::TestSinkIntegration::test_set_sink_radius_supersede_merge` (4-step drag
  collapses to 1 undo)
- `tests/test_scene.py::TestProcessObjectHandleCascadeDelete` (5 tests):
  - `test_delete_source_handle_cascades` — selecting handle + delete removes both Source and handle
  - `test_delete_sink_handle_cascades` — same for Sink
  - `test_delete_handle_cascade_is_undoable` — undo restores the ProcessObject from `to_dict`
  - `test_non_handle_point_deletes_normally` — regular Points still go through RemoveEntityCommand
  - `test_mixed_selection_handles_and_entities` — composite delete works when selection mixes types
- These tests build a stub AppController via `__new__`, attach a stub session with
  `SelectionManager` + `StatusBar` instances, and exercise `action_delete_selection` directly.

**Suite:** 557+1 → **564 passing + 1 skipped**. Session total: 523 → 564 (**+41 tests**).

**Smoke checks (round 2):**
- `SelectTool` source contains `_hit_test_process_object_resize`, `_start_resize_process_object_drag`,
  `_handle_resize_process_object_drag`, `_commit_resize_process_object`, `_build_set_radius_command`,
  and the `RESIZE_PROCESS_OBJECT` mode string ✓
- `AppController.action_delete_selection` source contains `DeleteSourceCommand`, `DeleteSinkCommand`,
  `get_process_object_for_handle` ✓

**Awaiting Lead in-GUI re-validation** of (a) drag-circumference-to-resize and (b) select-handle +
DEL cascading to ProcessObject removal, before any commit.

### Round 3: Source Properties dialog + Source ↔ material-palette refactor

Lead validated round 2 and asked for: (1) a properties dialog for Sources exposing radius / rate /
temperature, and (2) Sources should NOT directly expose sigma/epsilon/mass — they should reference the
existing material palette. Sinks stay simple for now.

**Schema change — `model/process_objects.py`:**
- `SourceProperties` drops `sigma`/`epsilon`/`mass`, gains `material_name: str = 'Water'`. Particle
  physics now comes from `sketch.materials[material_name]` resolved at spawn time.
- `from_dict` silently ignores legacy `sigma`/`epsilon`/`mass` keys so old saves still load (they
  fall back to Water).
- New `Source._resolve_material()` helper. Looks up the material via `_owner_scene.sketch.get_material`
  if attached; falls back to a default Water-like `Material(...)` for bare-Sim test code.
- `_try_spawn_particle` uses material.sigma/epsilon/mass/color. Spawned particles inherit the
  material's color so emissions stay visually consistent with the brush palette.
- `_sample_velocity(mass=1.0)` now takes mass explicitly (looked up from material) rather than from
  `self.properties.mass`.

**SourceTool — `ui/source_tool.py`:**
- `_create_source` reads `ctx.get_active_material()['name']` and passes it into the new
  `SourceProperties(material_name=...)`. Placing a Source while a different material is selected on
  the right-panel widget produces a Source whose emissions match that material — single source of
  truth.

**Dialog — `ui/ui_widgets.py`:**
- New `SourcePropertiesDialog` (~240 px tall, modeled on `AnimationDialog`'s compact pattern):
  - Material dropdown populated from `sketch.materials`. Single source of truth = the project's
    palette; no editing material properties inside this dialog (that's the right-panel widget's job).
  - Three numeric inputs: Radius, Rate (p/s), Temperature.
  - Apply / Cancel buttons; ESC closes via the existing modal Esc handling.
- Sets `done=True` on Apply (with `apply=True`) and on click-outside dismissal (with `cancelled=True`,
  `apply=False`).

**Context menu — `app/app_controller.py`:**
- `get_context_options('point', ...)` checks `scene.get_process_object_for_handle(entity)` first.
  If the Point is a Source handle, returns `["Source Properties...", "Delete"]` instead of the
  generic Anchor / Set Length. Sink handles get `["Delete"]` (stays simple per Lead direction).
  Non-handle Points keep the existing behavior.
- `handle_context_menu_action` routes `"Source Properties..."` to `open_source_properties_dialog`.
- `open_source_properties_dialog` resolves the Source via `ctx_vars['wall']`, opens the dialog,
  pushes onto the modal stack with type `'source_properties_dialog'`.
- `apply_source_properties_from_dialog` reads dialog values, builds a `SetSourceRadiusCommand` (if
  radius changed) + `SetSourcePropertiesCommand`, wraps in `CompositeCommand` so the whole edit
  collapses to a single undo step.
- `update()` polls the dialog's `done` flag each frame; routes through the apply method (which
  checks `apply` so click-outside cancellations are no-ops), then closes the modal.

**input_handler.py — click-outside dismissal:**
- Added `source_properties_dialog` to the click-outside dismissal branch (mirrors the existing
  `save_as_new_dialog` pattern: set `cancelled=True`, `done=True`, AppController.update() routes
  through the apply path which sees `apply=False` and just closes).

**Tests added (round 3 — +5, all green):**
- `TestSourceProperties::test_from_dict_silently_ignores_legacy_sigma_epsilon_mass` — old saves with
  legacy schema still load (Water fallback)
- `TestSourceMaterialLookup` (4 tests):
  - `test_bare_source_falls_back_to_default_material` — Source without a Scene still spawns
  - `test_attached_source_uses_named_material` — spawned particles' sigma matches the named material
    (Oil's sigma=1.2)
  - `test_unknown_material_falls_back_via_sketch_get_material` — `sketch.get_material` returns
    Water/Wall for unknown names, no crash
  - `test_spawned_particles_inherit_material_color` — `atom_color` matches the resolved material

**Tests updated (in-place; no count change):**
- `TestSourceProperties::test_defaults`, `test_dict_roundtrip` — now check `material_name` instead of
  `sigma`/`epsilon`
- `TestSourceRateGuards::test_overlap_rejection_prevents_spawn_when_dense` — dropped `sigma=1.0`
  kwarg (now comes from the material)
- `TestSourceVelocitySampling::test_directional_bias_...`, `test_isotropic_spread_...` — dropped
  `mass=1.0` kwarg (now comes from the material; default is Water mass=1.0 so behavior unchanged)
- `TestSerialization::test_source_dict_roundtrip` — `material_name='Oil'` instead of `sigma=1.5`

**Suite:** 564+1 → **569 passing + 1 skipped**. Session total: 523 → 569 (**+46 tests**).

**Smoke checks (round 3):**
- `SourcePropertiesDialog` constructs with a Source + Sketch, seeds inputs from the Source's state,
  `get_values()` round-trips ✓
- Material dropdown contains Oil (and other library materials) ✓
- `AppController.handle_context_menu_action` source contains `"Source Properties..."` dispatch ✓

**Awaiting Lead in-GUI validation** of: right-click a Source's center handle → "Source Properties..." →
dialog opens; change material/radius/rate/temperature, hit Apply → emissions immediately use new
material (color, sigma, epsilon, mass) and new rate/temperature. Click outside the dialog → cancels
with no changes.

### Round 4: dialog → command → applied-state test coverage

Lead asked for tests that confirm each Source property can be modified and applied via the dialog.
Built a new `TestSourcePropertiesDialog` class in `tests/test_scene.py` covering the full pipeline.

**Bug caught and fixed during test authoring:** `SetSourcePropertiesCommand.execute` (in
`core/source_commands.py`) still constructed `SourceProperties(sigma=..., epsilon=..., mass=...)`
for the undo snapshot — left over from the round-3 schema refactor. Tests caught it on the first
run as `AttributeError: 'SourceProperties' object has no attribute 'sigma'`. Fixed by replacing
with `material_name=...` field. Exactly the kind of stale-reference bug pre-flight tests are for.

**Test-helper refactor:** Hoisted `_make_app_controller_stub(scene)` from
`TestProcessObjectHandleCascadeDelete` (where it was a method) to module-level in `test_scene.py`
so both dialog tests and cascade-delete tests share one definition.

**TestSourcePropertiesDialog (+17, all green):**

*Seed verification (3):*
- `test_dialog_seeds_inputs_from_source_state` — dropdown selects the Source's material, input
  fields show Source's current radius / rate / temperature formatted to 2 dp
- `test_dialog_lists_all_sketch_materials_in_dropdown` — all preset materials (Water, Oil, Mercury,
  Honey, Wall) appear in the dropdown
- `test_dialog_with_unknown_material_falls_back_to_first_option` — Source with stale material_name
  falls back to dropdown index 0 instead of crashing on ValueError

*get_values widget readback (3):*
- `test_get_values_reads_current_inputs` — drive dropdown.selected_index + InputField.set_value,
  verify `get_values()` returns those values
- `test_get_values_clamps_radius_to_min` — radius < 0.5 clamps to 0.5 (placement floor)
- `test_get_values_clamps_rate_and_temp_non_negative` — negative rate / temp clamp to 0

*Apply path, per-property (5):*
- `test_apply_changes_material_name` — material switch propagates to Source.properties.material_name
- `test_apply_changes_radius` — radius edit propagates to Source.radius
- `test_apply_changes_rate` — rate edit propagates to Source.properties.rate
- `test_apply_changes_temperature` — temperature edit propagates to Source.properties.temperature
- `test_apply_preserves_unchanged_injection_direction_and_spread` — fields not exposed by the dialog
  (injection_direction / injection_spread) round-trip unchanged through the apply pipeline rather
  than being reset to defaults

*Apply path, command composition (2):*
- `test_apply_with_all_changes_collapses_to_one_undo_step` — all four changes (material, radius,
  rate, temp) bundle into one `CompositeCommand`; a single `scene.undo()` restores all four
- `test_apply_with_only_property_change_emits_single_command` — when radius is unchanged, no
  redundant `SetSourceRadiusCommand` is emitted

*Cancel paths (2):*
- `test_cancel_via_apply_flag_makes_no_changes` — `dialog.apply=False` (Cancel button or
  click-outside) leaves all four properties at their pre-dialog values
- `test_apply_then_cancel_subsequent_dialog_independent` — applying dialog 1 then cancelling
  dialog 2 preserves the first apply (the cancel doesn't accidentally revert it)

*Behavioral effect of apply (2):*
- `test_apply_material_change_affects_subsequent_spawned_particles` — switch to Mercury via dialog,
  emit, verify spawned particles' `atom_sigma` equals Mercury's sigma=0.8 (end-to-end physics
  verification)
- `test_apply_temperature_change_affects_velocity_sampling` — bump T 1.0→4.0 via dialog, verify
  mean spawned-particle speed roughly 2× (loose bound >1.5× to accommodate sampling noise; both
  measurements seed numpy + Python random for determinism)

**Suite:** 569+1 → **586 passing + 1 skipped**. Session total: 523 → 586 (**+63 tests**). Single
session-most-tests-added by a wide margin — the Sink + ProcessObject refactor surfaced a lot of
behavior worth pinning down.

**No outstanding work.** Source properties dialog is fully wired and end-to-end covered. Ready for
Lead in-GUI validation and (if it works) commit. Open follow-up candidates if the Lead has
appetite: properties dialog for Sinks (e.g. when filter behavior gets implemented), HUD readout of
Sink absorbed_count, or rate-limited absorption.

### Round 5: `rate` → `flux` refactor — intensive source metric

Lead's conceptual feedback: `rate` (particles/sec) is *extensive* — it couples with radius in an
unintuitive way. They want something *intensive*, like pressure or chemical potential. Implemented
**areal particle flux** (particles per unit time per unit area) as the core knob — the simplest
intensive analog, identical in spirit to a heat flux density or particle current density. A
fuller chemical-potential analog (density-regulated, equilibrium-seeking source) is flagged as a
possible richer follow-up but not implemented.

**Schema change — `model/process_objects.py`:**
- `SourceProperties.rate` → `SourceProperties.flux` (default 0.5 particles per unit time per unit
  area). Docstring documents the relationship: `effective_throughput = flux · π · r²`.
- `Source.execute` now computes `effective_rate = flux · π · radius²` and uses that to accumulate
  spawn credit.
- `Source._calculate_catchup_factor` uses the same effective-rate model as the target.
- `Source.from_dict` migrates legacy `rate` to `flux` using the Source's own radius: `flux = rate /
  (π · r²)`. Old saves preserve their total throughput exactly. If both `rate` and `flux` are
  present (forward-mixed save), `flux` wins.
- `SourceProperties.from_dict` no longer reads `rate` directly — that conversion happens in
  `Source.from_dict` since it requires the Source's radius. Legacy `sigma`/`epsilon`/`mass` still
  silently ignored from earlier rounds.

**Commands — `core/source_commands.py`:**
- `SetSourcePropertiesCommand.execute` undo snapshot updated to use `flux` instead of `rate`.

**Dialog — `ui/ui_widgets.py`:**
- `SourcePropertiesDialog.in_rate` → `SourcePropertiesDialog.in_flux`. Label changes from
  `"Rate (p/s):"` to `"Flux (p/s/u²):"`. Formatted to 3 dp since typical flux values are O(0.1)–
  O(10).
- `get_values()` returns `'flux'` instead of `'rate'`.
- `AnimationDialog.in_rate` was accidentally renamed during a `replace_all` and immediately reverted
  — AnimationDialog still uses its own `rate` (angular rate for constraint drivers, unrelated
  concept).

**Action layer — `app/app_controller.py`:**
- `apply_source_properties_from_dialog` builds `SourceProperties(flux=...)` instead of `rate=...`.
- Status message: `f"Source: {mat}, r={r:.1f}, flux={flux:.3f}"`.

**Tests updated and added (round 5):**

*Updated in place (no count change):*
- `TestSourceProperties::test_defaults` — checks `flux == 0.5` instead of `rate == 10.0`
- `test_dict_roundtrip` — `flux=2.5` instead of `rate=20.0`
- `test_from_dict_silently_ignores_legacy_sigma_epsilon_mass` — also asserts `not hasattr(p,
  'rate')`
- `TestSerialization::test_source_dict_roundtrip` — flux-based assertion
- Various `Source((..), .., SourceProperties(rate=X))` → `(flux=Y)` across
  `TestSourceSpawning` / `TestSourceRateGuards` / `TestSourceVelocitySampling` /
  `TestSourceMaterialLookup` (calibrated to maintain effective rate ≳ legacy values given each
  test's radius)
- `tests/test_persistence.py::test_round_trip_preserves_process_objects` — flux=1.5 round-trip
- `TestSourcePropertiesDialog._make_source` signature: `rate=` → `flux=` (defaults to 0.5)
- All dialog tests' `in_rate` references / `properties.rate` assertions converted to `in_flux` /
  `properties.flux`
- `test_apply_changes_rate` → `test_apply_changes_flux`
- `test_get_values_clamps_rate_and_temp_non_negative` → `test_get_values_clamps_flux_and_temp_...`

*New (+3):*
- `TestSourceProperties::test_legacy_rate_converts_to_flux_via_source_from_dict` — old save with
  `rate=π·r²` migrates exactly to `flux=1.0`
- `TestSourceProperties::test_explicit_flux_wins_over_legacy_rate` — forward-mixed save honours flux
- `TestSourcePropertiesDialog::test_flux_is_intensive_effective_rate_scales_with_area` — the core
  conceptual test. Verified at two layers: (1) target effective rate is exactly intensive — same
  flux at 9× area gives exactly 9× target throughput; (2) delivered count over 20 frames at 9×
  area is >3× greater (per-frame attempt cap masks the full 9× ratio, but directional signal is
  unmistakable)

**Suite:** 586+1 → **589 passing + 1 skipped** (+3 net from the legacy-migration + intensive-property
tests). Session total: 523 → 589 (**+66 tests**).

**Smoke checks (round 5):**
- `Source.from_dict({'radius': 3, 'properties': {'rate': π·9}})` → `source.properties.flux ≈ 1.0` ✓
- Dialog opens with "Flux (p/s/u²)" label and 3-dp formatted input ✓
- Suite green ✓

**Follow-up flagged (not implemented):** a true chemical-potential source would regulate spawn rate
to maintain a target *density* inside the spawn region — adjusting throughput as the region fills
or empties. That's an equilibrium-seeking behavior rather than constant-forcing. If the Lead wants
that richer model, the current flux refactor is the right precursor (intensive metric in place);
the next step is adding a `target_density` knob and a density-control loop in `execute()`.

**Awaiting Lead in-GUI re-validation** of the renamed Flux field and the intensive-scaling
behavior. The expected feel: doubling a Source's radius quadruples its actual emission rate while
the dialog's Flux value stays fixed — the knob now describes *how hard the source is pushing per
unit area* rather than *total throughput*.

### Round 6: widget tests + SmartSlider bug fixes

Lead reported three classes of GUI bugs:
1. No on-screen read-out of slider values
2. Modifications to slider limits don't stay
3. Sliders sometimes don't seem to work

Diagnosed all three as facets of two structural bugs in `SmartSlider.handle_event`:

**Bug A (no readout):** During a drag, `handle_event` returned True at the MOUSEMOTION branch
BEFORE the `if changed and not self.in_val.active: self.in_val.set_value(self.val)` line at the
bottom. That line was effectively dead code for every code path that mattered, so the
InputField text never tracked the drag. User sees a stuck number and concludes the slider's
broken (Lead's bug #3).

**Bug B (limits don't stay):** Typing a value into the InputField wrote the result straight into
`self.val` with no clamp. Outside [min_val, max_val], the visual handle stayed pinned at the
nearest end while `self.val` held the typed value. As soon as the user touched the slider
again, the typed value vanished — hence "modifications don't stay" (Lead's bug #2).

Reference: `MiniSlider` already had the correct behaviour (clamps typed input at line 2615,
updates `in_val.set_value(self.val)` inside the drag branch at 2624). Backported both fixes to
`SmartSlider`:

- Drag branch now calls `self.in_val.set_value(self.val)` inline (before the early return)
  whenever the field isn't actively being edited.
- InputField branch now clamps the new value to `[self.min_val, self.max_val]` before assigning,
  and writes the clamped value back into the field text so the user sees what stuck.

Removed the unreachable post-return `changed`/`set_value` block at the bottom of the method.

**Tests added (round 6 — +42, all green):**

*Expanded InputField coverage (13):*
- `TestInputFieldEditing` (12): cursor positioning (insert/delete/home/end/left/right), no-op
  edge cases (delete at end, backspace at start, left at 0, right at end), inactive ignores
  typing, non-printable unicode (tab) ignored, set_value formatting (2-dp float, int
  stringification, blocked while active)
- `TestInputFieldCursorBlink` (3): inactive holds visible, active toggles at blink rate,
  keypress resets blink state

*SmartSlider coverage (24):*
- `TestSmartSliderConstruction` (2): initial state, initial readout shows initial value
- `TestSmartSliderDrag` (10): click-on-track starts drag, mouseup ends drag, drag-to-middle
  produces midpoint val, drag-to-left/right edges produce min/max, drag-past-left/right clamps,
  **drag updates input-field readout (the bug-A test)**, motion when not dragging is no-op,
  repeated motions converge on cursor (absolute, not relative, positioning)
- `TestSmartSliderInputField` (4): in-range entry passes through, **above-max clamps to max
  (bug-B test)**, below-min clamps to min, in-range passes through
- `TestSmartSliderLayout` (3): set_position moves track + input field in lockstep; drag after
  set_position uses new track location
- `TestSmartSliderIndependence` (2): two sliders have independent val / dragging state

*MiniSlider reference coverage (5):* initial state with 2-dp readout formatting, drag updates
both val and readout, set_value clamps, InputField entry clamps, set_position moves all
sub-widgets. Documents MiniSlider as the canonical reference behaviour SmartSlider should
match.

**Suite:** 589+1 → **631 passing + 1 skipped**. Session total: 523 → 631 (**+108 tests**).

**Lead in-GUI validation expected:** drag any slider → the number on the right of the slider
should now track the handle position in real time. Type a value above the slider's max into
the field → on RETURN, value snaps to max and the field text shows max. Symmetric for below
min.

**Note on the user's "modifications to the limits" interpretation:** clamping is the
conservative fix — it matches MiniSlider and prevents the silent out-of-range state. A richer
interpretation is *auto-expanding* limits: typing 999 with no hard_max would stretch
max_val to 999 so the slider's draggable range grows. That would explain the unused
`hard_min`/`hard_max` constructor params (they'd be the absolute walls beyond which expansion
can't go). If the Lead wants auto-expansion, that's a small follow-up: replace the clamp with
`min_val/max_val = ...; respecting hard_min/hard_max if set`.
