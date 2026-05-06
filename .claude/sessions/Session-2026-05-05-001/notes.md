# Session-2026-05-05-001

## Current State (last updated: end of session, awaiting Lead direction)
- **Active document:** CR-116 (IN_EXECUTION v1.2)
- **Current EI:** EI-3 (free-form exploration) — benchmark suite + parallel build_neighbor_list + HUD fixes all landed
- **Blocking on:** Lead direction
- **Next:** Lead picks. Candidates queued: (a) `_draw_particles` vectorization (now the bottleneck since physics is faster), (b) more engine perf work (parallel cell-list construction is the model for further parallelization opportunities), (c) other beach-trip exploration, (d) eventual qualify (EI-4) → ship FLOW-STATE-1.3.
- **Subagent IDs:** none active
- **Branch state:** `.test-env/flow-state/` on `cr-116-beach-trip-exploration` at `b400a84` (13 commits this session). Submodule pointer in pipe-dream unchanged per CR-116 envelope.

## Session-start checklist
- New day (2026-05-05) → new session
- CURRENT_SESSION updated to Session-2026-05-05-001
- Read SELF.md
- Read previous session notes (Session-2026-05-04-001 + Session-2026-05-03-003 for deeper context)
- QMS-Policy / START_HERE / Glossary — deferred until QMS routing required (none for benchmark code under CR-116 envelope)
- No compaction-log → genuine new session

## Lead direction this session
- Build a robust benchmark suite for free LJ atoms only
- Constraints: gravity=0, no PBC available, BC=reflecting walls (Lead picked), primary metric=ns/atom-substep (Lead picked)
- Stay under CR-116 (the beach-trip umbrella CR), do not open a new CR
- Vary: density, temperature, LJ params, numerical dials (r_skin, etc.)

## Plan for benchmark suite
- Layout: `flow-state/benchmarks/` (sibling of tests/, NOT inside tests/ — pytest must not collect)
- Files: `__init__.py`, `scenarios.py`, `harness.py`, `run.py`, `README.md`, `baselines/`
- Three baseline scenarios + one parametric: `lj_gas` (ρ*=0.05, T*=2.0), `lj_liquid` (ρ*=0.7, T*=1.0), `lj_dense` (ρ*=0.85, T*=0.7), `lj_sweep(...)`
- Method: reflecting walls + Berendsen thermostat (mix=0.1), perturbed square lattice IC, MB velocities at T_init zeroed-momentum, equilibrate 200 substeps, prime JIT, time k=50 step() calls, report median ns/atom-substep
- Wall damping = 1.0 (elastic) — diverges from prod default 0.99; documented in README

## EI-1 scope (smallest landing increment)
- harness.py with timing + stats
- scenarios.py with just lj_liquid + a helper that lattice-packs and MB-distributes
- run.py minimal CLI (single scenario, fixed N)
- README documenting what's measured and known limitations (no PBC, wall_damping=1.0 divergence)

## Progress Log

### [start] Context loaded; Lead approved CR-116 envelope and defaults
- CR home: CR-116 (umbrella for beach trip work) — no new CR
- BC: reflecting walls
- Primary metric: ns/atom-substep

### EI-1 of benchmark suite — landed (uncommitted)
- New package `benchmarks/` in `.test-env/flow-state/`. Files: `__init__.py`, `__main__.py`, `harness.py`, `scenarios.py`, `run.py`, `README.md`.
- Single scenario for v1: `lj_liquid` (ρ*=0.7, T*=1.0, σ=ε=mass=1, dt=0.002, r_skin=0.3, reflecting walls, gravity=0, wall_damping=1.0, Berendsen thermostat ON mix=0.1).
- IC: perturbed square lattice (5% jitter), MB velocities at T* with zero net momentum and exact-KE rescale.
- Harness: 200 substep equilibration, **3 priming step() calls** (one wasn't enough — saw 577 ms first-sample outlier at N=1000, gone with 3), then k=50 timed step(physics_steps=10) calls. Reports median/min/max/p10/p90 ms-per-step, ns/atom-substep, MASPS.
- CLI: `python -m benchmarks [-N … --samples … --json …]`
- Smoke runs (current branch HEAD `b8653e1`):
  - N=500:  ns/atom-substep ≈ 175  (ms/step 0.875)
  - N=1000: ns/atom-substep ≈ 114  (ms/step 1.136)
  - N=5000: ns/atom-substep ≈ 74   (ms/step 3.721, p10=2.079, p90=5.526)
- Known limitations documented in README: no PBC (reflecting walls only), no component-level breakdown, no CI gating, single-machine baselines.
- **Open observation**: dispersion at N=5000 is ~2.7× p90/p10. Almost certainly intermittent neighbor-list rebuilds. Acceptable for v1; tightening is EI-2 territory.
- Pytest unaffected (`pytest.ini` testpaths=tests; benchmarks/ not collected).
- Existing test suite NOT re-run yet — no existing files touched, only additive package, but worth a confirmation pass before commit.

### Compared to last session's perf table
- Last session: N=4000 step() ≈ 1.03 ms = ~26 ns/atom-substep
- Today's lj_liquid at N=5000: ~47 ns/atom-substep on the canonical-grid run
- Difference is methodology: last session ran with thermostat OFF, no reflecting walls, no controlled IC. Today's setup is the controlled benchmark — apples to oranges. Today's number is the new baseline.

### EI-2 — gas + dense scenarios + grid runner — committed
- Commit `f95c727`: lj_gas + lj_dense + SCENARIOS registry + multi-scenario / multi-N grid CLI + per-host JSON baselines (gitignored).
- Smoke at N=1000 across scenarios: gas/liquid/dense ≈ 103/152/119 ns/atom-substep (numbers heavily noise-dominated; see characterization run for canonical figures).

### EI-3 — parametric sweep + --compare — committed
- Commit `19c24a1`: lj_sweep scenario + --sweep KEY=v1,v2,v3 + --compare flag (loads on-disk baseline, diffs ns/atom-substep, exits 1 on regression > --regression-pct).
- Sweepable keys restricted to numerical dials: rho_star, T_star, sigma, epsilon, dt, r_skin, physics_steps.

### Canonical grid characterization (3 scenarios × 6 N values, 50 samples each)
Saved to `/tmp/bench-grid.json` and `/tmp/bench-grid.txt`. Headline (ns/atom-substep):

| N      | lj_gas | lj_liquid | lj_dense |
|--------|--------|-----------|----------|
| 500    |  79.2  |  115.8    |   86.1   |
| 1000   |  42.5  |   71.1    |   72.5   |
| 2000   |  25.1  |   54.1    |   53.2   |
| 5000   |  16.0  |   46.7    |   40.6   |
| 10000  |  11.5  |   52.6    |   33.4   |
| 20000  |   9.8  |   45.2    |   27.4   |

Findings:
- Sub-linear ns/atom-substep with N — bigger N is better per atom (cache locality + amortized fixed costs).
- Liquid is the *worst* scenario at high N, not dense — counterintuitive. Likely the conjunction of moderate pair count + high thermal mobility (T*=1.0 vs dense's 0.7) → most-frequent neighbor-list rebuilds.
- Gas crushes everything because the pair count per atom is tiny.

### r_skin sweep — material finding
At lj_liquid N=5000 (saved `/tmp/bench-rskin.json`):

| r_skin | ns/atom-substep | vs default |
|--------|-----------------|------------|
| 0.1    | 59.4            | +19% slow  |
| 0.2    | 50.5            | tie        |
| **0.3 (current default)** | **49.9** | — |
| 0.4    | 42.9            | -14%       |
| 0.5    | 35.7            | -28%       |
| **0.7** | **32.4 (best)** | **-35%**  |
| 1.0    | 57.8            | +16% slow  |

Verified at N=10000 lj_liquid (best at 0.7, -37%) and at N=5000 lj_dense (best at 0.5, -23%). The U-shape is exactly what the model predicts: small r_skin → too-frequent rebuilds; large r_skin → too many candidate pairs to evaluate.

**Recommendation:** consider raising `DEFAULT_SKIN_DISTANCE` from 0.3 to 0.5. 0.5 is universally better than 0.3 in benchmark conditions — 28% improvement on liquid, 23% on dense, gas is unaffected. r_skin=0.7 is even better for sparse-pair regimes but degrades dense slightly. **0.5 is the safer universal default.** This is a tuning decision for the Lead — production has thermostat OFF and gravity ON, so the optimal may shift, but the benchmark is now the right tool to verify.

**Did not change `DEFAULT_SKIN_DISTANCE` in this session** — that's a production-tuning decision the Lead should make with full eyes-open visibility on the benchmark methodology vs production conditions.

### Pending observations / loose ends for next session
- Dispersion at N=5000+ is wide (p90/p10 ~2-3×). Median is robust but tightening would help regression detection. Either trimmed-mean reporting or rebuild-bucketed timing.
- Run-to-run noise on this Wil machine appears to be ~5-10% (across fresh-process invocations under the same scenario). Exceeded by the r_skin=0.3→0.5 finding (~28%) but borderline for 5% regression threshold in --compare.
- physics_steps sweep not run (production uses 20, benchmarks use 10). Worth checking whether per-step bookkeeping changes the scaling story.
- Component-level breakdown (build_neighbor_list vs integrate_n_steps vs apply_thermostat) still not measured. Would explain *why* liquid > dense at high N.
- The "Resizing simulation capacity" prints from `Simulation._resize_arrays` show up in benchmark stdout. Cosmetic noise.
- "Skipping Numba warmup (Model Builder Mode)" prints once per scenario construction — also cosmetic noise.

### Branch state at end of first report
flow-state@`19c24a1` on `cr-116-beach-trip-exploration` (pushed). Three commits this session:
- `5b803a8` — EI-1: harness + lj_liquid
- `f95c727` — EI-2: gas/dense + grid runner + baselines
- `19c24a1` — EI-3: lj_sweep + --sweep + --compare
Pipe-dream submodule pointer unchanged per CR-116 envelope.

### Lead returned and asked: "ensure maximal performance and high understandability"
Plan executed:
- A: validate r_skin under production conditions → don't change DEFAULT_SKIN_DISTANCE
- Production scenario added; r_skin=0.5 vs 0.3 verified to be a **false positive** (19% slower in production)
- B: investigate physics_steps tuning → caught a benchmark correctness bug (was dividing by requested, not actual substeps)
- Harness fixed; physics_steps=20 confirmed at the natural ceiling (kernel exits at ~20 via SUBSTEP_SAFETY_CHECK_FREQ)
- C: spatial_sort experiment skipped — would require coordinating 11+ per-atom arrays (tether refs, joints, color); high blast radius
- D: README rewritten with full methodology + worked r_skin example
- E: Updated user-facing report with corrected numbers

### Two new commits
- `fbb8368` — EI-4: lj_production scenario + actual-substep accounting + trimmed mean
- `cd0b46b` — README update

### Key correctness fix in harness
Before: `ns_per_atom_substep = median_ms × 1e6 / (N × physics_steps_requested)`
After: `ns_per_atom_substep = median_ms × 1e6 / (N × median_actual_substeps)`

Harness now captures `sim.total_steps` before/after each call. When the kernel exits early (displacement safety check), `actual < requested`. format_result surfaces this as `actual/requested` in the steps column.

Without this fix, a physics_steps sweep would have spuriously suggested raising DEFAULT_DRAW_M from 20 → 50 (28% improvement that doesn't exist — the kernel returns at substep ~20 either way).

### Final canonical-grid characterization (corrected harness)
ns/atom-substep at physics_steps=10:

| N      | lj_gas | lj_liquid | lj_dense | lj_production |
|--------|--------|-----------|----------|---------------|
| 500    |  83.3  |   97.1    |  116.8   |    141.5      |
| 1000   |  38.7  |   83.7    |   77.7   |     95.0      |
| 2000   |  34.3  |   53.3    |   44.8   |     80.1      |
| 5000   |  15.2  |   41.9    |   42.3   |     75.2      |
| 10000  |  11.8  |   51.7    |   36.5   |     65.6      |
| 20000  |  10.4  |   53.9    |   36.4   |     72.8      |

ms/step at physics_steps=10:

| N      | lj_gas | lj_liquid | lj_dense | lj_production |
|--------|--------|-----------|----------|---------------|
| 500    | 0.42   | 0.49      | 0.58     | 0.71          |
| 5000   | 0.76   | 2.10      | 2.11     | 3.76          |
| 20000  | 2.08   | 10.79     | 7.27     | 14.57         |

60-fps headroom at production conditions, physics_steps=20:
- N=10000: ~6.5 ms/frame (40% of budget) — comfortable
- N=15000: ~10 ms/frame (60% of budget) — workable
- N=20000: ~14.5 ms/frame (87% of budget) — at the edge
- N=25000+: exceeds 16.7 ms/frame budget

### Findings on what the benchmark suite tells us about Flow State
1. Production tuning is sound. Both r_skin and physics_steps are at their natural sweet spots; the suite cleared two would-be optimizations.
2. lj_liquid is the worst-case controlled scenario (worse than dense), driven by thermal mobility + moderate pair count → most-frequent rebuilds.
3. lj_production is 1.5-2× slower than lj_liquid at all N. Gravity injects energy, faster motion → more rebuilds → more cost. This sets the real-world ceiling.
4. Practical real-time limit at 60 fps: ~N=15000 free atoms in production conditions.
5. Flow State throughput at the canonical lj_liquid N=5000: ~24 MASPS = 240 ns per atom-substep at the 60fps user-facing scale.

### Open backlog for the Lead
- Component-level timing (`build_neighbor_list` vs `integrate_n_steps` vs `apply_thermostat`) — would explain *why* lj_liquid > lj_dense at high N. Slot in as a `--breakdown` flag.
- spatial_sort integration — risky engine change; needs full per-atom-array coordination. Likely 1.5-3× LJ pair loop speedup if done correctly.
- "Skipping Numba warmup" / "Resizing simulation capacity" prints leaking into benchmark stdout. Cosmetic.
- The benchmark scenario hardcodes `r_skin=0.3` if config default ever changes (now wired through `_DEFAULT_R_SKIN = config.DEFAULT_SKIN_DISTANCE` at module load — but this captures the value at import time, so a runtime-changed default isn't picked up).

### Updated branch state after recommendations executed
flow-state@`5526229` on `cr-116-beach-trip-exploration` (pushed). Eight commits this session:
- `5b803a8` — EI-1: harness + lj_liquid
- `f95c727` — EI-2: gas/dense + grid runner + baselines
- `19c24a1` — EI-3: lj_sweep + --sweep + --compare
- `fbb8368` — EI-4: lj_production + actual-substep accounting + trimmed mean
- `cd0b46b` — README update reflecting EI-4
- `5479d64` — EI-5: --breakdown component-level timing
- `b2d5a75` — EI-6: --spatial-sort-once experiment (negative result)
- `5526229` — README update reflecting EI-5/EI-6

Pipe-dream submodule pointer unchanged per CR-116 envelope. No production code touched.

### Component-level breakdown findings (N=5000)
Mean per phase across all timed calls:

| Scenario | rebuild_rate | total | rebuild | integrate | other |
|----------|--------------|-------|---------|-----------|-------|
| lj_gas | 50% | 0.76 ms | 22% (0.17) | 66% (0.50) | 12% |
| lj_liquid | 48% | 2.42 ms | 40% (0.97) | 55% (1.34) | 5% |
| lj_dense | 36% | 3.07 ms | 26% (0.81) | 69% (2.10) | 5% |
| **lj_production** | **88%** | **3.37 ms** | **54% (1.83)** | **43% (1.45)** | 3% |

Per-rebuild cost (when one fires) is ~1.6-1.8 ms across liquid/dense/production at N=5000 — this dominates production because rebuild rate is 88%.

### Spatial sort experiment — negative
Tested via external_spatial_sort in benchmarks/experiments.py (does NOT touch engine). Permutes all 16 per-atom arrays by spatial cell key. Tested with --spatial-sort-once flag.

| Scenario | N | Baseline | Sorted | Delta |
|----------|---|----------|--------|-------|
| lj_gas | 5000 | 15.91 | 15.79 | -0.7% (noise) |
| lj_liquid | 5000 | 42.12 | 54.44 | **+29% worse** |
| lj_dense | 5000 | 42.41 | 41.45 | -2% (noise) |
| lj_production | 5000 | 68.83 | 72.15 | +5% (noise) |
| lj_liquid | 10000 | 46.58 | 48.74 | +5% (noise) |
| lj_liquid | 20000 | 46.09 | 44.92 | -3% (noise) |

Conclusion: spatial sort is NOT a perf lever in this configuration. The Numba parallel atom-centric pair loop already has good locality. Experiment infrastructure preserved in benchmarks/experiments.py for future re-testing if kernel architecture changes.

### Three would-be optimizations cleared by the suite
1. r_skin=0.3→0.5 — false positive in controlled, -19% in production. Caught by lj_production scenario.
2. Raise DEFAULT_DRAW_M=20→50 — false positive due to harness dividing by requested-not-actual substeps. Caught by harness fix.
3. Spatial sort — no effect. Caught by direct measurement.

None shipped. Each represents a 25-35% candidate "improvement" that would have been a net loss or no-op.

### Real perf lever revealed
The component breakdown shows that **production spends 54% of step time in neighbour-list rebuilding**. The build_neighbor_list kernel was SERIAL (per docstring at physics_core.py:50: "Kept serial because writing to the linked list 'head' array...").

### Parallel build_neighbor_list — landed (commit 50c11f1)
Lead approved engine work; replaced linked-list cell layout with counting-sort CSR layout. Two-pass pair generation (count + write) eliminates atomic adds. Same architectural pattern as last session's atom-centric LJ pair loop refactor.

**Validation:** all 489 tests pass. Per-rebuild build_neighbor_list cost at N=5000:

| Scenario | Serial (ms) | Parallel (ms) | Speedup |
|----------|-------------|---------------|---------|
| lj_gas | 0.32 | 0.16 | 2.0× |
| lj_liquid | 1.63 | 0.39 | 4.2× |
| lj_dense | 1.79 | 0.43 | 4.1× |
| lj_production | 1.67 | 0.46 | 3.6× |

Whole-step ns/atom-substep improvements:

| Scenario | N | Before | After | Speedup |
|----------|---|--------|-------|---------|
| lj_production | 5000 | 75 | 58 | 1.29× |
| lj_production | 10000 | 66 | 41 | 1.61× |
| lj_production | 20000 | 73 | 38 | **1.92×** |
| lj_liquid | 20000 | 54 | 31 | 1.74× |

**Real-time impact at 60 fps under production conditions (physics_steps=20):**
- Before: ~N=15000 was at the edge; N=20000 exceeded budget
- After: N=20000 is now at ~15.0 ms/frame (under budget); new ceiling ~N=25-30000

This is the first real perf change committed this session. The benchmark suite measured the win directly.

### Re-running canonical grid post-parallelization (commit 50c11f1)
Re-ran `--scenario all -N grid` after pushing. Numbers more variable than the optimistic intermediate run. Honest comparison vs serial baseline:

| N | Scenario | Serial | Parallel (re-run) | Speedup |
|---|---|---|---|---|
| 5000 | lj_production | 75 | 63 | 1.20× |
| 10000 | lj_production | 66 | 59 | 1.11× |
| 20000 | lj_production | 73 | 51 | **1.43×** |
| 20000 | lj_liquid | 54 | 45 | 1.20× |

Speedup is **smaller and more N-dependent than the breakdown suggested** (per-rebuild kernel cost dropped 4×, but rebuild is only one of multiple step() phases). Run-to-run variance ~30-50% on this Wil VM. At very small N (500), the new parallel-dispatch overhead actually makes things slightly worse, but absolute impact is negligible at small N. Honest verdict: 30-40% speedup at large-N production conditions; 60fps ceiling moves from ~N=15k to ~N=20-25k (not 30k as initially overstated).

### Lead reported: "doesn't feel any faster" → render bottleneck
After parallel build_neighbor_list landed, Lead noted no perceptible speedup in the GUI. Investigation:
- `flow_state_app.py:249` calls `clock.tick()` with NO argument — uncapped FPS
- `_draw_particles` (renderer.py:195-216) is a Python loop over every atom: per-atom `sim_to_screen()` Python call, per-atom tuple construction, per-atom `pygame.draw.circle()` syscall
- For N=5000+, render cost (~15-30 ms) exceeds physics cost — render-bound
- Physics speedup just freed up time the renderer was already consuming

The render path could be ~10× faster via numpy-vectorized screen transforms + batched blit. Not landed this session; queued for next.

### SPS HUD readout was hidden — fixed (commits 6f99c6e, 57289a4)
Lead asked "where is SPS?" → it was being drawn but invisible. Two compounding bugs:
1. `_draw_stats` used `layout['LEFT_X']+15` (LEFT_X=0 in production layout); the UI tree's left panel was painting over the stats every frame.
2. After fixing the X coord, SPS line specifically was at `y = layout['H']-30`, exactly the y where the StatusBar widget begins. Status bar painted over SPS.

Both fixed. Stats now anchored at `MID_X+15`, with `stats_y = layout['H'] - status_bar_h - 130` so the entire block clears the status bar.

### Expanded HUD (commit b400a84)
Lead noted the metric soup: steps/frame, FPS, SPS, sim/real ratio. HUD now shows all of them in 5 lines (bottom-left of viewport):

    Particles: N
    Pairs: P | T: t
    SPS: s | FPS: f                       (green)
    steps/frame: m | dt: d
    sim time: r× real                     (light blue — the time-dilation factor)

Bottleneck-readable at a glance:
- SPS / steps_per_frame ≈ FPS → balanced
- SPS / steps_per_frame >> FPS → render-bound (current state at high N)
- SPS / steps_per_frame << FPS → physics-bound (or kernel early-exit)

### Final commit list this session (13 commits on cr-116-beach-trip-exploration)
| Hash | Subject | Theme |
|------|---------|-------|
| `5b803a8` | Add LJ benchmark suite (EI-1: harness + lj_liquid) | Benchmark infra |
| `f95c727` | Benchmark suite EI-2 — gas/dense scenarios + grid runner | Benchmark infra |
| `19c24a1` | Benchmark suite EI-3 — parametric sweep + --compare | Benchmark infra |
| `fbb8368` | Benchmark suite EI-4 — production scenario + actual-substep accounting | Benchmark fix + scenario |
| `cd0b46b` | Update benchmarks/README to reflect EI-4 changes | Docs |
| `5479d64` | Benchmark suite EI-5 — component-level breakdown | Diagnostic |
| `b2d5a75` | Benchmark suite EI-6 — spatial-sort experiment (negative result) | Experiment |
| `5526229` | Document --breakdown and the spatial-sort negative result in README | Docs |
| `50c11f1` | **Parallelize build_neighbor_list (atom-centric counting-sort)** | **Real perf win** |
| `6f99c6e` | Fix SPS / Particles / Pairs HUD readout being hidden under left panel | UI bug |
| `57289a4` | Lift SPS readout above the bottom status-bar widget | UI bug follow-up |
| `b400a84` | Show FPS, steps/frame, dt, and sim-time dilation in the HUD | UI enhancement |

Suite progression: 489 passing + 1 skipped + 0 xfails (unchanged from start; new tests not added — benchmarks aren't pytest-collected). Engine change validated by full suite passing.

Pipe-dream submodule pointer unchanged per CR-116 envelope.

### Key learnings from this session
1. **Build the measurement before the optimization.** Three optimization candidates (r_skin tuning, raising DEFAULT_DRAW_M, spatial sort) all looked like wins under naive measurement. The benchmark suite caught all three.
2. **Production conditions ≠ controlled conditions.** The lj_production scenario was the single most valuable scenario added — it caught the r_skin false positive that controlled benchmarks would have shipped.
3. **Cross-domain bottlenecks shift visibility.** Physics speedup only helps if rendering is fast; rendering is now the visible-frame-rate constraint. Future perf work should target the renderer.
4. **The HUD is the user's main signal**, and it had been silently broken (SPS hidden under panel). Worth investing in.
