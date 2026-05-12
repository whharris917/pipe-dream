# Session-2026-05-11-001

## Current State (last updated: session start)
- **Active document:** CR-116 IN_EXECUTION v1.2 — Exploration CR (beach-trip Flow State work)
- **Current EI:** EI-3 (free-form exploration) — still open from previous session
- **Blocking on:** Awaiting Lead direction
- **Next:** Lead to decide — continue CR-116 exploration / address known
  limitations / close out CR-116 for qualification / address
  PROJECT_STATE.md bloat
- **Suite:** **801 passing + 1 skipped** (end of Session-2026-05-10-002)
- **Subagent IDs:** none active
- **Branch state (carried from last session):**
  - `.test-env/flow-state/` on `cr-116-beach-trip-exploration`,
    R1-R6 work committed + pushed
  - pipe-dream `main` — `M .claude/settings.local.json` only

## Session-start checklist
- Previous session was Session-2026-05-10-002 (new day → Session-2026-05-11-001 = 001)
- CURRENT_SESSION updated; folder created
- Read SELF.md, prior session notes (2026-05-10-002), QMS-Policy.md,
  START_HERE.md, QMS-Glossary.md, PROJECT_STATE.md §§1-3
- Inbox: empty
- No compaction-log in this folder → genuine new session

## Concerns to surface to Lead
- **PROJECT_STATE.md is still bloated** (~30k tokens; one Read call fails the
  25k token limit). Previous session flagged this — §2 Current Status alone is
  multi-page paragraphs, each session paragraph re-litigating the round-level
  detail that already lives in `notes.md`. Recommendation unchanged: compress
  §2 to per-CR one-paragraph status; session-level detail belongs in
  session notes only. Needs Lead confirmation before action.

## Known limitations from R5/R6 (CR-116 EI-3), available follow-up:
- (a) `AddMoleculeCommand.undo` is truncation-based — loses any particles
  added between place and undo (matches brush-undo cliff). Cleaner fix
  needs a `molecule_id` array on Simulation.
- (b) No rotation control in placement UX (right-drag-to-rotate is the
  natural extension; `rotation` field already plumbed through
  AddMoleculeCommand).
- (c) MoleculeBuilderDialog's atom-mode material dropdown doesn't follow
  `session.active_material`; uses first material in the palette instead.

## Progress Log

### [start] Session-start checklist
- Created session folder
- Updated CURRENT_SESSION pointer
- Read all required QMS docs + prior session notes
- Verified inbox empty
- Flagged PROJECT_STATE.md bloat (carried from last session)

### PROJECT_STATE.md pruning (Lead-requested)
- Old file: 40927 tokens — exceeded the 25k Read-tool limit (could not
  read in a single call). Read full file in chunks to understand
  structure.
- Bloat sources identified:
  - §2 Current Status: six multi-page session-level paragraphs that
    re-litigated round-by-round detail already living in session notes.
    Each was 1-3k tokens.
  - §3 Arc to Date: dense phase narrative going back to January, each
    phase a paragraph.
  - §4-8: reasonable density, mostly fine.
- New file: 218 lines, 22602 bytes (~5-6k tokens). Reduction ~85%.
- Rewrite approach:
  - §2 collapsed to per-CR one-paragraph status (CR-116 IN_EXECUTION
    + CR-115/114/113/112 closed). Removed all round-by-round session
    paragraphs.
  - §3 compressed to bullet-list phases, one sentence each. Grouped
    related adjacent phases.
  - §4 trimmed redundant subsections (App+UI, Test surface).
  - §5-8 retained intact with minor tightening; §6 immediate items
    re-ordered to put CR-116 status at top, removed redundant
    sub-numbering (5a/5b/5c/5d collapsed into items 4-6).
- Verified post-write: full file now reads in a single Read tool call.
- No information lost — all session-level detail still lives in
  `.claude/sessions/{ID}/notes.md` per CLAUDE.md mandate.

**Files touched:** `.claude/PROJECT_STATE.md` (rewrite).

### Molecule-palette dropdown click-fall-through fix (CR-116 EI-3)

Lead reported: clicking the bottom-most item in the molecule selector
dropdown lands on the brush material atom-type selector below instead.

**Diagnosis.** `Dropdown` is registered as an `OverlayProvider` —
`UIManager.overlays` holds it, and `_draw_overlays` draws the expanded
list above other widgets. But events flowed only through
`ui.root.handle_event(event)`, which dispatches to children in
**reverse order** (`UIContainer.handle_event` line 241). In the right
panel, `molecule_palette` is added BEFORE `sld_brush` and
`material_widget`; reverse iteration visits `material_widget` →
`sld_brush` → `molecule_palette`. The molecule dropdown's expanded
overlay (6 entries × 28 px = 168 px) overlaps `btn_builder` (same
container, fine), `sld_brush`, and the top ~73 px of `material_widget`.
A click on the bottom-most overlay item lands inside
`material_widget.rect`, which consumes the click before the molecule
palette ever sees it.

**Fix.** New `UIManager.try_dispatch_to_overlay(event)` gives registered
overlays first crack at `MOUSEBUTTONDOWN` events that land inside their
`get_overlay_rect()`. `InputHandler._attempt_handle_hud` calls it
between the menu-bar dispatch and the tree dispatch. Only
`MOUSEBUTTONDOWN` is routed; `MOUSEMOTION` / `MOUSEBUTTONUP` still flow
through the tree so hover-state on overlay items continues to work via
tree dispatch reaching the Dropdown. The dispatch iterates a snapshot
of `self.overlays` (`list(...)`) because the Dropdown's `expanded.setter`
unregisters itself when the selection collapses the list — mid-iteration
mutation would otherwise skip an entry.

**Tests added (+5, all green):**
- `TestOverlayDispatch.test_overlay_consumes_click_in_expanded_rect` —
  direct case, no siblings
- `test_overlay_dispatch_runs_before_tree_for_click_under_overlay` —
  the bug-pinning test: a sibling InputField at y in [140, 180) overlaps
  the bottom dropdown option's rect; without overlay-first dispatch the
  InputField would steal the click. Verifies dropdown.selected_index=2
  AND sibling.active is False.
- `test_overlay_dispatch_skips_click_outside_overlay_rect` — clicks well
  below the overlay rect fall through (return False)
- `test_overlay_dispatch_only_routes_mousebuttondown` — MOUSEMOTION /
  MOUSEBUTTONUP don't consume via this path
- `test_overlay_dispatch_safe_when_overlays_list_mutates` — the
  Dropdown's expanded setter unregisters itself mid-handle_event; the
  dispatch must iterate a snapshot

**Files touched:**
- `ui/ui_manager.py` — new `try_dispatch_to_overlay` method
- `ui/input_handler.py` — `_attempt_handle_hud` calls it before tree
  dispatch
- `tests/test_input_dispatch.py` — `_OverlayHarness` (minimal harness
  binding `try_dispatch_to_overlay` without full UIManager construction)
  + new `TestOverlayDispatch` class with 5 tests

**Suite:** 801 → **806 passing + 1 skipped** (+5).

### R1: Per-pair LJ ε cross-overrides (CR-116 EI-3)

Lead picked R1 of the emergent-phenomena plan: add the mechanism that
breaks Berthelot's geometric-mean ε mixing rule on a per-material-pair
basis. This is the load-bearing engine addition that unlocks oil-water
demixing, micelle formation, and wetting — all of which need
ε_AB < √(ε_AA·ε_BB) to overcome miscibility.

**Design.**
- **Storage:** `Sketch.lj_cross_overrides: dict[frozenset({mat_a, mat_b}), float]`
  parallel to the existing `bond_defaults` pattern. Empty by default →
  L-B everywhere.
- **Stable per-atom id:** `Simulation.atom_material_id: int32[N]` carries
  the position-in-insertion-order of the atom's material in
  `sketch.materials`. -1 means "no material" (legacy bare-Sim paths) →
  kernel falls back to per-atom ε_sqrt geometric mean.
- **Effective ε matrix:** `Simulation.eps_ij_matrix: float32[M, M]` is
  built by `Sketch.build_eps_ij_matrix()` and pushed by Scene during
  `__init__` and on every `rebuild()`. Entry (i, j) is the override if
  registered, else L-B from materials' own ε.
- **Kernel:** both `integrate_n_steps` and `integrate_n_steps_newton3`
  take new `atom_material_id` + `eps_ij_matrix` params. LJ inner loop:
  `if n_mat>0 and mat_i,mat_j in range: e_24 = 24·eps_ij_matrix[mat_i, mat_j]`
  else fall back to `24·eps_sqrt_i·eps_sqrt_j`. σ_ij stays Lorentz
  arithmetic-mean (not overridden in R1; the σ side is the natural R2
  extension).

**Plumbing through atom-creation sites:**
- `Simulation._add_particle(material_id=-1)` — new kwarg.
- `Compiler._compile_line/_compile_circle` resolve `mat.name` →
  `sketch.get_material_index(name)` and pass through `_add_tethered_atom`
  / `_add_static_atom`.
- `Source._try_spawn_particle` resolves via the owning Scene's sketch.
- `Scene.paint_particles` resolves from the material dict's `name` key
  and passes through `ParticleBrush.paint`.
- `AddMoleculeCommand.execute` resolves each template atom's
  `material_name`.

**Lifecycle plumbing:**
- `Simulation._resize_arrays` grows `atom_material_id` (new slots = -1).
- `compact_arrays` slices `atom_material_id` alongside the rest.
- `snapshot` / `_push_to_stack` / `_restore_physics_state` save/restore
  `atom_material_id`. Pre-R1 snapshots without the key restore to -1.
- `to_dict` / `restore` serialize `atom_material_id` with the same
  pre-R1 back-compat behaviour.
- `spatial_sort` permutes `atom_material_id` alongside the eight other
  per-atom arrays.
- `_warmup_compiler` passes an empty matrix and the -1 material_id slice
  so the kernel JITs both branches (matrix path AND fallback path).

**Tests added (+31, all green):** `tests/test_lj_cross_overrides.py`
- `TestSketchLjCrossOverrides` (7) — defaults empty, set/get/remove,
  order-independence via frozenset, unknown-material fallback.
- `TestSketchEpsMatrixBuild` (4) — shape, diagonal-is-ε, symmetric
  L-B without overrides, override reflected at (i,j) and (j,i).
- `TestSketchSerialization` (2) — round-trip, pre-R1 saves restore
  with empty overrides.
- `TestSketchGetMaterialIndex` (2) — insertion-order position,
  unknown returns -1.
- `TestSimulationMaterialIdArray` (3) — defaults to -1,
  _add_particle stores material_id, default is -1.
- `TestSimulationEpsMatrix` (4) — default (0,0), float32 coercion,
  None resets, non-square rejected.
- `TestSimulationMaterialIdLifecycle` (4) — compact_arrays slice,
  snapshot/undo preserves, to_dict round-trip, pre-R1 restore is -1.
- `TestKernelUsesOverrideEpsilon` (3) — the bug-pinning tests:
  - attractive cross-ε (4.0 vs L-B's 1.0) pulls atoms closer than
    the L-B baseline after 200 substeps
  - near-zero cross-ε with atoms started inside r_min still
    separates them (repulsive core still active, just weak)
  - material_id=-1 atoms ignore the matrix → trajectory identical to
    a no-matrix reference run
- `TestSceneIntegration` (2) — Scene.__init__ pushes the matrix;
  Scene.rebuild picks up a new override.

**Deferred (not in R1 scope):**
- σ_ij override (Lorentz break) — R2 extension; would let cross-pairs
  have different equilibrium spacing
- Phenomenological end-to-end demixing test — requires a tuned palette
  (R2/R3 work). The kernel-level tests above prove the mechanism;
  the phenomenology test will land alongside the R3 demo presets.
- UI for editing overrides — R3 (currently they're set programmatically
  via `sketch.set_lj_cross_override` or via a saved scene)

**Files touched (8 modified, 1 new):**
- `model/sketch.py` — overrides dict, API, matrix builder, serialization
- `engine/simulation.py` — atom_material_id array, eps_ij_matrix,
  set_eps_ij_matrix method, plumbing through 8 lifecycle methods
- `engine/physics_core.py` — both kernels + spatial_sort signatures
- `engine/compiler.py` — material_id resolution + plumbing through
  _add_tethered_atom / _add_static_atom
- `engine/particle_brush.py` — paint accepts material_id, _add_particle
  writes it
- `core/scene.py` — rebuild pushes matrix; __init__ pushes initial
  matrix; paint_particles resolves material_id from material dict
- `core/molecule_commands.py` — AddMoleculeCommand resolves per-atom
  material_id from template's material_name
- `model/process_objects.py` — Source._try_spawn_particle resolves
  material_id from owner Scene's sketch
- `tests/test_lj_cross_overrides.py` (new)

**Suite:** 806 → **837 passing + 1 skipped** (+31).

### R2: Emergent-phenomena palette (CR-116 EI-3)

Layered onto R1's cross-ε mechanism: new materials, seeded cross-pair
overrides, and three new coarse-grained molecules. A fresh Sketch now
ships with everything needed for the micelle / bilayer / oil-water demos
to work out of the box (place the molecules and let physics run).

**New PRESET_MATERIALS entries (`model/properties.py`):**
- **Polar** σ=1.0 ε=1.0 m=1.0 color=(80,200,255) — water-like solvent
- **Nonpolar** σ=1.0 ε=1.0 m=1.0 color=(240,180,80) — matched σ with Polar
  so demixing is purely a cross-ε effect (no size-mismatch confound)
- **Heavy** σ=1.2 ε=2.0 m=3.0 color=(110,110,130) — dense, slow, useful
  for Brownian / crystal-seed demos
- **LightGas** σ=0.8 ε=0.3 m=0.5 color=(200,240,220) — stays vapor at
  typical T

Legacy species (Water/Oil/Mercury/Honey/Wall) unchanged — back-compat
intact.

**Seeded cross-ε overrides (`Sketch._seed_default_lj_overrides`):**
- {Polar, Nonpolar} → 0.25  (immiscible — the workhorse oil-water pair)
- {Polar, LightGas} → 0.15  (gas barely dissolves in polar liquid)
- {Heavy, LightGas} → 0.20  (gas doesn't dissolve in dense fluid)
- {Nonpolar, Heavy} → 1.5   (above L-B's √2 — "oil dissolves grease")

Seeds fire only on fresh `__init__`, NOT on `restore()` — legacy saves
have no surprise overrides. Pre-R2 save files restore as `{}` and the
old behaviour (L-B everywhere) is preserved.

**New molecule helpers (`model/molecule.py`):**
- `make_surfactant(n_tail=4)` — linear 5-atom amphiphile: 1 Polar head
  + 4 Nonpolar tails. Mild angle springs (k=30) along the chain at 180°
  give a persistence length without rigid-rod behaviour, so the
  surfactant can curve around a micelle surface.
- `make_lipid()` — 6-atom Y-shape amphiphile: head (Polar) → neck
  (Polar) → 2 branching Nonpolar chains of 2 atoms each at 60° opening.
  5 bonds, 5 angles. Splits head/neck so the molecule can hinge at the
  head-neck bond to pack into curved bilayer surfaces.
- `make_polymer(n=15)` — long bonded Nonpolar chain. Default material
  Nonpolar so the polymer collapses in Polar solvent ("bad solvent" /
  θ-condition mimicry); override `material="Polar"` for a soluble chain.

All three seeded into `Sketch._seed_default_molecules` so a fresh
Sketch ships with 9 starter molecules (was 6).

**Tests added (+40, all green):** `tests/test_r2_palette.py`
- `TestNewMaterials` (6) — Polar/Nonpolar/Heavy/LightGas presence and
  exact design parameters; Polar/Nonpolar share σ; legacy materials
  still present.
- `TestSketchSeedsR2Materials` (1) — fresh Sketch carries all four R2
  species with stable material_ids.
- `TestSeededLjOverrides` (6) — the four seeded pairs return the
  designed values; unrelated pairs fall back to L-B; restore from a
  pre-R2 save clears the seeded overrides (no surprise overrides on
  legacy scenes).
- `TestMakeSurfactant` (7) — atom count, materials per position,
  collinearity, centring, bond-in-series structure, 180° interior
  angles, custom n_tail scales, validate.
- `TestMakeLipid` (8) — 6 atoms (2 Polar / 4 Nonpolar), head above
  neck, tails below neck, V-shape splay, exactly 5 bonds with correct
  pairs, 5 angles, validate, custom tail_branch_angle setting.
- `TestMakePolymer` (6) — 15-atom default chain, all Nonpolar,
  collinear and centred, n−1 bonds in series, n−2 180° angles,
  custom material override, validate.
- `TestSketchSeedsR2Molecules` (3) — Surfactant/Lipid/Polymer in
  palette; legacy molecules still present; total count == 9.
- `TestR2MoleculePlacementUsesOverrides` (3) — placed Surfactant
  atoms carry the Polar / Nonpolar material_id correctly; placed
  Lipid has 2 Polar + 4 Nonpolar; Scene.simulation.eps_ij_matrix
  shows the seeded 0.25 at (polar_id, nonpolar_id) immediately after
  Scene.__init__ — end-to-end R1+R2 integration smoke test.

**Files touched (3 modified, 1 new):**
- `model/properties.py` — 4 new entries in PRESET_MATERIALS
- `model/sketch.py` — import new molecule helpers, seed them in
  `_seed_default_molecules`, new `_seed_default_lj_overrides` method
  called from `__init__`
- `model/molecule.py` — 3 new helper functions + R2 section comment
- `tests/test_r2_palette.py` (new)

**Suite:** 837 → **877 passing + 1 skipped** (+40).

**Deferred from R2 (for R3):** demo scenario presets ("Demixing,"
"Micelles," "Crystal anneal" buttons); color-by-molecule_id UI toggle.
End-to-end phenomenology test for micelle formation also deferred to
R3 — needs the demo preset to control initial conditions reliably.

### R3: Demo presets + demixing phenomenology (CR-116 EI-3)

One-call setup of canonical emergent-phenomena scenarios. Each preset
clears the simulation, sets physics params, and seeds an initial state
that exhibits the target phenomenon under the R1+R2 engine. Deterministic
when given a `seed`.

**New module: `core/demo_presets.py`** — three preset functions plus
helpers (`_seed_rngs`, `_clear_dynamic_and_compiled`, `_grid_positions`,
`_maxwell_boltzmann_velocity`):

- **`preset_demixing(scene, n_per_species=80, target_temp=0.5, seed=None)`**
  — 50:50 Polar+Nonpolar atomic mixture on a jittered grid at 1.3σ
  spacing. Reflecting walls, mild damping (0.995), thermostat on, no
  gravity. With the R2 seeded ε_AB=0.25, atoms phase-separate over a
  few seconds of sim time.

- **`preset_micelles(scene, n_solvent=100, n_surfactant=12, target_temp=0.5)`**
  — Polar solvent atoms on a grid + Surfactant molecules at random
  positions/rotations using `AddMoleculeCommand`. ~10-15% surfactant by
  molecule count is the sweet spot for micelle formation. Each Surfactant
  contributes 1 head + 4 tails (5 atoms, 4 bonds, 3 angles).

- **`preset_crystal_anneal(scene, n_atoms=120, target_temp=1.5, material="Polar")`**
  — Single-species LJ fluid started at high T (default 1.5). User dials
  target_temp down to drive crystallisation. damping=0.999 (almost
  elastic) so the fluid thermalises across cooling sweeps. `material`
  param accepts any Sketch material; Heavy gives deeper LJ wells →
  crystallises at higher T.

All three presets call `sim.set_eps_ij_matrix(sketch.build_eps_ij_matrix())`
after spawning so the kernel sees the current (possibly user-edited)
cross-pair overrides. `sim.clear(snapshot=True)` keeps the action
undoable via Ctrl+Z.

**Tests added (+20, all green):** `tests/test_demo_presets.py`
- `TestPresetDemixing` (8) — atom counts, material_ids, physics params,
  Maxwell-Boltzmann initial velocities, within-bounds placement,
  seed determinism, idempotent re-runs replace prior state, eps_ij_matrix
  carries the seeded override (R1+R2+R3 integration smoke test).
- `TestPresetMicelles` (6) — solvent count, surfactant count + atom
  count (= 5×molecules), total count consistency, material_id
  breakdown (4 heads + 16 tails for 4 surfactants + 20 polar solvent),
  bonds + angles attached (3 surfactants → 12 bonds + 9 angles),
  physics params.
- `TestPresetCrystalAnneal` (5) — atom count, all atoms share material,
  custom material override (Heavy → σ=1.2), high target_temp set,
  thermostat enabled.
- `TestDemixingPhenomenology` (1) — **end-to-end phenomenology**: run
  preset_demixing → simulate 25 × 200 = 5000 substeps → verify that
  the mean distance to the k=4 nearest LIKE neighbours is smaller
  than the mean distance to the k=4 nearest UNLIKE neighbours AND
  that this gap grew from the initial state. With R1's mechanism +
  R2's matched-σ species + R2's seeded ε_AB=0.25, demixing is now
  a robust, repeatable signal. The R1-era end-to-end attempt failed
  because the legacy Water/Oil species have mismatched σ — the R2
  Polar/Nonpolar pair was designed specifically to isolate the cross-ε
  effect, and it works.

**Files touched (1 new, 1 new test file):**
- `core/demo_presets.py` (new) — preset functions + helpers
- `tests/test_demo_presets.py` (new)

**Suite:** 877 → **897 passing + 1 skipped** (+20).

**Deferred from R3 (future):**
- Color-by-molecule_id UI toggle. Would need a new `molecule_id` array
  on Simulation. Bonus suggestion from the design discussion; not
  load-bearing for the demos to work.
- Programmable thermostat schedule (target_temp ramp/hold/ramp) —
  natural extension for the crystal-anneal preset; currently the user
  drives cooling manually.
- Live order-parameter HUD readouts (RDF peak detector, etc.).

### UI wiring for R1+R2+R3 (CR-116 EI-3)

Lead requested UI access to all the new features. Wired up the menu
bar, controller dispatch, and a modal dialog for ε-tuning.

**Surfaces verified auto-working via existing widgets (no UI code
needed — sketch.materials / sketch.molecules are the source of truth):**
- New R2 materials (Polar / Nonpolar / Heavy / LightGas) appear in
  the MaterialPropertyWidget dropdown (right panel) and in the Source
  Properties dialog material picker. They're in PRESET_MATERIALS so
  every Sketch ships with them.
- New R2 molecules (Surfactant / Lipid / Polymer) appear in the
  MoleculePaletteWidget dropdown (right panel). The palette reads
  `sketch.molecules` at refresh time, which is seeded with all 9
  templates in `Sketch._seed_default_molecules`.

**New UI surfaces added:**
- **Menu bar `Demos` category** with three items: Demixing, Micelles,
  Crystal Anneal. Each one-click. Names kept short so they fit the
  180px menu dropdown; the status bar prints the full description
  ("Demixing demo: 80 Polar + 80 Nonpolar — hit Play") on selection.
- **Menu bar `Tools` category** populated for the first time — entry
  point for the Cross-ε Overrides editor.
- **`LjOverrideDialog` modal** (new file `ui/lj_override_dialog.py`)
  — view + edit per-pair ε. Features:
  - Two Material dropdowns (A, B); changing either auto-refreshes the
    ε input field to the live effective value (override if set, else
    L-B). User sees what's in effect before editing.
  - Numeric input field for ε value (defaults to 2 dp display via
    InputField.set_value's standard `:.2f` format).
  - Hint string under the input showing whether the pair is currently
    using an override or L-B baseline, plus the L-B reference value.
  - Apply button → calls `sketch.set_lj_cross_override(...)`.
  - Reset button → calls `sketch.remove_lj_cross_override(...)` so the
    pair falls back to L-B; auto-refreshes the input to the L-B value
    so an immediate Re-Apply doesn't re-introduce the just-removed
    override.
  - Active-overrides list panel (up to 7 rows + "and N more" overflow)
    showing every registered override sorted alphabetically by pair.
  - Same-material (diagonal) pairs are silently ignored on Apply —
    diagonal of the ε matrix is the material's own ε and shouldn't be
    overridden.
  - Non-positive ε clamped to 1e-3 floor on Apply — protects the LJ
    well from going pathological.

**Controller wiring (`app/app_controller.py`):**
- `AppController.run_demo_preset(name)` — dispatcher for `'demixing'`
  / `'micelles'` / `'crystal_anneal'`. Auto-switches to MODE_SIM via
  `self.app.switch_mode(...)` if needed so the user can hit Play right
  away. Updates `session.status` with a one-line summary including the
  resulting atom / molecule counts.
- `AppController.open_lj_override_dialog()` — pushes LjOverrideDialog
  onto the modal stack with tag `'lj_override_dialog'`.
- `AppController.apply_lj_override_dialog(dialog)` — called from the
  per-frame modal-poll loop when the dialog closes. Pushes the
  refreshed eps_ij_matrix to `sim.set_eps_ij_matrix(...)` so the
  kernel sees the changes on the next physics step. Early-returns
  with no work if `dialog.apply is False` (user opened + closed
  without modifications).

**Menu dispatch (`ui/input_handler.py`):**
- Routes via `self.controller.actions.<method>` for the new menu items
  (controller is FlowStateApp; actions is AppController). Distinct from
  the existing File-menu pattern where methods live directly on
  FlowStateApp.

**Tests added (+21, all green):**
- `tests/test_lj_override_dialog.py` (13 tests):
  - Construction (3) — full sketch, initial pair distinct, input field
    seeded with current effective ε
  - Apply (3) — writes override, same-material noop, negative-ε floor
  - Reset (3) — drops existing override, safe-noop on no-override pair,
    refreshes input to L-B value
  - Done flag (3) — apply starts False, becomes True after mutation,
    Done button click sets done=True
  - Dropdown refresh (1) — switching either dropdown updates the input
    field to the new pair's effective ε
- `tests/test_ui_wiring.py` (8 tests):
  - run_demo_preset (5) — each preset populates the right atom count,
    unknown preset is safe noop, MODE_SIM switch fires from editor mode
  - open_lj_override_dialog (3) — modal pushed with correct type tag,
    apply pushes updated matrix to sim when dialog modified, apply is
    a noop when dialog not modified

**Files touched (3 modified, 2 new, 2 new tests):**
- `ui/ui_manager.py` — added `Tools` + `Demos` menu categories
- `ui/input_handler.py` — added menu dispatch cases routing through
  `controller.actions.*`
- `app/app_controller.py` — added `run_demo_preset`,
  `open_lj_override_dialog`, `apply_lj_override_dialog`; modal-poll
  loop handles the new `lj_override_dialog` type
- `ui/lj_override_dialog.py` (new)
- `tests/test_lj_override_dialog.py` (new)
- `tests/test_ui_wiring.py` (new)

**Suite:** 897 → **918 passing + 1 skipped** (+21).

**Session totals for 2026-05-11-001:**
- R1 +31 (mechanism)
- R2 +40 (palette)
- R3 +20 (presets)
- UI +21 (menu + dialog)
- Earlier fixes: +5 (overlay-dispatch click-fallthrough)
- **Total: +117 tests** (801 → 918 passing + 1 skipped)

### Menu dropdown render-order fix (2026-05-12)

Lead reported: "The demos button as well as the entire file menu isn't
working — it renders behind other elements and cannot be clicked
properly."

**Diagnosis.** The MenuBar is `self.root`'s first child, so its
`draw()` runs during the tree-order pass BEFORE other children (panels,
viewport). The original `MenuBar.draw()` painted the dropdown body
inside that same call, so the dropdown rendered first and then panels
painted over it. Events routed correctly (the menu's `handle_event`
gets first crack via `_attempt_handle_hud`'s menu-bar special case),
but the user was clicking blind because the dropdown was visually
hidden behind panels. Same class of bug as the molecule-palette
fallthrough — render-order issue, not event-order.

**Fix.**
- **`MenuBar.draw()` now draws only the bar** (background, top-bar
  labels) and keeps `dropdown_rect` up-to-date every frame for
  hit-testing.
- **New `MenuBar.draw_dropdown_overlay()`** does just the dropdown
  body rendering (shadow, panel, items, hover highlight). No-op when
  `active_menu is None` or `dropdown_rect is None`.
- **`UIManager._draw_overlays()`** calls `self.menu.draw_dropdown_overlay()`
  after the registered OverlayProviders so the menu dropdown lands on
  top of every other UI surface — including expanded Dropdowns from
  the right panel.
- **Render-pipeline order in `FlowStateApp.render()` swapped**: now
  draws `ui._draw_overlays` BEFORE `actions.draw_overlays` (modals).
  Modals stay on top of the menu — desirable since they're also
  blocking input via the Modal layer, so the visual stacking matches
  the event-priority stacking.
- **`dropdown_rect` is cleared to `None` when `active_menu` becomes
  `None`** so stale clicks can't fire phantom items.

**Tests added (+11, all green):** `tests/test_menu_overlay.py`
- `TestMenuBarDrawSplit` (5):
  - `draw()` keeps dropdown_rect up-to-date for hit-testing but
    doesn't paint the body
  - `draw_dropdown_overlay()` is a no-op when inactive (no
    dropdown_rect needed)
  - `dropdown_rect` clears to None when the menu closes
  - dropdown_rect.x aligns with the active top-bar item's x
  - `draw_dropdown_overlay()` actually paints pixels when active
    (framebuffer-pixel-difference sanity check)
- `TestDropdownClickFlow` (3):
  - MOUSEMOTION inside dropdown sets `hover_item_idx`
  - MOUSEBUTTONDOWN on a hovered item returns the item label and
    closes the menu
  - MOUSEBUTTONDOWN outside the dropdown closes the menu
- `TestUIManagerDrawsDropdownLast` (3):
  - `_draw_overlays` invokes `menu.draw_dropdown_overlay` (spy)
  - Safe when the shim has no `menu` attribute (defensive
    `hasattr` guard)
  - Safe when `menu is None` (defensive None guard)

**Files touched (3 modified, 1 new test file):**
- `ui/ui_widgets.py` — `MenuBar.draw()` split + new
  `draw_dropdown_overlay()` method
- `ui/ui_manager.py` — `_draw_overlays()` calls
  `menu.draw_dropdown_overlay()` last
- `app/flow_state_app.py` — `render()` re-orders so `ui._draw_overlays`
  runs before `actions.draw_overlays` (modals stay topmost)
- `tests/test_menu_overlay.py` (new)

**Suite:** 918 → **929 passing + 1 skipped** (+11).

**Updated session totals for 2026-05-11-001 + 2026-05-12:**
- R1 +31, R2 +40, R3 +20, UI +21, Overlay click-fallthrough +5,
  Menu render-order +11 = **+128 tests** (801 → 929)

### Menu hit-detection drift fix (2026-05-12)

Lead reported a follow-up after the render-order fix: "clicking Demos
opens the (empty) Help menu to its left."

**Diagnosis.** Two compounding bugs:

1. **`MenuBar.handle_event` rebuilt `item_rects` with a fixed width=60
   per item** (line 1033, pre-fix) — but `MenuBar.draw()` rebuilt the
   same dict with the actual text width (`ts.get_width() + 20`). With
   variable-width labels, the two dicts diverged: hit-rects in
   handle_event drifted to the RIGHT of the visible labels in draw.
   Clicking visually on "Demos" (x ≈ 192-262) actually hit the
   handle_event rect for "Help" (x ≈ 145-205).

2. **`MenuBar.__init__` seeded `Help: []` by default.** UIManager never
   populated it, but the empty category still rendered as a clickable
   label in the bar with a hit-rect. That's the "(empty) Help menu"
   the user saw.

**Fix.**
- **Deleted the duplicate `item_rects` rebuild in `handle_event`.**
  The render-runs-before-input ordering means draw()'s actual-width
  item_rects are always current by the time the user clicks.
  Documented the constraint with a NOTE comment to prevent regression.
- **Default `MenuBar.items` is now `{"File": []}`** instead of
  `{"File": [], "Tools": [], "Help": []}`. Callers add the categories
  they actually populate.
- **`draw()` skips categories with empty option lists.** Defensive
  even after the default cleanup — if a future caller adds an empty
  category mid-development, it won't render as a ghost-clickable item.

**Tests added (+8, all green):**
- `TestHitRectMatchesVisualLabel` (4):
  - `handle_event` no longer overwrites `item_rects` set by `draw`
  - Clicking the centre of the "Demos" visible label opens Demos
    (the literal bug-pinning test for the Lead's report)
  - Sweep: each item's centre click opens its own menu (covers
    File, Tools, Demos)
  - No two item_rects overlap (mathematical guarantee that the
    drift bug can't recur)
- `TestEmptyCategoriesSkipped` (4):
  - Empty category absent from `item_rects` after draw
  - Click at the gap where an empty category would have been
    doesn't activate it
  - `Help` is no longer a default key on a fresh MenuBar
  - Categories added after construction render in insertion order
    with strictly-increasing x positions

**Files touched (1 modified):**
- `ui/ui_widgets.py` — `MenuBar.__init__` default cleanup,
  `MenuBar.handle_event` duplicate item_rects rebuild removed,
  `MenuBar.draw()` skips empty categories
- `tests/test_menu_overlay.py` — `TestHitRectMatchesVisualLabel` +
  `TestEmptyCategoriesSkipped` classes

**Suite:** 929 → **937 passing + 1 skipped** (+8).

**Updated session totals:** **+136 tests** (801 → 937)
