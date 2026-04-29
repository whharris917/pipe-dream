## Current State (last updated: end of session)
- **Active document:** None (engine-submodule direct work on `dev/content-model-unification`)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Per Lead direction. Today's arc landed a unified Tabs vs Sequence visual motif in Experiment D — likely candidate for an engine-side surface (Tabs → horizontal T-junction, Sequence → vertical S-stack with pills intersecting the thread). Open threads from prior sessions remain: build real QMS workflows on Razem; framework rename `qms-workflow-engine` → Razem; Graph Builder ↔ Page Editor unification; compile-graph-to-Razem.
- **Subagent IDs:** none

## Session start checklist
- [x] Determined this is a new session (today is 2026-04-29; previous CURRENT_SESSION pointed to Session-2026-04-27-001 from 2026-04-27)
- [x] Created `.claude/sessions/Session-2026-04-29-001/` and updated CURRENT_SESSION
- [x] Read previous session notes (Session-2026-04-27-001 — liquid-glass theme realignment, Graph Builder rebuild in 12 directions, Experiment C/D rework, Razem JSON projection inspection)
- [x] Read SELF.md
- [x] Read QMS-Policy.md, START_HERE.md, QMS-Glossary.md
- [x] Read PROJECT_STATE.md
- [x] Inbox: empty
- [x] Submodule state: `qms-workflow-engine` on `dev/content-model-unification`, clean
- [x] Last engine commit: `663f7e8 Workshop visual unification + Graph Builder rebuild`
- [x] Last root commit: `4916b04 Session-2026-04-27-001: Bump engine — workshop unification + Graph Builder rebuild`

## Entry context
Auto mode active. PROJECT_STATE highlights two parallel tracks:

- **Strategic priority** (§6 Immediate): build real QMS workflows as component compositions — CR creation, review, document lifecycle. Critical gap noted: dev branch has full site shell but every shipping page seed is a demo or gallery.
- **Recently active surface**: Graph Builder workshop has been rebuilt as a recursive page-builder (Tabs/Sequence/Group only, railroad-track wiring, smooth Bezier branch+merge, BPMN sync-join diamond, nested threads descending from parent nodes, horizontal-Tabs prototype). Compile-to-Razem is parked but is the path that turns Graph Builder into a real authoring surface.

Standing by for Lead direction.

## Progress Log

### [bootstrap] Session bootstrapped
- Folder created, CURRENT_SESSION updated, prior context loaded.
- No queued work; standing by for Lead direction.

### Experiment D — T-junction motif for tabs + Sequence/Tabs semantic alignment

**Lead's two-part direction:**

1. *First message:* drop the JS-driven "shift the tab strip horizontally so the active tab centers on the thread" treatment in D. Replace it with a T-node on the thread connected by a horizontal line to the rest of the tab buttons (which sit at their natural position).

2. *Second message:* reuse that motif for **tabs** specifically (not sequence). Restructure D so it explicitly maps to Razem's Tabs vs Sequence semantics:
   - Outer Sequence: Phase 1 → Phase 2 (gated)
   - Each phase's three reviewers (Tech/Bus/QA) = Tabs (parallel, T-junction)
   - QA's two inner steps = Sequence (gated)

**Implementation in `qms-workflow-engine/app/templates/workshop_nesting.html`:**

CSS — three new blocks:
- `.expD-tabs-junction` — flex row with `align-items: center, gap: 0`, sits on the thread.
- `.expD-tabs-tnode` — 28px gradient circle (matching the bubble avatar style) with a "T" glyph, on the thread at x=14.
- `.expD-tabs-connector` — 16px horizontal gradient line between the T-node and the tab strip.
- `.expD-tabs-junction .exp431x-tabs { padding-left: 4px; }` — overrides the natural 40px padding so the strip starts right after the connector.
- `.expD-tabs-junction.is-locked` variants — both the T-node and the connector go dim when the parent phase is unreachable.
- `.expD-step-locked` — dim variant for the outer phase avatar (mirroring `.expD-sub-locked` from the QA inner sub-flow but at 28px). Used for Phase 2 while Phase 1 is incomplete.

JS — D's IIFE only:
- `tabLocked(stepIdx, tabIdx)` simplified to `return !stepReachable(stepIdx)` — within-phase gating dropped (parallel-tab semantics). Tech/Bus/QA all unlock simultaneously when their phase becomes reachable.
- `buildStep` rewired:
  - Phase avatar glyph: ✨ → numbered "1"/"2" (matches the QA sub-flow's numbered sub-step avatars). Done state still ✓ green; new locked state uses the `.expD-step-locked` dim styling.
  - The "Subsequent reviewers unlock once the current reviewer has submitted" gate-hint block was removed entirely — no longer applicable.
  - Tab strip now wrapped in `.expD-tabs-junction` with the T-node and connector preceding it. `is-locked` class is added when the phase is unreachable.
- `alignActiveTabsToThread()` removed from D — function definition, render() call, and panelshown listener all gone. (C still has its own copy and still uses the shift-to-thread treatment.)

Phase 1 instruction text updated to reflect parallel reviewers ("The three reviews proceed in parallel — submit in any order"). Phase 2 instruction updated similarly.

**Visual rule that emerges:**
- **Sequence steps** = numbered avatars on the thread (28px outer, 22px nested — same vocabulary, smaller for nested).
- **Tabs** = T-junction (T-node on thread + horizontal connector + tab pill row at natural position).
- Both go dim (greyed) when their parent gating doesn't reach them.

**Verification:**
- File: 2907 → 2997 lines (+90: ~52 CSS + ~38 JS net).
- Served HTML at `/workshop/nesting` returns 200; new selectors all present (`expD-tabs-junction`, `expD-tabs-tnode`, `expD-tabs-connector`, `expD-step-locked`, `expD-tabs-junction.is-locked` all appear with expected counts).
- D's `alignActiveTabsToThread` is gone — three remaining references in the file (lines 2314/2400/2411) are all in C's IIFE.
- Extracted JS passes `node --check`.
- The `.expC-gate-hint` CSS rules remain (still used by B and C); only D's gate-hint markup-construction was removed.
- **Visual review still required** — geometry (T-node center exactly on thread at x=14, connector terminates flush with first tab pill, locked dim states render correctly) is best confirmed in a browser.

### Experiment D — Unified S-junction motif for ALL gated sequences

**Lead's direction (after the previous round dropped tab-level gating and added numbered phase avatars):** *"my goal went further than this. If there are two actions where A must be complete before B, then A and B should be represented by a sequence, with accompanying buttons with lock symbols, as appropriate. There should be a unified visual motif for gated sequential actions."*

The previous round still had two competing visual representations of "sequential gated steps": (1) the outer phases as numbered chat-bubble nodes on the thread, and (2) the QA inner sub-flow as smaller numbered chat-bubble rows. Lead wants ONE motif everywhere there's a gated A→B relationship.

**The unified motif — S-junction:**

Same chat-bubble vocabulary as the T-junction (a node on the thread + horizontal connector + a row of clickable pills), but the pills can carry `.is-locked` (with a 🔒 prefix and dim styling). Used at every depth where there's a gated sequence — page-level Phase 1 → Phase 2, QA tab's inner Procedural compliance → Risk and impact, etc.

Visual rules that emerge:
- **Sequence (gated) → S-junction** with `🔒` lock prefix on locked pills.
- **Tabs (parallel) → T-junction** — same node + connector + pill row, but pills never carry `.is-locked` (they unlock together as a set, gated only by their parent Sequence).

**Implementation in D's IIFE (`qms-workflow-engine/app/templates/workshop_nesting.html`):**

CSS — added five new blocks:
- `.expD-seq-junction`, `.expD-seq-snode`, `.expD-seq-connector`, `.expD-seq-pills` — analogous to the T-junction primitives.
- `.expD-seq-junction .exp431x-tab.is-locked` (and the `::before` lock-glyph variant) — the sequence-specific locked-pill treatment.
- `.expD-instruction-row` — small contextual text below a junction's pill row, indented to align with where the pills start.

CSS — removed:
- `.expD-step-locked`, `.expD-sub-locked`, `.expD-sub-done` (old per-phase / per-sub-step avatar variants).
- `.expD-tabs-junction.is-locked` and its inner overrides (the locked-T-junction treatment is no longer needed; the active step's T-junction is always reachable).

JS — wholesale rewrite of D's IIFE structure:
- **Three orthogonal selection indices** (one per nav level): `selectedStep` (outer 0/1), `selectedTab` (active step's tabs 0/1/2 or null), `selectedQASubStep` (QA inner 0/1). Replaces the previous path-encoded `selectedTab` string.
- **Atomic builders**: `buildIntroBubble(label, text)`, `buildInstructionRow(text)`, `buildPill(item)` (shared between both junctions; reuses `.exp431x-tab` styling), `buildSeqJunction(items)`, `buildTabsJunction(items)`, `buildCompRow(comp)`, `buildSubmitToggle(submitVerb, submittedTxt, isDoneFlag, onClick)`.
- **Submit handlers**: `submitTab(stepIdx, tabIdx)` and `submitQASubStep(subIdx)` toggle the done-key and auto-advance only along sequence axes (outer Phase 1→Phase 2; QA inner sub-sequence). Tab navigation stays explicit (parallel semantics).
- **Render flow** (top to bottom on the thread):
  1. Container intro bubble (`✨` avatar — "Change Control review" + overall instruction).
  2. Outer S-junction with two phase pills (`1. Pre-approval review` / `🔒 2. Post-execution verification`).
  3. Active phase's instruction (small contextual text strip).
  4. T-junction with the active phase's three reviewer tabs (parallel — no locks).
  5. Active tab's content: either the plain reviewer form (comments + decision + Submit toggle) or, for the QA tab, the inner S-junction with the two sub-step pills + active sub-step's content.
  6. Workshop-complete celebration when both phases done.

The "Proceed to ..." button (between phases) was removed entirely — its function is now subsumed by (a) auto-advance on submit and (b) the unlocked phase pill becoming clickable directly.

The QA sub-step bubbles (small `expC-comp-row` chat bubbles with numbered avatars) are gone; QA sub-step navigation now happens entirely through the inner S-junction's pills.

**Verification:**
- File: 2997 → 2950 lines (-47 net; CSS added but JS structure simplified).
- Served HTML at `/workshop/nesting` returns 200.
- New selectors all present (5× `expD-seq-junction`, 2× each for snode/connector/pills, 2× `expD-instruction-row`).
- Old selectors gone except in the explanatory comment block (1× each in the "removed in this rewrite" annotation).
- No D-side references to `parseKey`/`activeStepIdx`/`buildStep`/`buildLeafFlat`/`buildQASubFlow`/`findNextStep` (all are in B/C's IIFEs only).
- No `Proceed to ` references remain in D (5 total in file, all in A's text or B/C's IIFEs).
- Extracted JS passes `node --check`.
- `buildSeqJunction` defined once and called twice (outer + QA inner) — confirms the unified motif is reused at both depths.

**Visual review still required.** This is a structural rewrite — the page layout is meaningfully different from before (single top bubble + step pills replaces the two per-phase chat bubbles; QA sub-step pills replace the small numbered bubbles). The unified motif's geometry and the auto-advance-on-submit UX both need browser confirmation.

### Experiment D — Sequence pills go vertical, content lives between siblings

**Lead's direction:** *"I want tab navigation buttons to remain horizontal as they are now, but I want sequential step navigation buttons to become vertical AND I want the content of the selected/active step to appear between its button and the next one."*

The previous round's S-junction stacked the step pills horizontally to the right of a single shared snode. The new layout makes the relationship "this content belongs to this step" explicit by geometry — each step is its own row on the thread, and when active, its content is rendered immediately after that row and before the next step's row. Tabs (parallel) keep their existing horizontal T-junction layout.

**Implementation:**

CSS (in `qms-workflow-engine/app/templates/workshop_nesting.html`):
- Replaced `.expD-seq-junction` (horizontal pill row container) with `.expD-seq-row` (per-step row: snode + connector + pill).
- Removed `.expD-seq-pills` (no longer used).
- Moved the locked-pill rules from `.expD-seq-junction` scope to `.expD-seq-row` scope.
- Added locked-row variants for the snode and connector (both go dim when the row is locked).
- The snode is now a plain 28px gradient circle with no glyph (font-size/font-weight rules dropped) — it's a visual anchor on the thread, not a data carrier; the step number lives in the pill label ("1. Pre-approval review") and doesn't need to be repeated on the snode.

JS — D's IIFE only:
- Removed `buildSeqJunction(items, opts)`.
- Added `buildSeqRow(item)` — single step row, identical primitives (snode + connector + pill via `buildPill`), but no list wrapper.
- `render()` rewired: instead of one `buildSeqJunction(STEPS.map(...))` call followed by the active step's content, now iterates `STEPS.forEach((cfg, i) => { append row; if (i === selectedStep) append content })`. Content = instruction + T-junction (still horizontal) + active tab content.
- `buildQATabContent()` rewired the same way: `QA_SUB_STEPS.forEach((sub, i) => { append row; if (i === selectedQASubStep) append content })`. Content = instruction + components + Submit toggle.

D's intro comment block updated to describe the visual rule explicitly: Sequence → vertical S-stack with content interleaved between rows; Tabs → horizontal T-junction.

**Verification:**
- Server returns 200; JS passes `node --check`.
- `buildSeqJunction` references = 0; `buildSeqRow` defined once and called 3 times in the served HTML (1 definition + outer + QA inner = unified motif still reused at both depths).
- Old `.expD-seq-junction` and `.expD-seq-pills` selectors gone (0 occurrences); new `.expD-seq-row` rules in place (7 = 6 CSS rules + 1 JS string).
- T-junction unchanged.

**Visual review still required** — confirming that the active step's content visibly sits between sibling pills, that the thread runs continuously through all step rows + active content + next row, and that locked-row dim styling reads correctly in the browser.

### Experiment D — Sequence pills shifted onto the thread

**Lead's direction:** *"Now, since those step buttons only ever come as one per line, they can now be shifted to intersect the main vertical line/bus."*

The previous round positioned each sequence step's pill to the right of an snode + horizontal connector. With the pills now strictly one-per-row, the snode and connector are redundant — the pill itself can sit on the thread, with the thread visually passing through its top and bottom.

**Implementation:**
- Removed snode and connector creation from `buildSeqRow` — the row now contains just the pill.
- CSS: dropped `.expD-seq-snode`, `.expD-seq-connector`, and the locked variants on `.expD-seq-row.is-locked` for snode/connector. Kept `.expD-seq-row` (z-index/position only) and the pill's locked styling.
- Removed the `is-locked` class on the row itself (it was only needed to dim the snode/connector; the pill carries its own `.is-locked` state).
- Updated intro comment to describe the geometry: pill sits flush at x=0 of row → thread at x=14 of `.expC-nav` intersects pill → thread visually enters top and exits bottom.

**Geometric consistency:** the pill's left padding (14px from `.exp431x-tab { padding: 7px 14px; }`) means the pill's leftmost content (the 🔒 icon when locked, or the first character of the label) lands exactly on the thread at x=14. This makes pills behave like the chat-bubble avatars on the thread — both are visual elements that sit on x=14 with the thread passing through them — just at the row level instead of the inline level.

**Verification:**
- Server returns 200; JS passes `node --check`.
- `expD-seq-snode` and `expD-seq-connector` references = 0 (fully removed from CSS and JS).
- `.expD-seq-row.is-locked` selector = 0 (gone, no longer needed).
- `expD-seq-row` references = 5 (1 base CSS rule + 3 nested locked-pill rules + 1 JS string).
- Tabs T-junction unchanged.

**Visual review still required** — confirming that the thread visually passes through the top and bottom edges of each sequence pill (creating an "intersected" appearance) and that the active step's content still reads as belonging to its parent pill above.
