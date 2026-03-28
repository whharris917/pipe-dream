# Project State

*Last updated: Session-2026-03-28-002 (2026-03-28)*

---

## 1. Where We Are Now

**Clean-room rebuild of the Workflow Engine.** The previous engine (v2) has been deleted. A new foundation is being built from scratch on the `dev/content-model-unification` branch of qms-workflow-engine, based on the architectural plan from Session-2026-03-24-001.

**Fractal complexity plan is complete.** All five phases (SwitchForm → Registry → Structural Persistence → Structural Actions → Self-Modifying Pages) are implemented and tested.

**What's running now:** Flask app at `http://127.0.0.1:5000` with 16 pages:
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
- **vendor-assessment**: Vendor Qualification Assessment composing all 23+ eigenform types
- **weird-experiments**: Playground exercising ValidationForm, DynamicChoiceForm, ActionForm, RepeaterForm
- **switch-demo**: SwitchForm with ticket type driving BugReport/FeatureRequest/Question compositions
- **mutable-demo**: Mutable structure page — add/remove/reorder eigenforms at runtime
- **survey-builder**: Self-modifying page — ActionForm generates questions that materialize from registry
- **eigenform-gallery**: Interactive tutorial covering all 29 eigenform types across 8 tabbed sections

**Eigenform architecture** — 29 eigenform types:

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
- `PageForm`: top-level container with Reset Page (recursive clear). Persistence boundary. Optional mutable_structure for Phase D/E. Feedback banner for action results.
- `TabForm`: tabbed container. Only active tab in JSON/HTML (faithful projection).
- `ChainForm`: sequential wizard. Auto-advances. Complete when all steps complete.
- `AccordionForm`: collapsible sections. Only expanded sections in JSON/HTML (faithful projection).
- `VisibilityForm`: wraps child with conditional visibility. Supports value, list, or callable predicates.
- `GroupForm`: named container for reusable compositions. Supports parameterization via subclassing.
- `RepeaterForm`: stamps template eigenforms per dynamic entry. Compound scopes, stable IDs, add/remove.
- `SwitchForm`: selects between named alternative subtrees based on sibling value. Faithful projection.

Sibling-reading forms:
- `ScoreForm`: read-only grading from answer key. Reads sibling values.
- `ComputedForm`: read-only derived display from arbitrary compute function. Optional store_result for cross-eigenform dependencies.
- `ValidationForm`: cross-field validation rules. Pending/pass/fail. Can block page completion.

Dynamic forms:
- `DynamicChoiceForm`: options depend on sibling value via options_fn or static_options. Stale detection.
- `ActionForm`: imperative button with preconditions, confirmation, side effects. Can return structural_actions for Phase E.

Showcase:
- `RubiksCubeForm`: full Rubik's Cube. Conditional affordances based on solved state.

**Infrastructure (Phases B-E):**
- **Eigenform Type Registry** (`engine/registry.py`): explicit mapping of type names to classes. 29 built-in types auto-registered. Custom types register under their own names.
- **Structural Persistence**: `to_descriptor()` on all types serializes tree structure. `from_descriptor()` reconstructs from descriptors + seed. PageForm stores `__structure` in the store.
- **Structural Actions**: `mutable_structure=True` pages support add/remove/move/rebuild_from_seed. Surgical data cleanup on removal.
- **Self-Modifying Pages**: ActionForm can return `structural_actions` that PageForm applies, reshaping the page in response to user interaction.

**Key design patterns:**
- **children property**: base Eigenform returns []. Containers override. Enables generic traversal.
- **Unified bind()**: base bind() deepcopies + calls _bind_children(). Containers override _bind_children() only.
- **PageForm is the persistence boundary**: PageForm.bind() takes data_dir and creates its own Store; children inherit it
- **Scope = parent key**: containers pass scope=self.key when binding children. Siblings share scope.
- **Batch actions**: handle() checks for {"action": "batch", "actions": [...]}. Subclasses implement _handle().
- **Universal clear**: base serialize() appends Clear affordance when has_data is True. base handle() intercepts {"action": "clear"}.
- **Base helpers**: `_base_state()` returns common state fields; `_error(msg, *, action, body)` eliminates per-file error helpers; `render_inline_button()` + style constants eliminate inline HTML duplication.
- **Affordance body templates**: fillable placeholders (`<value>`, `<true | false>`) + per-affordance instructions
- **is_complete**: required on all eigenforms (NotImplementedError). Green border when complete, gray when incomplete.
- **Conditional affordances**: affordance lists change based on state (Rubik's solved/unsolved, CheckboxForm normal/N/A mode)
- **Faithful projection**: TabForm/ChainForm/AccordionForm/SwitchForm hide non-visible eigenforms from both JSON and HTML. HTML has no browser-side validation — server is sole authority.
- **Structured errors**: error message + failed_action echoed in response, valid alternatives listed
- **Feedback banner**: PageForm captures action results as one-shot feedback (success/error), rendered as colored banner, visible in both JSON and HTML
- **Content negotiation**: single URL serves JSON (default) or HTML (when Accept: text/html). No `/view` suffix.
- **Path-based eigenform access**: URLs mirror containment hierarchy (e.g., `/pages/page-2/tabs/title`)
- **RESTful API**: GET /pages/{key} → page, GET /pages/{key}/{path} → eigenform, POST /pages/{key} → page action, POST /pages/{key}/{path} → eigenform mutation
- **Render derives from serialize**: render() calls serialize() then render_from_data(data). HTML is a pure function of the serialized dict. Cannot drift.
- **LNARF compliance**: JSON is canonical, HTML is faithful projection, purple "See JSON" buttons are human-only (exempt)
- **HATEOAS**: every eigenform carries affordances, POST returns full page state
- **SSE**: `/pages/{key}/stream` pushes updates on POST
- **Page definitions**: one file per page in `pages/` directory, auto-discovered. Key from definition.
- **Store file sync**: Store checks file mtime on every access. External deletes clear cache; external edits reload.
- **ComputedForm ordering**: when store_result=True, must appear before VisibilityForm that depends on its result (serialization is sequential).
- **Named compositions**: GroupForm enables reusable, parameterized eigenform groups via subclassing. Subclass gets own form type identity.
- **Compound scopes**: RepeaterForm uses `key/entry_id` scopes. Store treats scope as opaque string, so nesting works naturally.
- **Structural descriptors**: to_descriptor() auto-extracts serializable config. Containers add children. from_descriptor() reconstructs with seed for callables.
- **Seed preservation**: PageForm._seed holds unbound eigenforms for callable matching during _rebuild().

**Terminology:**
- **Eigenform** = self-contained unit (from German "eigen" = self)
- **Forms** = 29 types across data, container, sibling-reading, dynamic, and showcase categories
- **Seed** = the Python page definition; the genome
- **Structure** = the stored eigenform tree; the expressed organism
- **Structural action** = a mutation that reshapes the eigenform tree at runtime

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

**Expressiveness Expansion + Fractal Complexity Architecture** (Mar 27). Five new eigenform types addressing expressiveness gaps: ValidationForm (cross-field validation), DynamicChoiceForm (conditional options), ActionForm (imperative side effects), RepeaterForm (dynamic repeated structure), GroupForm (named parameterized compositions). Weird Experiments page exercising all new types. Architectural plan for dynamic fractal complexity: collapsing the boundary between structure and data so user interactions can reshape the eigenform tree itself. Biology metaphor: genome (Python types), expression (store), environment (user POSTs). Five-phase plan: SwitchForm → Registry → Structural Persistence → Structural Actions → Self-Modifying Pages.

**Fractal Complexity — Complete Implementation** (Mar 28, session 001). All five phases of the fractal complexity plan implemented. SwitchForm (Phase A): N-way structural selection based on sibling value. Eigenform Type Registry (Phase B): explicit name→class mapping, 29 built-in types. Structural Persistence (Phase C): to_descriptor/from_descriptor round-trip, __structure in store, seed-based reconstruction with callable preservation. Structural Actions (Phase D): mutable pages with add/remove/move/rebuild_from_seed, surgical data cleanup. Self-Modifying Pages (Phase E): ActionForm structural_actions flow up to PageForm, enabling pages that reshape themselves in response to user interaction. Survey Builder demo. README for qms-workflow-engine. 29 eigenform types, 15 pages.

**Gallery, Feedback, Faithful Projection, Store Sync, UI Polish** (Mar 28, session 002). Eigenform Gallery page: interactive tutorial covering all 29 types across 8 tabbed sections (16 pages total). Universal Clear affordance on all data eigenforms. Server-side validation: NumberForm/RangeForm/MemoForm reject invalid values with structured errors instead of silently accepting. Faithful projection enforcement: removed browser-side validation so humans see same errors as agents. PageForm multi-message feedback banner: errors accumulate per-target, success is singular, dismiss affordance per error. Store file sync: mtime-based cache invalidation. CheckboxForm/RankForm: explicit Done confirmation prevents ChainForm premature auto-advance; CheckboxForm N/A removed (Done with nothing checked = none apply). Condensed move affordances: ListForm/RankForm use two parameterized affordances (Move Up/Down) listing valid items. KeyValueForm: inline edit fields, duplicate key rejection, condensed affordances. ListForm: inline add/edit rows with green +/✓ buttons. Live tooltip updates codebase-wide: all input buttons show actual POST body on hover.

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
| `engine/eigenforms.py` | Eigenform base (children, bind, batch, render-from-serialize, to_descriptor, has_data, clear), TextForm, CheckboxForm |
| `engine/affordances.py` | Affordance (pure data), render_affordance_html utility, all affordance subclasses, disabled_button |
| `engine/store.py` | JSON file store, one file per page, scoped by eigenform key, delete() for surgical removal, mtime-based file sync |
| `engine/registry.py` | EigenformRegistry (register/lookup/available), from_descriptor(), lazy default with 29 types |
| `engine/page.py` | PageForm — persistence boundary, find_eigenform, structural persistence (__structure), mutable structure (add/remove/move/rebuild_from_seed), structural_actions from children, feedback banner |
| `engine/tab.py` | TabForm — tabbed container, faithful projection |
| `engine/chain.py` | ChainForm — sequential wizard with auto-advance + Continue |
| `engine/rubiks.py` | RubiksCubeForm + RotateAffordance — complexity showcase |
| `engine/table.py` | TableForm — inline editing, add/remove, batch support |
| `engine/choice.py` | ChoiceForm — single selection via radio buttons |
| `engine/listform.py` | ListForm — ordered list with add/edit/remove/reorder + N/A |
| `engine/multi.py` | MultiForm — groups FieldDescriptors under single affordance |
| `engine/visibility.py` | VisibilityForm — conditional visibility (value, list, or callable) |
| `engine/switch.py` | SwitchForm — N-way structural selection based on sibling value |
| `engine/score.py` | ScoreForm — read-only grading from answer key |
| `engine/number.py` | NumberForm — numeric input with min/max/step/integer, server-side validation |
| `engine/date.py` | DateForm — ISO 8601 date/datetime with bounds |
| `engine/boolean.py` | BooleanForm — binary yes/no toggle |
| `engine/range.py` | RangeForm — slider over continuous range, server-side validation |
| `engine/memo.py` | MemoForm — multi-line textarea with length constraints |
| `engine/rating.py` | RatingForm — ordinal 1-N rating |
| `engine/rank.py` | RankForm — fixed-set item reordering |
| `engine/keyvalue.py` | KeyValueForm — dynamic key-value pairs |
| `engine/computed.py` | ComputedForm — derived display from siblings, optional store_result |
| `engine/accordion.py` | AccordionForm — collapsible sections, faithful projection |
| `engine/validation.py` | ValidationForm — cross-field rules, pending/pass/fail, blocks completion |
| `engine/dynamic_choice.py` | DynamicChoiceForm — options from sibling value, stale detection |
| `engine/action.py` | ActionForm — imperative button, preconditions, confirmation, side effects, structural_actions |
| `engine/repeater.py` | RepeaterForm + EntryGroup — dynamic repeated structure, compound scopes |
| `engine/group.py` | GroupForm — named compositions, parameterizable via subclassing |
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

### Immediate

1. **CR-110 remaining EIs** — Update EI-5 (RS), EI-6 (push + pointer), EI-7 (post-exec) to reflect the rebuilt engine
2. **SDLC-WFE-RS rewrite** — Requirements spec needs full rewrite for eigenform architecture

### Engine Next Steps

- Agent integration testing (can an agent drive the API end-to-end?)
- QMS workflow page definitions (actual workflow pages using eigenforms)
- Performance / stress testing with large pages

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
