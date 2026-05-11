# Session-2026-05-10-002

## Current State (last updated: end of session — Lead validated + commits pushed)
- **Active document:** CR-116 IN_EXECUTION v1.2 — Exploration CR (beach-trip Flow State work)
- **Current EI:** EI-3 (free-form exploration) — still open
- **Blocking on:** Nothing — Lead validated the GUI ("This largely works!") after
  the Dropdown.on_change two-arg signature fix; all work committed and pushed
- **Next:** Lead to decide (continue CR-116 exploration, address known
  limitations, or close out CR-116 for qualification)
- **Subagent IDs:** none active
- **Branch state:**
  - `.test-env/flow-state/` on `cr-116-beach-trip-exploration` — uncommitted molecule
    builder work atop `5298dce`
  - Suite at **756 passing + 1 skipped** (was 653 + 1 → +103 tests this session)
- **pipe-dream branch:** `main` — `M .claude/settings.local.json` only

## Session-start checklist
- New day relative to most recent committed work; second session of 2026-05-10 → Session-2026-05-10-002
- CURRENT_SESSION updated to `Session-2026-05-10-002`; session folder created
- Read SELF.md, Session-2026-05-10-001/notes.md, QMS-Policy.md, START_HERE.md, QMS-Glossary.md, PROJECT_STATE.md
- Inbox: empty
- No compaction-log in this folder → genuine new session

## Concerns to surface to Lead
- **PROJECT_STATE.md has grown to ~29k tokens** — violates CLAUDE.md's "keep concise / prune
  aggressively" mandate. §2 Current Status alone is multi-page paragraphs of session-level detail
  that the doc explicitly says it should not accumulate ("does not accumulate session-level detail
  — for that, read the relevant session's notes.md"). The Session-2026-05-10-001 paragraph in §2
  is itself nearly the entire round-by-round breakdown that already lives in
  Session-001/notes.md. **Recommendation:** during this session or the next, compress §2 to
  per-CR one-paragraph status and let session notes carry the round-level detail. Don't do this
  unilaterally — needs Lead confirmation.

## Progress Log

### [start] Session-start checklist
- Created session folder
- Updated CURRENT_SESSION pointer
- Read all required QMS docs + prior session notes
- Verified inbox empty
- Flagged PROJECT_STATE.md bloat (see above)

## Direction picked: Molecule Builder (under CR-116 EI-3)

Lead wants a molecule builder feature. Once created, molecules can be placed
like single atoms can. Starting with one bond type: harmonic spring (k, r_eq).

**Lead scope decisions:**
- Builder UX = modal dialog (mini-canvas inside a dialog, mirrors
  SourcePropertiesDialog pattern)
- Per-atom material (each atom in a molecule can have its own material)
- Per-bond k/r_eq with default from a global material-pair table

**Plan:** 4 rounds under CR-116 EI-3.
- R1: engine — bond arrays + spring kernel + plumbing
- R2: data model + placement tool (hardcoded molecules first)
- R3: builder modal dialog
- R4: right-panel molecule palette + integration

### Round 1: Engine — bond arrays + spring kernel + plumbing ✅

**Files modified:**
- `engine/physics_core.py` — new `apply_spring_bonds` @njit (serial; per-bond
  writes to two atoms would race under prange). Wired into both
  `integrate_n_steps` (after Phase 3 LJ pair loop, before Phase 4 half-vel
  update) and `integrate_n_steps_newton3` (after Phase 4 force merge, before
  Phase 5 half-vel update). Same placement contract in both kernels. PBC
  minimum-image dx/dy supported. Static atoms (is_static==1) skipped on the
  write side, matching the LJ-loop pattern. Coincident-atom guard
  (r2 < 1e-12) skips rather than divide-by-zero.
- `engine/simulation.py` — new `bond_capacity` / `bond_count` / `bond_i` /
  `bond_j` / `bond_k` / `bond_r_eq` arrays alongside the existing atom
  arrays. New methods: `add_bond(i, j, k, r_eq)` (rejects self-bonds with
  -1), `remove_bond(b)` (swap-with-last), `clear_bonds()`,
  `_resize_bond_arrays()`. Plumbing extended through:
  - `clear()` — drops bonds (stale atom indices)
  - `compact_arrays(keep_indices)` — builds old→new index remap, rewrites
    bond_i/j for surviving bonds, drops bonds where either endpoint is
    removed via remove_bond(b)
  - `snapshot()` / `_push_to_stack()` / `_restore_physics_state()` — bonds
    are saved/restored alongside atoms. Pre-R1 snapshots without bond keys
    are handled gracefully (default to bond_count=0).
  - `to_dict()` / `restore()` — same back-compat treatment
  - `step()` — both classic and Newton-3 paths now pass bond arrays sliced
    to bond_count; empty bond list (bond_count==0) costs only a single
    bond-loop header check per substep
  - `_warmup_compiler()` — passes zero-length bond arrays so the kernel
    JIT-compiles for the bondless fast path
- `benchmarks/breakdown.py` — call site updated to match new kernel
  signature. Also fixed a pre-existing Round-8 staleness here
  (`np.float32(config.ATOM_MASS)` scalar → `sim.atom_mass[:sim.count]`
  array). Benchmark wasn't crashing because it isn't in the test suite, but
  the kernel signature mismatch would have broken it at first invocation.

**Tests added (+24, all green):**
- `TestBondArrayConstruction` (7): defaults, dtypes, add_bond return value
  + advance, self-bond rejection, remove_bond swap-with-last, clear_bonds,
  clear() drops bonds, _resize_bond_arrays preserves data and doubles
  capacity
- `TestSpringForceKernel` (7): force=0 at equilibrium, stretched pulls
  atoms together (verifies sign of force on both atoms), compressed pushes
  apart, Newton's 3rd law per-component, static atom skip (dynamic partner
  still feels pull, static slot stays zero), both-static bond skipped,
  PBC minimum-image (bonded atoms on opposite sides of periodic box
  experience min-image force, not in-domain)
- `TestSpringBondIntegration` (2): end-to-end through Simulation.step —
  bonded pair accelerates toward each other when stretched; bondless
  simulation behaviour unchanged from pre-R1 (regression case)
- `TestCompactArraysRemapsBonds` (3): surviving bond indices rewritten
  through keep_indices remap; bond dropped when either endpoint is
  removed; compact with no bonds is a no-op
- `TestBondSerializationRoundTrip` (4): snapshot/restore round-trip,
  to_dict/restore round-trip, pre-R1 saves treated as bond_count=0,
  undo/redo preserves bonds
- `TestSpringOscillation` (1): bonded pair displaced from equilibrium
  passes through r=r_eq within bounded substeps — sanity check that the
  kernel is actually invoked and bond forces participate in the Verlet
  update

**Suite:** 653 → **677 passing + 1 skipped** (+24).

**Branch state:** `.test-env/flow-state/` on `cr-116-beach-trip-exploration`,
uncommitted (Lead preference: no commit until asked).

**Status:** R1 complete. R2 (data model + placement tool) next.

### Round 2: Molecule data model + placement tool ✅

**Files created:**
- `model/molecule.py` — `MoleculeAtom`, `MoleculeBond`, `MoleculeTemplate`
  dataclasses with `to_dict` / `from_dict` round-trip and a
  `validate()` integrity check. Builder helpers `make_diatom()` and
  `make_water()` for seeded starter palette entries.
- `core/molecule_commands.py` — `AddMoleculeCommand`. Places N atoms +
  M bonds at a world position with optional rotation. Material
  parameters (sigma, epsilon, mass, color) resolved via
  `sketch.get_material(atom.material_name)` at execute time. Undo uses
  count truncation: stores `pre_atom_count` and `pre_bond_count` at
  execute, restores them at undo. **Documented limitation:** if other
  particle-adding operations happen between execute and undo, those
  particles are lost. Matches the existing brush-undo cliff (sim.undo
  also restores a full pre-stroke snapshot).
- `ui/molecule_tool.py` — `MoleculeTool`. Single-click placement of the
  currently-selected molecule template at the click world position.
  Live preview overlay shows atoms + bonds at the cursor before the
  click. Y-gate matches Source/Sink tools (ignores clicks in menu bar
  / panels). `set_template(template)` selects the template; `activate()`
  defaults to the first molecule in `sketch.molecules` if none selected.

**Files modified:**
- `model/sketch.py` — new `molecules: dict[str, MoleculeTemplate]` and
  `bond_defaults: dict[frozenset[str], (k, r_eq)]`. `_seed_default_molecules`
  populates the starter palette with Diatom + Water-mol. `get_molecule`,
  `add_molecule`, `remove_molecule` API. `get_bond_default(mat_a, mat_b)`
  uses sigma-average fallback when no override exists; `set_bond_default`
  records pair overrides. `to_dict` / `restore` extended to serialize
  molecules and bond_defaults (back-compat: pre-R2 saves re-seed the
  starter palette so the user isn't left with an empty palette).
- `shared/config.py` — `TOOL_MOLECULE = 9`.
- `app/flow_state_app.py` — `MoleculeTool` registered in `init_tools()`
  via `HAS_MOLECULE_TOOL` import guard.
- `ui/input_handler.py` — `'molecule': config.TOOL_MOLECULE` added to
  the tool-button map; Shift+M global hotkey added (mirrors Shift+S
  Source / Shift+D Sink pattern).

**Tests added (+31, all green):**
- `TestMoleculeAtomRoundTrip` (1), `TestMoleculeBondRoundTrip` (1),
  `TestMoleculeTemplateRoundTrip` (1), `TestMoleculeTemplateValidate`
  (4 — diatom/water OK, out-of-range index fails, self-bond fails)
- `TestStarterMolecules` (3): diatom geometry matches r_eq, water is
  V-shaped 3-atom with two bonds from the central atom
- `TestSketchMoleculePalette` (5): defaults seeded, add overwrites by
  name, remove drops, unknown returns None
- `TestBondDefaultsTable` (5): sigma-average fallback, same-material
  pair, unknown name falls back via get_material, override beats
  fallback, order-independent (`frozenset` key)
- `TestSketchMoleculeSerialization` (2): round-trip preserves palette
  + overrides; pre-R2 saves re-seed starter molecules
- `TestAddMoleculeCommand` (7): places atoms + bonds, atom_mass /
  sigma / color from material, rotation transforms positions correctly,
  undo truncates to pre_count, redo restores, invalid template returns
  False with no partial mutation, bonds link to NEW (placement) atom
  indices not template-local
- `TestMoleculeIntegrationWithScene` (2): bond force pulls placed
  atoms together; undo through scene.commands removes molecule

**Suite:** 677 → **708 + 1 skipped** (+31).

**Status:** R2 complete. R3 (Builder dialog) next.

### Round 3: Molecule Builder modal dialog ✅

**Files created:**
- `ui/molecule_builder_dialog.py` — `MoleculeBuilderDialog`. Modal
  dialog with a mini-canvas (480×280 inside the 520×540 dialog) where
  the user places atoms and draws bonds.
  - **Atom mode** (default): click in canvas → adds a `MoleculeAtom`
    at the local coordinate, material from the dropdown. Overlap
    rejection via pixel-threshold check.
  - **Bond mode**: click atom → highlights; click another atom →
    creates a `MoleculeBond` with (k, r_eq) defaulted from
    `sketch.get_bond_default(mat_a, mat_b)`. Self-bonds and duplicates
    rejected. Most-recent bond becomes the "selected bond" whose
    `k`/`r_eq` are editable via two `InputField`s.
  - **Clear** button wipes the working template (atoms + bonds).
  - **Name** `InputField` at top.
  - **Save** commits the template to `Sketch.molecules` via
    `apply_to_sketch(sketch)` (pulls pending bond-input edits before
    saving). **Cancel** closes without modification.
  - Programmatic API for tests: `add_atom_local`, `begin_bond`,
    `complete_bond`, `cancel_pending_bond`, `clear_template`,
    `select_bond`, `apply_bond_input_edits`, `apply_to_sketch`,
    `set_mode`.
  - Coordinate transforms: `local_to_canvas` / `canvas_to_local` with
    Y inverted (molecule-convention positive y is up, pygame is down).
    Scale = `min(canvas_w, canvas_h) / CANVAS_VIEW_RANGE=8`.

**Files modified:**
- `app/app_controller.py` — `open_molecule_builder_dialog(template=None)`
  pushes the modal (centered on screen). `apply_molecule_builder_dialog`
  saves on Apply, refreshes the right-panel palette (R4 hook), updates
  status. Per-frame modal poll in `update()` checks the
  `molecule_builder_dialog` type and dispatches.

**Tests added (+34, all green):**
- `TestConstruction` (4): empty template defaults, mode defaults to
  'atom', existing template deep-copied (mutating dialog doesn't touch
  original), seeded dialog carries atoms+bonds
- `TestModeToggle` (4): set_mode atom/bond toggles button is_active,
  invalid mode ignored, mode switch clears pending bond
- `TestAtomPlacement` (5): add_atom_local appends, dropdown material
  applied, explicit override, overlap rejected (pixel-threshold), atoms
  at distinct positions both added
- `TestBondCreation` (6): begin+complete creates correctly indexed bond,
  self-bond rejected, duplicate rejected (unordered pair), defaults pulled
  from `sketch.bond_defaults`, `cancel_pending_bond` drops state, complete
  without begin no-ops
- `TestBondEditor` (4): new bond becomes selected, InputField text
  populated from selected bond, `apply_bond_input_edits` propagates
  values, non-positive k/r_eq rejected (keeps prior values)
- `TestClear` (1): clear_template empties atoms+bonds and resets
  selected/pending state
- `TestApply` (4): name field used, blank name keeps existing template
  name, save overwrites collision, pending input edits pulled before save
- `TestCoordinateTransforms` (4): canvas center ↔ local origin round-trip,
  y inverted, nearest-atom pick, pick returns None when far
- `TestBondSelection` (2): creating a second bond updates selected_bond
  index, `select_bond(idx)` repopulates InputFields

**Suite:** 708 → **742 + 1 skipped** (+34).

**Status:** R3 complete. R4 (right-panel palette + integration) next.

### Round 4: Right-panel molecule palette + integration ✅

**Files created:**
- `ui/molecule_palette_widget.py` — `MoleculePaletteWidget` (extends
  `UIContainer`). Right-panel surface for the molecule palette with:
  - Dropdown of molecule names from `sketch.molecules` (placeholder
    `"(no molecules)"` when empty)
  - "Molecule Builder..." button that opens
    `MoleculeBuilderDialog` via `controller.actions.open_molecule_builder_dialog()`
  - `refresh()` rebuilds dropdown options from the current sketch palette,
    preserving the currently-selected name when it still exists (falls
    back to index 0 otherwise)
  - `_on_select_molecule(name)` sets `MoleculeTool.template` and activates
    the tool via `controller.change_tool(TOOL_MOLECULE)`

**Files modified:**
- `ui/icons.py` — `draw_icon_molecule` (procedural). Three atoms in
  a triangle with bonds — recognisable "molecular cluster" silhouette
  without echoing Source's dashed circle or Sink's converging arrows.
  Registered as `'molecule'` in `PROCEDURAL_ICONS`.
- `ui/ui_manager.py` — imports `MoleculePaletteWidget`. Right panel now
  has a single-button row containing the molecule tool button
  (`self.tools['molecule']`) followed by the `MoleculePaletteWidget`
  (assigned to `self.molecule_palette`). Controller-less construction
  (e.g., in test contexts) leaves `molecule_palette = None`.
- `app/app_controller.py` — `apply_molecule_builder_dialog` now calls
  `app.ui.molecule_palette.refresh()` after a successful save so the
  new molecule appears in the dropdown without a UI rebuild. Graceful
  no-op when `ui` is None or has no `molecule_palette` attribute (test
  contexts).

**Tests added (+14, all green):**
- `TestConstruction` (3): dropdown seeded from sketch, builder button
  present, empty palette shows placeholder
- `TestRefresh` (3): refresh picks up new molecules; preserves
  selection by name when possible; falls back to index 0 when the
  selected name is removed
- `TestSelectionCallback` (4): selecting sets MoleculeTool.template
  and activates the tool, placeholder is no-op, unknown name is no-op
- `TestBuilderButton` (1): button click reaches
  `controller.actions.open_molecule_builder_dialog`
- `TestApplyRefreshesPalette` (2): apply path saves to sketch.molecules
  and calls `palette.refresh()`; cancel path saves nothing and does
  not refresh
- `TestEndToEnd` (1): full round-trip — author a triangle molecule in
  the dialog → save → select via palette → place via MoleculeTool →
  verify 3 atoms + 3 bonds in the Simulation

**Suite:** 742 → **756 + 1 skipped** (+14).

**Status:** R4 complete. All four rounds done.

## Final state (post-R4)

**Suite:** 653 → **756 passing + 1 skipped** (+103 tests across four rounds).

**New files (10):**
- `model/molecule.py`
- `core/molecule_commands.py`
- `ui/molecule_tool.py`
- `ui/molecule_builder_dialog.py`
- `ui/molecule_palette_widget.py`
- `tests/test_molecule.py`
- `tests/test_molecule_builder.py`
- `tests/test_molecule_palette.py`
- (Round 1 added bond tests to existing `tests/test_simulation.py`)
- (Round 1 added kernel to existing `engine/physics_core.py`)

**Modified files (8):**
- `engine/physics_core.py` — `apply_spring_bonds` + kernel-signature changes
- `engine/simulation.py` — bond arrays + plumbing
- `benchmarks/breakdown.py` — kernel call site
- `model/sketch.py` — molecules palette + bond_defaults + serialization
- `shared/config.py` — `TOOL_MOLECULE = 9`
- `app/flow_state_app.py` — MoleculeTool registration
- `ui/input_handler.py` — tool map + Shift+M hotkey
- `ui/icons.py` — `draw_icon_molecule`
- `ui/ui_manager.py` — right-panel wiring
- `app/app_controller.py` — open/apply dialog methods + palette refresh

**Lead in-GUI validation passed** — "This largely works!" after one fix:

**Bug found and fixed during GUI validation:**
- `Dropdown.on_change` calls back with `(index, name)` (two args, per
  `ui_widgets.py:834`), but `MoleculePaletteWidget._on_select_molecule`
  was defined with only `(self, name)`. Crash on first dropdown click.
  Fixed by accepting `(index_or_name, name=None)` and sniffing the call
  shape — handles both Dropdown's two-arg invocation AND the unit tests'
  single-arg call shape. Tests still green (14/14 in test_molecule_palette).

**Branch state:** `.test-env/flow-state/` on `cr-116-beach-trip-exploration`,
all R1-R4 work committed + pushed in four round-aligned commits.

**Known limitations (not fixed in this arc — flagged for follow-up if
Lead validates):**
- `AddMoleculeCommand.undo` is truncation-based; if other particle-adding
  operations happen between the place and the undo, those particles are
  lost. Matches the existing brush-undo cliff. Cleaner fix would be to
  add a molecule_id array on Simulation so atoms can be removed
  selectively.
- No rotation control in the placement UX. Right-drag-to-rotate would
  be a natural extension (MoleculeTool's `rotation` field is already
  threaded through AddMoleculeCommand).
- The default material in MoleculeBuilderDialog's atom-mode dropdown
  is the first one in `sketch.materials` (alphabetical or insertion
  order); doesn't follow the right-panel's active material. Could be
  wired up to `session.active_material` if Lead wants consistency.


