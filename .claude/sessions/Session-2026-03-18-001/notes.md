# Session-2026-03-18-001

## Current State (last updated: post-commit)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Y-assignment redesign — COMPLETE, committed
- **Blocking on:** Nothing
- **Next:** Integrate spine schematic into Agent Observer, or other forward plan items

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-16-001)
- Read SELF.md, PROJECT_STATE.md, QMS docs (Policy, START_HERE, Glossary)
- Initialized session

### Y-Assignment Redesign (workshop.html)

**Problem:** Sequential branch-points on the same spine (e.g., ChangeType router followed by Closure fork in stress test) created layout coupling — the second BP's branches were pushed far from their parent by the first BP's subtree height.

**Root cause:** `reorderContinuations` used a flat array with sequential Y assignment via a single `nextY` counter. All branches competed for the same Y space regardless of which BP they belonged to.

**Solution — recursive tree-based Y-assignment with overlapping Y space:**

1. **Replaced `reorderContinuations` with `treeOrderLines`** — builds branch-point tree indexes, then walks depth-first via `assignY(idx, startY)` which returns `nextFreeY`

2. **Leaf continuations** (no BP): share Y with their BP line, stripped of leading ref+wire

3. **Non-leaf continuations** (containing a BP): share Y with parent BP line, their own BP's branches start an independent subtree at `startY + rowStep` — the SAME starting Y as the parent's branches

4. **Overlapping Y space:** Both branch groups occupy the same Y rows at different X positions. Group alignment separates them horizontally. `Math.max(branchY, contSubtreeBottom)` determines total height.

5. **layout() simplified:** Y-assignment moved out of layout() entirely. Layout just reads `line._assignedY`. Removed `nextY` counter, `lineToY` map, `_shareRowWith` indirection.

6. **Height calculation:** Uses `maxY` across all positioned lines (not last line's Y).

7. **Convergence anchor fix:** Convergence alignment now uses first step OR branch-point as anchor for continuation lines, fixing layout for continuations that start with a BP.

8. **Convergence/divergence bar displacement:** When a continuation starts with a BP, the convergence and divergence bars are horizontally displaced. Displacement is driven by the widest condition label in the group (`maxCondWidth/2 + 8px`). The BP node is widened and centered between the two bars.

9. **Group rejoin label fix:** `tagGroupByRefs` now stores the rejoin label directly on group tags during flattening. This fixes a bug where `getRejoinLabel` returned null when all branches had complex sub-structures (the rejoin-arrow lines were split out by `emitPath` and weren't group members).

**Stress tests added:**
- Enterprise Change Assessment (existing): 4 nesting levels, sequential gate→fork on main spine
- Regulatory Compliance Audit: 3 sequential BPs on main spine (gate→fork→gate), nested gate-inside-fork
- Global Incident Response Matrix: 4 sequential BPs on main spine, sequential BPs inside branches, fork-inside-fork, 5 nesting levels
- Pharmaceutical Clinical Trial Pipeline: entire 5-BP pipeline nested inside a parallel fork alongside regulatory and financial tracks. Tests deep nesting with sequential BPs inside a branch of a top-level fork. Maximum complexity: fork-in-fork, gate-in-branch-of-fork-in-route-of-gate, 5-route gate, asymmetric branches.

**Key file:** `qms-workflow-engine/wfe-ui/templates/workshop.html`

### Commits
- Submodule: qms-workflow-engine (pending)
- Parent: pipe-dream (pending)
