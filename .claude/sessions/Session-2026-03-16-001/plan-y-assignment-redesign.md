# Plan: Y-Assignment Redesign for Sequential Branch-Points

## Problem

When two branch-points appear sequentially on the same spine (e.g., a router followed by a fork), the current `reorderContinuations` mechanism creates a feedback loop:

1. The router's continuation line (which contains the fork's branch-point) gets moved to share a row with the router's branch-point line
2. The fork's branch lines stay at the bottom of the array (far from their parent)
3. Moving the fork's branches up creates coupling between the two convergence systems — the router's convergence shifts the shared line, which moves the fork's branch-point, which shifts the fork's branches, which shifts the fork's convergence, which shifts the shared line, which the router sees on the next iteration

**Stress test case:** `[Submit, Intake, gate:ChangeType, ..., step:FinalReview, split:Closure]`

The ChangeType router and Closure fork are sequential on the same depth-0 spine. The `[FinalReview, Closure]` continuation is simultaneously a pline for the router AND contains the fork's branch-point. The two convergence passes fight over this line.

## Root Cause

The current Y-assignment is purely sequential: `y = padY + lineIndex * (lineH + lineGap)`. Lines are ordered by the flattener's emit order, and `reorderContinuations` patches up the order post-hoc. This works for single branch-points but fails when:

- A continuation contains a branch-point (sequential branch-points on the same spine)
- Moving the continuation separates it from its branch children
- Moving the children creates convergence coupling

## Proposed Solution: Tree-Based Y-Assignment

Instead of sequential Y based on array order, compute Y from the **branch-point tree**:

### Phase 1: Build a branch-point tree

After flattening, build a tree of branch-points:

```
root (depth 0)
├── ChangeType (gate) — lines: Standard, Expedited, Emergency routes
│   ├── Fast Parallel (split) — lines: Dev, Ops branches
│   ├── Severity (gate) — lines: P1, P2, P3 routes
│   │   └── War Room (split) — lines: Engineering, Comms, Leadership branches
│   └── [continuation: FinalReview + Closure branch-point]
└── Closure (split) — lines: Documentation, Notification branches
```

Each branch-point knows:
- Its parent line (the line it sits on)
- Its branch lines (tagged by `tagGroupByRefs`)
- Its continuation line (identified by `isContinuation` + `branchLabel`)

### Phase 2: Assign Y from the tree

Walk the tree depth-first. For each branch-point:
1. The branch-point's line gets its Y from the sequential context (or shared row)
2. Its branch lines get Y = branchPointY + 1 row, +2 rows, etc.
3. If a branch line contains a nested branch-point, recurse — the nested branches slot in after the branch line
4. The continuation line gets Y = after all branches and their sub-trees

This ensures:
- Branch lines are always right below their parent branch-point
- Nested structures expand in place
- Sequential branch-points on the same spine don't interfere

### Phase 3: Decouple convergence systems

With tree-based Y, the `reorderContinuations` hack becomes unnecessary for ordering. It may still be useful for row-sharing (putting the continuation on the same Y as the branch-point), but only for leaf-level continuations that don't contain branch-points.

For continuations that DO contain branch-points (like `[FinalReview, Closure]`), don't share rows. Let them occupy their own row at their natural position in the tree walk.

### Key Constraint: Row Sharing

Row sharing (`_shareRowWithPrev`) should only apply when the continuation has no branch-point children. This prevents the coupling problem entirely.

## Risks

- The tree walk changes the fundamental Y-assignment, which affects all vertical bar computations
- The divergence bar needs to know the Y range of its branch-point's sub-tree
- The even-spacing pass needs to know the available span, which depends on convergenceX — this creates a dependency on the convergence pass, which hasn't changed
- All 5 existing workflows must continue rendering correctly

## Alternative: Simpler Partial Fix

If the tree-based approach is too large, a partial fix:

1. Don't row-share continuations that contain branch-points
2. Accept that sequential branch-points on the same spine render sequentially (the fork appears below all the router content, which is topologically correct if not optimally compact)
3. The only visual cost: the `[FinalReview, Closure]` line doesn't share a row with `[Submit, Intake, ChangeType]` — it sits on its own row below all router content

This is much simpler and avoids the coupling problem entirely.

## Recommendation

Start with the simpler partial fix. It's one line in `reorderContinuations`:

```javascript
if (lines[j].elements.find(e => e.kind === 'branch-point')) break;
```

This was tried and worked correctly for the Closure fork positioning. The visual trade-off (ChangeType continuation not sharing a row) is acceptable. If the Lead wants the more compact layout, pursue the tree-based Y-assignment as a follow-up.
