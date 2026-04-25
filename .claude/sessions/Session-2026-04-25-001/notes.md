# Session-2026-04-25-001

## Current State (last updated: Experiment A consolidated + workshop slimmed)
- **Active document:** None (no open QMS work; engine-submodule direct work)
- **Current EI:** N/A
- **Blocking on:** Nothing (commit & push pending per Lead direction)
- **Next:** Commit + push engine submodule work, update root submodule pointer, push root
- **Subagent IDs:** none

## Final Nesting Workshop Outcome

After 6 iteration rounds adding ~25 experiments to `/workshop/nesting`, the canonical winner has been promoted to the **Experiment A** series. Key invariants discovered along the way:

1. **"Node on line" motif** — vertical thread with avatars/nodes at each navigation level reads as "you are here on a chain of decisions."
2. **Drill-down with collapse** — only the current step is fully expanded; ancestors collapse to compact go-back nodes on the same thread. Breadcrumb-style semantics ("Top › Tab 1") for label vs click target.
3. **Read-only ancestor tabs + "Change selection" button** — past depths show all 3 alternatives (active highlighted) as `<span>` elements with no click handler. The button is the only interactive path back. **Invariant: no choice is made without exposure to its associated instruction.** This was specifically called out as an agent-governance requirement.
4. **Default state: zero ancestors, scope=[], no leaf selected** — user/agent must drill all the way down. No auto-selection.

### Experiment A series (canonical winners)

- **Experiment A** (`.expA-` namespace) — promoted from 4.3.1.2.1.1. Drill-down on the thread with read-only ancestor tabs + Change selection. The original 4.3.1.2.1.1 stays untouched as a snapshot.
- **Experiment A.1** (`.expA1-` namespace) — A + circular progress indicators: 18px SVG ring around each ancestor's thread node, 36px ring replacing the current-step avatar, N/M pip on each read-only ancestor tab. Shared `expA1-grad` SVG gradient emitted once per render.
- **Experiment A.1.1** (`.expA11-` namespace) — A.1 + non-navigation components on the thread. After each committed ancestor, an italic-`i` dashed-border node + an info card sits on the thread. `INTERLEVEL_NOTES = [{ meta, text }, ...]` shape lets future variants swap in arbitrary content (forms, references, acknowledgments) without changing the threading logic.
- **Experiment A.1.2** (`.expA12-` namespace) — A.1 + sequential gating. Tab N+1 is locked until Tab N's subtree is complete. Locked tabs get 🔒 + dimmed treatment; click handlers stripped via `cloneNode + replaceWith`; `title` attribute surfaces "Locked — complete the previous selection first" on hover. Footer hint names the dependency.

### Earlier-round variants (retained for comparison)

Group 1 (4.3.1.X — visual nesting without indent/box): 4.3.1.1 chromatic, 4.3.1.2 thread (winner), 4.3.1.3 SVG connectors.
Group 2 (4.3.3.X — go-back in drill-down): 4.3.3.1 Up button, 4.3.3.2 breadcrumb (winner), 4.3.3.3 `..` parent row.
Group 3 (4.3.1.2.1.X — descendants of the thread winner): 4.3.1.2.1.1 (then-promoted to A), 4.3.1.2.1.2 horizontal stepper, 4.3.1.2.1.3 conversational transcript, 4.3.1.2.1.4 stamped history, 4.3.1.2.1.5 progress-ring nodes (informed A.1), 4.3.1.2.1.6 anchored "you-are-here".

### Shared infrastructure

- `.exp43v-*` shared CSS classes (chat-aesthetic tree internals: rows, chevrons, icons, checks, counters)
- `exp43vShared` JS — `buildTree(treeBody, hooks)`, `syncTreeProgress`, `progressForFn`, `buildBubble`
- `exp431xShared` JS — `buildStep(opts)`, `buildLeafPanel(opts)`, `makePathState(initial)`, `INSTRUCTIONS`, `STEP_LABELS`
- `exp43121xCore` JS — `makeNavigator({ initialScope, initialLeaf, initialDone, onRender })` drill-down state machine. Default state: `scope=[]`, `selectedLeaf=null`, `done={1.1.1, 1.2.3}`.
- `exp433xDrilldown` JS — `mount(root, { goBackBuilder, handleClick })` for the 4.3.3.X family
- `expRing` JS — `makeRing({ size, strokeWidth, completed, total, gradientId, includeDefs })` for A.1.X family

`workshop_nesting.html` grew from 3406 lines (start of session) to ~8800 lines.

## Nesting Workshop Verdicts (this session)

After two iteration rounds adding 11 new experiments to `/workshop/nesting`:

**Verdicts so far:**
- **4.3.1.X winner:** **4.3.1.2** (vertical thread / spine — frameless steps with a 2px gradient line running down the avatar column; avatars are nodes on the thread)
- **4.3.3.X winner:** **4.3.3.2** (drill-down menu + clickable breadcrumb at top — `Top › Tab 1 › Tab 1.1`, multi-level back in one click)

**Other variants shipped this session (current status: superseded by winners but retained for comparison):**
- 4.3.1 (stacked steps with chip-tabs — original; lost the tree)
- 4.3.1.1 (chromatic depth coding via depth-shifted accent colors)
- 4.3.1.3 (causal connectors via SVG curves between active tab and next avatar)
- 4.3.2 (tree + stacked instructions in right pane)
- 4.3.3 (tree with inline path instructions)
- 4.3.3.1 (drill-down + Up pill button)
- 4.3.3.3 (drill-down + ".." parent row in menu)
- 4.3.4 (three-column: tree | instructions | content)

## Session start checklist
- [x] Determined this is a new session (last was 2026-04-21-001; today is 2026-04-25)
- [x] Created `.claude/sessions/Session-2026-04-25-001/`
- [x] Wrote `Session-2026-04-25-001` to CURRENT_SESSION
- [x] Read previous session notes (Nesting Visualizations workshop + 11 experiments)
- [x] Read SELF.md (no edits this boot)
- [x] Read QMS-Policy.md, START_HERE.md, QMS-Glossary.md
- [x] Skimmed PROJECT_STATE.md §1 (Where We Are Now) — current focus is the nesting visualizations workshop in `qms-workflow-engine/app/templates/workshop_nesting.html`
- [x] Inbox: empty
- [x] Workspace: clean (no checked-out documents)
- [x] Submodule state: qms-workflow-engine on `dev/content-model-unification`, commit `a002304` ("Nesting Visualizations workshop — 11 experiments…"). All other submodules on their default branches. No uncommitted submodule changes.
- [x] Root repo: only the CURRENT_SESSION pointer flip + harness `settings.local.json` are dirty.

## Entry context
Previous session (04-21-001) shipped 11 experiments in a new "Nesting Visualizations" workshop at `/workshop/nesting`. Lead's verdicts:
- **Group 1 winner:** Exp 4 (decoupled tree + details)
- **Group 2 winners:** Exp 4.1 (inline disclosure) + Exp 4.3 (chat-aesthetic tree, completion-enhanced from 4.5)
- **Discontinued:** Exp 4.4 original (multi-pin compare)
- **Awaiting evaluation:** Exp 4.1.1 (vertical group brackets variant of 4.1), Exp 4.5 (VS Code aesthetic comparison — may be discontinued if redundant)

## Observation
PROJECT_STATE.md is 562 lines / ~41.8K tokens — well past what CLAUDE.md says it should be ("keep it concise … prune aggressively … should not grow endlessly"). Session-notes-style entries are accumulating in §1 ("Where We Are Now") that have outlived their context-adding usefulness. Worth proposing a prune pass when there's a natural pause.

## Progress Log

### [09:17] Session bootstrapped
- Folder created, CURRENT_SESSION updated, prior context loaded.
- No queued work; standing by for Lead direction.

### Pruned `.claude/PROJECT_STATE.md`
- **Lead instruction:** "PROJECT_STATE should track overall project progress, not session notes. Reference actual session notes to ensure final state accurately reflects the arc."
- **Before:** 562 lines / ~42K tokens. §1 ("Where We Are Now") had ~84 lines of session-by-session changelog prose dating back to Session-2026-04-14-004; §2 ("The Arc") had per-session-granular phase entries; §5 (Forward Plan) and the Engine Backlog inside it carried `LANDED` markers for items already shipped.
- **After:** 200 lines (~64% line reduction; proportional token reduction). New structure:
  - §1 Project Overview (what Pipe Dream is)
  - §2 Current Status (active branch, engine surface, SDLC table, open work)
  - §3 Arc to Date (phase-level narrative — each phase 1-3 sentences, dates, no per-session breakdown; explicit pointer to `.claude/sessions/` for detail)
  - §4 What's Built (controlled docs, engine surface grouped by category, app/UI, page seeds, test surface)
  - §5 Open QMS Documents (table)
  - §6 Forward Plan (forward-only — all `LANDED` items removed; engine backlog kept)
  - §7 Backlog (Ready / Bundleable / Deferred)
  - §8 Gaps & Risks
- **Methodology:** read full prior PROJECT_STATE.md, sampled session notes (2026-04-13-001, 2026-04-19-001, 2026-04-19-004, 2026-04-21-001) to validate arc framing, cross-referenced engine submodule git log to confirm phase boundaries. Removed all `LANDED` entries from forward sections; preserved all genuinely open backlog items.
- **Note:** the `.claude/sessions/` directory remains the canonical source of session-level detail — PROJECT_STATE no longer duplicates it.

### Nesting workshop iteration round 1: lineage indicators + Exp 4.3.1
- **Topbar restructured** from a single flat 11-pill row into hierarchical rows with explicit lineage labels (`↳ from Experiment 4`, etc.). Tabs use the existing `.nest-ws__tab` class so the click handler is untouched.
- **Exp 4.3.1 added** — chat-aesthetic stacked instruction steps: 3 step cards stacked vertically, each with its own chat bubble (avatar + meta + text + per-step progress) followed by a row of three pill-tabs at that depth. Demonstrated the Lead's "always show instructions for tabs the user can click on" — 9 navigation targets visible simultaneously when on a leaf.

### Nesting workshop iteration round 2: 4.3.X variants that retain the tree
- **4.3.2 (tree + stacked instructions in right pane), 4.3.3 (tree with inline path instructions), 4.3.4 (three-column)** added as alternatives to 4.3.1 that keep the left vertical navigation bar.
- **Refactor:** introduced `.exp43v-` shared CSS namespace and `exp43vShared` JS module exposing `buildTree(treeBody, hooks)`, `syncTreeProgress`, `progressForFn`, and `buildBubble`. Each variant composes these primitives; 4.3 itself untouched on its `.exp43-` namespace.

### Nesting workshop iteration round 3: 4.3.1.X (visual nesting cues) + 4.3.3.X (go-back affordance)
- **Topbar:** added a new `.nest-ws__row--great-grandchild` indent level (84px) for the new 4.3.X.Y rows.
- **4.3.1.X:** three variants attempting to convey nesting WITHOUT noisy indentation or bounding boxes — 4.3.1.1 chromatic depth coding, **4.3.1.2 vertical thread/spine (winner)**, 4.3.1.3 causal connectors via SVG. Shared `exp431xShared` module exposes `buildStep`, `buildLeafPanel`, `makePathState`.
- **4.3.3.X (initial pass — wrong model):** first shipped as adornments on top of the always-expanded tree from 4.3.3 (Up button on right pane / breadcrumb on right pane / in-tree ↑ icon on selected row). Lead clarified intent: drill-down navigation in the LEFT menu, not adornments on the existing tree.
- **4.3.3.X (rewrite — drill-down):** rebuilt all three. Menu now shows ONLY the directly-nested children of the current scope. Shared `exp433xDrilldown.mount(root, { goBackBuilder, handleClick })` helper drives the drill-down state machine; variants differ only in their go-back affordance — 4.3.3.1 Up pill button, **4.3.3.2 clickable breadcrumb (winner)**, 4.3.3.3 `..` parent row.

### Round 4 — 4.3.1.X / 4.3.3.X verdicts
- **4.3.1.2** (vertical thread/spine) — winner of the 4.3.1.X series
- **4.3.3.2** (drill-down + breadcrumb in menu) — winner of the 4.3.3.X series

### Round 5 — 4.3.1.2.X iteration on the thread motif
- **Topbar:** added `--great-great-grandchild` indent level (112px).
- **4.3.1.2.1** — applied 4.3.3.2's drill-down + collapse-history idea to 4.3.1.2's thread. Only the current step fully expanded; ancestors collapse to compact go-back nodes on the same thread.
- Reaching the leaf component: refactored all variants in the thread family so the leaf panel is rendered *inside* the thread-bearing container (not as a sibling), so the existing `top: 14px; bottom: 14px;` thread visually extends through the panel area. Added `position: relative; z-index: 1;` to `.exp431x-leaf-panel` to ensure it covers the thread instead of the thread painting on top. Horizontal stepper variant (4.3.1.2.1.2) gets a 36px CSS-only vertical "drop" line below the current node.
- Default state changed to `scope=[], selectedLeaf=null` (was `[1, 1]` / `'1.1.1'`) — user/agent must drill all the way down to reach a leaf.

### Round 6 — 4.3.1.2.1.X advanced-features family
- **Topbar:** added `--great-great-great-grandchild` indent level (140px).
- **6 variants on "node on line":** 4.3.1.2.1.1 sibling-aware spine (the future Experiment A core), .2 horizontal stepper, .3 conversational transcript, .4 stamped history, .5 progress-ring nodes (informed A.1), .6 anchored you-are-here.
- Shared `exp43121xCore.makeNavigator` extracted — encapsulates the drill-down state machine, exposes `selectAt`, `switchAt`, `navigateTo`, `toggleDone`, `getStepPath`. Each variant supplies only its `onRender` callback.

### Round 7 — Experiment A established as the winner
- **Lead's instruction sequence (informed the final design):**
  1. "Past depths still allow switching tabs without exposure to the instruction" → replaced ancestor chip-tabs with a `<span>` label + "Change selection" button (the only path back).
  2. "Show all 3 tabs at past depths even with the Change selection button" → ancestor tabs are read-only `<span>` elements; active highlighted, others muted; `cursor: default`, no click handlers. Button stays as the only interactive control.
  3. "Promote 4.3.1.2.1.1 to Experiment A" → fresh `.expA-` namespace, prominent topbar row labeled "★ Winner series", original 4.3.1.2.1.1 retained.
- **Invariant established:** every selection is preceded by exposure to its instruction. An agent cannot bypass an instruction by clicking a sibling tab; the only way to revise a past choice is via the button, which navigates back so the instruction is re-presented.

### Round 8 — Experiment A.1 (progress rings)
- 18px SVG ring around each ancestor's thread node showing subtree completion %.
- 36px ring replacing the current-step avatar with the ✨ glyph centered.
- N/M pip on each read-only ancestor tab (subtree completion of THAT specific choice).
- Shared `expA1-grad` SVG `<linearGradient>` emitted once per render via a `defsEmitted` boolean.

### Round 9 — Experiment A.1.X advanced features
- **Topbar:** new child row "↳ from Experiment A.1".
- **A.1.1 (non-nav components on the thread):** dashed-border italic-`i` node + dashed-border info card after each committed ancestor. `INTERLEVEL_NOTES = [{ meta, text }, ...]` shape allows future variants to swap in forms / references / acknowledgments without changing the threading logic.
- **A.1.2 (sequential gating):** tab N+1 locked until tab N's subtree is complete. Locked tabs get 🔒 + dimmed treatment + `cursor: not-allowed`; click handlers stripped via `cloneNode + replaceWith`; `title` attribute surfaces "Locked — complete the previous selection first" on hover. Footer hint (`.expA12-gate-hint`) names the dependency when ≥1 tab is locked.
- **`expRing` shared helper extracted** — `makeRing({ size, strokeWidth, completed, total, gradientId, includeDefs })`. Inline `stroke="url(#...)"` instead of a CSS class for the fill, so each variant emits its own gradient ID under one shared helper.

### Round 10 — workshop slimming (deletion of pre-A variants)
- **Lead instruction:** "delete everything before Experiment A to get rid of unnecessary code in the workshop"
- File rewritten from scratch to keep only Experiment A series + shared infrastructure.
- Removed 25+ pre-A IIFEs, the `.exp43v-*` namespace, `exp43vShared`, `exp433xDrilldown`, deeper indent class modifiers (--grandchild through --great-great-great-grandchild). 8756 → 1539 lines (~82% reduction).

### Round 11 — refinements on Experiment A.1.2's gate hint placement
- Fix 1: hint was sitting in `navWrap` after the leaf panel; the absolutely-positioned thread `::before` painted through it (line crossed "S" of "Sequential gating active"). Moved to inside the bubble body of the current step, which has `z-index: 1` and covers the thread. Also reframes the hint as part of the AI's voice ("Note: …").
- Fix 2: dropped the asymmetric `border-left: 3px` callout treatment; now a soft tinted rounded card sitting inline within the bubble.

### Round 12 — "Proceed to..." button + workshop-complete celebration in A.1.2
- Two helpers added: `checkCurrentComplete(scope, done, progressFor)` and `findNextTarget(scope, progressFor)`. The latter walks up the scope path looking for the next incomplete sibling.
- When all current-scope tabs are done: render a gradient-filled "Proceed to Tab X →" pill button on the thread (with its own gradient `→` node).
- When the entire tree is done: render an `expA12-complete` element instead — green gradient `✓` node + "Workshop complete — every leaf is done." text.
- Both elements are inside `navWrap` with `z-index: 1` so the thread visually terminates at their nodes.

### Round 13 — auto-select first incomplete + reachable leaf
- Lead's request: "first incomplete and reachable leaf node of a navigation hierarchy auto-selected as long as the user has drilled down to that level."
- Baked into `exp43121xCore.makeNavigator` as `autoSelectIfAtLeafLevel()`. Fires after `selectAt` (when drilling reaches MAX_DEPTH-1), `navigateTo`, and on initial setup. Walks the 3 leaves under the current scope; picks the first incomplete one whose previous sibling is done (the first sibling is always reachable). In non-gated configurations this collapses to "first incomplete leaf."
- `toggleDone` deliberately does NOT auto-advance — user stays on the just-completed leaf so they can see its completed state.

### Round 14 — consolidation into a single Experiment A
- Lead instruction: "combine Experiment A.1.1 and Experiment A.1.2 into a single new Experiment A. I want to be better about stripping out all but the obvious winners this time around."
- Rewrote the file from scratch. The new Experiment A merges every feature explored across A → A.1 → A.1.1 → A.1.2 into a single `.expA-` namespace + IIFE: drill-down + read-only ancestor tabs + Change selection + circular progress rings + N/M pips + INTERLEVEL_NOTES on the thread + sequential gating + Proceed-to-next + workshop-complete + auto-select-first-incomplete-reachable.
- Topbar trimmed to a single row with one button (`Experiment A`); no lineage labels. Dropped the previously-shared `.expA1-ring-bg` / `.expA1-ring-fill` CSS classes (unused after standardizing on `expRing.makeRing`'s inline SVG attributes).
- File: 1689 → 1191 lines (~30% further reduction). JS brace balance 83/83.
