# Session-2026-05-04-001

## Current State (last updated: end of session)
- **Active document:** CR-116 (IN_EXECUTION v1.2)
- **Current EI:** EI-3 (free-form exploration) — 9 commits across 3 sessions; suite at 489 passing + 1 skipped + 0 xfailed
- **Blocking on:** Nothing — Lead asked what's pending before closing this session
- **Next session:** Lead drives. Likely candidates: first real gameplay/CAD/sim feature CR (perf headroom now in hand), or continued EI-3 exploration. Eventual CR-116 closure → qualify → ship as FLOW-STATE-1.3.
- **Subagent IDs:** none active
- **Branch state:** flow-state@`b8653e1` on `cr-116-beach-trip-exploration` (pushed). Pipe-dream submodule pointer unchanged per CR-116 envelope.

## Session summary — six commits from this session, all on `cr-116-beach-trip-exploration`

| Hash | Subject | Theme |
|------|---------|-------|
| `48f2c1c` | Clear xfail registry in tests/README.md | Cleanup carried over from prior session |
| `e045506` | Route Source creation through AddSourceCommand | Bug fix (Air Gap completion) |
| `ee56ee0` | Sync Resize-World input field on undo/redo | Bug fix (UI ↔ model sync) |
| `18e4778` | Initialize atom_color in Simulation._add_particle | Bug fix (colour residue from old slots) |
| `5eb0b44` | Drop parallel=True from apply_thermostat | Perf (2-30× faster at typical N) |
| `b8653e1` | Parallelize the LJ pair loop (atom-centric CSR) | Perf (6-7× faster, 10× target reached) |

Suite progression: 469 → 472 → 476 → 479 → 484 → 489 over the session (+20 new tests). Shipped one perf experiment (option 1: Berendsen serial), explored and reverted another (option 4: DPD), then went after the actual bottleneck (parallel LJ pair loop) and got the 10× headroom directly.

## Session-start checklist (complete)
- Detected new day (2026-05-04 vs last session 2026-05-03-003) → new session
- CURRENT_SESSION updated to Session-2026-05-04-001
- Read SELF.md
- Read previous session notes (Session-2026-05-03-003/notes.md)
- Read QMS-Policy.md, START_HERE.md, QMS-Glossary.md (excerpts)
- Read PROJECT_STATE.md (full — note: file is large, ~30K tokens, candidate for pruning per CLAUDE.md "should not grow endlessly")
- Inbox empty; no checked-out documents
- No compaction-log → genuine new session

## Carry-forward state from Session-2026-05-03-003
- CR-116 IN_EXECUTION v1.2; EI-3 active. Four commits on `cr-116-beach-trip-exploration`:
  - `b441452` — initial regression suite (327 tests)
  - `9c51d70` — TU-driven additions (+125 tests)
  - `0bfe6b1` — TU review-feedback refinements
  - `6b6ad45` — six-fix cleanup (3 xfail latent bugs cleared + 2 CR-114-deferred candidates landed + SourceTool Y-gate)
- Suite: 469 passing + 1 skipped + 0 xfailed in 8.44s
- All three previously-pinned latent bugs now fixed; xfail registry empty

## Forward queue at session start (per PROJECT_STATE §6)
1. CR-116 EI-3 free-form Flow State exploration — **active**; Lead picks next exploration target or moves to qualify (EI-4–7)
2. Process-improvement CR for QA-as-sole-assignee auto-close pattern — observe through next Exploration CRs first
3. First real gameplay/CAD/sim Flow State CR — Lead picks first feature
4. Tool-facade architectural follow-up (Path A queued, deferred)
5. Auto-mode-vs-subagent permissions resolution
6. Razem track items (paused — resume after beach trip)

## Notes / observations
- PROJECT_STATE.md is now 290+ lines and ~30K tokens. CLAUDE.md says "prune aggressively" and "completed items are removed once their context no longer adds value." Several CLOSED CRs have ~paragraph-length §2 entries (CR-112, CR-113, CR-114, CR-115) that could collapse to one-liners now that they're closed and downstream work has moved on. Worth raising with Lead.

## Progress Log

### [session start] Context loaded; awaiting Lead direction

### EI-3 work item: Ctrl+Z does not undo source creation
- **Lead ask:** "It seems that ctrl+z does not undo the creation of sources. We should fix that."
- **Diagnosis:** `SourceTool._create_source` (`flow-state/ui/source_tool.py:154`) called `self.ctx.add_process_object(source)` directly. That bypasses the Command pattern entirely — Air Gap violation. `AddSourceCommand` already exists in `core/source_commands.py` (with correct execute/undo/redo) but was dead code: zero production callers.
- **Fix (within `.test-env/flow-state/` per QMS write-guard):**
  - `ui/source_tool.py` — replaced direct `ctx.add_process_object(source)` with `AddSourceCommand` constructed against `ctx._get_scene()` and run via `ctx.execute(cmd)`. Source instance is then read back from `cmd.source` for the optional Ctrl-snap coincident-constraint follow-up.
  - Added `from core.source_commands import AddSourceCommand` import.
- **Regression tests added (`tests/test_tools.py::TestSourceTool`):**
  1. `test_source_creation_is_undoable` — two-click workflow → `scene.undo()` → `process_objects` empty + `can_undo` true between
  2. `test_source_creation_supports_redo_after_undo` — undo then redo restores
  3. `test_source_undo_unregisters_handles` — sketch entity count returns to baseline (handle Points are unregistered, not orphaned)
- **Suite:** 472 passing + 1 skipped + 0 xfailed in 11.47s (was 469 + 1 + 0; +3 tests).
- **Lead confirmed fix works** — moved on to next item.

### EI-3 work item: Resize-World input field doesn't track world_size on undo/redo
- **Lead ask:** "the input field next to Resize World does not update to reflect current reality through resizes that occur via undo and redo"
- **Diagnosis:** `ResizeWorldCommand.execute/undo` correctly mutate `sim.world_size`, but the `session.input_world` InputField (held on Session as transient state, displays the world size next to the Resize World button) was never refreshed on undo/redo. CR-114's `apply_resize_confirm` already established the explicit-sync pattern (`input_world.set_value(sim.world_size)` on cancel); undo/redo just didn't follow it.
- **Fix:** new private helper `AppController._sync_world_size_input()` that calls `set_value(sim.world_size)` on the field if non-None. Called from `action_undo` and `action_redo` after the underlying undo/redo runs. Safe because `InputField.set_value` is gated on `not self.active` — typing into the field is preserved if an unrelated undo fires.
- **Regression tests added (`tests/test_commands.py::TestResizeWorldInputFieldSync`):**
  1. `test_undo_of_resize_refreshes_input_field` — execute resize, undo, field text matches restored size
  2. `test_redo_of_resize_refreshes_input_field` — undo+redo, field tracks final size
  3. `test_focused_input_field_is_not_overwritten_on_undo` — when `input_world.active=True`, typed text is preserved
  4. `test_undo_with_no_input_field_is_safe` — `session.input_world=None` is tolerated (default state in Session)
- **Suite:** 476 passing + 1 skipped + 0 xfailed in 6.78s (+4 tests).

### EI-3 work item: Wall-coloured "free" atoms appearing inside a wall enclosure
- **Lead ask:** "I put a source of water atoms inside a circle made of wall atoms, and after some time there were free wall atoms (or at least, wall-colored atoms) bouncing around inside the circle."
- **Diagnosis:** `Simulation._add_particle` (used by Sources via `Source._try_spawn_particle`) wrote `pos_x`, `pos_y`, `vel_x`, `vel_y`, `is_static`, `atom_sigma`, `atom_eps_sqrt` at slot `idx = self.count` but **never wrote `atom_color[idx]`**. The slot retained whatever colour the previous occupant had. After Compiler/Compact/escape-filter cycles, slot indices that previously held wall (is_static=1/3) atoms can be reassigned to source-spawned dynamic atoms — and those new atoms render in the residual wall colour. ParticleBrush has its own parallel `_add_particle` in `engine/particle_brush.py:154` that DOES set `atom_color`, which is why brush-painted water never showed this. Verified the parenthetical reading is correct: confirmed by sweep that no production code mutates `is_static` from non-zero to zero, so it's a colour-residue issue, not actual wall atoms breaking free.
- **Fix:** added a `color=(50, 150, 255)` parameter to `Simulation._add_particle` (water-blue default, matching the project's water material colour and the brush default) and an unconditional `self.atom_color[idx] = color` write. Source-spawned particles now get a proper colour every time, no leak.
- **Regression tests added (`tests/test_simulation.py::TestParticleAddition`):**
  1. `test_add_particle_writes_default_color` — fresh particle has water-blue colour
  2. `test_add_particle_does_not_inherit_residual_slot_color` — hand-stain the next slot with a wall colour, add a particle, verify the wall colour is overwritten (this is the exact scenario from the bug report)
  3. `test_add_particle_honours_explicit_color` — explicit colour kwarg works
- **Suite:** 479 passing + 1 skipped + 0 xfailed in 12.12s (+3 tests).
- **Backlog candidate (not in scope):** ParticleBrush's parallel `_add_particle` is now structurally redundant with `Simulation._add_particle` and could call it instead. Also: `SourceProperties` could grow a `color` field so users can choose source colour. Both are post-bug-fix enhancements.

### EI-3 work item: Parallelize the LJ pair loop (atom-centric refactor)
- **Lead direction:** the DPD experiment showed thermostat-only optimization had a small ceiling (~10% of step cost at N=10k); the LJ pair loop was the real bottleneck. Lead picked: parallelize the LJ loop.
- **Approach:** the loop was previously serial because every pair (i,j) wrote to both `force_x[i] += fx` and `force_x[j] -= fx`, creating race conditions under parallelism. Refactored to **atom-centric**: each atom's iteration owns the writes to its own `force_x[i]` slot, with each pair computed twice (once per direction). Net 2× force evaluations, but pure data-parallel — no atomic adds needed.
- **Implementation:**
  - Added `build_atom_neighbor_csr(N, pair_i, pair_j, pair_count, nbr_start, nbr_idx)` to `physics_core.py` — converts the existing half-pair list to atom-centric CSR (count degrees → prefix-sum → scatter both directions). O(N + pair_count); runs once per neighbour-list rebuild.
  - Refactored `integrate_n_steps`'s LJ pair loop from serial `for k in range(pair_count)` to parallel `for i in prange(N)` with inner `for k in range(nbr_start[i], nbr_start[i+1])`.
  - Static atoms (`is_static==1`) skipped entirely — their forces are never used.
  - All pair-symmetric guards (intra-entity tethered skip, joint exclusion) preserved; both pair directions hit the same skip when applicable.
  - `Simulation` allocates `nbr_start` (capacity+1) and `nbr_idx` (2 * max_pairs); resized in step() during overflow loop and grown in `_resize_arrays`.
  - Both `Simulation.step()` and `_warmup_compiler` updated to call `build_atom_neighbor_csr` and pass CSR to `integrate_n_steps`.
- **Tests:** added `TestBuildAtomNeighborCSR` (5 cases covering empty list, single pair, complete graph, isolated atoms, monotonic nbr_start). Existing 484 tests all still pass — physics is preserved.
- **Suite:** 489 passing + 1 skipped + 0 xfailed (+5 from CSR tests).
- **Performance — full Simulation.step() benchmark (20 calls × 10 substeps):**

| N | Serial baseline | Parallel atom-centric | Speedup |
|---|---|---|---|
| 250 | 2.39 ms | 0.39 ms | **6.1×** |
| 1 000 | 3.20 ms | 0.43 ms | **7.4×** |
| 4 000 | 6.07 ms | 1.03 ms | **5.9×** |
| 10 000 | 10.56 ms | 1.54 ms | **6.9×** |

  Substantially over the predicted 2× (one core × 2× recompute). Likely sources of the bonus: better cache behaviour (atom-centric access pattern is sequential per atom, whereas the half-pair list jumped between atoms randomly), better Numba SIMD vectorization on the dense per-atom inner loop, and the static-atom skip avoiding wasted writes that the previous code did. Sub-linear scaling: 10× N now costs only ~3.6× per-substep.
- **10× target status:** at N=10k the new step cost is 1.54 ms — comfortably real-time (650+ steps/sec). The 10× headroom we wanted is now in hand. Future ceiling: more cores would scale further; deeper wins would require GPU.
- **Commit:** flow-state@`b8653e1` "CR-116 EI-3: Parallelize the LJ pair loop (atom-centric CSR)" — pushed to origin.

### EI-3 work item: Thermostat performance — option (4) explored and reverted
- **Lead direction:** after option (1), implement option (4) — DPD pair thermostat folded into the LJ pair loop.
- **Implementation:** added `use_dpd_thermostat` + `gamma_dpd` to Simulation, threaded `use_dpd, gamma_dpd, sigma_dpd_dt, inv_r_cut` through `integrate_n_steps`, added Groot-Warren-style dissipative + random pair forces to the existing `r2 < r_cut2_base` block (gated on `is_static[i]==0 && is_static[j]==0`), used Numba `np.random.standard_normal()` for the per-pair Gaussian. Added `DEFAULT_DPD_GAMMA=1.0` to shared/config.py. Added `TestDPDPairThermostat` (4 tests: off-is-noop, hot→cool, cold→warm, static-atoms-protected).
- **Physics correct:** all 4 DPD tests pass after redesigning to sparse atom layouts (initial packed setup blew up via LJ before DPD could thermostat). Suite 488 passing + 1 skipped + 0 xfailed.
- **Performance — the deciding finding:** full Simulation.step() benchmark (20 calls × 10 substeps) at varying N showed DPD is **2–3× SLOWER** than Berendsen, not faster:

| N | None | Berendsen | DPD | DPD vs Berendsen |
|---|---|---|---|---|
| 250 | 2.39 ms | 2.30 ms | 2.39 ms | tie |
| 1 000 | 3.20 ms | 2.65 ms | 4.78 ms | **1.8× slower** |
| 4 000 | 6.07 ms | 5.79 ms | 14.22 ms | **2.5× slower** |
| 10 000 | 10.56 ms | 12.07 ms | 29.14 ms | **2.4× slower** |

  Root cause: `np.random.standard_normal()` per pair (~50–100 ns each in Numba) dominates. With tens of thousands of pairs per substep, RNG alone is multiple ms. Berendsen's two cache-friendly add-multiply passes over N are extremely cheap by comparison. My theoretical reasoning about asymptotics ("folds into O(pairs) work that's already paid") was right about shape, wrong about constants.
- **Wider observation:** at N=10k the *non-thermostat* step cost is 10.56 ms — dominated by the LJ pair loop. The thermostat is ~10% of step cost in any configuration. Thermostat-only optimization has a small ceiling for the 10× target. The real headroom is parallelizing the LJ pair loop with proper atomic adds.
- **Lead decision:** option A — don't commit DPD; keep option (1)'s win; move on. Code reverted to HEAD via `git checkout` on physics_core.py, simulation.py, shared/config.py, tests/test_simulation.py. Working tree clean. Suite still 484 passing + 1 skipped + 0 xfailed.

### EI-3 work item: Thermostat performance — try option (1), drop `parallel=True`
- **Lead ask:** "ways to apply thermostats in a way that doesn't degrade performance as much as it currently does. Eventually a 10x increase in simulation size without significantly degraded performance." Lead picked option (1) from a 4-option menu.
- **Diagnosis:** `apply_thermostat` was `@njit(fastmath=True, parallel=True)` with two `prange` loops (KE reduction, velocity rescale). Hypothesis: thread-dispatch overhead dominates the actual O(N) arithmetic for typical N.
- **Microbenchmark (50 iters each, parallel vs serial @njit):**

| N | Parallel (median µs) | Serial (median µs) | Winner |
|---|---|---|---|
| 700 | 90.9 | 3.1 | serial **29×** |
| 2 800 | 77.6 | 11.5 | serial **6.7×** |
| 12 000 | 83.0 | 42.8 | serial **1.9×** |
| 35 000 | 129.3 | 122.3 | tie |
| 110 000 | 208.4 | 411.4 | parallel 2× |
| 220 000 | 462.7 | 944.1 | parallel 2× |

  Parallel has a fixed ~75-90 µs floor (thread dispatch). Serial scales linearly with N. Crossover ≈ N=30 000-35 000. The 10× simulation-size target sits right at the crossover; for today's N (hundreds to a few thousand), serial is dramatically faster.
- **Fix:** removed `parallel=True` decorator and replaced both `prange` with `range`. Math/signature unchanged. Added a docstring explaining the regression baseline.
- **Tests added (`tests/test_simulation.py::TestApplyThermostat`)** — there were no existing tests for `apply_thermostat`. Added 5 tests pinning the contract:
  - hot velocities pulled toward target (Berendsen direction + magnitude check)
  - cold velocities pushed toward target
  - static atoms unchanged
  - all-static is no-op (count==0 guard)
  - zero-velocity is no-op (current_T < 1e-6 guard)
- **Suite:** 484 passing + 1 skipped + 0 xfailed in 12.27s (+5 tests).
- **Status:** uncommitted. The crossover behaviour means a future 10× target needs a different approach (option 4: DPD pair-thermostat folded into the LJ loop). For now this is the right move.

### Commits landed and pushed (Lead approved "commit and push")
Four small commits on `cr-116-beach-trip-exploration`, pushed to origin:

| Hash | Subject |
|------|---------|
| `48f2c1c` | CR-116 EI-3: Clear xfail registry in tests/README.md |
| `e045506` | CR-116 EI-3: Route Source creation through AddSourceCommand |
| `ee56ee0` | CR-116 EI-3: Sync Resize-World input field on undo/redo |
| `18e4778` | CR-116 EI-3: Initialize atom_color in Simulation._add_particle |

- Branch HEAD: flow-state@`18e4778` on `cr-116-beach-trip-exploration` (pushed).
- Pipe-dream submodule pointer unchanged per CR-116 envelope.
- All within CR-116 bounds (flow-state-only, no SDLC-FLOW-RS modifications).
- Suite: 479 passing + 1 skipped + 0 xfailed (was 469 at session start; +10 tests).
