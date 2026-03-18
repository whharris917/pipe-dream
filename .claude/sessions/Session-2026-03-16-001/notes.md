# Session-2026-03-16-001

## Current State (last updated: post even-spacing commit)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Schematic renderer — feature-complete for workshop
- **Blocking on:** Nothing
- **Next:** Commit 3 of ref removal (cleanup dead ref code), integration into Agent Observer

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-15-004)
- Read SELF.md, PROJECT_STATE.md, QMS docs (Policy, START_HERE, Glossary)
- Initialized session

### Spine Model Design

Designed a canonical representation for arbitrarily complex workflows:
- **Three recursive segment types:** Step, Gate (router/OR), Split (fork/AND)
- **Key insight:** Every workflow decomposes into a recursive sequence of these three primitives
- **Properties:** Lossless (full topology), renderable (any format), context-aware (execution state), recursive (arbitrary nesting)

### Workshop Page — HTML/CSS Prototype

Built initial prototype at `/workshop` route. Iterated through:
1. Raw SVG approach — rejected (not intuitive or visually appealing)
2. HTML/CSS stepper approach — liked the style, but needed full-detail mode
3. Electrical schematic convention — reference markers, left-aligned lines, divergence/convergence bars

### Electrical Schematic Convention

Adopted reference marker pattern from electrical schematics:
- Branch points terminate with reference markers (circles with letters)
- Each route/branch starts on its own left-aligned line with that marker
- Lines read left-to-right and terminate with a rejoin marker
- Vertical bars indicate grouping: dotted amber for OR (gates), solid blue for AND (splits)
- `/` separator for OR, `+` separator for AND (later replaced by vertical bars)

### Canvas-Based Custom Engine

Replaced CSS/SVG hybrid with a single-canvas renderer after persistent alignment issues with mixed layout systems. Three-phase architecture:

1. **Flatten:** Spine → lines (reference markers, branch points, steps, wires, rejoin arrows)
2. **Layout:** Compute all x,y positions in one coordinate system
   - Group alignment: shift grouped lines so ref markers align under parent branch-point
   - Rejoin alignment: iterative pass aligning convergence columns, resolving cross-dependencies
   - Continuation alignment: shift continuation lines to meet convergence columns
3. **Draw:** Render everything to canvas — vertical bars first (behind), then elements on top

### Key Layout Challenges Solved

1. **Nested group alignment:** Process outermost groups first so inner branch-points see shifted positions
2. **Deepest-group ownership:** Lines in multiple groups align to their deepest (most specific) group
3. **Continuation line deferral:** Lines after nested branch-point resolution escape to parent depth
4. **Cross-column dependencies:** Iterative alignment resolves D-column/A-column ordering
5. **Convergence bars by X-position:** Only connect rejoin refs that are visually aligned
6. **Continuation ordering:** Push continuations right after their producing branch to avoid crossings

### Design Decisions

- **All branches must converge:** Every workflow bounded by final Close; no dangling terminal paths
- **Right-align rejoin markers:** Fill gaps with wire lines rather than leaving empty space
- **Continuation lines escape nesting:** Drop to parent depth after branch resolution
- **Avoid intersection:** Reorder continuation lines to prevent convergence bars crossing content

### Post-Commit Refinements (commits 2b0dd17, 022e236)

1. **Continuation reorder + row sharing** — Post-merge continuation lines moved above routes and share Y with branch-point line (no extra vertical gap)
2. **Ref labels removed** — Circles with A/B/C/D labels made invisible; vertical bars and visual structure communicate the same information
3. **Condition labels on divergence bar** — Branch labels (risk=low, Compliance) centered on the vertical bar, saving horizontal space
4. **Wire stripping** — Post-merge nodes sit directly at convergence point, no connecting wire

### Known Issue: Convergence Bar Alignment

The convergence bar meets post-merge nodes at their left edge, not center. Root cause: the layout system uses invisible zero-width ref anchors (vestigial from the label era) as positioning targets. The convergence bar X is computed from these refs, and nodes are placed after them. A centering post-pass was attempted but is a band-aid — the correct fix is to remove ref anchors entirely and use node centers as the canonical anchor points for bar positioning.

### Ref Anchor Redesign (commits 86d8586, b718692, 93090c1)

Three-phase plan executed:
1. **Commit 1 (86d8586):** Added line-level metadata (branchLabel, branchType, isContinuation) — purely additive
2. **Commit 2 (b718692):** Switched all flattener reads to metadata; node-center convergence with per-label convergenceX map; deepest-first label ordering
3. **Convergence inflation fix (93090c1):** Eliminated `wireFromX` entirely — wire start computed at draw time via `lastItemRight` tracking. Continuation lines use `contentEndX + arrowW` (not inflated arrow tips) for convergenceX. Inner merge lines constrain outer merge positions.

### Visual Polish (commits df43dfa, current)

1. **Monochrome palette** — removed amber/blue distinction; dotted vs solid bars + shape carry semantics
2. **Hexagon gates** — decision nodes rendered as `< >` hexagons instead of rounded pills
3. **Fork bars** — parallel nodes rendered as rounded rects with double vertical bars on each side
4. **Condition label borders** — all pills now have consistent borders
5. **Even node spacing** — nodes distributed evenly across available span between divergence and convergence points; wires become elastic gaps

### Commits
- Submodule: qms-workflow-engine `2f9d8f0` → `2b0dd17` → `022e236` → `86d8586` → `b718692` → `93090c1` → `df43dfa` → current
- Parent: pipe-dream `26ffc2a` → `3ba806a` → `6f3a7ed` → `cd9522b` → `fe4cb09` → current
