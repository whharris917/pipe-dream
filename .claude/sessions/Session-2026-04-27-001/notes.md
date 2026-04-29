## Current State (last updated: Experiment D + QA nested sub-flow)
- **Active document:** None (engine-submodule direct work on `dev/content-model-unification`)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Per Lead direction. Open-ended threads include: Page Editor view as a second projection of the same tree (see Razem-alignment notes); Graph Builder ↔ Page Editor toggle; deeper integration between graph node data model and Razem's actual class hierarchy
- **Subagent IDs:** none

## Session start checklist
- [x] Determined this is a new session (today is 2026-04-27; previous was Session-2026-04-26-001)
- [x] Created `.claude/sessions/Session-2026-04-27-001/`
- [x] Wrote `Session-2026-04-27-001` to CURRENT_SESSION
- [x] Read previous session notes (Session-2026-04-26-001 — Graph Builder workshop through 7 design iterations: scaffold → typing/merge/collapse → SP enforcement → edge-splice → horizontal-slice layout → tree model + parentRel → containers as labelled bbox)
- [x] Read SELF.md
- [x] Read QMS-Policy.md, START_HERE.md, QMS-Glossary.md
- [x] Read PROJECT_STATE.md
- [x] Inbox: empty
- [x] Submodule state: `qms-workflow-engine` on `dev/content-model-unification`, clean, in sync with origin
- [x] Last engine commit: `628e4be Workshop graph-builder + nesting consolidation`
- [x] Last root commit: `570a40b Session-2026-04-26-001: Bump engine — Graph Builder workshop`

## Entry context
Auto mode is active. PROJECT_STATE points to two parallel tracks:

- **Strategic priority** (§6 Immediate): build real QMS workflows as component compositions — CR creation, review, document lifecycle. Critical gap: dev branch has full site shell but every shipping page seed is a demo or gallery.
- **Recently active surface**: Graph Builder workshop (`/workshop/graph-builder`) — tree-shaped DAG authoring tool. Item 4 (compile graph → Razem composition) is the parked next step that would turn it into an authoring surface for QMS workflow pages.

These tracks intersect: the Graph Builder is intended to *become* the authoring surface for the workflow pages, but compile-to-Razem hasn't shipped, so it can't yet be used that way.

Per Lead's prior direction, item 4 is parked but valued. Standing by for Lead direction on which track to pull on this session.

## Progress Log

### [bootstrap] Session bootstrapped
- Folder created, CURRENT_SESSION updated, prior context loaded.
- No queued work; standing by for Lead direction.

### Experiment B — two consecutive, non-nested tab sets

**Lead's direction:** create an Experiment B in the Nesting Visualizations workshop showing two consecutive, non-nested tab sets.

**Razem shape modeled:** `SequenceForm{TabForm, TabForm}` — two parallel-branch containers chained by a sequence. Within a step, tabs are siblings (parallel); across steps, the second is the sequential successor of the first.

**Implementation in `qms-workflow-engine/app/templates/workshop_nesting.html`:**
- **Topbar:** added the `Experiment B` button alongside `Experiment A` in the existing single-row tabs container. The outer experiment switcher (lines ~720-749) was already capable of multiple panels.
- **Section:** added a `<section data-panel="exp-b" hidden>` containing `<div class="expB-root"></div>`.
- **CSS:** new block scoped to `.expB-*` styles. `.expB-root` mirrors `.expA-root` (max-width 760px, flex column). `.expB-nav` uses a `gap: 32px` (vs A's 16px) so the two consecutive tab sets read as distinct sequential steps. Added a thread `::before` matching A's. Per-step state styling: `.expB-step .exp431x-tab.is-active`, `.is-locked` (with the 🔒 prefix), `.expB-avatar-done` (green gradient when a step is fully complete), `.expB-gate-hint` (the inline locked-tabs note inside a bubble).
- **JS:** new IIFE that builds two stacked steps from a `STEPS` config array. State: `done` Set keyed by `"<step>.<tab>"` and `selectedTab`. Helpers: `tabDone`, `stepDone`, `stepReachable` (step S reachable iff steps 0..S-1 all done), `tabLocked` (step locked OR previous tab in same step not done). `autoSelect` picks the first reachable+incomplete tab on initial render so the user lands on Tab 1.1 ready to read. Per-step DOM constructed via `buildStep(stepIdx)` reusing the shared `.exp431x-bubble`/`.exp431x-tabs` visual primitives. Active step's selected tab gets a `buildLeafPanel(stepIdx, tabIdx)` rendered inline. `findNextStep` + the existing `.expA-proceed` / `.expA-complete` classes drive a "Proceed to Step 2 →" button when Step 1 is done while user is still on a Step 1 tab, and a "Workshop complete" indicator when both steps are done.

**Leaf body** (per tab) uses real Razem-component HTML — a `TextForm` (reflection prompt) + a `ChoiceForm` (3 radio options). Pared down from A's 5-component leaf since B's purpose is structural, not a content showcase. Forms `preventDefault` on submit; state isn't persisted across re-renders.

**Behavior summary:**
- Initial state: Step 1 active, Tab 1.1 auto-selected and unlocked, Tab 1.2/1.3 🔒. Step 2 fully 🔒.
- User reads Tab 1.1, marks done → Tab 1.2 unlocks. After all three Step 1 tabs done, Step 1's avatar turns green; Step 2 unlocks.
- A "Proceed to Step 2 →" button appears on the thread once Step 1 is done if the user is still on a Step 1 tab; clicking jumps to Tab 2.1.
- After all 6 tabs done: green "Workshop complete — both steps done." indicator.

**Verification:**
- File: 1347 → 1779 lines (+432 lines: ~95 CSS, ~270 JS, plus markup).
- JS: 40,590 chars, 123/123 braces, 522/522 parens, `node --check` passes.
- HTTP 200 at `/workshop/nesting`.
- Served HTML contains 11 references to B markers (`Experiment B`, `data-tab="exp-b"`, `data-panel="exp-b"`, `expB-root`, `expB-nav`, etc.) and A markers still present (Experiment A button, `expA-root`).
- B's served JS contains `STEPS` (10×), `expB-step` (7×), `tabLocked` (3×), `stepReachable` (5×), `buildLeafPanel` (8×), `expB-avatar-done` (2×) — all expected.
- **Visual review still required** — interactions (gating progression, proceed button, completion celebration) cannot be exercised from the shell.

### Liquid-glass theme realigned to nesting-workshop palette

**Lead's direction:** update the `liquid-glass` theme so that the actual themed page renders (e.g. `/pages/fa79abc2`) match the visual language we built for the nesting visualizations workshop. Not the Agent Portal dashboard itself — the *theme* applied to instances when "liquid-glass" is selected from the page-footer theme picker.

**Diagnosis:** the prior `liquid-glass.css` used Apple-style blue (`#007aff`) on a pink/blue/purple gradient. The workshop's distinctive visual language is indigo→violet (`#6366f1` → `#a855f7`) with pink (`#ec4899`) gradient-clipped titles, a 4-radial pastel canvas background, and purple-tinted soft shadows. So the change is a palette + treatment swap — not a structural rewrite. All existing selectors are preserved.

**Implementation in `qms-workflow-engine/app/static/liquid-glass.css`:**
- **Custom-property block** rebuilt around the workshop's palette (mirrored as `--lg-accent` / `--lg-accent-2` / `--lg-pink` / text/muted/subtle, glass surfaces at 0.62/0.78/0.95 opacities, purple-tinted shadows `rgba(59, 41, 102, 0.08/0.14)`, button shadow `rgba(99, 102, 241, 0.32)`, and gradients: `--lg-gradient` 135deg indigo→violet for active states and `--lg-gradient-text` 90deg indigo→pink for clipped page titles).
- **Body background:** identical 4-radial pattern from the workshop canvas (pink at 15%/20%, blue at 85%/15%, purple at 70%/85%, mint at 20%/90%, on a `linear-gradient(160deg, #f7f9ff, #fdf4ff)` base).
- **Component card:** ups the surface from 0.55 → 0.78 opacity to match the workshop's `.exp431x-leaf-panel`, retains 16px radius and the soft purple-tinted shadow.
- **Page title (`.component[data-form="page"] > h2`)** now uses the gradient-clipped indigo→pink text treatment that the workshop's `.exp431x-leaf-title` uses (`-webkit-background-clip: text`).
- **Primary action buttons** (`button[data-c-post]`, `[data-c-submit]`, `.c-aff-btn`) carry the indigo→violet gradient pill with the workshop's halo shadow `0 4px 14px rgba(99, 102, 241, 0.32)`.
- **Tab strip (`.c-nav-bar` + `.c-nav-tab`):** mirrors the workshop's chip-pill row — bar is transparent; chips use translucent white with soft borders for inactive, indigo→violet gradient with `0 2px 8px rgba(99, 102, 241, 0.28)` halo for `--active`. Locked tab variant uses dimmed neutral background. Completion variant uses the green accent (preserved from prior theme — workshop also uses green for the final completion ring).
- **Icon buttons / inline buttons:** retuned to indigo accents on hover; danger keeps the red palette but uses the brighter `#ef4444`. Confirm button keeps the workshop's green completion palette.
- **Inputs / textareas / selects:** 12px radius (up from 10px), 14px font (up from 13px), indigo focus ring with the same `box-shadow: 0 0 0 3px var(--lg-accent-soft)` halo pattern.
- **Editing outline:** uses `--lg-accent-soft-2` (violet-tinted soft) for the halo.
- **Feedback / error boundary / theme picker / depends-on line:** all retuned with the new palette.

**Verification:**
- File: 499 → 517 lines, 17,291 bytes served from `/static/liquid-glass.css` (HTTP 200).
- 61/61 braces balanced.
- A live page `/pages/fa79abc2` rendered with `Cookie: c-theme=liquid-glass` includes `<body data-theme="liquid-glass">` and `<link rel="stylesheet" href="/static/liquid-glass.css">`.
- Served CSS contains 12 references to the workshop palette tokens (`#6366f1`, `#a855f7`, `#ec4899`, `--lg-gradient`).
- **Visual review required** — palette / surface / shadow / gradient changes are appearance-only, can only be confirmed in a browser.

### Liquid-glass theme — chat-bubble + thread layout (workshop structural mirror)

**Lead's pushback:** the previous palette swap didn't go far enough — themed pages still didn't *look like* Experiments A/B. The workshop's distinctive feature is its layout: avatar + chat-bubble per navigation step on a vertical thread, with the active step rendered as a leaf-panel glass card and inner forms as light sub-panels.

**Implementation across three files:**

1. **`qms-workflow-engine/app/templates/components/navigation.html`** — removed the inline `style=` attributes on the tabs-mode `.c-nav-bar` (which set `display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px`) and on the `.c-nav-tab--active` span (which set `font-weight: bold; padding: 2px 8px; border-bottom: 2px solid #333`). Inline styles beat CSS without `!important`; with them gone, themes can override cleanly.

2. **`qms-workflow-engine/app/static/style.css`** — added the equivalent default-theme rules so the rendered look in the default theme is unchanged: a `.c-nav-bar` block (flex/gap/margin) and a `.c-nav-tab--active` block (bold + black border-bottom).

3. **`qms-workflow-engine/app/static/liquid-glass.css`** — appended a new "Workshop layout" section after the existing rules:
   - `.component[data-form="page"]` becomes a centered 760px column with `position: relative` and a `::before` vertical thread (indigo→violet gradient, identical to `expA-nav::before`) running from below the title block to the bottom. `#page-content` horizontal padding tightened from `8%` to `24px` so the centered column lands sensibly.
   - `.component[data-form="tabs" | "sequence" | "accordion"]` overrides the default glass card: transparent background, `padding: 0 0 0 40px` (room for the avatar), `position: relative`. The `::before` is a 28px gradient circle with the workshop's signature multi-layer halo (`0 0 0 4px rgba(247, 249, 255, 0.95), 0 2px 8px rgba(99, 102, 241, 0.32)`) and a `✨` glyph, positioned at `left: 0; top: 0` so its center sits on the page wrapper's thread at `left: 14px`.
   - The container's `> h3` becomes the bubble meta label (uppercase + 0.06em tracking + 11px + subtle color); the `> p` becomes bubble text (14px, primary text color).
   - `.c-nav-tab--active` gets `border-bottom: 1px solid transparent` to neutralize the (now-base-CSS) black underline that would otherwise draw under the gradient pill.
   - `.c-nav-content` becomes the leaf panel: 78% white surface, 16px radius, soft purple-tinted shadow, 22px padding — the workshop's `.exp431x-leaf-panel` treatment.
   - Inside the leaf panel: `.c-container` and `.component[data-form="group"]` are stripped to transparent (so a Group inside an active tab doesn't double-card), with the Group's `> h3` styled as a gradient-clipped section title (matching `.exp431x-leaf-title`); `.component:not(.c-container)` becomes a sub-panel (55% white, 10px radius, light border, 14px padding) — matching the workshop's `.exp431x-leaf-body .component` rule.

**Verification:**
- Liquid-glass CSS: 77/77 braces balanced, served at `/static/liquid-glass.css` with the new selectors (`.component[data-form="tabs"]::before`, `.c-nav-content .component`, `--lg-gradient-text`) all present (10 matches).
- Default theme CSS: gained `.c-nav-bar` flex layout and `.c-nav-tab--active` bold-underline rules so default rendering is unchanged.
- Navigation template: rendered HTML for the gallery page now has clean `<div class="c-nav-bar">` and `<span class="c-nav-tab c-nav-tab--active">Computed, Scoring &amp; Validation</span>` with **zero** inline `style=` attributes.
- **All 79 parity tests pass** — JSON↔HTML action surfaces unaffected.
- **Visual review required** — the chat-bubble layout is structural; needs a browser to confirm avatars, thread, and leaf-panel render as intended.

### Liquid-glass theme — sequence-mode CSS extraction + per-nav thread

**Lead's report:** the Control Flow Gallery (`/pages/b3c3394d`) had still-old-looking inactive tabs. Two follow-on issues:

1. The inactive tabs were `<button data-c-post=...>` elements that matched the theme's `button[data-c-post]` "primary action" rule (specificity 0,2,2) — *higher* than `.c-nav-tab` (0,2,1) — so the gradient pill was winning. Fix: prefix all tab-pill rules with `.c-nav-bar` to bump specificity to 0,3,1, definitively beating the primary-action rule.

2. The Control Flow Gallery uses `sequence` mode with `c-nav-step` classes (not `c-nav-tab`), and the navigation template still had **inline `style=`** on every sequence element. Stripped them all from `navigation.html` (the `.c-nav-bar--sequence`, the `.c-nav-step` per-state spans, the `.c-nav-arrow`, the back/next button row), moved equivalents into `static/style.css` so default-theme rendering is unchanged, and added `.c-nav-bar--sequence .c-nav-step` styling in `liquid-glass.css` (chip pill with the indigo→violet gradient for `--active`, soft green for `--complete`, dimmed for `--locked`).

### Liquid-glass theme — per-nav vertical thread (no longer page-wide)

**Lead's report:** on `/pages/f8ffdd21` (Quiz Portal — two nested Tabs), the page-wrapper thread extended up too far, well above the first node ("Quizzes" avatar). The thread was a `::before` on `.component[data-form="page"]` with `top: 92px` — a hardcoded approximation of "below the page header" that didn't match this page's header height.

**Fix:** moved the thread off the page wrapper and onto each navigation container individually. Now `.component[data-form="tabs"|"sequence"|"accordion"]::after` draws a `top: 14px; bottom: 14px` thread *inside the container*, so it starts exactly at the container's first avatar's vertical center and ends at its last. Side benefit: works correctly on every page regardless of header height; downside: stacked top-level navs no longer share a single connected thread (each owns its own short thread). For the 2-nested-tabs case the user was looking at, the thread now begins precisely at the "Quizzes" avatar.

### Graph Builder workshop — full rebuild

**Lead's direction:** "I want to rebuild the Graph Builder. When the user first navigates to it, they should simply see a vertical line segment with a `+` symbol in a dashed circle at the top. I'll tell you where to go from there."

Subsequent direction-by-direction iteration over the Graph Builder workshop page (`/workshop/graph-builder`):

1. **Initial scaffold** — 964-line file → 140 lines. Just a topbar (`←` back + "Graph Builder" title) and a centered stem: a 32px dashed `+` button with a 200px indigo→violet gradient line below it. No JS, no graph state.

2. **Picker for component types** — Lead's prompt: "click the + button and choose what component to add." Implemented an inline picker that takes the ghost's slot when `+` is clicked, showing five options (Info / Text Form / Choice Form / Tabs / Sequence) plus Cancel. Picking pushes a record into `state.components` and re-renders; trailing `+` ghost moves to the bottom of the stem. State is `{ components: [{ id, type, ... }], picking: bool }`; render is a pure function of state.

3. **Visual alignment with the nesting workshop's chat-bubble aesthetic** — Lead: "I want it to look visually similar to the nesting visualization examples." Restructured every node into a chat-bubble row (28px gradient avatar on the thread + body to the right). Per-type bodies: Info = paragraph; Text/Choice = sub-panel with form fields; Tabs = chip-pill strip with `+ Add tab`; Sequence = vertical step list with `+ Add step`. Stem layout switched from `align-items: center` to a left-aligned flex column with a `::before` thread at `left: 14px; top: 14; bottom: 14`.

4. **Add-tab/add-step affordances inside containers** — already part of step 3 above. Tab and step labels are auto-generated ("Tab 1", "Step 1", etc.); clicking the dashed `+ Add tab/step` chip pushes into the container's array.

5. **Wire-with-inline-gates / bus-with-side-taps motif** — Lead's metaphor: "Sequence is a wire with inline gates (each step is a node ON the line); Tabs is a bus with parallel taps (each tab is a stem branching off, the line stays uninterrupted because charge reaches all tabs simultaneously and isn't blocked like in Sequence)." Replaced the chip-pill / numbered-step lists with the new motif: Sequence sub-rows use a vertical sub-line at `left:11px` with 22px gradient nodes covering it; Tabs sub-rows use an uninterrupted bus at `left:0` with 18×2px horizontal stems extending to tab nodes.

6. **Branch + sub-line + merge wiring + visible vertical segments** — Lead: "the region of connected wiring for tabs and steps need to branch from the main line and also merge with it at the end." Restructured the container row to vertical (`flex-direction: column`): chat-bubble header on top, sub-flow region below. Sub-flow has explicit branch connector (horizontal `x=14 → x=44`), sub-line (`x=44`, `top:12; bottom:12`), and merge connector. Then Lead noted that consecutive Sequence step nodes still had no visible wire between them — root cause was the 4px canvas-color halo on each node which extended coverage to 30px (= row height), butting halos right up against each other. Removed the canvas halo; visible 8px wire segments now show between consecutive nodes.

7. **Synchronizing-join diamond on Tabs** — Lead's question: "How might we visually represent the fact that all tabs have to be finished before moving on?" Recommended option (BPMN parallel-join gateway): a 12×12 gradient diamond at the bottom of the bus where the merge connector starts. Adds one element, conveys "wait for all parallel paths." Implemented as a positioned `span` with `transform: translate(-50%, 50%) rotate(45deg)`.

8. **Recursive nesting — components inside tabs/steps** — Lead: "theoretically each tab and each step represents a place where other components can be added, using the same logic and affordances as the main starting branch." Refactored the data model to make slots `{ label, components: [] }`, replaced `state.picking: bool` with `state.pickingArray: ref` (a direct reference to the array currently being added to), made `render()` recursive via `renderStem(arr, container)` that renders components into a container then appends a picker (if `pickingArray === arr`) or ghost (otherwise) bound to that array. Each tab/step row now has a flex-column structure: header (node + label) + content (`renderStem(slot.components, ...)` recursively). Sub-rows became flex-flow (variable height) instead of absolutely positioned (fixed 30px pitch).

9. **Nested threads emerge from parent nodes (not from indented islands)** — Lead: "the vertical line of a particular tab should descend from the tab node itself, not appear as a disconnected island." Each tab/step's `.gb__sub-row-content` indent was tuned so the nested-stem's thread (at `left:14` of the nested-stem) lands directly under its parent node's center: `padding-left: 63px` for tabs (tab node center at `x=77` of flow region) and `padding-left: 30px` for sequence steps (step node center at `x=44`, which coincides with the parent wire — the wire visually continues straight through the step's content). The thread's `top: -8px` extends it 8px upward through the content's padding-top so it physically reaches the parent node's bottom edge.

10. **Smooth railroad-track curves at branch and merge** — Lead: "I would like to return to the smooth railroad track aesthetic — really the only difference is that it smooths out right turns." Replaced the sharp horizontal branch and merge `.gb__flow-line--branch / --merge` elements with cubic-Bezier SVG curves: `M 14,0 C 14,15 44,15 44,30` (branch) and `M 44,0 C 44,15 14,15 14,30` (merge). Both endpoints tangent-vertical so the curves blend seamlessly into the main thread and the sub-line. Sub-line, sub-flow-list padding, and join-diamond positions all moved from 12px to 30px insets to match the curves' 30px height.

11. **Control-flow-only, plus Group as a generic node** — Lead: "the graph view should represent a map of control flow, and should not contain actual data-entry or info components, or really any components other than Tabs, Sequence, and Group (for now). I'm imagining eventually combining the Graph Builder with the Nesting Visualization, to create a unified Page Builder where one can switch between the Graph Editor and the Page Editor." Removed Info / Text / Choice from the picker and from the rendering pipeline entirely. Added Group as a third type. Initially I rendered Group as Tabs-without-the-diamond (bus + side-stems); Lead corrected: "A Group is just a generic node into which components can be added later. It should not render like tabs or sequence." Stripped Group to just a chat-bubble header (avatar + meta + description), no flow region. Group's `c.components = []` is on the data model ready for drill-down / future Page Editor mode.

12. **Horizontal Tabs prototype** — Lead's design suggestion: "arrange tabs horizontally, and keep steps (of sequences) vertical. Vertical = sequential time, horizontal = parallel options coexisting in space." Implemented as a new `.gb__container-flow--horiz` variant: top-bus and bottom-bus horizontal lines connecting tab columns, each column owning its own vertical thread (`::before` from top to bottom) with the tab header at the top and nested-stem descending. Two new SVG curve variants: `branch-h` (`M 14,0 C 14,15 29,30 44,30` — vertical → horizontal quarter-arc) and `merge-h` (`M 44,0 C 29,0 14,15 14,30` — horizontal → vertical). Top/bottom bus left+width are positioned by JS (`positionHorizontalBuses`) after layout, since column widths are content-driven. Sync diamond moved to the left end of the bottom bus.

### Nesting workshop — Experiment C rebuilt as nodes-on-thread

**Lead's takeaway from the experiments:** "components inside tabs (for example, the text forms and selection forms) are represented by nodes on the main vertical line. My main takeaway from the nesting experiments is that nesting should not be represented by indentation or horizontal movement at all."

Restructured Experiment C in `workshop_nesting.html`:
- Removed `.expC-leaf` (the indented `padding-left: 40px` content area) along with the now-redundant "Step N · Now reading" crumb and gradient-clipped tab title.
- Each component (Reflection TextForm + Comprehension-check ChoiceForm) is now its own `.expC-comp-row` chat-bubble row on the same `.expC-nav` thread that runs through the step bubbles. 22px gradient avatar at `left: 3` (centered on `x=14`) with a per-type glyph (`T`, `?`); body to the right contains the component HTML.
- Mark-as-done toggle is also a row on the thread: dashed `○` avatar when undone, green `✓` when done, with a "Mark as done" / "✓ Completed" pill button to the right.
- A `.expC-leaf-group` wrapper holds the rows for one tab's content with `gap: 16px` (tighter than the nav's 32px between phases), so consecutive components feel related while step-to-leaf-to-step transitions still get the larger gap.

### Nesting workshop — Experiment D, real Change Control workflow

**Lead's direction:** "create Experiment D, that is visually similar to Experiment C, but implements an actual plausible real-world change control workflow, not just filler scenarios."

D mirrors C's two-consecutive-tab-sets shape but populates it with a CR review workflow:

- **Phase 1 of 2 · Pre-approval review** — three reviewers, each in their own tab:
  - Technical review (TU sign-off)
  - Business review (BU sign-off)
  - Quality assurance (QA sign-off)
- **Phase 2 of 2 · Post-execution verification** — same three reviewers in tabs, gated on Phase 1 being fully signed off (matches the real CR rule that post-review can't happen until pre-approval is fully signed off and execution has occurred):
  - Technical verification
  - Business verification
  - QA closure

Each tab carries a real review form: `✎` *<reviewer> — review comments / verification notes* (TextForm with phase-specific guidance text including a nod to review-independence) and `⚖` *Decision* (ChoiceForm — Recommend approval / Request changes for Phase 1; Confirm closure / Reject closure for Phase 2). The toggle becomes "Submit review" → "✓ Review submitted" (Phase 1) or "Submit verification" → "✓ Verification submitted" (Phase 2). Final state: "CR closed — pre-approval and post-execution verification complete."

D shares all of C's CSS classes (`.expC-step`, `.expC-comp-row`, `.expC-comp-avatar`, etc.) since the spatial language is identical — only the content differs. Just the canvas background and `.expC-root, .expD-root` rules were extended via comma-list selectors.

### Nesting workshop — Experiment D's QA tab as a nested 2-step Sequence

**Lead's direction:** "Let's suppose that the Quality assurance review contained two consecutive steps in a sequence."

Inside D's QA tab (Phase 1, Tab 3), instead of the single comments + decision + Submit-review pattern, render a nested two-step Sequence:

- **`1` QA · Step 1 of 2 · Procedural compliance** — verify CR follows SOP-002, has complete EI table + scope + justification. Components: Procedural compliance notes (TextForm) + Decision (Pass / Flag procedural concerns) + Submit toggle.
- **`2` QA · Step 2 of 2 · Risk and impact** — locked until Step 1 submitted. Verify risk assessment + impact analysis. Components: Risk and impact notes + Decision (Pass / Flag risk concerns) + Submit toggle.

Both sub-step bubbles render even when locked (the user can see the upcoming structure); components and the submit toggle for a locked sub-step are suppressed until the previous one is submitted. Sub-step keys are `"1.3.1"` and `"1.3.2"` in the global `done` set; `tabDone()` is overridden via an `isQATab()` helper to return true only when both keys are present, which keeps Phase 2 unlocking, the Proceed button, and the "CR closed" finale all working with no other changes downstream.

Crucially honors the Lead's "no horizontal indentation" takeaway: every sub-step bubble, every component, every toggle still sits at `x=14` of the main thread. The only signal that "this is nested" is the smaller avatar (22px vs the Phase bubble's 28px ✨) and the explicit "QA · Step N of 2" meta label — not horizontal position.

Two new CSS classes for the sub-step avatar states: `.expD-sub-done` (green gradient with halo, when submitted) and `.expD-sub-locked` (dim grey, when waiting on a predecessor).

### Razem JSON inspection — runtime projection vs structural source

**Lead's prompt:** "Look at the JSON representation of the Nested Tabs Stress Test in the agent portal" and then "is the JSON understandable to you as an AI agent? Is there a risk that you would get lost in the nesting?"

Read `/pages/0b9ab529` (5-level deep tree: `main → deep → deep-tabs → deep-tabs-inner → abyss`) and the corresponding seed at `pages/nested_tabs_test.py`. Key observations recorded for future architectural alignment:

- The runtime JSON is a **single-active-branch projection**: only the active step's body is expanded as `component: {...}` (singular); siblings collapse into `progress: [{key, label, complete}]`. The projection bounds JSON size to `O(depth)` regardless of total tree size, which is what keeps the nesting comprehensible. Off-active-branch contents are literally invisible until the agent POSTs a tab switch.
- **URLs are the spine of agent comprehension.** `/pages/0b9ab529/main/deep/deep-tabs/deep-tabs-inner/abyss` says exactly where the abyss form is in a single string. Without the URL, distinguishing "which `component:`" at depth 5 from indentation alone gets fragile.
- Razem's structural model in the seed: `Tabs / Sequence / Accordion(steps=[...])`, `Group / Page(components=[...])`, where each "step" is itself a component (no `{label, components}` slot wrapper — the slot's display label is the child component's `label`). This is **different from the data model the Graph Builder currently uses**, which has explicit slot wrappers. Aligning would mean: drop the wrapper, use child components directly, add `key` (programmatic) alongside `label` (display), add Accordion as a fourth Navigation mode, and consider Switch / Visibility as reactive control-flow types for later.
- Honest answer on agent comprehension: Razem's projection is well-designed for AI consumption (boundedness + URL-pathed locality + explicit affordances). The risk isn't in this 5-level test page — it's in repetition (every node carries `affordances`/`progress`/`complete`/`label`/`instruction` even when defaults), which dilutes signal/noise as depth grows.
