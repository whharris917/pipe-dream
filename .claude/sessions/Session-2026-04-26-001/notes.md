# Session-2026-04-26-001

## Current State (last updated: Graph Builder v2 — typing + merge + container collapse)
- **Active document:** None (engine-submodule direct work on `dev/content-model-unification`)
- **Current EI:** N/A
- **Blocking on:** Lead visual review of Graph Builder v2
- **Next:** Per Lead — item 4 (compile graph to Razem composition) is the ultimate goal but parked; iterate on v2 first
- **Subagent IDs:** none

## Session start checklist
- [x] Determined this is a new session (new date 2026-04-26; previous was Session-2026-04-25-002)
- [x] Created `.claude/sessions/Session-2026-04-26-001/`
- [x] Wrote `Session-2026-04-26-001` to CURRENT_SESSION
- [x] Read previous session notes (Session-2026-04-25-002 — bus iterations rejected, A.X component-integrated showcases adopted)
- [x] Read SELF.md
- [x] Read QMS-Policy.md, START_HERE.md, QMS-Glossary.md
- [x] Read PROJECT_STATE.md
- [x] Inbox: empty
- [x] Submodule state:
  - `qms-workflow-engine` on `dev/content-model-unification` — clean
  - Root repo clean
- [x] Last commit: `24564a3 Session-2026-04-25-002: Bump engine — A.X component-integrated showcases`

## Entry context
Per PROJECT_STATE §6 the immediate priority is **building real QMS workflows as component compositions** — CR creation, review, document lifecycle pages — and wiring QMS / Workspace / Inbox to real data. The dev branch has full site shell but every shipping page seed is still a demo or gallery. The previous session closed the nesting-workshop chapter (Experiment A is canonical; bus variants rejected; component-integrated showcases retained).

Auto mode is active.

## Progress Log

### [bootstrap] Session bootstrapped
- Folder created, CURRENT_SESSION updated, prior context loaded.
- No queued work; standing by for Lead direction.

### Collapsed A.1 / A.2 / A.3 into a single Experiment A

**Lead's direction:** collapse the three component-integrated showcase variants into a single Experiment A that includes everything; we'll iterate on that.

**Implementation in `qms-workflow-engine/app/templates/workshop_nesting.html`:**
- Topbar: deleted the child row with A.1/A.2/A.3 buttons; only the `Experiment A` tab remains.
- Sections: deleted the three `<section>` panels for `exp-a1`, `exp-a2`, `exp-a3`.
- CSS: simplified `.nest-ws__canvas[data-panel="exp-a"]` and `.expA-root` selectors (dropped the `, …a1, …a2, …a3` comma lists). Updated comment block above the embedded-component styles since those rules now style A's leaf body directly, not "showcase variants."
- JS: deleted the orphaned `expABase` IIFE (~225 lines of duplicate scaffolding), the `renderShowcase` function (~60 lines), and the three `renderShowcase('.expA*-root', …)` invocations (~80 lines).
- A's IIFE: added a `buildLeafBody(leafPath)` helper that returns the combined Razem-component HTML, and modified the leaf-panel block to call it and replace `.exp431x-leaf-body`'s innerHTML.

**Combined leaf now contains 5 components:**
1. **Reflection** — TextForm (1–2 sentence reflection on the article)
2. **Comprehension check** — ChoiceForm with 3 radio options
3. **Notes** — TextForm (brief notes from the article)
4. **Date read** — DateForm
5. **Topics covered** — CheckboxForm (Recursion / Iteration / Induction)

Reflection and Notes overlap conceptually (both freeform text); kept both since the Lead asked to "include everything." Easy to consolidate or split apart in further iteration.

**Verification:**
- File: 1683 → 1347 lines (≈336 lines removed, ~20% reduction).
- No remaining references to `expA1|expA2|expA3|exp-a1|exp-a2|exp-a3|expABase|renderShowcase`.
- JS: 28371 chars, 86/86 braces, 352/352 parens, `node --check` passes.
- HTTP 200 at `/workshop/nesting`.
- Only one tab in served HTML (`data-tab="exp-a"`).
- Served HTML contains all 5 component types (text×2, choice, date, checkbox).
- **Visual review still required** — cannot drive a real browser from this shell.

### Graph Builder workshop — scaffolded

**Lead's direction:** new workshop page "Graph Builder" — inspired by but not programmatically connected to the nesting visualizations' "node on line" motif. Aerial railroad-yard aesthetic (tracks split + merge, vertical orientation). Initial state: single centered node + dotted stub + dashed `+` ghost below. Hover affordances: Add Node on the ghost; Add Node Before / Add Node After / Create Branch on existing nodes.

**Files:**
- `qms-workflow-engine/app/routes.py` — added a fourth entry to `_WORKSHOPS` (slug `graph-builder`).
- `qms-workflow-engine/app/templates/workshop_graph_builder.html` — new template (~370 lines), self-contained HTML/CSS/JS.

**Architecture:**
- **Layers:** SVG underneath for tracks (curved cubic-bezier paths and dotted ghost stubs) + two HTML layers above (`gb__layer[data-layer="ghosts"]` and `[data-layer="nodes"]`). Layered approach lets nodes use HTML/CSS for hover affordances while edges stay SVG for natural curves.
- **State:** `state.nodes[id] = { id, label, x, y, parents:[ids], children:[ids] }` plus `state.nextId`. DAG model (multiple parents/children allowed).
- **Mutations:**
  - `addAfter(t)` — splice: parents → t → N' → (t's existing children). New node takes (t.x, t.y+ROW_H); existing children shift down by ROW_H so the new row fits.
  - `addBefore(t)` — splice: (t's existing parents) → N' → t. New node takes t's old slot; t and its descendants shift down by ROW_H.
  - `createBranch(t)` — adds a new leaf child of t at (t.x+COL_W, t.y+ROW_H), with collision-aware horizontal search (`findFreeX`).
- **Layout:** explicit (x, y) per node; no auto-relayout. `shiftSubtreeY(rootId, dy)` cascades shifts. `resolveCollision(nodeId)` bumps right by COL_W until clear.
- **Edges:** `M x1 y1 C x1 midY, x2 midY, x2 y2` cubic bezier from parent.bottom to child.top — gives the smooth railroad-yard curve when split and (eventually) merge happen.
- **Ghosts:** every leaf gets one — dashed circle with `+` at (leaf.x, leaf.y+ROW_H), connected by a dotted SVG stub. Hover shows "Add Node" pill tooltip; click invokes `addAfter(leaf)`.
- **Node affordances:** on hover, three pill buttons fade in — "Add Before" above, "Create Branch" right, "Add After" below. Buttons are `pointer-events:auto` inside an `opacity:0` cluster that triggers on `:hover`.
- **Reset button** in the topbar to clear back to initial state.

**Aesthetic:**
- Indigo→violet gradient on rails (SVG `linearGradient` with `id="gb-rail"`).
- Glass topbar, pastel radial-gradient background (matched to the nesting workshop for visual consistency across the workshop hub).
- Node: 44px gradient-filled circle with white outer ring and soft purple shadow; hover scales 1.04× and adds an aura.
- Ghost: 32px dashed circle, indigo outline, "+" glyph; hover fills with indigo tint and scales 1.1×.

**Verification:**
- File: 369 lines.
- JS: 9017 chars, 44/44 braces, 145/145 parens, `node --check` passes.
- HTTP 200 at `/workshop/graph-builder` and at `/workshop`.
- Hub now lists 4 workshops including `graph-builder`.
- **Visual review required** — initial node placement uses `requestAnimationFrame` to wait for the canvas to have measurable dimensions; should center horizontally and sit at ~1/3 from the top. Affordance fade-in is purely CSS-driven.

**Known limits / next-iteration material:**
- No merges yet — the graph can split via "Create Branch" but there's no affordance to merge two branches back into a common downstream node. The data model already supports merges (multi-parent), so this is just a UI gap.
- No drag/reposition — nodes are at fixed computed positions.
- Node labels are auto ("Node 1", "Node 2"). No rename UI.
- No undo/redo or persistence — page reload resets the graph.
- No automatic layout — manual offsets work for a few additions but get awkward for dense graphs.

### Graph Builder v2 — node typing + merge + container collapse

**Lead's direction:** Connected the workshop to its real purpose — a graph-based authoring view of the same flows expressible via Razem's Tabs/Sequence/Components. After discussion (BPMN as closer reference than Studio 5000; ladder logic's deterministic-scan model misleads for user-paced workflows), Lead asked to implement my proposed items 1-3 (item 4 — compile-to-Razem-composition — parked as the ultimate goal):
1. **Node typing** — `form` / `container` / `action` / `gate` with distinct shapes
2. **Merge affordance** — drag to fuse tracks (data model already supported multi-parent)
3. **Container expand/collapse** — `Tabs`-like nodes that hide their subtree as a single block

**Implementation in `qms-workflow-engine/app/templates/workshop_graph_builder.html`** (1683→369→868 lines):

**Item 1 — Node typing.** Each node gets a `type` field defaulting to `form`. Visual differentiation via separate `.gb-node-shape` element (so `clip-path` doesn't clip the affordance buttons that live one level up):
- `form` — rounded square (border-radius 12px), indigo→violet gradient.
- `container` — pill (80×44, border-radius 999px), violet→pink gradient. Wider footprint signals "groups things."
- `action` — chevron pointing down (`clip-path: polygon(0% 0%, 100% 0%, 100% 65%, 50% 100%, 0% 65%)`), pink→amber gradient.
- `gate` — diamond (`clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0% 50%)`), amber→indigo gradient.
A small italic "type" pill in the right-side label stack shows the current type and cycles on click.

**Item 2 — Merge.** Added a 4th cardinal affordance "⇢ Merge" on the LEFT side of the node (balancing "Create Branch" on the right). On `mousedown`:
- `root.classList.add('is-merging')` — hides all affordance clusters and switches cursor to crosshair.
- `markEligibleTargets(sourceId, true)` — every visible non-self, non-existing-child, non-ancestor node gets `data-merge-eligible="true"` and a green-glow box-shadow.
- A `<path class="gb-edge gb-edge--ghost">` (dashed, semi-transparent) is appended to the SVG and updated on each `mousemove` with `clientPointToCanvas` translating cursor to canvas coordinates (accounts for canvas scroll).
- On `mouseup`, `document.elementFromPoint` resolves the drop zone; if it lands inside a `.gb-node`, we call `merge(source, target)` which appends to `source.children` and `target.parents`. Cycles are prevented by `isAncestorOrSelf(targetId, sourceId)` walking parent links upward from source. Self-merge and duplicate edges are also rejected.
- Cleanup: temp path removed, eligibility attributes cleared, `is-merging` class dropped.

**Item 3 — Container expand/collapse.** Container-typed nodes get a small caret button (▾/▸) in the top-right corner, click to toggle `n.collapsed`. When a container is collapsed:
- `isHidden(nodeId)` walks parents and returns `true` if any strict ancestor is a collapsed container; `visibleNodes()` filters them out.
- The container itself stays visible. A "(N hidden)" badge joins the right-side label stack.
- Edges, ghosts, and node DOM all skip hidden nodes. The container becomes a leaf-for-rendering-purposes and gets its own ghost stub + ghost `+` below it.
- When expanded, descendants reappear and a dashed bounding box (`<rect class="gb-container-frame">` plus `<text class="gb-container-frame-label">`) wraps the container's full subtree, with the container's label in small caps above.

**Other changes:**
- Removed the SVG `<defs>` gradient (unused after switching edges to solid `#6366f1`).
- Hint text updated: "Hover a node for affordances · Click + to grow · Drag Merge to fuse tracks · Click a type to cycle".
- Refactored `makeNode(label, x, y)` → `makeNode({label, x, y, type})` for forward-compatibility.

**Verification:**
- File: 868 lines (was 369; ~2.4× growth for three substantial features).
- JS: 19530 chars, 89/89 braces, 335/335 parens, `node --check` passes.
- HTTP 200 at `/workshop/graph-builder`.
- Tokens for new functions (`TYPES`, `cycleType`, `toggleCollapse`, `merge`, `markEligibleTargets`) all present in served HTML.
- **Visual review required** — interactions (drag merge, type cycling, container collapse with subtree hide and bbox draw on expand) cannot be exercised from the shell.

**Item 4 (compile graph → Razem composition) parked** per Lead's direction.

**Correction on Razem's expressiveness.** I had claimed that the merge feature produces "multi-parent shapes Razem's nested-container model can't directly express." Lead corrected: Razem already expresses merges via container nesting. A `Tabs` (or any divergent container) embedded in a `Sequence` IS a split-and-merge: each tab is a branch, and the next step in the outer Sequence is the merge point. So `TabForm{A, B, C}` followed by `D` in a `SequenceForm` is exactly the diamond `[A|B|C] → D`. The pattern composes recursively (a merge inside a tab is just another container whose successor is the inner merge node).

This makes item 4 more tractable than I claimed. The compile step is essentially a **series-parallel decomposition**: walk the graph, find each split-merge pair, wrap the branches in a divergent container, place the merge as the container's successor. The genuine constraint is that the graph must be series-parallel — arbitrary DAGs where a path "escapes" one divergent region and merges into another can't be cleanly expressed without node duplication.

### Series-parallel enforcement at merge time

**Lead's direction:** restrict merges so the graph stays series-parallel by construction. Without this, the user can interactively build non-SP topologies (Wheatstone bridges, cross-merges) that would block the eventual graph→Razem compilation.

**Approach.** `addAfter` / `addBefore` / `createBranch` are SP-preserving by their nature (chains, splits, splices) — only `merge` can violate. Validation runs at two points:
1. **Drop time** — `merge()` calls `wouldRemainSP(s, t)` which tentatively pushes the new edge, runs `isSeriesParallel()`, and reverts. If non-SP, the merge is silently rejected.
2. **Drag time** — `markEligibleTargets()` runs the same SP-test on every visible candidate target, so the green eligibility glow only appears on SP-preserving targets. The user gets visual feedback before they release the mouse.

**`isSeriesParallel()` — Valdes-Tarjan-Lawler reduction.** Add a virtual source `VS` connected to every root and a virtual sink `VT` connected from every leaf, then repeatedly apply:
- **Series:** contract any non-`VS`/`VT` node with in-degree 1 and out-degree 1 (replace `u → x → w` with `u → w`).
- **Parallel:** collapse duplicate `(u, v)` edges into one.
SP iff the graph reduces to a single `VS → VT` edge. O((V+E)²) worst case; trivially fast for the small graphs the workshop produces.

**Verification.** Standalone test of the SP algorithm on 8 known cases (chain, diamond, fork, Wheatstone bridge, cross-merge, nested SP, parallel chains, single-node) — all correct. JS parses cleanly: 22946 chars, 99/99 braces, 390/390 parens. HTTP 200 at `/workshop/graph-builder`.

**Known UX gap.** Rejected merges are currently silent — the temp ghost line vanishes on release with no visible feedback. The eligibility highlighting during drag *should* prevent invalid drops in practice, but a brief flash on the source node or a small toast on rejection would harden it. Parked as a polish-pass item.

### Edge-splice replaces Add Before / Add After

**Lead's direction:** drop the `Add Before` and `Add After` affordance buttons. Keep the dashed-circle leaf ghost as the only "Add After" path, and add a `+` button that appears on edge hover to splice a node into an existing edge between two nodes.

**Why it's better.** The edge `+` is more general than the old buttons:
- For a node with multiple parents/children, edge-splice is precise about *which* edge to insert into; the old `addBefore`/`addAfter` had to reroute *all* parents or *all* children.
- The new node always lands in the right structural slot (between exactly two specific nodes).
- Splice is SP-preserving by construction: it inserts a series-reducible node (in-deg 1, out-deg 1), so no SP check is needed.

**Implementation in `workshop_graph_builder.html`** (868→1032 lines):
- **Removed:** `addBefore` function (now orphaned), the two `aff.appendChild(makeAffBtn(...))` calls for Before and After, and the now-unused `[data-pos="before"]` and `[data-pos="after"]` CSS rules. Affordance cluster on hover is now just two: `Create Branch` (right) and `⇢ Merge` (left).
- **Added `spliceEdge(parentId, childId)`** — places a new node at `(child.x, parent.y + ROW_H)`, re-links `parent → newNode → child`, shifts the child + its descendants down by one row to make space.
- **Edge rendering refactored:** each edge is now a `<g class="gb-edge-group">` containing three children — a wide invisible `<path class="gb-edge-hit">` (stroke-width 18, `pointer-events: stroke`) for reliable hover detection, the visible `<path class="gb-edge">` rail, and a `<g class="gb-edge-btn">` at the parametric midpoint with a dashed circle + `+` glyph. CSS shows the button only when the parent group is hovered (`.gb-edge-group:hover .gb-edge-btn`), and the button stays visible while it's directly hovered. Click invokes `spliceEdge(from, to)`.
- **Merge-drag interlock:** during a merge drag, `.gb.is-merging` disables both the splice buttons (`opacity: 0; pointer-events: none`) and the hit-paths (`pointer-events: none; cursor: crosshair`) so neither interferes with `elementFromPoint` drop detection.
- **Hint text updated:** "Click + below a leaf to grow · Hover an edge for + to splice · Hover a node for Branch/Merge · Click a type to cycle"

**Bezier midpoint property used:** for cubic beziers from `(x1, y1)` to `(x2, y2)` with control points at `(x1, midY)` and `(x2, midY)` (both sharing midY), the parametric midpoint at t=0.5 lands exactly at the straight midpoint `((x1+x2)/2, (y1+y2)/2)`. So no curve-tracing needed — the splice button position is the line midpoint.

**Accepted limitation:** the root node has no way to "add a parent above" anymore, since there's no edge above it to splice into. Acceptable since the root is the natural entry point. If a user wants to wrap the entire graph later, that would need a new affordance (e.g., a `+` ghost above the root).

**Verification:** HTTP 200 at `/workshop/graph-builder`. JS: 25006 chars, 101/101 braces, 411/411 parens, `node --check` passes. Served HTML contains 15 references to the new code (`spliceEdge`, `gb-edge-group`, `gb-edge-hit`, `gb-edge-btn`) and 0 to the removed code (`addBefore`, `Add Before`, `Add After`, `data-pos="before"|"after"`).

### Layout-driven horizontal-slice invariant

**Lead's prompt:** lay out the graph so a horizontal line drawn through the canvas intersects exactly the components visible on the user's screen at any given moment. Vertical = time / user progression; horizontal = things coexisting at one moment.

**Reframing:** the graph stops being abstract topology and becomes a literal runtime preview. Group children share a row (parallel — visible together); Tabs/Switch branches stack into separate Y bands (alternative — only one branch active at any user state). The compile step (item 4) becomes near-trivial: walk the graph, group children by parent type, emit Razem JSON.

**Type taxonomy refined.** Dropped `container` and `gate`; introduced four new types covering the Razem container vocabulary:
- `form` — rounded square, indigo→violet (data-input leaf)
- `action` — chevron, pink→amber (imperative leaf)
- `group` — pill, violet→pink (parallel container; children share a row)
- `tabs` — folder-tab trapezoid, indigo→violet (alternative container with strip; branches stack in separate Y bands)
- `switch` — diamond, amber→indigo (conditional alternative; branches stack in separate Y bands)

Cycling order: form → action → group → tabs → switch. `CONTAINER_TYPES` and `ALT_CONTAINER_TYPES` sets gate the collapse-caret, the bounding-frame draw, and the layout's row-offset rule.

**`layout()` — the new owner of all positioning.** Mutations (`addAfter`, `createBranch`, `spliceEdge`, `merge`) no longer set positions; they update topology and call `layout()`. Collision-resolution helpers (`resolveCollision`, `findFreeX`, `shiftSubtreeY`) deleted. Algorithm:
1. Visible-node topological sort via Kahn's algorithm.
2. For each node: `row = max over visible parents of (parent.row + childRowOffset(parent, child))`.
   - `childRowOffset = 1` for non-alt-container parents.
   - For tabs/switch parents: `1 + sum(branchDepth(siblings before this child))`.
3. `branchDepth(rootId)` is a memoized recursive walk that **stops at multi-parent nodes** (which belong to the enclosing scope, not the current branch). Group/leaf parents use `1 + max(child branch depths)`; alt-container parents use `1 + sum(...)`.
4. `col` = average over parents of `(parent.col + childColOffset)`. `childColOffset` centres siblings around the parent's col: rank `r` of `N` siblings sits at `(r - (N-1)/2)`. Single-child chains inherit parent's col.
5. Pixel positions: `n.x = anchorX + col*COL_W; n.y = anchorY + row*ROW_H`. Anchor is canvas centre / 1/3 from top.

**Standalone test (`/tmp/layout_test.js`) — 20 / 20 cases pass:**
- Linear chains stack at col 0, rows 0..N.
- Group children all share row 1; merge at row 2.
- Tabs with single-node branches: A at row 1, B at row 2, C at row 3, M at row 4.
- Tabs with uneven depths (A is 3-deep, B and C are 1-deep): A at 1, A1 at 2, A2 at 3, B at 4, C at 5, M at 6.
- Nested tabs (T2 inside T's branch 1): T2 at 1, A2a at 2, A2b at 3, MA at 4, B at 4, M at 5.

**SP test suite still 8/8.** SP enforcement is purely topological and was unaffected by the layout refactor.

**Invariant interpretation.** The "horizontal slice = visible components" property is satisfied **at any specific user state**: each runtime path through the graph visits at most one node per row. Globally, two nodes from different outer branches *can* share a row (e.g., test 5: MA in T's branch 1 and B in T's branch 2 both at row 4) — but no single user state ever sees them together because the two branches are mutually exclusive. The strong "at most one node per global row" reading would require a full dominator-tree subtree depth (rather than the local `branchDepth`), and is parked as a v2 tightening if visual overlap becomes a problem in practice.

**Implications for item 4 (compile to Razem):** Because `branchDepth` already encodes "branches are alternatives" vs "branches are parallel," the layout's structure IS the Razem container nesting. A walk over the graph emitting Razem JSON: at each node, look at children — if parent is `group`, emit a `Group` wrapping them; if `tabs`/`switch`, emit a `TabForm`/`Switch` wrapping each branch as a `SequenceForm`; if a chain, emit linear sequence steps. The compile step is now structurally trivial.

**Files changed:** `qms-workflow-engine/app/templates/workshop_graph_builder.html` (1032 → 1142 lines; ~110 lines of new layout logic + helper, with ~75 lines of deleted positional-mutation code netting to a smaller code-mass-per-feature).

**Verification:** HTTP 200, JS 30480 chars, 110/110 braces, 486/486 parens, `node --check` passes. Layout test suite 20/20. SP test suite 8/8.

### Tree model — branches go right, sequence steps go below

**Lead's clarification:** The horizontal-slice idea was right but my layout had it backwards. Branches from a Tabs node should extend **horizontally to the right** (not below), because the user has free navigation between tabs — they're "options accessible at this moment." A node added **below** a Tabs node is the next step in an enclosing Sequence, "since the second cannot be seen until the first is done."

This fundamentally changes the data model. The graph becomes **strictly tree-shaped** with two kinds of parent-child edge:
- `branch` (horizontal) — container members: tabs, group siblings, switch alternatives.
- `next` (vertical) — sequence successor.

No multi-parent merges. SP enforcement becomes vacuous (trees are always SP). The merge feature is retired entirely.

**Data model.** Each node now carries a `parentRel: 'branch' | 'next' | null`. Roots have `null`. Each node has at most one `'next'` child and any number of `'branch'` children. Helper accessors `branchesOf(node)` / `nextOf(node)` filter by `parentRel`.

**Affordances:**
- **`+` below a leaf** (the dashed ghost): adds a sequence successor. If the node already has a `next` child, the new node splices in between.
- **`+` on an edge midpoint**: splices a node onto a `next` edge only. Branch edges aren't spliceable in v1 (semantic ambiguity — splicing on a branch could mean "wrap" or "sibling").
- **`Create Branch`** (single hover button at bottom-centre of node): adds a `branch` child. CSS hides this affordance on `form` / `action` types — only visible on `group` / `tabs` / `switch`.
- **Removed:** `Drag Merge`, the merge-eligibility highlighting, the SP check, the `is-merging` state.

**Layout algorithm.** Recursive top-down with subtree-width allocation:
- `subtreeWidth(node) = max(1 + Σ branch widths, nextWidth)` — accounts for both row-of-branches and any wider descendants reached via the `next` chain.
- `place(node, col, row)`:
  - branches at `row`, starting from `col + 1`, each shifted right by the previous sibling's full subtree width;
  - `next` at `col`, `row + 1`.
- This avoids collisions between nested branches: e.g., for `T → {X (tabs), Y}` with `X → V (branch)`, we get `T(0,0) X(1,0) V(2,0) Y(3,0)` — Y gets pushed to col 3 because X's subtree width is 2.

**Standalone tests** (`/tmp/layout_tree_test.js`) — **24 / 24 pass** across:
- Linear chains.
- Tabs with N branches and no next.
- Tabs with branches AND a next.
- A branch with its own sub-sequence (next).
- Nested tabs (width-aware allocation prevents sibling collisions).
- Containers with both branches AND a next that has its own branches.

**File simplified.** `workshop_graph_builder.html` went from 1142 → 892 lines because removing merge + SP machinery netted out negative even after adding `parentRel`-aware layout.

**Compile-to-Razem (item 4) trajectory.** With the tree model and explicit edge kinds, the compile step is one recursive walk:
- A node's `branches` become its container's `tabs` / `members` / `alternatives` (depending on type).
- A node's `next` chain becomes the steps of the enclosing `SequenceForm`.
- Roots produce the top-level page composition.

No structural inference required — the graph IS the Razem nesting.

### Containers as concept, not node — labelled bbox replaces the container shape

**Lead's clarification:** "The 'Tabs' component should not be a node though, it should be the concept that describes a horizontal row of nodes, perhaps enclosed in a bounding box that indicates it is of tab-type." Containers are groupings, not nodes. Render them as a labelled frame around their branches, not as a separate circle/pill/diamond.

**Implementation.** Container nodes (`group` / `tabs` / `switch`) still exist in the data model — they own their branches and the next-edge anchor — but they're **visually invisible**:
- The `.gb-node-shape` is hidden via CSS for container types; the wrapper is sized to 0×0.
- A new `.gb-container-tag` (HTML, anchored to the bbox top-left via `translateY(-100%)`) is the interactive handle. It shows the container kind ("TABS" / "GROUP" / "SWITCH"), a `+` button to add a branch, and a `▾`/`▸` collapse caret. Clicking the tag itself cycles the container's kind.
- The bounding box (`<rect class="gb-container-frame" data-kind="...">`) is drawn around the branches with kind-specific colour (indigo for tabs, purple for group, amber for switch).

**Bbox computation.** `computeContainerBBoxes()` runs once per render in **bottom-up order** (children first, parents second) so a parent container's bbox correctly encloses any nested container's bbox — `visualBBox(child)` returns the child's `_bbox` if it has one, else the leaf's shape footprint.

**Layout.** When a container has branches, its logical col is **re-anchored to the centre of its branches** so the next-edge drops from bbox-centre rather than the leftmost column. This means M (the container's next sequence step) sits below the visual centre of the box, which is what reads naturally.

**Edge anchoring.** The `nextEdgeStart(n)` helper returns `(bbox.x + bbox.w/2, bbox.y + bbox.h)` for containers, `(n.x, n.y + NODE_R)` for leaves. Both `drawNextEdge` and the leaf-ghost positioning use it. Containers no longer have `parent → first-branch` edges drawn — membership is implicit in the bbox.

**Dead code removed.** The `.gb-aff` cluster, the `.gb-node-collapse` caret, and `makeAffBtn()` are gone — all that machinery moved into the container tag. File: 892 → 946 lines (the additions for the container tag and bbox computation outweigh the deletions).

**Workflow now matches the Lead's vision:**
1. Single Node 1 (form): a single form circle.
2. Cycle to Tabs: form circle disappears; a small "TABS" labelled tag appears with an empty placeholder bbox.
3. Click + on the tag: a branch (form) appears inside the now-properly-sized bbox.
4. Click + again: a second branch joins the row.
5. Click + below the bbox (leaf ghost): a sequence step appears below the Tabs frame.

**Verification:** HTTP 200, JS 24132 chars, 97/97 braces, 396/396 parens, `node --check` passes. Layout test suite still 24/24 (the layout invariants are unchanged; only rendering moved).
