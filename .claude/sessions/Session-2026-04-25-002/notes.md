# Session-2026-04-25-002

## Current State (last updated: showcases shipped, ready to commit)
- **Active document:** None (engine-submodule direct work on `dev/content-model-unification`)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Commit engine submodule + root pointer + push
- **Subagent IDs:** none

## Session arc (one-line summary)
Three iteration rounds on the nesting workshop: (1) A.X subtree-grouping motifs (5 variants, all rejected); (2) A.1.X left-bus refinements (3 variants, all rejected — bus metaphor adds visual weight without new information); (3) A.X component-integrated showcases (3 variants — kept; A's structure with realistic Razem-component HTML in leaves). Final file: 1683 lines.

## Session start checklist
- [x] Determined this is a new session (continues today after Session-2026-04-25-001)
- [x] Created `.claude/sessions/Session-2026-04-25-002/`
- [x] Wrote `Session-2026-04-25-002` to CURRENT_SESSION
- [x] Read previous session notes (Session-2026-04-25-001 — Experiment A consolidated, workshop slimmed)
- [x] Read SELF.md
- [x] Read QMS-Policy.md, START_HERE.md, QMS-Glossary.md
- [x] Read PROJECT_STATE.md
- [x] Inbox: empty
- [x] Workspace: only stale `CR-001.md` (legacy cancellation candidate per PROJECT_STATE §5)
- [x] Submodule state:
  - `qms-workflow-engine` on `dev/content-model-unification` @ `2644a4b`
  - `flow-state` on `main` @ `a26f7fb`
  - `qms-cli` on `309f217`, `claude-qms` on `d3c34e5`, `Quality-Manual` on `5650425`
  - No uncommitted submodule changes
- [x] Root repo: only the CURRENT_SESSION pointer flip + harness `settings.local.json` are dirty.

## Entry context
Last session (04-25-001) consolidated 14 rounds of nesting-workshop iteration into a single canonical **Experiment A** in `qms-workflow-engine/app/templates/workshop_nesting.html` (~1.2K lines). Per PROJECT_STATE §6, the strategic next step is to build real QMS workflow pages on top of Razem rather than continue engine-side iteration. Auto mode is active.

## Progress Log

### [bootstrap] Session bootstrapped
- Folder created, CURRENT_SESSION updated, prior context loaded.
- No queued work; standing by for Lead direction.

### Experiment A.X series — five subtree-grouping motifs

**Lead's direction:** continue iterating on Experiment A; initiate an A.X series exploring ways to add visual grouping for "what belongs to Tab 1.2?" Currently the boundary between subregions is purely positional. Suggested vertical bus lines as one option; asked for at least 5 approaches.

**Decided 5 mechanically-distinct approaches:**

1. **A.1 · Cumulative bus** — multiple parallel vertical wires (one per depth-of-choice). Wire k anchors at depth-k's row and runs to the bottom. As scope drills down, wires accumulate.
2. **A.2 · Nested brackets** — each ancestor + everything-subsidiary wraps in a soft tinted card; cards nest. Each card is labeled with its scope ("Inside Tab 1.2").
3. **A.3 · Branching wire path** — SVG path bends out of the active tab at each level, traces the actual selection, joins the next ancestor's node. Unselected siblings get short dead-end stubs (CSS-only).
4. **A.4 · Section dividers** — labeled horizontal dividers separate scope regions ("▼ Inside Tab 1.2"). Chapter-style demarcation.
5. **A.5 · Hue zones** — each tab choice carries a hue (1=indigo, 2=violet, 3=pink); the region below adopts the active tab's hue via CSS variable cascade. Visual grouping is purely chromatic.

Distinctions in mechanism: parallel structural duplication / nested containment / literal line-graph / horizontal demarcation / non-structural color cascade.

### Implementation
- File: `qms-workflow-engine/app/templates/workshop_nesting.html`. Grew from 1191 → 2146 lines.
- **Topbar:** added second row with 5 child-experiment tabs and `↳ from Experiment A · subtree-grouping motifs` lineage label.
- **Helper module:** new `expABase` IIFE provides shared builders for ancestor row, info note, current step (with ring + gating), proceed/complete elements. A's existing IIFE was kept untouched (lower regression risk); each variant composes via `expABase` + their own outer namespace.
- **Topbar event:** `panelshown` CustomEvent now fires on the active panel after a tab switch — A.1 and A.3 listen for it and recompute layout-dependent decoration (wire heights, SVG path coords) when their panel becomes visible.
- **A.1:** wires positioned absolutely at left:14/22/30 (per depth). Ancestor nodes shifted via per-depth `[data-depth="N"]` attribute selectors so each sits on its wire. Current step ring and proceed/complete nodes shift via `[data-scope-length="N"]` on navWrap so the deepest element sits on the rightmost wire. Wire colors progressively shift indigo→violet, violet→pink, pink→orange.
- **A.2:** recursive `renderRegion(parentEl, depth)` opens a deeper bracket containing the next depth's content. Each bracket is a tinted rounded card with a left-rule and a `Inside Tab N.M` label; deeper brackets are tinted further along the indigo→violet→pink scale.
- **A.3:** SVG overlay positioned absolutely behind navWrap (z-index 0; content elevated to z-index 1). Path computed from `getBoundingClientRect` of node + active tab + node + active tab + ... + step ring. Uses cubic Bezier with control points at midY for smooth bends. Dead-end stubs are CSS-only (`.expA3-nav .expA-ancestor-tab:not(.is-active)::after`).
- **A.4:** flat structure with `.expA4-divider` inserted after each (ancestor row + info note) pair. Divider has top/bottom border, gradient background, chevron + label.
- **A.5:** zones nest progressively. Each zone has `data-hue=scope[d]` and sets `--zone-bg` / `--zone-edge` via attribute selector. Active tabs styled by their own `data-choice` (works for both ancestor tabs and current-step tabs).

### Verification
- Server returns 200 at `/workshop/nesting` (85K bytes).
- JS extracted from template parses cleanly under `node --check`.
- Brace/paren balance: 188/188, 733/733.
- All 5 variant CSS namespaces present in served HTML.
- **NOT verified in a real browser** — cannot drive a headless browser from this shell. Visual review required from Lead: tab switching, drill-down, "Change selection" back-navigation, sequential gating, "Proceed to next" button, workshop-complete celebration, hue cascade in A.5, dead-end stubs in A.3.

### Bug found and fixed mid-session
- A.5's first attempt at active-tab tinting used `.expA5-zone[data-hue="N"] > .expA-ancestor` selectors. This was wrong: zone N's direct-child ancestor row carries choice `scope[N]`, not `N` itself. Replaced with a simpler selector keyed off the tab's own `[data-choice]` attribute, which works at any nesting depth.

### Lead's verdict
- Only A.1 is acceptable. A.2 / A.3 / A.4 / A.5 all rejected.
- Iterate on an A.1.X series with the constraint: content should NOT be pushed right as scope drills down.

### Slim — A.2 through A.5 deleted
- HTML panels (4 sections), CSS blocks (~175 lines), JS IIFEs (~330 lines, 13.3K chars), shared-selector list memberships removed.
- File reduced 2146 → 1647 lines (~23% reduction).
- Page returned 200 after slim; JS still parses; verified before adding new variants.

### A.1.X — three left-bus refinements

Common architecture:
- Each row has `padding-left:56px` reserving a 56px gutter on the left.
- Ancestor nodes, info nodes, current-step ring, and proceed/complete nodes are absolutely-positioned within the gutter at their wire's x.
- Tab strips, leaf panel, button content all live in the post-gutter content area at navWrap x=56+ — they NEVER shift horizontally as scope drills down.
- Bubble's flex layout `gap:0` so the body flows from the bubble's left edge (the ring is absolute and out of flex flow).

**A.1.1 · Left bus, dynamic accumulation** (Lead's specific suggestion)
- Wires born only at committed depths.
- Cursor (current-step ring) at fixed navWrap x=48; older commitments shift LEFT to x=40, 32, ... as scope deepens.
- Wire colors keyed by depth: wire 0 = indigo→violet, wire 1 = violet→pink, wire 2 = pink→orange (same palette as A.1).
- Wire heights computed from row offsetTop after layout (`requestAnimationFrame` + `panelshown` listener).

**A.1.2 · Pre-allocated bus**
- All MAX_DEPTH wires always rendered at fixed positions (x=16, 28, 40).
- Wire state via `data-state` attribute: `committed` (bright), `current` (bright + glow), `future` (dashed/dim border-left).
- Cursor walks across the wires as depth grows — but content stays at x=56+.
- Gives the user a journey-progress sense ("you have N more levels to go") via the visible future-state ghost wires.

**A.1.3 · Choice-keyed colors**
- Same layout as A.1.1 (left-bus, dynamic).
- Wire color is keyed off scope[d] (the choice value), not depth: Tab 1 = always indigo, Tab 2 = always violet, Tab 3 = always pink.
- Cumulative bus pattern becomes a path color fingerprint (e.g., "indigo + violet" = path 1.2.x).
- The cursor's wire (no committed choice yet) renders neutral grey via `data-choice="0"`.

### Topbar
- New `.nest-ws__row--grandchild` indent style (padding-left:56px).
- Lineage label: `↳ from A.1 · left-bus refinements (content not pushed right)`.

### Verification
- Page returns 200; JS extracts at 49369 chars and passes `node --check`.
- Brace/paren balance 0/0.
- Served HTML confirms 5 tabs (A + 3 children + ... wait actually 4 tabs total: A, A.1, A.1.1, A.1.2, A.1.3 → 5 tabs), 3 A.1.X roots, 4 wire-color CSS classes, 3 data-choice attributes.
- Final file size: 2083 lines (1647 + ~436 added for variants).
- Visual review still required from Lead — cannot drive a real browser from this shell.

### Lead's verdict on A.1 + A.1.X
- None of the bus iterations introduced winning features. They re-decorate the same structural relationships A already exposes.
- Slim everything back to A only; pivot showcases to test A with realistic Razem content rather than abstract leaves.

### A.1 + A.1.X slimmed
- Topbar child + grandchild rows deleted; only Experiment A remains in the topbar.
- 4 panels removed (exp-a1, exp-a11, exp-a12, exp-a13).
- ~10.7K chars CSS + ~15.1K chars JS removed via Python (single bulk delete each).
- File: 2083 → 1441 lines.
- Kept: expABase shared helper (~250 lines). Will be reused by the new showcases.

### A.X showcase variants — A's structure, real Razem content in leaves
Each variant uses A's exact nesting structure (via expABase) and replaces the placeholder `[Leaf content for X.Y.Z]` body with realistic Razem-component-style HTML matching what the engine's default-theme rendering produces (`<div class="component" data-form="...">` + `<h3>` + `<p>` + form elements).

**A.1 — Text response.** Each leaf shows a TextForm-style prompt: "Reflection on Leaf 1.2.3 — Write a 1-2 sentence reflection." Single-input case.

**A.2 — Quiz question.** Each leaf shows a ChoiceForm-style 3-radio question: "Comprehension check on Leaf 1.2.3 — Pick the option that best matches what you read." Realistic for QMS workflows.

**A.3 — Composite log.** Each leaf contains 3 components in a Group: TextForm (notes) + DateForm (date read) + CheckboxForm (topics covered). Tests how the leaf panel grows under richer content.

### Architecture
- One small JS helper `renderShowcase(rootSelector, opts)` factors out the shared rendering logic. Each variant calls it with `{ gradId, crumb, body }` where `body(leafPath) → HTML string`.
- Leaf panel built via existing `exp431xShared.buildLeafPanel`; the showcase mutates the `.exp431x-leaf-crumb` and `.exp431x-leaf-body` after creation.
- Form elements (`<input>`, `<button>`) are interactive in the browser sense but `onsubmit="event.preventDefault();"` so they don't navigate. State isn't persisted across re-renders — these are visual showcases, not functional demos.
- New CSS scoped to `.exp431x-leaf-body .component` styles the embedded components reasonably (input focus, gradient submit buttons, indigo accent on radio/checkbox).

### Investigated to design
- Read `app/templates/components/text_human.html`, `choice.html`, `boolean.html`, `group.html` to understand template structure.
- Programmatically rendered TextForm, ChoiceForm, CheckboxForm, BooleanForm, DateForm, NumberForm via Page+bind to capture exact HTML output (saved transcript: `~/.claude/projects/.../tool-results/bgjlhnval.txt`).
- Confirmed that real Razem default-theme rendering is just `<div class="component" data-form="X"><h3>Label</h3><p>Instruction</p>...form elements</div>` — minimal class hierarchy, mostly inline-styled.

### Verification
- HTTP 200 at `/workshop/nesting`.
- JS at 40988 chars, brace/paren balance 0/0, `node --check` passes.
- 4 tabs in topbar (A + 3 children), 3 showcase roots, 4 calls to `renderShowcase` (3 invocations + 1 function definition).
- File size: 1683 lines (1441 + ~242 added for showcases).
- Visual review still required from Lead — cannot drive a real browser from this shell.

### Open questions for Lead (showcase iteration)
- Form state isn't persisted across re-renders (typing then clicking a tab wipes input). Acceptable for a showcase, but if you want to evaluate "does this feel right with real persistence," I'd need to wire up actual Razem store binding.
- A.2 (quiz) uses generic Option A/B/C. Could swap to actual quiz content if that's more useful for evaluation.
- A.3 (composite) has 3 fixed fields. Could add or remove.
- All three showcases use the same INTERLEVEL_NOTES (chapter/section/article framing). Could change framing per variant if it'd help.
