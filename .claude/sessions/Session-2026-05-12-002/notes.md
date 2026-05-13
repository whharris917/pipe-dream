# Session-2026-05-12-002

## Current State (last updated: after micelles pre-organized layout + phenomenology test)
- **Active document:** CR-116 IN_EXECUTION v1.2 — Exploration CR (beach-trip Flow State work)
- **Current EI:** EI-3 (free-form exploration) — open across sessions
- **Blocking on:** Awaiting Lead direction
- **Next:** Await Lead direction
- **Suite:** **968 passing + 1 skipped** (+27 cumulative this session)
- **Subagent IDs:** none active
- **Branch state:**
  - `.test-env/flow-state/` — `cr-116-beach-trip-exploration` — PBC density-spectrum demos + demo→UI sync + existing-demos PBC refactor + micelles empirical-driven rewrite **uncommitted** (7 files modified). Awaiting Lead before commit.
  - `pipe-dream/main` — clean, last commit `b886029` (Session-2026-05-12-001 PBC fix notes)

## Session-start checklist
- Today is 2026-05-12; previous session this date is Session-2026-05-12-001 → this session is Session-2026-05-12-002.
- CURRENT_SESSION updated; folder created.
- Read SELF.md, prior session notes (Session-2026-05-12-001), QMS-Policy.md, START_HERE.md, QMS-Glossary.md, PROJECT_STATE.md.
- Inbox: empty.
- No compaction-log in this folder → genuine new session.
- `git status` on pipe-dream clean before any session-init work.

## Known limitations carried from CR-116 EI-3
- (a) `AddMoleculeCommand.undo` truncation-based — loses any particles added between place and undo.
- (b) No rotation control in molecule placement UX.
- (c) `MoleculeBuilderDialog` atom-mode material dropdown doesn't follow `session.active_material`.

## Concerns to surface to Lead
- None new yet.

## Progress Log

### [start] Session-start checklist
- Created session folder, updated CURRENT_SESSION pointer.
- Read all required docs + prior session notes.
- Verified inbox empty and pipe-dream main clean.
- Awaiting Lead direction.

### PBC density-spectrum demos (CR-116 EI-3)

Lead asked: "Please add several demos that involve periodic boundary conditions and a dense liquid that fills the entire space at different densities."

**Design.** One parameterized `preset_pbc_liquid(scene, density, target_temp, material, seed)` doing all the heavy lifting; four thin controller wrappers picking canonical (ρ*, T) pairs:

| Menu item | ρ* | T | N (at L=50) | Regime |
|-----------|----|----|-------------|--------|
| PBC Sparse | 0.20 | 0.7 | 484 | Dilute gas/vapor |
| PBC Liquid | 0.50 | 0.7 | 1225 | Typical LJ liquid |
| PBC Dense | 0.80 | 0.7 | 2025 | Dense liquid near triple |
| PBC Packed | 1.00 | 1.2 | 2500 | Overcompressed — higher T to stay fluid |

Same material (Polar — σ=ε=mass=1, clean reduced LJ units) across all four; density is the only swept variable. T bumped to 1.2 at ρ*=1.0 to avoid freezing on contact (2D HCP transition is near T~0.7 at that density). The status bar reports actual N and achieved ρ*; small rounding loss from side-squared-integer (e.g. ρ*=0.5 → 35² = 1225 atoms → ρ* = 0.49).

**Key design choices.**
- **N from density, not user-set.** ρ* = N σ² / L². Compute side = round(L √ρ / σ); N = side². Tiles [0, L)² uniformly under PBC with grid pitch L/side (≥ σ for ρ ≤ 1, so no initial overlap).
- **New helper `_grid_positions_pbc_fill(side, L, jitter)`.** Distinct from the existing `_grid_positions` — that one centres a sub-tile inside the world (leaves vacuum at edges, fine for clustered demos but wrong for PBC-fill). The new helper covers [0, L)² uniformly, no edge bias, no centring; jitter to break lattice degeneracy.
- **`_pbc_safe` gate.** At default L=50 / cs=2.8, floor(L/cs)=17 ≫ 3, so PBC always sets. If the user shrinks the world below ~8.4, the preset falls back to REFLECTING and reports `pbc_set=False` in the return dict (no crash, no scary error).
- **Same physics knobs as crystal_anneal.** Gravity 0, damping 0.999 (near-elastic — no walls to bleed energy), thermostat on, MB-sampled initial velocities.

**Files touched (6 modified):**
- `core/demo_presets.py` — new `_grid_positions_pbc_fill` helper + new `preset_pbc_liquid` function. Module docstring extended.
- `app/app_controller.py` — 4 new branches in `run_demo_preset` (pbc_sparse / pbc_liquid / pbc_dense / pbc_packed) each calling `preset_pbc_liquid` with the canonical (ρ*, T) pair and setting a status-bar message.
- `ui/ui_manager.py` — 4 new items in the Demos menu category.
- `ui/input_handler.py` — 4 new elif branches in `_dispatch_menu`.
- `tests/test_demo_presets.py` — new `TestPresetPbcLiquid` class (12 tests).
- `tests/test_ui_wiring.py` — 3 new controller-dispatch tests.

**Test coverage (+15 tests):**
- TestPresetPbcLiquid (12): density-match at typical ρ*, count==side², monotonic-in-ρ*, PBC mode set, physics params, material id, atoms in [0, L), grid spans full box (not centred), nonzero MB velocity, deterministic seed, clears prior state, runs stably for 1000 substeps (no NaN, atoms stay wrapped).
- TestRunDemoPreset (3 new): pbc_sparse sets boundary_mode==2; all four presets give distinct monotonic atom counts; packed uses higher T than dense.

**Suite:** 941 → **956 passing + 1 skipped** (+15). Zero regressions across the full run (46s).

**Status of changes.** Working tree on flow-state `cr-116-beach-trip-exploration` has 6 modified files, uncommitted. Awaiting Lead before commit per the no-commit-unless-asked rule.

### Demo→UI sync fix (CR-116 EI-3, follow-up)

Lead flagged: "Ideally I wouldn't need to turn gravity off and set up periodic boundary conditions after loading the demo. The demo should fully define the simulation, not just the temperature and the initial configuration/identity of particles."

**Root cause.** `flow_state_app.update` reads UI widgets into `sim` every frame in MODE_SIM:
```python
sim.gravity = ui.sliders['gravity'].val
sim.target_temp = ui.sliders['temp'].val
sim.damping = ui.sliders['damping'].val
sim.dt = ui.sliders['dt'].val
sim.skin_distance = ui.sliders['skin'].val
sim.use_thermostat = ui.buttons['thermostat'].active
sim.use_boundaries = ui.buttons['boundaries'].active
```
The presets write to `sim.gravity = 0.0`, `sim.boundary_mode = 2 (PERIODIC)`, etc., but the very next frame the UI read clobbers gravity (back to whatever the slider was — 9.81 default), thermostat (back to off), and use_boundaries=False (drops PBC). This is a UNIVERSAL bug affecting all demo presets, not just the new PBC ones — the Lead happened to notice it with PBC because gravity under PBC piles atoms at the bottom with no walls to soak the momentum, making the failure mode highly visible.

The `use_boundaries` setter has a no-downgrade-from-PERIODIC rule when given `True`, so keeping the `boundaries` button active preserves PBC across frames. The fix is "push sim → UI after preset runs" — symmetric mirror of the per-frame UI → sim read.

**Fix.**
- `ui/ui_widgets.py` — added `SmartSlider.set_val(new_val)` public method. Thin wrapper around `_apply_value_with_expansion` + `in_val.set_value`, so the controller can drive sliders programmatically without poking private methods. Honours hard walls + soft-range expansion same as user-typed input.
- `app/app_controller.py` — new `_sync_sim_controls_to_ui()` helper that pushes sim.gravity, target_temp, damping, dt, skin_distance, use_thermostat, and `boundary_mode != 0` out to the corresponding sliders/buttons. Safe no-op when `app.ui` is absent (test stub path). Called at the tail of `run_demo_preset` for every preset branch, so the fix is universal (Demixing/Micelles/Crystal Anneal/all four PBC variants).

**Test coverage (+7 tests in `TestRunDemoPresetSyncsUi`):**
- `_FakeSlider` / `_FakeButton` / `_FakeUi` test fixtures; `_make_controller_stub` extended with `with_ui=False` default.
- Each PBC preset pushes gravity=0 to slider, boundaries=True to button, target_temp to temp slider, thermostat=True to button.
- Existing presets (Demixing/Micelles/Crystal Anneal) also push gravity=0 to slider (regression coverage for the universal-fix scope).
- Existing presets set boundaries=True (REFLECTING is non-OPEN, button reflects that).
- `with_ui=False` path is a safe no-op (test-stub robustness).

**Files touched (7 modified):**
- `core/demo_presets.py` — (carry-over from earlier this session, no changes this round)
- `app/app_controller.py` — `_sync_sim_controls_to_ui` helper + call at tail of `run_demo_preset`
- `ui/ui_manager.py` — (carry-over)
- `ui/input_handler.py` — (carry-over)
- `ui/ui_widgets.py` — `SmartSlider.set_val` public method
- `tests/test_demo_presets.py` — (carry-over)
- `tests/test_ui_wiring.py` — 7 new sync tests + 3 fixture classes

**Suite:** 956 → **963 passing + 1 skipped** (+7 sync tests; 944s cumulative additions across the session: +22). Zero regressions across the full 44s run.

**Status of changes.** Working tree on flow-state `cr-116-beach-trip-exploration` has 7 modified files, uncommitted. Awaiting Lead before commit.

### Existing demos PBC refactor (CR-116 EI-3, follow-up)

Lead flagged: "the original three demos (demixing, micelles, crystal anneal) are not very satisfying because they don't fill up the available volume - and they too should have gravity turned off and all variables appropriately set to illustrate the phenomena."

**Root cause.** The three original presets centred their atoms on a sub-tile via `_grid_positions` (which positions ceil(√N) × ceil(√N) cells centred in the world) and used REFLECTING walls. Two effects:
- Vacuum at the edges (the centred grid covers ~80% of the box at the existing defaults; at the higher counts I should have been using, even less)
- Wall-induced nucleation / clustering biased the phenomenology (atoms accumulate near walls under demixing; surfactants curve toward walls under micelle formation)

The atom counts were also way too low for clear bulk physics: demixing at 160 atoms (ρ*≈0.06) was a sparse vapor where LJ attraction barely operates; crystal_anneal at 120 atoms (ρ*≈0.05) couldn't form a visible crystal on cooling.

**Refactor.**
- New shared helper `_seed_pbc_demo_state(sim, target_temp, damping=0.999)` applies the canonical PBC-demo physics setup: gravity=0, damping=0.999, target_temp, thermostat=on, boundary_mode=PERIODIC (falls back to REFLECTING if `_pbc_safe()` refuses — only happens if user has shrunk world below ~8.4 sim units). Returns `pbc_set` bool for the caller to surface.
- All four presets (Demixing / Micelles / Crystal Anneal / PBC Liquid) now share this setup path. DRY: 16 lines deleted across the three existing presets, replaced by one call each.
- All four switch their initial placement to `_grid_positions_pbc_fill` — uniform tiling of [0, L)² under PBC, no edge vacuum.

**New defaults (motivated by 2D LJ phase diagram):**

| Preset | Old default N | New default N | Old ρ* | New ρ* | Old T | New T | Boundary |
|--------|---------------|---------------|--------|--------|-------|-------|----------|
| Demixing | 160 (80/sp) | 1200 (600/sp) | 0.06 | 0.48 | 0.5 | 0.7 | REFL → PBC |
| Micelles | 160 (100+60) | 1100 (1000+100) | 0.06 | 0.44 | 0.5 | 0.6 | REFL → PBC |
| Crystal Anneal | 120 | 1600 (= 40²) | 0.05 | 0.64 | 1.5 | 1.5 | REFL → PBC |

Rationale:
- **Demixing T=0.7** (was 0.5): keeps the system above 2D vapor-liquid coexistence so the visible phase separation is purely by *species*, not also by vapor/liquid coexistence. Higher diffusion → faster domain coarsening.
- **Micelles T=0.6**: warm enough for surfactant rearrangement, cool enough that micelle interiors stay condensed. Margin=3σ retained for surfactant centres so the ~5σ Surfactant template stays inside [0, L) at placement.
- **Crystal Anneal n=1600 = 40²**: exact square so the PBC grid tiles cleanly with no slice loss. ρ*≈0.64 puts the cooling path through a clean fluid→solid transition (above the triple-point density of 0.83 in N=∞ terms, but in finite-N at this ρ the system crystallises on cooling to T≈0.3-0.4).

Other dead parameters removed: `spacing` (Demixing, Crystal Anneal), `solvent_spacing` (Micelles). The PBC fill grid pitch is purely a function of `L / side`, so no caller-set spacing makes sense.

**Files touched (4 modified this round):**
- `core/demo_presets.py` — new `_seed_pbc_demo_state` helper; demixing/micelles/crystal_anneal rewritten; preset_pbc_liquid also switched to use the helper (DRY). Module docstring updated.
- `tests/test_demo_presets.py` — `boundary_mode==1 → ==2` in TestPresetDemixing.test_physics_params_set + TestPresetMicelles.test_physics_params_set; added TestPresetCrystalAnneal.test_periodic_boundary_set + test_no_gravity (the latter was previously missing); tightened world-bounds assertion to `< sim.world_size` (PBC keeps atoms strictly inside); demixing phenomenology test bumped to n_per_species=300 / T=0.6 so the like-clustering signal survives the move to PBC (at the old n=120/T=0.4 the system is too sparse for LJ attraction to drive clustering against thermal motion under PBC, which has no wall nucleation).
- `tests/test_ui_wiring.py` — count assertions updated for new defaults: 160 → 1200 (demixing), 160 → 1100 (micelles), 120 → 1600 (crystal_anneal).

**Test coverage (+2 net):**
- TestPresetCrystalAnneal: +2 new tests (`test_periodic_boundary_set`, `test_no_gravity`). These were missing previously — the existing class only checked count + material + temperature + thermostat, never the boundary or gravity.

**Suite:** 963 → **965 passing + 1 skipped** (+2 from new crystal_anneal physics checks; pre-existing tests unchanged in count, just updated assertions). Zero regressions across the full 25-second run.

**Status of changes.** Working tree on flow-state `cr-116-beach-trip-exploration` has 7 modified files, uncommitted. Awaiting Lead before commit.

### Micelles preset: empirical evidence + pre-organized rewrite (CR-116 EI-3, follow-up)

Lead challenged: "Do you have theoretical evidence to support that the micelle simulation will show what it aims to show, and any quantitative evidence that it indeed shows the behavior it purports to demonstrate?"

**Honest answer up front: I had neither.** The previous version of the preset asserted "self-organise into micelles" but I had not verified it. The empirical diagnostic showed the previous random-IC preset at default parameters produces *no* aggregation at all on demo timescales — tail atoms ended up uniformly mixed with solvent (tt-NN ≈ 5.3σ matches what random distribution would give).

**Diagnostic methodology.** Wrote `_micelle_diagnostic.py` (one-off, deleted at end of round) that loads the preset, integrates for 50k-500k substeps, and measures four metrics: mean nearest-neighbour distances (tail-tail / tail-solvent / head-solvent / head-tail) and connected-component sizes of tail atoms (1.5σ adjacency, same-molecule pairs masked). Ran across multiple seeds, plus a parameter sweep varying concentration / temperature / hydrophobic mismatch.

**Findings:**
- Default params (n=20, T=0.6, ε_PN=0.25): zero aggregation. Final tt-NN ≈ 5.3σ ≈ random distribution.
- 2× concentration: small leftover initial-placement clusters dissolve to size 3-4.
- Cooler T=0.4 + stronger ε_PN=0.10: same dispersed outcome.
- Aggressive (n=80, T=0.3, ε_PN=0.05, 500k substeps): proto-clusters from random placement persist and tighten, but ~60% of tails remain singletons. Equilibrium self-assembly not feasible.
- **Root cause:** at our concentration, surfactant-surfactant diffusive encounter takes ~10⁶ substeps. Demo viewing scope is ~10⁵.

**Resolution: option 1 (pre-organized initial state).** Replaced the random-placement layout with a deterministic micelle arrangement. New `_compute_micelle_layout` helper distributes `n_surfactant` across ⌈n_surfactant / surfactants_per_micelle⌉ clusters on a uniform grid; within each cluster, K surfactants on a ring of radius R_micelle=3.3σ at evenly-spaced angles, with rotation = θ + π so heads point outward and tails converge near the cluster centre.

Geometry constants (5-atom Surfactant template: head_half_length=2σ, r_eq=1σ):
- Tail-tip ring at radius 1.3σ; K=6 gives tangential spacing 1.3σ (clear of LJ r_min ≈ 1.122σ).
- Head ring at radius 5.3σ; K=6 gives head spacing 5.5σ in solvent.
- Inter-cluster margin = head_ring_r + 1σ = 6.3σ.

New `_surfactant_atom_positions` computes the world positions of every planned surfactant atom (5 per molecule) analytically before placement. Solvent fill then filters out grid cells within 1σ of any planned surfactant atom — this prevents the LJ kernel from seeing overlapping atoms at t=0, which would otherwise blast the micelle structure apart in the first substep.

Default parameters changed: n_surfactant 20 → 24 (clean 4×6 layout), new `surfactants_per_micelle` param (default 6). n_solvent semantic changed from "exact count" to "target — actual reported in info['n_solvent']" (some cells excluded; at default geometry ~895-905 placed of 1000 requested).

**Empirical verification (the new diagnostic was run on the new layout):**
- All 3 seeds, t=0 → t=50k substeps: 4 distinct tail-tip clusters of size 6 persist; cluster sizes GROW to 9-13 as surfactants tighten (consolidation, not dissociation).
- Head-out structure preserved: hs-NN ≈ 1.2σ (heads in contact with solvent) vs ht-NN ≈ 3.5-3.8σ (heads far from other-molecule tails). 3× separation, robust.
- No micelle fuses or dissolves across the integration. No single dominant blob forms.

**Phenomenology test added (`TestMicellesPhenomenology`, +3 tests):**
- `test_initial_state_has_n_micelles_distinct_clusters`: t=0 layout is exactly 4 clusters of size 6 each.
- `test_micelles_remain_stable_after_relaxation`: 10k substeps later, still 4 clusters of size ≥ 4; largest cluster < 50 (no blob fusion).
- `test_micelles_head_out_structure_preserved`: hs-NN < ht-NN by a wide margin (hs-NN < 1.8σ, ht-NN > 2.5σ).

Status text updated to honestly describe what's happening: "4 pre-arranged proto-micelles (24 surfactants) in 897 Polar solvent — hit Play."

**Files touched (5 modified this round):**
- `core/demo_presets.py` — new `_compute_micelle_layout` + `_surfactant_atom_positions` helpers; preset_micelles rewritten end-to-end with pre-organized layout + exclusion-zone solvent filtering. Docstring rewritten to honestly describe what the demo shows.
- `app/app_controller.py` — status text revised.
- `tests/test_demo_presets.py` — new `TestMicellesPhenomenology` class with 3 quantitative tests.
- `tests/test_ui_wiring.py` — micelles count assertion changed from `==1100` to band `1000..1130` (depends on exclusion-zone hit count).

**Suite:** 965 → **968 passing + 1 skipped** (+3 from phenomenology). Zero regressions across the 28-second full run.

**Status of changes.** Working tree on flow-state `cr-116-beach-trip-exploration` has 7 modified files, uncommitted. Diagnostic file deleted.

## Session Summary

Four-round arc reworking the Flow State Demos menu to actually deliver what the labels claim:

| Round | Theme | Files | Tests |
|-------|-------|-------|-------|
| R1 | New PBC density-spectrum demos (4 variants) | demo_presets, app_controller, ui_manager, input_handler, +tests | +15 |
| R2 | Universal demo→UI sync fix | ui_widgets (SmartSlider.set_val), app_controller (_sync helper), +tests | +7 |
| R3 | Existing 3 demos rewritten under PBC with proper volume fill + density | demo_presets, tests | +2 |
| R4 | Micelles empirical-driven rewrite (pre-organized layout + phenomenology test) | demo_presets, app_controller, tests | +3 |

**Cumulative:** 941 → **968 passing + 1 skipped** (+27 tests, zero regressions).

**Files modified (7):**
- `core/demo_presets.py` — extensive (4 rounds touched this file): new `_seed_pbc_demo_state`, `_grid_positions_pbc_fill`, `_compute_micelle_layout`, `_surfactant_atom_positions` helpers; `preset_pbc_liquid` (new); `preset_demixing` / `preset_micelles` / `preset_crystal_anneal` rewritten end-to-end.
- `app/app_controller.py` — `_sync_sim_controls_to_ui` helper, 4 new preset branches (PBC variants), micelles status text revised.
- `ui/ui_manager.py` — 4 new Demos menu items.
- `ui/input_handler.py` — 4 new menu→dispatch elif branches.
- `ui/ui_widgets.py` — new `SmartSlider.set_val` public method.
- `tests/test_demo_presets.py` — `TestPresetPbcLiquid` (12), `TestMicellesPhenomenology` (3), updated existing tests for new boundary mode + defaults.
- `tests/test_ui_wiring.py` — `TestRunDemoPresetSyncsUi` (7), 3 new PBC dispatch tests, updated count assertions.

**Methodology highlight: empirical verification before claiming behaviour.** R4 began with an honest "I don't have evidence" answer to a Lead challenge. Diagnostic script revealed the previous micelles preset produced zero aggregation. Parameter sweeps confirmed self-assembly infeasible on demo timescales. Pre-organized layout was chosen with empirical re-verification across 3 seeds × 50k substeps confirming structure stability, and three quantitative phenomenology tests pinning the new contract. Diagnostic deleted at the end.

**Carry-forward for next session:**
- Working tree to be committed + pushed at end of this session.
- No new known limitations from this session — the R5/R6 carry-overs (`AddMoleculeCommand.undo` truncation, no rotation control, MoleculeBuilderDialog dropdown not following session.active_material) remain open.
