# Project State

*Last updated: 2026-04-26 (Session-2026-04-25-002)*

This is the living planning document for Pipe Dream. It tracks where the project is, what's next, and what's waiting. Per CLAUDE.md it is pruned aggressively and does not accumulate session-level detail — for that, read the relevant session's `.claude/sessions/{ID}/notes.md`.

---

## 1. Project Overview

Pipe Dream has two intertwined objectives:

- **Flow State** — a Python application combining a geometric constraint solver (CAD) with a particle-based physics engine.
- **The QMS** — a GMP-inspired Quality Management System governing AI agent orchestration, with a recursive governance loop where the QMS controls its own evolution through the same mechanisms it uses to control application code.

The current center of gravity is the Razem framework (in the `qms-workflow-engine` submodule, rename queued), which will host the QMS's own UI as the first real application built on it.

---

## 2. Current Status

**Active branch:** `dev/content-model-unification` on the engine submodule. Full UI shell ported; ready to build real QMS workflows.

**Engine surface:** 26 component classes (29 registered names), 11 page seeds, 7 themes (default, sleek, debug, liquid-glass, paper, chat, task), 79/79 parity tests passing. Stateless server with instance spawning. See §4.

**SDLC docs (Flow State + qms-cli):**
| Document | Version | Notes |
|----------|---------|-------|
| SDLC-QMS-RS | v22.0 EFFECTIVE | 143 requirements |
| SDLC-QMS-RTM | v27.0 EFFECTIVE | 687 tests, qualified at `918984d` |
| SDLC-CQ-RS | v2.0 EFFECTIVE | 6 requirements |
| SDLC-CQ-RTM | v2.0 EFFECTIVE | Inspection-based, qualified at `d3c34e5` |
| SDLC-WFE-RS | v0.1 DRAFT | 30 requirements (needs full rewrite for v2) |
| Qualified Baseline | CLI-18.0 | qms-cli main at `309f217` |

**Open work:** Most recent landings are workshop/theme-system improvements (workshop hub, right-click inspect panel, Navigation split, theme refactor + 6 themes, nesting-visualizations workshop). The nesting workshop converged on a stable design (**Experiment A**) for nested-navigation UX with strong agent-governance properties — see §3 arc and Session-2026-04-25-001 notes. The strategic next step is to build real QMS workflow pages on top of Razem rather than continuing engine-side iteration. **65 CRs CLOSED, 5 INVs CLOSED.**

**Critical gap:** the dev branch has full site shell but no real QMS workflow pages — every shipping page seed is a demo or gallery.

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

**Nesting Workshop — Bus Iterations Rejected, Component-Integrated Showcases Adopted (Apr 25–26).** Two further iteration rounds attempted to extend Experiment A. **First** an "A.X subtree-grouping motifs" series (5 variants — Cumulative bus, Nested brackets, Branching wire path, Section dividers, Hue zones) explored ways to make the implicit "what belongs to Tab 1.2?" grouping visible. Lead picked A.1 (cumulative bus) as the only acceptable variant; the rest were rejected. **Second** an "A.1.X left-bus refinements" series (3 variants — Left bus content fixed, Pre-allocated bus, Choice-keyed colors) addressed the content-pushed-right complaint in A.1. **All bus iterations were ultimately rejected** — the metaphor adds visual weight without new information, and the "what belongs to Tab 1.2?" question A allegedly didn't solve was somewhat theoretical. Slimmed everything back to canonical A; pivoted to "A.X component-integrated showcases" testing A's structure with realistic Razem-component HTML in the leaf body: **A.1 — TextForm leaf** (single text input), **A.2 — ChoiceForm leaf** (3-radio quiz question), **A.3 — Composite log leaf** (Group containing TextForm + DateForm + CheckboxForm). The showcases are visual-only (form `onsubmit` is `preventDefault`'d; no actual store binding), but they rendered the engine's default-theme component HTML faithfully (verified by programmatically rendering each component via `Page().bind()` and matching the output structure). Helper `expABase` (extracted in this session for the bus iterations) now drives all showcases via a small `renderShowcase(rootSelector, { gradId, crumb, body })` factor-out. File: 1191 → 2146 (peak with bus iterations) → 1441 (slim) → 1683 (final with showcases).

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

19 seeds in `pages/`. The main user-facing routes outside the seed catalog: `/portal` (Agent Portal), `/qms`, `/workspace`, `/inbox`, `/manual`, `/learn`, `/wiki`, `/framing`, `/components`, `/deepdive`, `/workshop` (with sub-pages: `page-builder`, `nesting`, `component-creation` stub).

### Test surface

`tests/test_parity.py` — 79 tests across 9 categories; verifies JSON↔HTML affordance alignment for every shipping page.

---

## 5. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| CR-110 | IN_EXECUTION v1.1 | Workflow engine development. EI-1-4 Pass. EIs 5-7 need rescoping for the rebuild. |
| CR-107 | DRAFT v0.1 | Unified Document Lifecycle. On hold (superseded by engine direction; may need cancellation). |
| CR-106 | DRAFT v0.1 | System Governance. Depends on CR-107. Same hold. |
| CR-091-ADD-001-VAR-001 | PRE_APPROVED v1.0 | Type 2 VAR. CLI title bug + SOP-004/TEMPLATE-VR alignment gap. |
| CR-001 | IN_EXECUTION v1.0 | Legacy. Cancellation candidate. |
| CR-020 | DRAFT v0.1 | Legacy test document. Cancellation candidate. |
| INV-002 through INV-006 | Various | Legacy investigations. Low priority. |
| CR-036-VAR-002, -004 | IN_EXECUTION v1.0 | Legacy. Low priority. |

---

## 6. Forward Plan

### Immediate

1. **Build real QMS workflows as component compositions.** The primary goal: making the QMS usable through Razem. CR creation, review, document lifecycle pages.
2. **Wire QMS / Workspace / Inbox to real data.** Connect to `qms-cli` or the QMS document store rather than placeholder lists.
3. **Triage demo pages.** Decide which seeds in `/portal` are valuable vs gallery cruft.

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
| **Nesting workshop follow-through.** Promote **Experiment A** (drill-down on the thread + read-only ancestor tabs + "Change selection" button) into a real engine surface. Evaluate which of A.1's progress rings and A.1.X's advanced features (interlevel info nodes, sequential gating) belong in the engine vs as opt-in container behaviors. Possibly retire the earlier-round variants (4.3.1.X, 4.3.3.X, 4.3.1.2.1.X) once the engine surface is stable. | Medium | Session-2026-04-25-001 |

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

- **Dev branch has full site shell but no real QMS workflows.** All shipping page seeds are demos or galleries. This is the critical gap; resolving it is the §6 immediate priority.
- **SDLC-WFE-RS needs a full rewrite** for the rebuilt engine. v1 requirements no longer apply.
- **Legacy QMS debt.** Nine open documents from early iterations; bulk cleanup recommended after workflows ship.
- **`qms-workflow-engine` submodule pointer** must be kept current with pushes — easy to forget after working in the submodule directly.
