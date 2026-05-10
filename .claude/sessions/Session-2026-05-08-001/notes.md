# Session-2026-05-08-001

## Current State (last updated: session wrap-up, ready to commit)
- **Active document:** CR-116 (IN_EXECUTION v1.2) — Exploration CR umbrella for beach-trip Flow State work
- **Current EI:** EI-3 (free-form exploration)
- **Blocking on:** Nothing — session wrapping up
- **Next:** Commit + push the session's work; PROJECT_STATE update; close session.
- **Subagent IDs:** none active
- **Branch state:**
  - `.test-env/flow-state/` on `cr-116-beach-trip-exploration` upstream @ `6ae00d0`; **uncommitted local changes** across 8 files (render-mode toggle + Newton-3 opt-in kernel + breakdown.py signature fix + 10 new tests)
  - Suite: 523 passing + 1 skipped (was 513 + 1 → +10 new tests this session: 6 render-mode + 4 Newton-3 equivalence)

## Session-start checklist
- New day (2026-05-08); first session of the day → Session-2026-05-08-001
- CURRENT_SESSION updated; session folder created
- Read SELF.md
- Read previous session notes (Session-2026-05-05-002)
- Read QMS-Policy / START_HERE / QMS-Glossary
- Read PROJECT_STATE.md (full)
- Inbox: empty
- No compaction-log → genuine new session

## Progress Log

### [start] Context loaded; awaiting Lead direction
- Session-start checklist complete
- CR-116 still active under the Exploration CR envelope
- Auto Mode banner present but no Lead task surfaced yet — pausing here rather than autonomously picking from the candidate list, since the Lead has been the one to choose direction at the start of each beach-trip session

### Render-mode troubleshooting toggle (under CR-116 EI-3)
Lead asked for a diagnostic render-mode toggle: (a) skip particle drawing entirely, (b) cheapest-possible "dots only" view, in addition to (c) the existing full render. Doubles as instrumentation for the §6.5b standing item ("`_draw_particles` is now the visible-frame-rate bottleneck" — this lets us observe how much of the budget is spent in the particle path).

**Design.** Three modes on `Session.render_mode` (transient view state, lives next to `show_wall_atoms` / `show_constraints`):
- `RENDER_FULL` (0) — existing per-atom `pygame.draw.circle` path (unchanged behavior)
- `RENDER_DOTS` (1) — vectorized single-pixel scatter via `pygame.surfarray.pixels3d` fancy indexing; sim_to_screen transform inlined as numpy ops; bypasses the Python per-atom loop entirely. Per-particle atom_color preserved. Fallback to `set_at` if surfarray rejects the surface format (rare on modern Windows pygame-ce).
- `RENDER_OFF` (2) — early-return; no particle work at all.

Cycle: `Session.cycle_render_mode()` rotates 0→1→2→0. F7 hotkey (F8 already taken by boundary cycle, F9-F11 by solver). HUD `_draw_stats` gains a 7th line `render: <Mode>  [F7 to cycle]`; `stats_y` lifted from −150 to −170 to keep room above the StatusBar widget.

**Files modified (in `.test-env/flow-state/`):**
- `core/session.py` — three `RENDER_*` constants, default-FULL state, `cycle_render_mode()` method
- `ui/renderer.py` — `_draw_particles` becomes a dispatcher; existing body renamed to `_draw_particles_full`; new `_draw_particles_dots` method; HUD gains the render-mode line
- `ui/input_handler.py` — F7 cycles modes via `session.cycle_render_mode()` and updates the status bar
- `tests/test_session.py` — `TestRenderMode` class (5 tests: constants are 0/1/2, default is FULL, FULL→DOTS, DOTS→OFF, OFF→FULL, three-cycles wraps to start)

**Verification.**
- Test suite: 519 passing + 1 skipped (was 513 + 1 → +6 new tests, all pass; existing 513 unchanged)
- Smoke harness on a dummy SDL surface: confirmed FULL renders normally, DOTS writes pixels via the vectorized path, OFF leaves the viewport untouched, cycle wraps correctly
- Lead validation in the GUI: **Full→Dots gave a significant FPS jump; Dots≈Off**

### Diagnosis: Dots ≈ Off because physics, not render, is the ceiling at high N
Lead reports both Dots and Off at ~10-14 FPS at very high N. Frame budget at that point is ~70-100 ms. UI tree + geometry + HUD draw are on the order of single-digit ms — far below the floor. `update_physics()` runs every frame regardless of render mode and dominates at high N. Both modes are physics-bound, hence indistinguishable. This conclusively answers the §6.5b question: at moderate N render dominates (vectorizing buys frames), at very high N physics also exceeds budget.

### Physics breakdown — diagnosing the bottleneck
Ran `python -m benchmarks --scenario lj_production --breakdown` (had to fix breakdown.py for the new `boundary_mode` arg added in last session's PBC work). At N=5000, 10000, 20000 the picture is consistent:
- `integrate_n_steps`: **~80% of frame time** (the LJ pair force loop)
- `build_neighbor_list`: 11-15% (rebuild rate 88-92% — already nearly every call)
- Other phases: <5% combined

The LJ pair loop is the target. Note: benchmark variance is huge (~2× run-to-run; p10/p90 ratio ~6×) which means only large wins are detectable.

### Experiment: force-reset fusion
Fused the per-substep "force reset" prange loop into the LJ accumulation loop (single write per atom instead of write+RMW; one fewer parallel dispatch per substep). Theoretical win: 1-3%. Measured: indistinguishable from noise. **Reverted** — the code is cleaner but no measurable benefit, and a kernel rewrite was queued anyway.

### Experiment: Newton-3 half-pair kernel (`integrate_n_steps_newton3`)
Built a new kernel that iterates the half-pair list (`pair_i, pair_j`) directly with thread-local force accumulators (`local_force_x[T, N]`, `local_force_y[T, N]`), then merges T contributions per atom in a final pass. Halves the LJ pair work in theory. Co-exists with the classic kernel; opt-in via `Simulation.use_newton3` (default False).

**Equivalence verified:** 4 new tests in `TestNewton3KernelEquivalence` confirm the two kernels produce identical state within float32 sum-order noise (max position delta 1.7e-5 over 200 substeps at N=2000).

**Performance — direct A/B (30 samples, median):**
| N | Classic ms | Newton-3 ms | Ratio |
|---|---|---|---|
| 5000 | 25.6 | 18.1 | **1.42× faster** |
| 10000 | 23.1 | 33.3 | 0.69× (slower) |
| 20000 | 36.8 | 57.5 | 0.64× (slower) |

**Why the regression at high N:** the thread-local buffers are T×N×8 bytes (≈1.3 MB at N=20k, T=8) and per-pair writes go to TWO atoms (i and j) at random indices, both in the local_force buffer. Total memory bandwidth per substep is much higher than the classic kernel, which writes once per atom in well-localized fashion. At N=5000 the working set fits in L2 and the half-work win dominates; above that, memory bandwidth dominates and the win flips negative.

### Status
- Render-mode toggle: working in GUI, validated by Lead
- Newton-3 kernel: shipped as opt-in, equivalence-tested. Useful at moderate N (≤~5000); does not deliver "higher FPS at high N." Stays available behind `use_newton3` flag for future experimentation
- The classic kernel remains the default and is at the limit of what atom-centric parallelization achieves on this hardware
- Test suite: 523 passing + 1 skipped (was 513 + 1 → +10 new tests this session: 6 render-mode + 4 Newton-3 equivalence)

### What didn't deliver, and what's next
The Lead's stated goal was "higher FPS at high N" with no specific target. Newton-3 was the right hypothesis but the wrong direction at high N. Genuine FPS wins at high N now require one of:
- **Reduce r_cut** (e.g. 2.5σ → 2.0σ): smaller pair count, modest physics-fidelity tradeoff. Estimated 1.3-1.5× win. Needs Lead approval (changes simulation behavior).
- **GPU offload** (Numba CUDA): biggest possible jump but largest scope.
- **Multi-time-stepping (RESPA)**: evaluate far-field LJ less often than near-field. Complex, error-prone.
- **SIMD-friendly memory layout** (packed pos_xy as (N,2) array): cache-line-aligned gathers. Big refactor; uncertain payoff.
- **Auto-select kernel by N**: classic >5000, Newton-3 ≤5000. Marginal at the typical use range; cosmetic.

Files modified this session (in `.test-env/flow-state/`, all uncommitted, on `cr-116-beach-trip-exploration`):
- `core/session.py` — render-mode constants + cycle method
- `ui/renderer.py` — three-mode dispatch, vectorized DOTS path, HUD line
- `ui/input_handler.py` — F7 hotkey
- `engine/physics_core.py` — `integrate_n_steps_newton3` kernel
- `engine/simulation.py` — `use_newton3` flag, lazy `_local_force_*` buffers, dispatch
- `benchmarks/breakdown.py` — fix stale signature for `build_neighbor_list` and `integrate_n_steps`
- `tests/test_session.py` — 6 render-mode tests
- `tests/test_simulation.py` — 4 Newton-3 equivalence tests
