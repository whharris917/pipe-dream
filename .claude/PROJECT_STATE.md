# Project State

*Last updated: Session-2026-03-26-002 (2026-03-26)*

---

## 1. Where We Are Now

**Clean-room rebuild of the Workflow Engine.** The previous engine (v2) has been deleted. A new foundation is being built from scratch on the `dev/content-model-unification` branch of qms-workflow-engine, based on the architectural plan from Session-2026-03-24-001.

**What's running now:** Flask app at `http://127.0.0.1:5000` with 11 pages:
- **page-1**: TextForm + TextForm + CheckboxForm (basic eigenforms)
- **page-2**: TabForm with 3 tabs (Document Title, Scope, Impact Areas)
- **page-3**: RubiksCubeForm (arbitrarily complex eigenform, conditional affordances)
- **page-4**: ChainForm wizard (4-step sequential form with auto-advance)
- **example-table**: TableForm (dynamic columns, stable row IDs, agent-reviewed API)
- **page-6**: MultiForm + ChoiceForm + CheckboxForm + 2x ListForm (change request form)
- **math-test**: TextForm + ChoiceForm + CheckboxForm + TabForm (6-tab scavenger hunt) + ChainForm (4-clue chain)
- **upgraded-math-test**: All questions wrapped in outer ChainForm (one at a time)
- **visibility-experiments**: ChoiceForm controlling VisibilityForm children (Simple/Advanced/Expert)
- **quiz-portal**: 3 quizzes (Geography/Science/History) in nested TabForms, ScoreForm grading per quiz
- **vendor-assessment**: Vendor Qualification Assessment composing all 23 eigenform types

**Eigenform architecture** — 23 eigenform types:

Data forms:
- `TextForm`: single free-form string. Complete when value not None.
- `CheckboxForm`: multi-select with N/A mode. Complete when any checked or N/A.
- `ChoiceForm`: single selection via radio buttons. Complete when valid option selected.
- `MultiForm`: groups FieldDescriptors under single affordance. Complete when all fields filled.
- `ListForm`: ordered list with add/edit/remove/reorder + N/A. Complete when items > 0 or N/A.
- `TableForm`: dynamic columns + rows with stable IDs. Inline editing for cells, headers, add/remove.
- `NumberForm`: numeric input with min/max/step/integer constraint. Complete when not None.
- `DateForm`: ISO 8601 date or datetime with optional bounds. Complete when not None.
- `BooleanForm`: binary yes/no toggle with custom labels. Complete when not None.
- `RangeForm`: slider over continuous range with unit. Complete when not None.
- `MemoForm`: multi-line textarea with min/max length. Complete when non-empty and meets min_length.
- `RatingForm`: ordinal 1-N rating with optional labels. Complete when not None.
- `RankForm`: fixed-set item reordering with move up/down + set_order. Complete when explicitly ranked.
- `KeyValueForm`: dynamic key-value pairs with stable IDs. Complete when at least one entry with key+value.

Container forms:
- `PageForm`: top-level container with Reset Page (recursive clear). Persistence boundary.
- `TabForm`: tabbed container. Only active tab in JSON/HTML (faithful projection).
- `ChainForm`: sequential wizard. Auto-advances. Complete when all steps complete.
- `AccordionForm`: collapsible sections. Only expanded sections in JSON/HTML (faithful projection).
- `VisibilityForm`: wraps child with conditional visibility. Supports value, list, or callable predicates.

Sibling-reading forms:
- `ScoreForm`: read-only grading from answer key. Reads sibling values.
- `ComputedForm`: read-only derived display from arbitrary compute function. Optional store_result for cross-eigenform dependencies.

Showcase:
- `RubiksCubeForm`: full Rubik's Cube. Conditional affordances based on solved state.

**Key design patterns:**
- **children property**: base Eigenform returns []. Containers override. Enables generic traversal.
- **Unified bind()**: base bind() deepcopies + calls _bind_children(). Containers override _bind_children() only.
- **PageForm is the persistence boundary**: PageForm.bind() takes data_dir and creates its own Store; children inherit it
- **Scope = parent key**: containers pass scope=self.key when binding children. Siblings share scope.
- **Batch actions**: handle() checks for {"action": "batch", "actions": [...]}. Subclasses implement _handle().
- **Affordance body templates**: fillable placeholders (`<value>`, `<true | false>`) + per-affordance instructions
- **is_complete**: required on all eigenforms (NotImplementedError). Green border when complete, gray when incomplete.
- **Conditional affordances**: affordance lists change based on state (Rubik's solved/unsolved, CheckboxForm normal/N/A mode)
- **Faithful projection**: TabForm/ChainForm/AccordionForm hide non-visible eigenforms from both JSON and HTML
- **Structured errors**: error message + failed_action echoed in response, valid alternatives listed
- **Content negotiation**: single URL serves JSON (default) or HTML (when Accept: text/html). No `/view` suffix.
- **Path-based eigenform access**: URLs mirror containment hierarchy (e.g., `/pages/page-2/tabs/title`)
- **RESTful API**: GET /pages/{key} → page, GET /pages/{key}/{path} → eigenform, POST /pages/{key} → page action, POST /pages/{key}/{path} → eigenform mutation
- **Render derives from serialize**: render() calls serialize() then render_from_data(data). HTML is a pure function of the serialized dict. Cannot drift.
- **LNARF compliance**: JSON is canonical, HTML is faithful projection, purple "See JSON" buttons are human-only (exempt)
- **HATEOAS**: every eigenform carries affordances, POST returns full page state
- **SSE**: `/pages/{key}/stream` pushes updates on POST
- **Page definitions**: one file per page in `pages/` directory, auto-discovered. Key from definition.
- **ComputedForm ordering**: when store_result=True, must appear before VisibilityForm that depends on its result (serialization is sequential).

**Terminology:**
- **Eigenform** = self-contained unit (from German "eigen" = self)
- **Forms** = 23 types across data, container, sibling-reading, and showcase categories
- Data forms: TextForm, CheckboxForm, ChoiceForm, MultiForm, ListForm, TableForm, NumberForm, DateForm, BooleanForm, RangeForm, MemoForm, RatingForm, RankForm, KeyValueForm
- Container forms: PageForm (shows all children), TabForm (one at a time), ChainForm (sequential wizard), AccordionForm (collapsible sections)
- Conditional: VisibilityForm (wraps child, depends on sibling value or callable)
- Sibling-reading: ScoreForm, ComputedForm

**CR-110** is IN_EXECUTION (v1.1). EI-1-4 Pass. Remaining EIs (5-7) will need to be scoped to reflect the rebuild.

**65 CRs CLOSED. 5 INVs CLOSED.**

---

## 2. The Arc

**Foundation through Quality Manual** (Feb 1-24, CR-042 through CR-105).

**Workflow Engine v1** (Mar 3-7, CR-108 through CR-110). CLI-based graph engine. Proved concepts but revealed design limits.

**Workflow Engine v2 — UI-Driven Redesign** (Mar 8-12). Built a web UI and Agent Portal sandbox. Proved field-based and table-based workflow patterns. Four separate handler implementations.

**Unified Workflow Engine** (Mar 14). Clean-room rewrite formalizing the patterns discovered in v2. Single runtime replacing 4 handlers. Added lists, conditional navigation, dynamic options, side effects.

**Engine Hardening + Experimental Renderers + Parallel Execution** (Mar 15). Six architectural refinements, flowchart visualization, router/fork/merge primitives, builder full engine parity.

**Spine Model + Unified Rendering** (Mar 16-19). Canonical schematic representation, HTML-over-canvas rendering, DOM measurement, interactive collapse/expand, architecture formalization (LNARF).

**Repository Restructure + Documentation** (Mar 20). Removed v1 CLI engine. Restructured directories. Consolidated docs. AffordanceSource protocol + external state providers.

**Multi-Instance + LNARF Portal + Observer Simplification** (Mar 21). Transformed to multi-instance. Unified Renderer Principle. First page-specific LNARF renderer. Observer simplified to two modes. Interactive affordances. Faithful projection for all workflow pages. Agent API evaluation.

**Workshop + Focus Excision + Field Groups + Content Array** (Mar 22-23). Workshop experimentation, focus mechanism excision, renderer registry, field groups, unified content array, element type vocabulary, Element Library rebuild.

**Content Model Unification Plan** (Mar 24). Architectural audit of the engine. Developed comprehensive plan: one content array, one element protocol, one dispatch loop. Seven element types. Python-native definitions with JSON persistence. Four-phase implementation plan. Adversarial audit found and resolved 20 issues. YAML elimination decision.

**Clean-Room Rebuild — Eigenform Architecture** (Mar 25). Deleted all engine code. Built new foundation from scratch. Coined "Eigenform" (self-contained, self-rendering, self-sufficient). Ten eigenform types across data forms (TextForm, CheckboxForm, ChoiceForm, MultiForm, ListForm, TableForm), container forms (PageForm, TabForm, ChainForm), and showcase (RubiksCubeForm). Key patterns: bind() produces independent copies, is_complete required on all forms, conditional affordances, faithful projection, N/A mode for CheckboxForm/ListForm, recursive PageForm reset, structured error responses. TableForm agent-reviewed through two iterations. MultiForm reduces agent round-trips by grouping fields under a single affordance. ListForm has inline up/down/remove controls. 6 demo pages exercising all types.

**State Isolation + Render-from-Serialize + URL Overhaul + Primitive Expansion** (Mar 26). Per-page state files. Page definitions with auto-discovery. Content negotiation. Path-based eigenform URLs. Render-from-serialize architectural fix. ScoreForm for quiz grading. Quiz Portal page. 10 new eigenform primitives (NumberForm, DateForm, BooleanForm, RangeForm, MemoForm, RatingForm, RankForm, KeyValueForm, ComputedForm, AccordionForm). ComputedForm with store_result for cross-eigenform dependencies. VisibilityForm callable predicates. Vendor Assessment page composing all 23 types with 3-level container nesting and derived computed scores. 11 pages total.

---

## 3. What's Built

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v22.0 EFFECTIVE | 143 requirements |
| SDLC-QMS-RTM | v27.0 EFFECTIVE | 687 tests, qualified commit 918984d |
| SDLC-CQ-RS | v2.0 EFFECTIVE | 6 requirements |
| SDLC-CQ-RTM | v2.0 EFFECTIVE | Inspection-based, qualified commit d3c34e5 |
| SDLC-WFE-RS | v0.1 DRAFT | 30 requirements (needs rewrite for v2) |
| Qualified Baseline | CLI-18.0 | qms-cli commit 309f217 (main) |

### Controlled Document State

| Document | Version |
|----------|---------|
| SOP-001 through SOP-007 | v21.0 / v16.0 / v3.0 / v9.0 / v7.0 / v5.0 / v2.0 EFFECTIVE |
| TEMPLATE-CR | v10.0 EFFECTIVE |
| TEMPLATE-VAR | v3.0 EFFECTIVE |
| TEMPLATE-ADD | v2.0 EFFECTIVE |
| TEMPLATE-VR | v3.0 EFFECTIVE |

### Workflow Engine — Clean-Room Rebuild (dev branch)

| Component | Description |
|-----------|-------------|
| `engine/eigenforms.py` | Eigenform base (children, bind, batch, render-from-serialize), TextForm, CheckboxForm |
| `engine/affordances.py` | Affordance (pure data), render_affordance_html utility, all affordance subclasses |
| `engine/store.py` | JSON file store, one file per page, scoped by eigenform key |
| `engine/page.py` | PageForm — persistence boundary, find_eigenform, clear_recursive via children |
| `engine/tab.py` | TabForm — tabbed container, faithful projection |
| `engine/chain.py` | ChainForm — sequential wizard with auto-advance + Continue |
| `engine/rubiks.py` | RubiksCubeForm + RotateAffordance — complexity showcase |
| `engine/table.py` | TableForm — inline editing, add/remove, batch support |
| `engine/choice.py` | ChoiceForm — single selection via radio buttons |
| `engine/listform.py` | ListForm — ordered list with add/edit/remove/reorder + N/A |
| `engine/multi.py` | MultiForm — groups FieldDescriptors under single affordance |
| `engine/visibility.py` | VisibilityForm — conditional visibility (value, list, or callable) |
| `engine/score.py` | ScoreForm — read-only grading from answer key |
| `engine/number.py` | NumberForm — numeric input with min/max/step/integer |
| `engine/date.py` | DateForm — ISO 8601 date/datetime with bounds |
| `engine/boolean.py` | BooleanForm — binary yes/no toggle |
| `engine/range.py` | RangeForm — slider over continuous range |
| `engine/memo.py` | MemoForm — multi-line textarea with length constraints |
| `engine/rating.py` | RatingForm — ordinal 1-N rating |
| `engine/rank.py` | RankForm — fixed-set item reordering |
| `engine/keyvalue.py` | KeyValueForm — dynamic key-value pairs |
| `engine/computed.py` | ComputedForm — derived display from siblings, optional store_result |
| `engine/accordion.py` | AccordionForm — collapsible sections, faithful projection |
| `app/__init__.py` | Flask app factory |
| `app/routes.py` | Routes + SSE + content negotiation (JSON/HTML) |
| `app/templates/` | index.html, page.html (SSE client) |
| `pages/` | One file per page, auto-discovered. Key from definition, not filename. |
| `run.py` | Entry point (threaded=True) |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| CR-110 | IN_EXECUTION v1.1 | Workflow engine development. EI-1-4 Pass. |
| CR-107 | DRAFT v0.1 | Unified Document Lifecycle. On hold. |
| CR-106 | DRAFT v0.1 | System Governance. Depends on CR-107. On hold. |
| CR-091-ADD-001-VAR-001 | PRE_APPROVED v1.0 | Type 2 VAR. VR title bug + SOP-004/TEMPLATE-VR alignment gap. |
| CR-001 | IN_EXECUTION v1.0 | Legacy. Candidate for cancellation. |
| CR-020 | DRAFT v0.1 | Legacy test document. Candidate for cancellation. |
| INV-002 through INV-006 | Various | Legacy investigations. Low priority. |
| CR-036-VAR-002, CR-036-VAR-004 | IN_EXECUTION v1.0 | Legacy. Low priority. |

---

## 5. Forward Plan

### Immediate (Rebuild)

1. **Remaining eigenform types** — DisplayForm (all other planned types now built)
2. **Flow control** — ProceedDef, NavigationDef, RouterDef, ForkDef as page/node-level affordances
3. **Workflow definition** — Python-native WorkflowDef with nodes containing eigenforms
4. **Expression evaluator** — visible_when, gates, side_effects
5. **Builder** — Create Workflow via the engine itself

### CR-110 Remaining EIs

EI-5 (RS update), EI-6 (push + pointer), EI-7 (post-exec) remain valid. The RS will reflect the rebuilt engine.

### On Hold: CR-107 / CR-106

Both superseded by the engine. May need cancellation or significant revision.

---

## 6. Backlog

### Ready (no blockers)

| Item | Effort | Source |
|------|--------|--------|
| Fix CLI title metadata propagation | Small | CR-091-ADD-001-VAR-001 |
| Align SOP-004 Section 9C.4 with TEMPLATE-VR | Small | CR-091-ADD-001-VAR-001 |
| Govern checkin.py bug fix (commit `532e630`) via CR | Trivial | INV-012 |
| Delete `.QMS-Docs/` | Trivial | CR-103 |
| Standardize metadata timestamps to UTC ISO 8601 | Small | Session-2026-02-26-001 |

### Bundleable

**Identity & Access Hardening** (~1 session) — proxy header validation, Git MCP access control
**Agent Hub Robustness** (~1-2 sessions) — C3 (root user), H4 (no hub shutdown on GUI exit), M6/M8/M9/M10
**GUI Polish** (~1-2 sessions) — H6, M3/M4/M5/M7, L3-L6

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value |
| Metadata injection into viewable rendition | No current pain point |
| Consolidate SDLC namespaces into system registry | Depends on CR-106 |
| Interactive document write protection (REQ-INT-023) | Deferred pending UI-based interaction design |
| Remove stdio transport option from MCP servers | Low priority |
| Propagate Quality Manual cleanup from workshop | Medium effort, not blocking |

---

## 7. Gaps & Risks

**Engine is in rebuild.** The v2 engine code has been deleted on the dev branch. The old engine remains on main until the rebuild is ready to merge.

**SDLC-WFE-RS needs full rewrite.** v1 requirements don't apply to the rebuilt engine.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**qms-workflow-engine submodule pointer** should be kept current with pushes.
