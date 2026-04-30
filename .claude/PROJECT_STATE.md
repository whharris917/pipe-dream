# Project State

*Last updated: 2026-04-30 (Session-2026-04-30-001 — CR-111 EIs 1-9 complete; EI-10 + post-review pending)*

This is the living planning document for Pipe Dream. It tracks where the project is, what's next, and what's waiting. Per CLAUDE.md it is pruned aggressively and does not accumulate session-level detail — for that, read the relevant session's `.claude/sessions/{ID}/notes.md`.

---

## 1. Project Overview

Pipe Dream has two intertwined objectives:

- **Flow State** — a Python application combining a geometric constraint solver (CAD) with a particle-based physics engine.
- **The QMS** — a GMP-inspired Quality Management System governing AI agent orchestration, with a recursive governance loop where the QMS controls its own evolution through the same mechanisms it uses to control application code.

The current center of gravity is the Razem framework (in the `qms-workflow-engine` submodule, rename queued), which will host the QMS's own UI as the first real application built on it.

---

## 2. Current Status

**Active focus:** Flow State adoption into QMS governance. Engine / Razem track is paused (see §6 — beach-trip pivot).

**CR-111 (Adopt Flow State into QMS Governance)** is IN_EXECUTION at v1.0. A lightweight Adoption CR establishing Flow State's first SDLC document pair and qualifying `flow-state/main@a26f7fb` as System Release `FLOW-STATE-1.0`. Document-only CR (no flow-state code modifications); 12 high-level requirements verified by qualitative-proof inspection mirroring `SDLC-CQ-RS/RTM`. Three pre-review cycles converged on v1.0; pre-execution baseline committed at `d6f003d`. **EIs 1–9 complete: SDLC-FLOW-RS v1.0 EFFECTIVE, SDLC-FLOW-RTM v1.0 EFFECTIVE, FLOW-STATE-1.0 git tag applied at `a26f7fb` and pushed to flow-state remote. EI-10 (post-execution baseline commit) and post-review/closure pending.**

**Razem engine** (paused): 26 component classes, 12 page seeds (incl. cr-create scaffold from Session-002), 7 themes, 86/86 parity tests. Stateless server with instance spawning. The terminal-execution primitive remains the load-bearing missing piece for engine-driven workflows, but engine work is on hold while Flow State CRs flow through the existing qms-cli "old fashioned way."

**SDLC docs:**
| Document | Version | Notes |
|----------|---------|-------|
| SDLC-QMS-RS | v22.0 EFFECTIVE | 143 requirements |
| SDLC-QMS-RTM | v27.0 EFFECTIVE | 687 tests, qualified at `918984d` |
| SDLC-CQ-RS | v2.0 EFFECTIVE | 6 requirements |
| SDLC-CQ-RTM | v2.0 EFFECTIVE | Inspection-based, qualified at `d3c34e5` |
| **SDLC-FLOW-RS** | **v1.0 EFFECTIVE** | **12 reqs across ARCH/CAD/SIM/UI/APP — clean first-cycle approval** |
| **SDLC-FLOW-RTM** | **v1.0 EFFECTIVE** | **Qualitative-proof inspection across 12 reqs; qualified baseline `flow-state/main@a26f7fb`** |
| SDLC-WFE-RS | v0.1 DRAFT | Razem track; rewrite deferred while Flow State is active |
| **Qualified Baselines** | **CLI-18.0 + FLOW-STATE-1.0** | **qms-cli main at `309f217`; flow-state main at `a26f7fb` (annotated tag pushed)** |

**66 CRs CLOSED + 1 IN_EXECUTION (CR-111), 5 INVs CLOSED.**

---

## 3. Arc to Date

The full per-session record lives in `.claude/sessions/`. This is the compressed phase narrative.

**QMS Foundation (Jan – Feb 24).** ~80 sessions establishing the document control system: CR/INV/VAR/ADD/VR document types, SOP-001 through SOP-007, the Quality Manual, the qms-cli, agent orchestration patterns, and the recursive governance loop.

**Workflow Engine v1 — CLI graph engine (Mar 3-7).** First attempt at modeling QMS workflows as a directed graph executed via CLI. Proved core concepts (state machines, gating, evidence capture); revealed design limits around fanout, conditionality, and human ergonomics.

**Workflow Engine v2 — UI-driven redesign (Mar 8-12).** Built a web UI and Agent Portal sandbox. Field-based and table-based workflow patterns proven, but accreted four parallel handler implementations.

**Unification + Hardening + Spine (Mar 14-19).** Clean-room rewrite formalizing v2 patterns into a single runtime. Added flowchart visualization, router/fork/merge, then a canonical "spine" representation with HTML-over-canvas rendering and DOM measurement. Architecture formalized as LNARF (literal, normalized, agent-readable form).

**Restructure + Multi-Instance + Workshop Era (Mar 20-23).** Removed the v1 CLI engine, restructured directories, transformed to multi-instance, added the AffordanceSource protocol, and ran a workshop-driven exploration of element types, field groups, and content arrays.

**Content Model Unification + Clean-Room Rebuild (Mar 24-25).** Architectural audit produced a comprehensive plan: one content array, one element protocol, one dispatch loop. Adversarial audit found 20 issues; YAML eliminated. Then **all engine code was deleted and rebuilt from scratch** — the foundation of the current Razem. Coined "Component" as the base concept (initially "self-contained, self-rendering"). Ten initial component types and 6 demo pages.

**Component Expansion (Mar 26-31).** Fractal complexity plan implemented across five phases (Switch, registry, structural persistence, structural actions, self-modifying pages). Component count grew to 30+ types. Component Gallery with all types. OrderedCollection extracted from ListForm. TableForm gained typed columns. SequenceForm added. Edit mode infrastructure across data and container forms. Theoretical re-examination revised the meaning of "Component" from "self-contained" to **"identity-preserving under transformation"** (eigenvector reading) — the real invariant is HATEOAS-completeness, not encapsulation. Dependency visibility (`render_dependency_line`), Historizer, Control Flow Gallery.

**Rendering Modernization + HTMX Detour (Apr 1-4).** Three-step modernization: event delegation (eliminates XSS class structurally), CSS extraction with semantic classes, and Jinja2 templates with a parity test (JSON↔HTML). HTMX integration was attempted as the agent-facing representation, then **fully excised** after evaluation. Stateless server refactor: server is a pure function `(seed + store + request) → response`. Instance spawning: page seeds are templates, users spawn named instances. Three independent agent integration tests surfaced and resolved 11 usability issues.

**Affordance & Container Consolidation (Apr 4-5).** Affordance flotation: separable affordances (Clear, Edit, Batch) bubble from arbitrary depth to Page in agent-facing serialization (~61% block reduction on flat pages). Container navigation collapsed O(N)→O(1) via parameterized affordances. InfoDisplay added. Component Reference Menu page. Embedded Page (Page-in-Page with independent stores). Supervisor/Operator + theme-aware wrapper foundation. Sleek theme (VS Code dark palette, card-based layout).

**Sleek Theme Polish (Apr 5-7).** Margin-positioned vertical sidebars, edit-mode unification across all components, large stress-test page (115 components across 6 tabs), container edit mode for all 5 container types.

**UI Shell Port + Strategic Refocus (Apr 13-14).** Lead-driven refocus: stop side quests, return to building QMS for Flow State. Ported main-branch site shell into dev (sidebar nav, Agent Portal, Quality Manual viewer, QMS dashboard, Workspace, Inbox, README). UUID instance IDs. Page Builder. Add Component card-based picker. Tile-based structural editor with drag-and-drop reorder/reparent/group/ungroup at any nesting depth. Universal POST-body tooltips, including live-tracking drag tooltips.

**Documentation, Framing, Naming (Apr 16-18).** Framing design plan in three passes: naming (`from_descriptor` → "reconciliation"), typed composition (`SiblingRef` value type with `expects=`, `_validate_field_value` at mutation boundaries, `Literal` tightening), and error boundaries (`render_safely`, `_error_boundary.html`). Parity test grew from 12 to 79 tests. Wiki, Learning Portal (8 progressive lessons + Anatomy of a Component diagram), Components Reference page. **Eigenform → Component** rename, then **class taxonomy refactor** (flat `*Component` suffix → role-specific suffixes: `*Form` for state-producing, unsuffixed for containers/derivations, `*Display`, `*Action`, `*Runner`, `*App`). Action-dispatch registry (`_actions` dict per class, 89 if/elif branches eliminated). Callable-preservation diagnostic. Megafile splits via mixins. Score and DynamicChoiceForm removed in favor of SiblingBind generalization (any field can carry `SiblingBind(sibling_key, fn)` and resolve reactively at serialize time).

**Framework naming decision (Apr 17-003).** The general-purpose framework — currently called "QMS Workflow Engine" — is being renamed to **Razem** (Polish, "together"). Razem = the framework; QMS Workflow Engine = the application to be built with it (not yet implemented). Rename queued in the forward plan.

**Workshop Hub, Inspect, Themes, Nesting Visualizations (Apr 18-21).** `/workshop` restructured as a hub with a card-based index. Right-click inspect panel (Chrome DevTools-style component inspector — full page JSON, affordances, raw store data; live-refreshed via `c-page-updated` events). UI polish pass (Inspect Data fix, TextForm consistency, ghost Clear buttons, live form tooltips). `Navigation` split into three concrete subtypes: `Tabs`, `Sequence` (with `auto_advance` flag), `Accordion`. Theme system refactor: retired operator/supervisor distinction; `<body data-theme="X">` server-rendered; `wrapper.html` receives `data=data` so themes can introspect children; `_serialize_full()` preserves `form`/`key` so themes dispatch per-type. **Five new themes** (paper, chat, task, debug-as-theme, liquid-glass) joining sleek and default — task is a theatrical-stage theme with per-container-type idioms (Tabs → Marquee Carousel, Sequence → Milestone Trail, Group → organic Huddle blob). New nesting visualizations workshop with 11 experiments exploring tree/tab idioms; Lead's verdicts: Exp 4 (decoupled tree+details) wins Group 1; Exp 4.1 (inline disclosure) and Exp 4.3 (chat-aesthetic tree with completion) win Group 2.

**Nesting Workshop Convergence — Experiment A (Apr 25).** 14 iteration rounds in the nesting visualizations workshop produced a stable canonical design called **Experiment A**, then progressively consolidated and stripped back to a single self-contained implementation. Key invariants: a vertical "thread" with avatars/nodes at each navigation level (the "node on line" motif); drill-down navigation where only the current step is fully expanded and ancestors collapse to compact go-back nodes; read-only ancestor tabs (active highlighted, others muted, no click handlers) plus a "Change selection" pill button as the *only* path back — guaranteeing **no choice is made without exposure to its associated instruction** (an explicit agent-governance requirement). The final Experiment A also includes: circular SVG progress rings around ancestor and current-step nodes plus N/M pips on each ancestor tab; non-navigation content (info notes via the generic `INTERLEVEL_NOTES = [{ meta, text }, ...]` shape) inserted on the thread between navigation levels; sequential gating where Tab N+1 is locked (🔒 + dimmed + non-interactive) until Tab N's subtree is complete; a "Proceed to Tab X →" button on the thread when all current-scope tabs are done; a green "Workshop complete" celebration when nothing's left; and auto-selection of the first incomplete + reachable leaf when scope drills to the leaf level. Shared scaffolding: `exp431xShared` (step + leaf-panel primitives), `exp43121xCore.makeNavigator` (drill-down state machine with built-in auto-select), `expRing.makeRing` (parameterized SVG progress rings via inline gradient IDs). The workshop file (`workshop_nesting.html`) peaked at ~8.8K lines mid-session, then was slimmed to ~1.2K once the Lead established the consolidated A as the only retained surface. Experiment A is the candidate UX foundation for real QMS workflow pages.

**Nesting Workshop — Bus Iterations Rejected, Component-Integrated Showcases Adopted (Apr 25–26).** Two further iteration rounds attempted to extend Experiment A. **First** an "A.X subtree-grouping motifs" series (5 variants — Cumulative bus, Nested brackets, Branching wire path, Section dividers, Hue zones) explored ways to make the implicit "what belongs to Tab 1.2?" grouping visible. Lead picked A.1 (cumulative bus) as the only acceptable variant; the rest were rejected. **Second** an "A.1.X left-bus refinements" series (3 variants — Left bus content fixed, Pre-allocated bus, Choice-keyed colors) addressed the content-pushed-right complaint in A.1. **All bus iterations were ultimately rejected** — the metaphor adds visual weight without new information, and the "what belongs to Tab 1.2?" question A allegedly didn't solve was somewhat theoretical. Slimmed everything back to canonical A; pivoted to "A.X component-integrated showcases" testing A's structure with realistic Razem-component HTML in the leaf body: TextForm, ChoiceForm, and a composite log (Group of TextForm + DateForm + CheckboxForm). Showcases are visual-only (form `onsubmit` is `preventDefault`'d; no actual store binding), but render the engine's default-theme component HTML faithfully.

**Nesting Workshop — Showcases Consolidated; Graph Builder Workshop Born (Apr 26-27).** Lead requested A.1/A.2/A.3 collapsed back into a single Experiment A leaf body containing all three component types together (Reflection / Comprehension check / Notes / Date read / Topics covered). Then the conversation pivoted to a brand-new workshop, **Graph Builder** (`/workshop/graph-builder`) — an aerial railroad-yard canvas for sketching workflow DAGs interactively. The workshop went through six successive design iterations driven by Lead's clarifications, each adding a distinct architectural layer:

1. **Initial scaffold.** SVG canvas + HTML node layer; vanilla JS state. Single root node, dashed `+` ghost below leaves for Add Node, three hover affordances per node (Add Before / Create Branch / Add After). Smooth bezier rails in indigo→violet gradient.
2. **Item 1-3 of "node typing + merge + container collapse".** After a discussion about the connection to Razem (BPMN closer than Studio 5000 ladder logic), implemented node typing (form/action/group/tabs/switch — earlier 5-type taxonomy with `container`/`gate`), drag-to-merge with green-glow eligibility, and container collapse with bounding-box framing.
3. **SP enforcement.** Lead correctly noted Razem CAN express merges (TabForm-in-SequenceForm = diamond merge); enforced series-parallel via Valdes-Tarjan-Lawler reduction at merge time and during drag eligibility computation. Standalone test suite 8/8 (chains, diamonds, Wheatstone bridge, cross-merges).
4. **Edge-splice replaces Add Before/After.** Removed those affordances; the leaf ghost stays as Add After, new `+` button on hover of any next-edge splices a node into that edge. Bezier midpoint formula gave a clean parametric centre (the symmetric control points make it land at the straight midpoint).
5. **Horizontal-slice invariant + layout-driven positioning.** Lead's reframing: vertical = time / progression, horizontal = things coexisting on screen at one moment. Delete `resolveCollision`/`findFreeX`; introduce `layout()` that derives positions from typed structure. Standalone test suite 20/20.
6. **Tree model + parentRel — branches go right, sequence goes below.** Lead clarified: branches expand horizontally (free navigation), sequence steps go vertically (must complete one before seeing the next). Data model refactored to a strict tree with `parentRel: 'branch' | 'next' | null` per child. SP machinery retired (trees are trivially SP). Layout uses recursive subtree-width allocation. Standalone test suite 24/24.
7. **Containers as concept, not node.** Lead's final clarification: Tabs/Group/Switch shouldn't be a node — they're a *grouping concept* over a horizontal row of nodes, visualised as a labelled bounding box. Container nodes are now invisible; their visual is the `<rect class="gb-container-frame">` with kind-specific colour and an HTML `.gb-container-tag` handle anchored to the bbox top-left (kind label + `+` add-branch + `▾` collapse caret). Bbox computed bottom-up so nested containers' frames enclose inner containers. Container's logical col re-anchors to its branches' centre so the next-edge drops from bbox-centre.

The workshop ended at 946 lines, with `/workshop/graph-builder` as the most architecturally ambitious workshop to date. **Item 4 — compile graph to Razem composition — is parked as the ultimate goal** but the structure is now ready: tree-shaped, with edge kinds matching Razem's container vocabulary; a recursive walk emits `SequenceForm` for next-chains and `TabForm` / `Group` / `Switch` for branch rows.

**Beach-Trip Pivot — Flow State Adoption (Apr 29 Session-003, paused mid-session).** Lead opened by shelving the Razem / QMS Workflow Engine track entirely for an upcoming working vacation, returning to the chemical-engineering game (Flow State) with the existing operational QMS as the governance vehicle. The pivot exposed a structural fact: Flow State had never been adopted into the QMS — it sat in the genesis sandbox per SOP-005 §7.4 with no SDLC docs and no qualified commit. Two prior sessions had sketched but never executed an adoption CR. Session opened with the Lead choosing **Option #2: Lightweight adoption** — minimal high-level RS verified by qualitative-proof inspection, mirroring SDLC-CQ. Plan approved (`/happy-drifting-mitten.md`); CR-111 drafted (12 reqs across ARCH×4 / CAD×3 / SIM×2 / UI×2 / APP×1, 10 EIs, document-only — §7.4/§7.5 omitted). Pre-review converged in three cycles: v0.1 → v0.2 fixed three blocking factual errors traced to CLAUDE.md drift (REQ-FS-APP-001 sim/simulation flag, REQ-FS-UI-002 input layer order, REQ-FS-ARCH-003 interaction_data ownership); v0.2 → v0.3 added is_static=1 vs is_static=3 distinction in REQ-FS-SIM-002 per tu_sim's escalated request-updates; v0.3 cleared all five reviewers, QA approved, CR-111 v1.0 PRE_APPROVED → released → IN_EXECUTION. EI-1 pre-execution baseline committed at `d6f003d`. EI-2/3/4 — SDLC-FLOW-RS v0.1 authored, reviewed by 6 (qa+bu+4 TUs all clean recommend), approved → v1.0 EFFECTIVE on first cycle. EI-5 — SDLC-FLOW-RTM v0.1 authored with 12 qualitative-proof rows + Qualified Baseline section anchored at `flow-state/main@a26f7fb`. EI-6 mid-cycle — RTM v0.1 reviewed; qa+tu_sim+tu_ui recommend; tu_scene + tu_sketch request-updates: brush-operations exception in REQ-FS-ARCH-001 evidence (Scene.paint_particles/erase_particles use time-travel snapshot pattern per CLAUDE.md §3.3 — documented authorized exception not previously acknowledged), DeleteEntityCommand→RemoveEntityCommand correction, tools.py direct sketch.interaction_data mutation (the ctx.set_interaction_data facade method exists but is unused), solve() dispatcher framing imprecision. RTM checked out for v0.2 revision; revision NOT yet applied — paused before edits. Session lessons: (1) for Adoption CRs of existing systems, anchor RS/RTM evidence to actual code, not narrative docs (CLAUDE.md drift surfaced repeatedly); (2) follow-up CR queued for CLAUDE.md §2.3, §6.2, §7 + module docstrings in input_handler.py and compiler.py. Comprehensive resume instructions in `.claude/sessions/Session-2026-04-29-003/notes.md`.

**First Real QMS Workflow Page on Razem — cr-create scaffold (Apr 29 Session-002).** Lead opened with self-reflection on having spent recent weeks perfecting Razem before putting it into practice. Confirmed: every commit since Apr 25 has been workshop / motif iteration while "Build real QMS workflows" stayed unmoved as the §6.1 immediate item. Conversation reframed Razem's purpose: it is an **API builder/coupler** whose primary application has always been a high-level, *constrained* API (with GUI for free) for qms-cli, so terminal execution is a load-bearing primitive, not a downstream feature. Pivoted to building the smallest real workflow page on the existing engine: `pages/cr_create.py` (~330 lines) — a Create Change Record authoring scaffold capturing the pre-approved sections of TEMPLATE-CR (sections 1–9 plus 12 References) using TextForm, ChoiceForm, ListForm, TableForm with `fixed_columns`, Group, Tabs, Visibility (`parent_doc_id` shown only when a parent_kind is selected), InfoDisplay, and a stub Action. The Submit Action is honest about being a stub: its `action_fn` returns the qms-cli command sequence (`qms create CR --title "..."` → checkout → write content → checkin) that *would* run once Razem gains a terminal-execution primitive. Engine fix landed en route: parity test `test_no_empty_url_affordances` was filtering DisabledAffordance offenders by label-substring matching, which only worked accidentally for the existing case (Action nested inside a Tabs that hides it from serialization when the tab is inactive); replaced with a structured `disabled: True` flag on the affordance dict (`engine/action.py`) and a corresponding test filter (`tests/test_parity.py`). 86/86 parity tests passing (was 79). Page was dogfooded with a hypothetical "Adopt Flow State under SDLC governance" CR — Document-only CR, genesis-sandbox-to-adoption framing per QMS-Policy §7.4, 8-step change description, 7-domain RS structure proposed (REQ-FS-SCENE/SKETCH/SIM/COMPILER/TOOLCONTEXT/UI/PERSIST), 12-phase implementation plan, 11 references. Final populated draft remains at /pages/27342915. Three engine bugs surfaced during dogfooding (see §8). Design constraint discovered: Visibility's `depends_on` resolves to same-scope siblings only, so code-CR-only sections (TEMPLATE-CR §7.4, §7.5) cannot conditionally appear inside the per-section Tabs based on a page-level `cr_type` choice — omitted from this scaffold; resolution is a future cross-scope ref form or moving conditional sections to page level.

**Experiment D — Unified Tabs vs Sequence Motif (Apr 29 Session-001).** Six-iteration refinement of Experiment D's Change Control review page that converged on a single visual rule: **Tabs (parallel) → horizontal T-junction; Sequence (gated) → vertical pills intersecting the thread, with active-step content interleaved between sibling pills**. Iterations: (1) T-junction for tabs replaces the JS shift-to-thread treatment (T-node on thread + horizontal connector + tabs at natural position); (2) tab-level gating dropped so the three reviewers within each phase are genuinely parallel — only the outer phase sequence is gated; phase avatars switched from `✨` to numbered `1`/`2` with locked dim variant; (3) "Phase X of 2" / "Step X of 2" textual framing dropped from labels because the gated UI conveys it; (4) the prior session's two ad-hoc representations of gated sequence (chat-bubble avatars for outer phases, smaller chat-bubble rows for QA's inner sub-flow) collapsed onto a single S-junction motif with 🔒-prefixed pills, reused at both depths via `buildSeqJunction`; (5) sequence pills go vertical (one per row) with active-step content interleaved between sibling rows — making "what content belongs to which step" geometric; (6) since pills are now strictly one-per-row, the snode + horizontal connector scaffolding is dropped and the pill itself sits flush at x=0 of its row, so the main thread (at x=14 of `.expC-nav`) intersects the pill top-to-bottom — pill behaves like a row-level analog of the chat-bubble avatar that sits on x=14 inline. Final D structure: container intro bubble → outer vertical S-stack of phase pills (with active phase's instruction + horizontal T-junction reviewer tabs + active reviewer's content interleaved) → workshop-complete celebration. The QA tab's content is itself a nested S-stack with the same vocabulary (Procedural compliance → Risk and impact, gated). State refactored from a path-encoded `selectedTab` string to three orthogonal indices (`selectedStep`, `selectedTab`, `selectedQASubStep`); `submitTab`/`submitQASubStep` auto-advance only along sequence axes (parallel tab navigation stays explicit).

**Liquid-Glass Theme Realignment + Graph Builder Rebuild + Experiment C-D (Apr 27-28).** Lead-driven session focused on tightening the visual language across both real pages and the design workshops, plus exploration of the Razem JSON projection from an AI-agent comprehension angle. Major landings:

- **Liquid-glass theme reimagined to match the nesting workshop.** Three passes: (1) palette swap from Apple-blue to indigo→violet→pink with the workshop's 4-radial pastel canvas; (2) chat-bubble + thread layout for Tabs/Sequence/Accordion containers (avatar + meta + tab strip + glass leaf-panel); (3) sequence-mode CSS extracted from inline styles in `navigation.html` and moved to `style.css` (default theme unchanged) so the theme can override `c-nav-step` chip pills cleanly; (4) per-nav vertical thread (was page-wide with hardcoded `top: 92px`, now `::after` on each nav container with `top:14; bottom:14` matching the container's first/last avatar centers). All 79 parity tests still pass.

- **Graph Builder workshop rebuilt from scratch in 12 incremental directions.** Started at "single dashed `+` button on a 200px line" (964 → 140 lines), then iteratively grew: component picker (Info/Text/Choice/Tabs/Sequence — later narrowed to Tabs/Sequence/Group only); chat-bubble visual treatment with 28px gradient avatars on a vertical thread; per-type body builders (form fields, tab strips, step lists); switched to "wire with inline gates" (Sequence) and "bus with parallel taps" (Tabs) per Lead's electrical-circuit metaphor; explicit branch + sub-line + merge wiring with smooth cubic-Bezier S-curves at the corners (railroad-track aesthetic); BPMN-style sync-join diamond at the bottom of Tabs' bus (parallel-join semantics); recursive nesting via `state.pickingArray` ref + `renderStem(arr, container)` (each tab/step is a slot with its own `components: []` array, picker UX is identical at every depth); nested threads descending from parent nodes (no disconnected islands — `padding-left: 63` for tabs to align with tab-node center, `padding-left: 30` for steps which coincides with the parent wire); horizontal-Tabs prototype with `branch-h`/`merge-h` quarter-arc curves, top + bottom horizontal buses positioned by JS based on measured column widths, sync diamond at the bottom-bus left end. After Lead clarified the Page-Editor / Graph-Editor split, Group was simplified to a single labeled chat-bubble row (no flow region — components are added later via drill-down).

- **Nesting workshop Experiment C reworked + Experiment D added.** C rebuilt around the Lead's takeaway "nesting should not be represented by indentation or horizontal movement at all": each component (TextForm + ChoiceForm) inside an active tab is now a chat-bubble row directly on the main thread (22px gradient avatar with type glyph + body), with the mark-as-done toggle as a third row. The `.expC-leaf` indented panel and the redundant "Now reading" crumb / gradient-clipped tab title were removed. **Experiment D** then mirrored C's two-tab-set shape but populated with a real CR review workflow: Phase 1 (Pre-approval review with Technical / Business / QA reviewers each in a tab, each with comments + Recommend/Request-changes decision + Submit toggle) → Phase 2 (Post-execution verification with the same three reviewers, gated on Phase 1 fully signed off). To demonstrate "nested = smaller, not indented," D's QA tab was then refactored into a nested 2-step Sequence (Procedural compliance → Risk and impact, gated), with sub-step bubbles using a smaller 22px avatar and `QA · Step N of 2` meta label as the only visual signals of nesting — every node still sits at `x=14` of the main thread.

- **Razem JSON projection inspection.** Read `/pages/0b9ab529` (Nested Tabs Stress Test, 5-level deep) and the corresponding seed in `pages/nested_tabs_test.py`. Recorded findings on the runtime projection's design properties (single-active-branch compression bounds JSON to `O(depth)` regardless of total tree size; URL paths in affordances are the spine of agent comprehension; off-active-branch contents are invisible until the agent POSTs a tab switch) and the structural divergence between Razem's seed model (`Navigation(steps=[Component, ...])` where each step IS a component, no slot wrapper, with `key`+`label`) and the Graph Builder's current data model (slot wrappers with their own labels). Noted as architectural input for future Graph Builder ↔ Razem alignment.

---

## 4. What's Built

### Controlled documents

| Document | Status |
|----------|--------|
| SOP-001 through SOP-007 | All EFFECTIVE (latest revs: v21 / v16 / v3 / v9 / v7 / v5 / v2) |
| TEMPLATE-CR / VAR / ADD / VR | v10 / v3 / v2 / v3 EFFECTIVE |

### Engine modules (Razem, in `qms-workflow-engine/`)

Major surfaces — not an exhaustive file list. See `engine/` for the full directory.

- **Core:** `component.py` (base), `page.py` + `page_mutations.py` (persistence boundary, structural mutations), `store.py` (JSON file store), `registry.py` (type registry, `from_descriptor`, `TYPE_CATALOG`), `affordances.py`.
- **Data forms:** TextForm, NumberForm, DateForm, BooleanForm, ChoiceForm, CheckboxForm, MultiForm, ListForm, SetForm, TableForm (+ `tableform_actions.py`), DictionaryForm.
- **Containers:** Tabs, Sequence, Accordion (sharing the `Navigation` base), Group, Repeater, Switch, Visibility.
- **Sibling-reading:** Computation, Validation. (Reactive fields via `SiblingBind` are cross-cutting on any field.)
- **Imperative / wrapper / runner / showcase:** Action, Historizer, TableRunner, RubiksCubeApp.
- **Display:** InfoDisplay.
- **Helpers:** `helpers.py` (`grade`, `graded`), `sibling_bind.py`, `ordered_collection.py`, `templates.py` (Jinja env, `set_theme`, `render_aff`, `render_btn`).

### App + UI

- `app/__init__.py` Flask factory; `app/routes.py` (routes, SSE, content negotiation, instance management, manual/QMS/workspace/inbox); `app/registry.py` (InstanceRegistry, `data/instances.json`); `app/manual.py` (Quality Manual markdown rendering).
- **Templates:** `base.html` shared shell with dark sidebar nav (Home, Portal, QMS, Workspace, Inbox, Manual, README, Workshop, Wiki, Learning Portal, Components, Deep Dive); per-component templates in `app/templates/components/`; theme overrides in `components/{theme}/` (sleek, paper, chat, task each with 9-10 templates).
- **Themes:** `static/style.css` (base) + per-theme CSS (`sleek.css`, `debug.css`, `liquid-glass.css`, `paper.css`, `chat.css`, `task.css`).
- **Static assets:** `component.js` (~75 lines, event delegation + morphdom), `morphdom-umd.min.js` (vendored).

### Currently-shipping page seeds

19 seeds in `pages/`. The main user-facing routes outside the seed catalog: `/portal` (Agent Portal), `/qms`, `/workspace`, `/inbox`, `/manual`, `/learn`, `/wiki`, `/framing`, `/components`, `/deepdive`, `/workshop` (with sub-pages: `page-builder`, `nesting`, `component-creation` stub, `graph-builder`).

### Test surface

`tests/test_parity.py` — 79 tests across 9 categories; verifies JSON↔HTML affordance alignment for every shipping page.

---

## 5. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| **CR-111** | **IN_EXECUTION v1.0** | **Adopt Flow State into QMS Governance. EIs 1–9 done (RS + RTM both EFFECTIVE; FLOW-STATE-1.0 tag pushed). EI-10 post-execution baseline + post-review/closure pending. Active.** |
| CR-110 | IN_EXECUTION v1.1 | Workflow engine development. EI-1-4 Pass. EIs 5-7 need rescoping. **Paused for the beach-trip pivot.** |
| CR-107 | DRAFT v0.1 | Unified Document Lifecycle. On hold. |
| CR-106 | DRAFT v0.1 | System Governance. Depends on CR-107. Same hold. |
| CR-091-ADD-001-VAR-001 | PRE_APPROVED v1.0 | Type 2 VAR. CLI title bug + SOP-004/TEMPLATE-VR alignment gap. |
| CR-001 | IN_EXECUTION v1.0 | Legacy. Cancellation candidate. |
| CR-020 | DRAFT v0.1 | Legacy test document. Cancellation candidate. |
| INV-002 through INV-006 | Various | Legacy investigations. Low priority. |
| CR-036-VAR-002, -004 | IN_EXECUTION v1.0 | Legacy. Low priority. |

---

## 6. Forward Plan

### Immediate (Flow State track — active during beach trip)

1. **Resume CR-111 from session pause.** Apply the seven RTM v0.2 fixes documented in `.claude/sessions/Session-2026-04-29-003/notes.md` ("RTM v0.2 fix list"); checkin; re-route for review; iterate until clean recommend; route for approval; RTM EFFECTIVE.
2. **Complete CR-111 EIs 7–10** — apply `FLOW-STATE-1.0` git tag to `flow-state/main`, update PROJECT_STATE SDLC table to reflect the qualified baseline, post-execution baseline commit, route for post-review, address feedback, close.
3. **First real Flow State CRs.** Once CR-111 closes, normal CRs against `flow-state/` for actual gameplay/CAD/sim feature work. The fun stuff. Likely first candidates: small bug fixes or quality-of-life improvements identified during the beach trip; possibly the CLAUDE.md follow-up CR (§2.3, §6.2, §7 narrative drift).

### Razem track (paused — resume after beach trip)

These items remain in the queue but are not active during the Flow State arc:

4. **Terminal-execution primitive (Exec/Command/Run Action variant).** The load-bearing piece for the Razem-driven QMS UI. Sketched shape: a new Action variant holding a command *template* with sibling-bound substitutions, runs the subprocess on the server, returns a structured result (stdout / stderr / exit code / parsed doc_id) into bound store keys consumable by other components. Engine permits arbitrary commands; page seeds curate which command shapes are exposed.
5. **Continue building real QMS workflow pages.** After the exec primitive: CR review, document lifecycle, inbox actions, route-for-review/approval. cr-create is the model.
6. **Wire QMS / Workspace / Inbox to real data.** Connect to `qms-cli` or the QMS document store rather than placeholder lists.
7. **Triage demo pages.** Decide which seeds in `/portal` are valuable vs gallery cruft.

### Before the first QMS workflow ships

4. **Framework rename: `qms-workflow-engine` → Razem.** Decided 2026-04-17-003. Scope: GitHub repo rename + remote URL update; `.gitmodules` and submodule path; `CLAUDE.md` references; Framing page (hero/§1/§8 Pass 4); README; Lessons 1 & 5; Deep Dive intro. Wiki was already rewritten as if the rename had occurred. Effort: one focused session, low technical risk. The eventual application name "QMS Workflow Engine" is preserved (or to be renamed separately).

### After workflows are working

5. **Merge dev into main.** Dev branch preserved until confirmed working.
6. **CR-110 remaining EIs.** Update to reflect the rebuilt engine.
7. **SDLC-WFE-RS rewrite.** v1 requirements don't apply to the rebuilt engine.

### Engine backlog (post-workflow)

| Item | Effort | Source |
|------|--------|--------|
| **Concurrency model** — last-write-wins, no optimistic concurrency or conflict detection. Fine for single-user; broken for collaboration. | Medium | Wiki Limitations §4; Deep Dive §5 #4 |
| **Move showcase/runner demos to `engine/_examples/`.** RubiksCubeApp (~400 LoC) and TableRunner ship in the production registry and appear in the builder type-picker; should live alongside `pages/` demos, not as engine primitives. README still lists them as production categories. | Small | Deep Dive rec #7 |
| **Delete `_migrate_legacy_overrides` with kill-date.** Runs in the bind hot path on every request. Once existing instances are migrated (finite event), this is overhead with no value. | Trivial | Deep Dive rec #8 |
| **Promote mutable-structure schematic editor out of `sleek/page.html`.** The most ambitious feature is gated behind a stylesheet choice. Default theme has no visual editor. Either build in default or move the editor into the engine. | Medium | Deep Dive §5 #5 |
| **Rename `form` class attribute** (lowercase `form = "text"` is inconsistent with PascalCase `Component`). Candidates: `type`, `component_type`. Cosmetic. | Small | 2026-04-17-002 follow-on #1 |
| **Rename branch `dev/content-model-unification`.** Historical and not breaking. Rename at next major checkpoint. | Trivial | 2026-04-17-002 follow-on #2 |
| **Component class taxonomy follow-up** — see MEMORY.md note: Form / containers unsuffixed / derivations unsuffixed / Display / Action / Runner / App. Largely landed; verify any stragglers. | Small | MEMORY.md |
| **Nesting workshop follow-through.** Two candidate engine surfaces have emerged: (a) **Experiment A** — drill-down on the thread + read-only ancestor tabs + "Change selection" button, and (b) **Experiment D's unified Tabs/Sequence motif** — horizontal T-junction for parallel Tabs, vertical pills intersecting the thread for gated Sequence, with active-step content interleaved between sibling pills. D's motif maps directly to Razem's existing `Navigation` subtypes (Tabs / Sequence) and renders gating with a single visual rule applied at any nesting depth. Decide which of A vs D becomes the canonical engine surface for navigation containers; possibly both with different roles. Evaluate which of A.1's progress rings and A.1.X's advanced features (interlevel info nodes, sequential gating) belong in the engine vs as opt-in container behaviors. Retire the earlier-round variants (4.3.1.X, 4.3.3.X, 4.3.1.2.1.X) once the engine surface is stable. | Medium | Session-2026-04-25-001, 2026-04-29-001 |
| **Graph Builder follow-through (post-rebuild).** Now a recursive page-builder with railroad-track wiring, Tabs/Sequence/Group only. Open threads: (a) align data model with Razem's seed model — drop slot wrappers, treat each tab/step as a component with its own `key`+`label`, add Accordion as a fourth Navigation mode, consider Switch/Visibility for reactive control flow; (b) compile-to-Razem so the graph emits a real `Page(components=[...])` tree (then Graph Builder becomes a real authoring surface for QMS workflow pages); (c) **unified Page Builder** combining Graph Builder + Nesting Visualization — Graph Editor view is the structural projection (full tree at once), Page Editor view is the runtime projection (single active branch, like the JSON), with right-click-to-open drill-down between them; (d) horizontal-Tabs prototype is functional but not yet evaluated against vertical against deeply-nested or wide-tabs trees. | Medium | Session-2026-04-27-001 |

**Correctly parked** (do not action without a concrete use case): Context primitive (no ancestor-to-descendant channel; most likely earned when user/permissions arrive with QMS workflows). First-class interception mechanism for containers. Affordance flotation future phases. Agent integration testing. Performance/stress testing on large pages. Error-boundary expansion (`serialize_safely`, bind-error scoping, `_handle()` partial-mutation scoping).

---

## 7. Backlog

### Ready (no blockers)

| Item | Effort | Source |
|------|--------|--------|
| Fix CLI title metadata propagation | Small | CR-091-ADD-001-VAR-001 |
| Align SOP-004 §9C.4 with TEMPLATE-VR | Small | CR-091-ADD-001-VAR-001 |
| Govern checkin.py bug fix (commit `532e630`) via CR | Trivial | INV-012 |
| Delete `.QMS-Docs/` | Trivial | CR-103 |
| Standardize metadata timestamps to UTC ISO 8601 | Small | Session-2026-02-26-001 |

### Bundleable

- **Identity & Access Hardening** (~1 session) — proxy header validation, Git MCP access control.
- **Agent Hub Robustness** (~1-2 sessions) — C3 (root user), H4 (no hub shutdown on GUI exit), M6/M8/M9/M10.
- **GUI Polish** (~1-2 sessions) — H6, M3/M4/M5/M7, L3-L6.

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value. |
| Metadata injection into viewable rendition | No current pain point. |
| Consolidate SDLC namespaces into system registry | Depends on CR-106. |
| Interactive document write protection (REQ-INT-023) | Pending UI-based interaction design. |
| Remove stdio transport option from MCP servers | Low priority. |
| Propagate Quality Manual cleanup from workshop | Medium effort, not blocking. |

---

## 8. Gaps & Risks

- **No terminal-execution primitive in Razem.** Every QMS workflow page beyond static authoring needs it. cr-create is the diagnostic; Submit is honest about being a stub. This is now the load-bearing engine work — see §6.1.
- **Dev branch has only one real QMS workflow page (cr-create).** CR review, document lifecycle, inbox actions still don't exist. Most shipping page seeds remain demos or galleries.
- **Three engine bugs surfaced during cr-create dogfooding (Session-002):**
  - **`Page._do_reset` doesn't fully clear TableForm cell data on Windows.** After reset, files_impact retained empty rows from a prior partial run. Suspect: store atomic-write rename leaves orphaned cell data, OR `_clear_recursive` doesn't reach into typed-table internal scopes correctly. Workaround: iterative `remove_row`. Worth its own CR.
  - **JSON store atomic-write hits Windows file-lock race.** `PermissionError: [WinError 5]` on the .tmp→target rename when rapid sequential POSTs hit the same instance file. Reproducible with table operations issuing add_row + N set_cell back-to-back. Workaround: retry-with-backoff at the client. Proper fix: per-instance write serialization or Windows-aware retry inside the Store.
  - **TableForm auto-seeds row_0** when `fixed_columns` is provided. Authoring tools that "add a row before filling" produce one too many. Behavior is correct but surprising; worth a docstring note and possibly a `is_seed_row()` helper.
- **Visibility cross-scope limitation.** `depends_on` resolves to same-scope siblings only; conditional sections deep inside containers can't reference page-level fields. Surfaced when designing cr-create — code-CR-only sections (TEMPLATE-CR §7.4, §7.5) had to be omitted. Resolution would be a cross-scope `SiblingRef` form (e.g. `SiblingRef("../../cr_type")`) or always-visible sections with instruction-text gating.
- **SDLC-WFE-RS needs a full rewrite** for the rebuilt engine. v1 requirements no longer apply.
- **Flow State has never been formally adopted into the QMS.** It exists in the genesis sandbox per SOP-005 §7.4 but has no SDLC-FS-RS, no SDLC-FS-RTM, no qualified commit. The hypothetical CR populated at /pages/27342915 in Session-002 is a sketch of what that adoption would look like.
- **Legacy QMS debt.** Nine open documents from early iterations; bulk cleanup recommended after workflows ship.
- **`qms-workflow-engine` submodule pointer** must be kept current with pushes — easy to forget after working in the submodule directly.
