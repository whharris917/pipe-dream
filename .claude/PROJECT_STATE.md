# Project State

*Last updated: Session-2026-03-31-003 (2026-03-31)*

---

## 1. Where We Are Now

**Clean-room rebuild of the Workflow Engine.** The previous engine (v2) has been deleted. A new foundation is being built from scratch on the `dev/content-model-unification` branch of qms-workflow-engine, based on the architectural plan from Session-2026-03-24-001.

**Fractal complexity plan is complete.** All five phases (SwitchForm → Registry → Structural Persistence → Structural Actions → Self-Modifying Pages) are implemented and tested.

**What's running now:** Flask app at `http://127.0.0.1:5000` with 18 pages:
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
- **eigenform-gallery**: Interactive tutorial covering all 33 eigenform types across 10 tabbed sections
- **control-flow-gallery**: Control flow demos (SequenceForm, Fork/Merge, Routing, HistoryForm)
- **page-builder**: Mutable page for composing eigenform structures from the registry

**Eigenform architecture** — 33 eigenform types:

Data forms:
- `TextForm`: single free-form string. Complete when value not None.
- `CheckboxForm`: multi-select with N/A mode. Complete when any checked or N/A.
- `ChoiceForm`: single selection via radio buttons. Complete when valid option selected.
- `MultiForm`: groups FieldDescriptors under single affordance. Complete when all fields filled.
- `ListForm`: ordered list with add/edit/remove/reorder + N/A. Fixed items, ordering constraints (static + dynamic), topological sort enforcement. Complete when items > 0 or N/A.
- `SetForm`: unordered collection of unique items. Add/remove by value, duplicates rejected. Complete when non-empty.
- `TableForm`: dynamic columns + rows with stable IDs. Inline editing for cells, headers, add/remove. Typed columns: fixed_columns accepts Eigenform instances, cells become bound eigenforms with compound scopes and path-based routing.
- `NumberForm`: numeric input with min/max/step/integer constraint. Complete when not None.
- `DateForm`: ISO 8601 date or datetime with optional bounds. Complete when not None.
- `BooleanForm`: binary yes/no toggle with custom labels. Complete when not None.
- `RangeForm`: slider over continuous range with unit. Complete when not None.
- `MemoForm`: multi-line textarea with min/max length. Complete when non-empty and meets min_length.
- `RankForm`: fixed-set item reordering with move up/down + set_order. Complete when explicitly ranked.
- `KeyValueForm`: dynamic key-value pairs. Edit/remove by key (not internal ID). Key rename via new_key. Complete when at least one entry with key+value.

Container forms:
- `PageForm`: top-level container with Reset Page (recursive clear). Persistence boundary. Optional mutable_structure for Phase D/E. Feedback banner for action results.
- `TabForm`: tabbed container. Only active tab in JSON/HTML (faithful projection).
- `ChainForm`: sequential wizard. Auto-advances. Complete when all steps complete.
- `SequenceForm`: gated sequential container. Like ChainForm but without auto-advance. Steps unlock progressively. Manual Back/Next navigation.
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

Wrapper forms:
- `HistoryForm`: wraps an eigenform with append-only change history. Lazy detection on serialize — compares child state to last snapshot, appends if different. Timeline browsing with read-only historical views. History is never editable or clearable.

Runner forms:
- `TableRunner`: reads a sibling TableForm and presents its rows as a gated sequential workflow. Only typed columns are executable; text columns provide row labels. Row ordering constraints become execution gates.

Showcase:
- `RubiksCubeForm`: full Rubik's Cube. Conditional affordances based on solved state.

**Infrastructure (Phases B-E):**
- **Eigenform Type Registry** (`engine/registry.py`): explicit mapping of type names to classes. 30 built-in types auto-registered. Custom types register under their own names.
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
- **Two-tier serialization**: `_serialize_full()` produces internal dict (with form, key, render_hints) for HTML rendering. `serialize()` strips agent-noise fields. render() uses `_serialize_full()` for HTML, `serialize()` for "See JSON" button. Containers override `_serialize_full()`.
- **Render derives from serialize**: render() calls _serialize_full() then render_from_data(data). HTML is a pure function of the internal dict. Cannot drift.
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
- **ListForm constraints**: ID-based ordering constraints (static must_follow + dynamic add/remove). Stable topological sort enforcement. Transitive cycle detection. Inline constraint UI per item.
- **OrderedCollection**: Reusable ordering engine extracted from ListForm. Manages stable IDs, fixed items, must_follow constraints, cycle detection, topological sort. ListForm wraps one (items). TableForm wraps two (rows + columns).
- **TableForm reordering**: move_row_up/down, move_col_left/right with inline arrow buttons. Fixed rows/columns. Row/column ordering constraints. Legacy state auto-migration. Inline constraint UI (row: green pills, column: blue pills). Row controls in borderless column outside data grid.
- **TableForm typed columns**: fixed_columns accepts `str | Eigenform`. Eigenform entries become typed columns — each cell is a bound eigenform with compound scope (`table_key/row_id`), path-based URL routing (`table/row_id/col_id`), and RowGroup routing nodes. set_cell guards typed columns; set_row skips them. Serialization includes nested eigenform state. is_complete checks typed cell eigenforms.
- **TableForm fixed_rows**: seeds row metadata AND cell data on first access. Enables pre-populated table definitions.
- **Edit mode infrastructure**: `editable: bool = False` on base Eigenform. `set_mode` affordance with `edit`/`execute` modes. Pencil icon (✏) enters edit mode, play icon (▶) returns to execution. Edit mode: dashed border on container, label/instruction become inline editable inputs with `font: inherit` and position-matched margins. Label overrides in `{key}.__label`, instruction overrides in `{key}.__instruction`. `_chrome_rendered` flag prevents duplicate affordance rendering. `_get_edit_affordances()` extensible by subclasses. Type-specific config (NumberForm min/max/step/integer, BooleanForm true/false labels) persisted via `{key}.__config` with `_effective_config` property. ChoiceForm/CheckboxForm embed a child ListForm for options/items editing — visible in edit mode (faithful projection), routable via standard children. Undo stack (`{key}.__undo`) with snapshot-based restore; initial snapshot (`{key}.__snapshot`) for discard. Chrome buttons: ↩ undo (conditional on depth > 0), ✕ discard (red, restores snapshot and exits edit mode). Child ListForm handle wrapped to push undo on parent.
- **Edit/execution mode distinction**: TableForm structural operations (add/remove/rename columns, reorder, constraints) are edit-mode activities. Execution mode = structure frozen, only typed cell eigenforms are interactive. Text columns are authoring-only. TableRunner enforces this distinction.
- **BUTTON_GAP**: shared constant in affordances.py. Transparent border matches button box height. Used by tableform, listform, rankform, keyvalueform.
- **Dependency visibility**: `render_dependency_line()` in eigenform.py. All sibling-reading eigenforms render "Depends on: /path/to/sibling" with full URL paths. Applied to SwitchForm, DynamicChoiceForm, ComputedForm, ValidationForm (per-rule), ActionForm, ScoreForm. Makes the shadow dependency graph visible in the UI.
- **Mutable page UI**: PageForm.render_from_data renders custom HTML for mutable_structure pages: type dropdown toolbar, per-eigenform ▲/▼/✕ control bars, empty state placeholder, subtle Rebuild from Seed. Eigenforms added via Page Builder get `editable=True` automatically; `editable` round-trips through to_descriptor/from_descriptor.

**Terminology:**
- **Eigenform** = a form that preserves its identity under transformation (serialize, render, handle, recompose). "Eigen" as in eigenvector — identity-preserving — not "self-contained." Revised from original meaning after theoretical analysis (Session-2026-03-30-001).
- **Forms** = 32 types across data, container, sibling-reading, dynamic, wrapper, runner, and showcase categories
- **Seed** = the Python page definition; the genome
- **Structure** = the stored eigenform tree; the expressed organism
- **Structural action** = a mutation that reshapes the eigenform tree at runtime

**CR-110** is IN_EXECUTION (v1.1). EI-1-4 Pass. Remaining EIs (5-7) will need to be scoped to reflect the rebuild.

**32 eigenform types. 18 pages.**

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

**Module Reorganization + Agent JSON Cleanup** (Mar 29). One eigenform per module: extracted TextForm/CheckboxForm from base, renamed all 27 modules to consistent `*form.py` convention. Two-tier serialization: `_serialize_full()` (internal, for HTML) and `serialize()` (agent-facing). Agent JSON no longer includes `form`, `key`, `render_hints`, or `_rendered` — eigenforms are self-describing through instructions and affordances. NumberForm affordance now includes integer constraint in instruction text.

**ListForm Expansion + SetForm + KeyValueForm Simplification** (Mar 29, session 001). ListForm: fixed_items (immutable seed items), must_follow ordering constraints (ID-based, static + dynamic), stable topological sort enforcement, transitive cycle detection, inline constraint UI with per-item add dropdown and remove buttons. SetForm: 30th eigenform type, unordered unique collection. KeyValueForm: API simplified to key-based edit/remove, internal IDs hidden from agent. Consistent layout polish: remove buttons on left, pill badges for IDs, aligned columns across all collection forms. Gallery: dedicated Lists tab with 4 use cases.

**OrderedCollection Extraction + TableForm Unification** (Mar 29, session 002). Extracted `OrderedCollection` utility from ListForm — reusable ordering engine (stable IDs, fixed items, must_follow constraints, cycle detection, topological sort). ListForm refactored to delegate to one OC (zero API change). TableForm refactored to wrap two OCs (rows + columns), gaining: move_row_up/down, move_col_left/right with inline arrows, fixed_columns/fixed_rows, row/column ordering constraints. Legacy state auto-migration. AddConstraintAffordance moved to affordances.py for shared use. Inline constraint UI for both axes (row: green pills in control column, column: blue pills in headers). Row controls moved to borderless column outside data grid. BUTTON_GAP constant for consistent button/gap alignment. Gallery: Tables tab with 5 demos (basic, fixed columns, row constraints, column constraints, full-featured). Fixed _current_states() seeding bug for fixed_columns.

**TableForm UI Overhaul + Configuration Panel** (Mar 29, session 003). Comprehensive TableForm rendering redesign. Column headers: pill badge IDs centered between move arrows (3-column grid), editable inputs with ✓ confirm buttons, remove buttons on label row. Row controls: dedicated bordered columns for remove (−), up (▲), down (▼), and prerequisite (☑) — all shaded #f0f0f0. Prerequisite UI split into ☑ button column (custom button-styled select overlay) and "Prerequisites" column (auto-appears when any prereq exists, pills use ID badge style, vertical layout). Horizontal scroll via overflow-x wrapper. Uniform font sizes (removed per-element overrides). Auto-seed one empty row when columns exist. Add_row affordance body includes column key placeholders. box-sizing: content-box on all inline button styles fixes alignment across ListForm and TableForm. Configuration panel above the table with checkbox toggles for auto-chain rows/columns — when enabled, each row/column automatically depends on the previous one, maintained across add/remove/move operations.

**Typed Columns + Constraint UI + SequenceForm + Edit Mode + TableRunner + Workflow Builder** (Mar 29, session 004). TableForm typed columns: fixed_columns accepts Eigenform instances alongside strings. Cell eigenforms use compound scopes (table_key/row_id). RowGroup routing node. fixed_rows now seeds cell data. ListForm constraint UI unified with TableForm (checkbox button overlay, monospace pills). SequenceForm: gated sequential container without auto-advance (intermediate between TabForm and ChainForm). Edit mode infrastructure: editable flag on base Eigenform, pencil icon toggle, label overrides in store, _chrome_rendered for affordance dedup. TextForm edit mode with inline label editor. TableRunner: new Runner category — reads sibling TableForm, presents rows as gated sequential workflow. Only typed columns are executable; text columns provide row labels; ordering constraints become execution gates. Workflow Builder page: 6-tab tool composing 14 eigenform types for designing workflows with stage gates, parallel paths, conditional branches, merge gates, and acceptance criteria. Gallery: SequenceForm in containers tab, TableRunner in tables tab with pre-populated Design/Build/Test source table.

**Theoretical Analysis + Dependency Visibility + HistoryForm + Control Flow Gallery** (Mar 30, session 001). Rigorous examination of eigenform concept prompted by TableRunner introduction. Found: "eigen" (self-contained) was a special case — eroded gradually across ScoreForm, ComputedForm, VisibilityForm, DynamicChoiceForm, SwitchForm, TableRunner. Real invariant: HATEOAS-complete interaction node. Revised eigenform meaning to "identity-preserving under transformation" (eigenvector reading). Further: eigenform is a *program* — state + instruction set (affordances) + halt condition (is_complete). Agent is the runtime. Runners reframe as interpreters. Identified `depends_on` as a shadow dependency graph invisible in the UI — coupling without containment. Implemented `render_dependency_line()`: all sibling-reading eigenforms now render "Depends on: /path/to/sibling" with full URL paths (6 types updated). HistoryForm: new wrapper type with append-only change history, lazy detection on serialize, timeline browsing. Control Flow Gallery page. AuditForm attempted (HistoryForm + mandatory reason per change) — required monkey-patching child's handle(), which was the first inter-eigenform behavior modification. Rejected as architecturally wrong and deleted. Open question: first-class interception mechanism needed in routing layer.

**Control Flow Gallery + Page Builder** (Mar 31, session 001). Control Flow Gallery expanded: SequenceForm demo (3-step gated workflow), Fork/Merge demo (TabForm inside SequenceForm gives parallel-branch-then-merge for free), Routing demo (SwitchForm inside SequenceForm gives conditional branching with state-preserving route switching). Workflow Builder replaced with Page Builder — generic mutable PageForm with type dropdown toolbar, per-eigenform ▲/▼/✕ controls, editable=True on dynamically added eigenforms. PageForm mutable HTML overhauled.

**Reverted bases.py abstraction** (Mar 31, session 002). The 7-class base hierarchy (ScalarForm, SelectionForm, etc.) added 251 lines of indirection without sufficient value. Reverted all engine/ changes from that commit, restoring each form's own _handle() and is_complete. Net -145 lines. Page Builder and Control Flow Gallery preserved.

**Edit mode expansion + RatingForm deletion** (Mar 31, session 003). Full edit mode for TextForm, NumberForm, BooleanForm, ChoiceForm, CheckboxForm. Same-shape principle: edit mode preserves layout, fields become inline editable inputs with `font: inherit` and position-matched margins. Base infrastructure: `effective_instruction`, `set_mode` replacing `toggle_edit`, pencil/play icons. Type-specific config editing via `__config` store pattern (NumberForm, BooleanForm). ChoiceForm/CheckboxForm refactored: child ListForm manages options/items, visible in edit mode via faithful projection. Undo/discard: snapshot-based undo stack with `_push_undo()` before each edit mutation, initial snapshot for discard-all. Child ListForm handle wrapped to push undo on parent. Chrome buttons: undo (↩, conditional), discard (✕ red). RatingForm deleted — replaced with NumberForm(integer=True). 32 eigenform types.

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
| `engine/ordered_collection.py` | OrderedCollection — reusable ordering engine (stable IDs, fixed items, constraints, cycle detection, topological sort) |
| `engine/eigenform.py` | Eigenform base (children, bind, batch, two-tier serialize, to_descriptor, has_data, clear) |
| `engine/textform.py` | TextForm — single free-form string input |
| `engine/checkboxform.py` | CheckboxForm — multi-select with Done confirmation |
| `engine/affordances.py` | Affordance (pure data), render_affordance_html utility, all affordance subclasses, disabled_button |
| `engine/store.py` | JSON file store, one file per page, scoped by eigenform key, delete() for surgical removal, mtime-based file sync |
| `engine/registry.py` | EigenformRegistry (register/lookup/available), from_descriptor(), lazy default with 28 types |
| `engine/pageform.py` | PageForm — persistence boundary, find_eigenform, structural persistence, mutable structure, feedback banner |
| `engine/tabform.py` | TabForm — tabbed container, faithful projection |
| `engine/chainform.py` | ChainForm — sequential wizard with auto-advance + Continue |
| `engine/rubikscubeform.py` | RubiksCubeForm + RotateAffordance — complexity showcase |
| `engine/tableform.py` | TableForm — inline editing, add/remove, batch support, typed columns (RowGroup, compound scopes), fixed_rows cell seeding |
| `engine/stepform.py` | SequenceForm — gated sequential container without auto-advance |
| `engine/tablerunner.py` | TableRunner — executes a TableForm as a gated sequential workflow |
| `engine/historyform.py` | HistoryForm — wraps eigenform with append-only change history, lazy detection, timeline browsing |
| `engine/choiceform.py` | ChoiceForm — single selection via radio buttons |
| `engine/listform.py` | ListForm — ordered list, fixed items, ordering constraints, topological sort |
| `engine/setform.py` | SetForm — unordered unique collection, add/remove by value |
| `engine/multiform.py` | MultiForm — groups FieldDescriptors under single affordance |
| `engine/visibilityform.py` | VisibilityForm — conditional visibility (value, list, or callable) |
| `engine/switchform.py` | SwitchForm — N-way structural selection based on sibling value |
| `engine/scoreform.py` | ScoreForm — read-only grading from answer key |
| `engine/numberform.py` | NumberForm — numeric input with min/max/step/integer, server-side validation |
| `engine/dateform.py` | DateForm — ISO 8601 date/datetime with bounds |
| `engine/booleanform.py` | BooleanForm — binary yes/no toggle |
| `engine/rangeform.py` | RangeForm — slider over continuous range, server-side validation |
| `engine/memoform.py` | MemoForm — multi-line textarea with length constraints |
| `engine/rankform.py` | RankForm — fixed-set item reordering |
| `engine/keyvalueform.py` | KeyValueForm — dynamic key-value pairs |
| `engine/computedform.py` | ComputedForm — derived display from siblings, optional store_result |
| `engine/accordionform.py` | AccordionForm — collapsible sections, faithful projection |
| `engine/validationform.py` | ValidationForm — cross-field rules, pending/pass/fail, blocks completion |
| `engine/dynamicchoiceform.py` | DynamicChoiceForm — options from sibling value, stale detection |
| `engine/actionform.py` | ActionForm — imperative button, preconditions, confirmation, side effects, structural_actions |
| `engine/repeaterform.py` | RepeaterForm + EntryGroup — dynamic repeated structure, compound scopes |
| `engine/groupform.py` | GroupForm — named compositions, parameterizable via subclassing |
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

- **Edit mode for remaining eigenform types** — TextForm, NumberForm, BooleanForm, ChoiceForm, CheckboxForm have full edit mode (label, instruction, config). Remaining types (DateForm, RangeForm, MemoForm, RankForm, etc.) need edit mode added.
- **First-class interception mechanism** — containers need `handle_child_action(child, body)` so wrappers can gate child mutations without monkey-patching. Required for AuditForm-style patterns. Lead is thinking through approaches.
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
