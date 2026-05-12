# Session-2026-05-12-001

## Current State (last updated: after PBC density-gradient fix)
- **Active document:** CR-116 IN_EXECUTION v1.2 — Exploration CR (beach-trip Flow State work)
- **Current EI:** EI-3 (free-form exploration) — open across sessions
- **Blocking on:** Awaiting Lead direction
- **Next:** Await Lead direction
- **Suite:** **941 passing + 1 skipped** (+4 from PBC fix)
- **Subagent IDs:** none active
- **Branch state:**
  - `.test-env/flow-state/` — `cr-116-beach-trip-exploration` — PBC fix committed + pushed; pipe-dream submodule pointer intentionally NOT bumped per Exploration-CR convention (dev branch only)
  - `pipe-dream/main` — session notes + PROJECT_STATE.md committed + pushed; submodule pointer unchanged

## Session-start checklist
- Previous session was Session-2026-05-11-001 (spanned 2026-05-11 → 2026-05-12); today is 2026-05-12, user announced new session → Session-2026-05-12-001
- CURRENT_SESSION updated; folder created
- Read SELF.md, prior session notes (Session-2026-05-11-001), QMS-Policy.md, START_HERE.md, QMS-Glossary.md, PROJECT_STATE.md
- Inbox: empty
- No compaction-log in this folder → genuine new session

## Known limitations carried from R5/R6 + menu fixes (CR-116 EI-3)
- (a) `AddMoleculeCommand.undo` truncation-based — loses any particles added between place and undo (matches brush-undo cliff). Cleaner fix needs a `molecule_id` array on Simulation.
- (b) No rotation control in molecule placement UX (right-drag-to-rotate is natural extension; `rotation` field already plumbed through `AddMoleculeCommand`).
- (c) `MoleculeBuilderDialog`'s atom-mode material dropdown doesn't follow `session.active_material`; uses first material in the palette instead.

## Concerns to surface to Lead
- None new. PROJECT_STATE.md bloat was addressed last session (~85% reduction).

## Progress Log

### [start] Session-start checklist
- Created session folder
- Updated CURRENT_SESSION pointer
- Read all required QMS docs + prior session notes
- Verified inbox empty
- Verified branch state consistent: pipe-dream main clean (sans CURRENT_SESSION), .test-env/flow-state clean on cr-116 branch at parent's submodule pointer

### PBC density-gradient root-cause fix (CR-116 EI-3)

Lead reported: "with PBC the density is lower at the boundaries in large simulations, which of course should not be the case."

**Diagnosis.** Off-by-one in the cell-list count in `build_neighbor_list`:

```python
n_cells = int(world_size // cell_size) + 1
```

The `+1` exists so OPEN/REFLECTING has a padding cell for atoms briefly outside `[0, world_size)`. Under PBC the wrap forces positions into `[0, world_size)` so the padding cell is partly or fully empty — but the wrap arithmetic (`nx += n_cells`) used this inflated count as the cell-count modulus, so an atom in cell 0 looking left landed on cell `n_cells-1` (the empty/partial padding cell) instead of on the populated cell across the boundary.

Two regimes:
- **Exact divisibility** (`world_size % cell_size == 0` — e.g. user resizes to 28.0, 56.0, etc.): cell `n_cells-1` is fully empty. All cross-boundary cell-list pairs missed.
- **Non-exact** (default ws=50, cs=2.8): cell `n_cells-1` is partly populated; pairs in a strip `(n_cells*cs - world_size)` wide on each side are missed (cell `n_cells-2` not searched).

In either case atoms within ~`cell_size` of either edge lose some cross-wrap LJ partners. Inside neighbours push at full strength; missing wrap partners don't push back. Net inward force → steady-state low-density boundary layer. The pair-force loop's minimum-image arithmetic is fine; the bug is purely in **which pairs the neighbour list emits**.

**Why "large simulations" make it evident.** Per-pair effect is small but persistent; more particles + more time = clearer steady-state gradient. Existing `TestPeriodicNeighbourList` tests only probed atoms at `x=0.5` and `x=L-0.5` — these sit in the populated last cell at default ws, so they passed while the bug hid one cell deeper.

**Fix.** Branch `n_cells` and `inv_cell` on `boundary_mode` in `build_neighbor_list`:
- PBC: `n_cells = max(3, int(world_size // cell_size))`, `inv_cell = n_cells / world_size`. Cells tile `[0, L)` exactly with width `L / n_cells` (≥ cell_size since floor rounds down). Wrap arithmetic now lands on populated cell.
- OPEN/REFLECTING: unchanged (`+ 1` padding cell, `1/cell_size`).

Also tightened `_pbc_safe` to the matching condition: `int(world_size // cell_size) >= 3` (formerly `+ 1 >= 3` i.e. `>= 2`, which was permissive AND buggy).

**Tests added (+4, all green):** new `TestPeriodicCellListBoundaryDepth` in `tests/test_simulation.py`.
- `test_wrap_pair_found_at_exact_divisibility` — ws=28 (= 10 × cs); atom at x=0.5 paired with atom at x=L−0.5 via wrap. Pre-fix: 0 pairs; post-fix: 1.
- `test_wrap_pair_found_beyond_last_cell_under_default` — default ws=50; atom at x=0.1 paired with atom at x=47.5 (in cell 16, one deeper than wrap target cell 17). Wrap dist 2.6 < r_list 2.8. Pre-fix: 0 pairs; post-fix: 1.
- `test_wrap_pair_found_at_exact_divisibility_corner` — diagonal wrap at ws=28; atoms at opposite corners. Pre-fix: 0 pairs; post-fix: 1.
- `test_no_double_count_at_exact_divisibility` — control: 3 interior atoms at ws=28 still give 3 pairs (no false positives).

**Files touched (3 modified):**
- `engine/physics_core.py` — `build_neighbor_list` n_cells/inv_cell branch on boundary_mode; comment block at module top updated.
- `engine/simulation.py` — `_pbc_safe` matches new formula.
- `tests/test_simulation.py` — new `TestPeriodicCellListBoundaryDepth` class.

**Suite:** 937 → **941 passing + 1 skipped** (+4). Zero regressions across the full suite (27 seconds).
