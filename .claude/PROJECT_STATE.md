# Project State

*Last updated: Session-2026-04-19-004 (2026-04-20)*

---

## 1. Where We Are Now

**Theme system refactor + six new themes (Session-2026-04-19-004).** Theme system promoted from "CSS overlay over one fixed rendering" to "full rendering-pipeline hook — themes can rewrite how data is visualized, not just how it looks."

*Infrastructure:* Retired the `operator-view` / `supervisor-view` distinction entirely. New model: cookie `c-theme` = one of `{default, sleek, debug, liquid-glass, paper, chat, task}`; `<body data-theme="X">` set server-side (no FOUC); footer `<select>` for switching. Thread-safe theme state via `ContextVar`. `.c-container` class added to container wrappers by `engine/component.py::render()` — collapses per-form CSS blocks. `engine/component.py` now passes `data=data` to `wrapper.html` so themes can introspect children; `engine/page.py::_serialize_full()` no longer strips `form`/`key` on children (themes read these to pick per-type idioms). `style.css` base is minimal; each theme competes on equal footing at `body[data-theme="X"]` scope.

*Six themes built in order of sophistication:*
- **debug** — the former supervisor view: full borders, visible JSON pane, all chrome exposed (`app/static/debug.css`).
- **liquid-glass** — Apple-inspired frosted-glass cards over pastel-gradient body; CSS-only (zero template overrides); 368 lines of CSS proved the refactor works.
- **paper** — document-style serif typography; innovation is **completed data forms collapse into inline prose** while incomplete stay as full forms; a filled page reads like a filled-out paper form.
- **chat** — conversational dialogue; each component is a Q&A turn with app-avatar ✨ question-bubble and user-avatar "You" reply-bubble; ChoiceForm/BooleanForm render as suggestion chips; CheckboxForm as multi-chip with `--on` state; InfoDisplay as centered "system" message; containers are frosted panels with form-type badges (`tabs`, `group`, etc.). Green ✓ badge on answered bubbles.
- **task** — **theatrical stage with per-type container idioms**. Each container TYPE gets its own visual shape, not a variant: **Tabs → Marquee Carousel** (active tab scaled 1.15 with gold glow, dim flanking thumbnails); **Sequence → Milestone Trail** (circular stations connected by gradient path, active station is pulsing 56px gold disc); **Group → Huddle** (irregular border-radius organic blob, tri-color translucent gradient, off-axis highlight). Data forms as **Performers**: active = spotlit frame with cone-of-light pseudo-element + "Your turn" gold tag; done = stepped-back teal-bordered frame with mint-teal plaque + edit link; info = violet-left-bar "Aside" — "whispered from the wings." Deep indigo canvas with radial spotlights, 3em italic gold-gradient title, pulsing "Act N of M" ribbon. Button text: "Take the stage →"; placeholders: "Speak your line…".

*Bug fix:* Custom theme templates (`paper`, `chat`) initially emitted a hidden `<input name="action" value="set">` alongside `<input name="value">`. Engine's action registry dispatches `None → _do_set` (no action key means set); `"set"` wasn't in `_actions`, so POSTs silently fell through to `_handle()` no-op — values weren't saving from those themes until user submitted from a theme using the default template. Fixed by removing the hidden inputs in 4 templates (chat + paper, text + number).

*Files retired:* `body.operator-view` / `body.supervisor-view` selectors (348 in sleek.css), Debug Mode toggle JS, `_CONTAINER_FORMS` duplication in CSS, `.ch-section` dashed divider.

*Not covered by bespoke templates (fall back to default inside each theme's wrapper):* TableForm, TableRunner, ListForm, SetForm, DictionaryForm, MultiForm, Repeater, Switch, Visibility, Historizer, Validation, RubiksCubeApp. Edit modes fall back across all new themes.

**UI polish pass (Session-2026-04-19-003).** Four improvements: (1) **Inspect Data view fix** — right-click > Data was returning `{}` for leaf components because it looked up `storeData[key]` but leaf data lives under `storeData[parentKey]`; fix extracts scope from URL path. (2) **TextForm rendering consistency** — standardized across Debug Mode and Sleek Theme: "Value: \<value\>" read-only display followed by blank input field; removed pre-populated values, ghost text placeholders, and the styled blue-accent value strip in sleek. (3) **Universal ghost Clear buttons** — all Clear buttons in sleek theme now render as ghost buttons (transparent bg, gray text, subtle border) via `c-btn-clear` class on `_render_button()`, matching TextForm's style. (4) **Live form tooltips** — POST tooltips on form submit buttons now update dynamically as the user types via `_cSyncFormTooltip()` and an `input` event listener; applies universally to all `data-c-submit` forms.

**Right-click inspect panel (Session-2026-04-19-002).** Chrome DevTools-style component inspector accessible via right-click context menu on any component. Establishes the general pattern: right-click actions are human-only chrome — no affordances, no parity tests, invisible to agents. Context menu: Inspect (full page JSON tree with target component expanded/highlighted), Affordances (component's affordances array), Data (raw store data via new `GET /pages/{id}/_store` endpoint). Collapsible JSON tree viewer with syntax coloring (VS Code dark palette), inline previews, target matching via affordance URL propagation. Right-side drawer with resize handle, toolbar (Expand/Collapse/All Affs/Labels). Live refresh: `_cSwap` fires `c-page-updated` CustomEvent, inspect panel re-fetches current view on every page update (user POSTs + SSE), preserving scroll position. Also: `app.json.sort_keys = False` for canonical key order in all JSON responses, `data-url` attribute on all component wrapper divs.

**Navigation split into Tabs/Sequence/Accordion (Session-2026-04-19-001).** The unified `Navigation` class with a `mode` field has been split into three concrete subclasses: `Tabs` (free access, one visible), `Sequence` (gated, in order; `auto_advance=True` replaces old chain mode), and `Accordion` (free access, all visible with expand/collapse). `Navigation` remains as the shared base class but is not registered directly. All 6 page definitions migrated, CSS selectors updated, mutable page palette shows three entries instead of one. Mode switching removed from edit mode — the type *is* the mode. Auto-key generation in `_add_component` and `_add_step` switched from counter-based (`type-1`) to UUID-based (`type-{8-char-hex}`) to match `Component.__post_init__`.

**Workshop restructured as hub (Session-2026-04-19-001).** `/workshop` is now an index page listing workshop sub-pages as cards. Existing page builder moved to `/workshop/page-builder`. New `/workshop/component-creation` stub created for future Interactive Component Creation workshop. `_WORKSHOPS` registry in routes.py for easy addition. Page builder improvements: instruction field on components, eliminated all UI jumpiness (deferred canvas re-render to focusout, removed entrance animations), fixed Navigation tab switching to show only active tab's child.

**Learning Portal: Miscellaneous Topics section (Session-2026-04-19-001).** New third section on the learn index below Fundamentals and Deep Dives. First topic: "Anatomy of a Component" (`/learn/anatomy`) — annotated SVG diagram of a TextForm with all parts labeled, detailed explanations organized by role (Identity/State/Protocol/Chrome), program analogy (state + instruction set + halt condition).

**Component engine with full site shell and streamlined UX.** The clean-room rebuild on `dev/content-model-unification` now has both the component engine and the complete UI shell ported from main (sidebar nav, Agent Portal, Quality Manual viewer, QMS dashboard, Workspace, Inbox, README page). Next step: build real QMS workflows as component compositions, then merge dev into main.

**Workshop page builder (Session-2026-04-18-005):** New `/workshop` route — standalone interactive canvas for mocking up Razem pages, completely independent of the real engine. Features: drag-and-drop palette (21 component types, 4 groups), dot-grid canvas, live interactive mocks (all inputs functional — text fields, toggles, radios, sliders, checkboxes, lists, sets, dictionaries, tables), per-card completion rings + global completion percentage, slash command palette (Notion-style fuzzy search), connection wiring mode (SVG bezier curves between components), context menu (right-click), properties panel, undo/redo, JSON export. Custom mouse-based drag system (HTML5 drag API's `setDragImage` broken on Windows). Thin-line drop indicators between cards (no layout shift). Independent scroll for palette and canvas. Route in `app/routes.py`, sidebar link in `base.html`.

**Components reference page + Score/DynamicChoiceForm removal + SiblingBind generalization (Session-2026-04-18-004):** Three thematic streams. **(1) Doc alignment pass** — wiki intro got a new ¶4 on impedance mismatch + affordance flotation; README, Framing (added Pass 5 covering action-registry + callable diagnostic + megafile split), and Learning Portal updated; Lesson 1 got real `curl` commands replacing the fake "change Accept in address bar" instruction, actual serialized JSON output captured by binding the example on a temp dir, "When keys matter" section explaining auto-keys with two reasons to use explicit ones, "Extracting children for legibility" section, and a correction that Page keys do NOT appear in URLs (URLs use the 8-char hex instance_id); Lesson 2 rewrote "4. Handle" for registry dispatch. **(2) New `/components` reference page** — taxonomy of every built-in component class with sidebar entry, grouped by category (Data Forms, Containers, Derivations, Imperative, Wrappers, Runners, Apps). Static `_COMPONENT_TAXONOMY` structure in `app/routes.py`, rendered by `app/templates/components_taxonomy.html`. **(3) Class taxonomy shrinkage via generalization** — *Score removed* (redundant with Computation; `grade(answer_key)` and `graded(answer_key, **kwargs)` helpers in new `engine/helpers.py` preserve the declarative ergonomics). *DynamicChoiceForm removed* (redundant with ChoiceForm + `SiblingBind`). New `engine/sibling_bind.py`: a `SiblingBind(sibling_key, fn, *, expects=None, default=None)` wrapper makes any component field reactive. `Component._sibling_refs()` base auto-discovers refs from SiblingBind-valued fields; `Component._resolve_field(name)` is the one call site a subclass migrates when wiring a field as reactive. `NumberForm` (`min_val`, `max_val`, `step`) and `ChoiceForm` (`options`) both wired; new `pages/reactive_demo.py` validates end-to-end (tier-driven bounds, cross-tier stale detection, Clear affordance). Callable-preservation diagnostic extended to auto-flag lost SiblingBinds after seed-mismatch reconciliation. **26 → 24 classes, 31 → 29 registered names. 79/79 tests pass.**

**Framework naming decision (Session-2026-04-17-003):** The general-purpose component/affordance framework — currently conflated with its first intended application under the name "QMS Workflow Engine" — is being renamed to **Razem** (Polish, "together"). The framework has no QMS-specific code; naming it after the QMS is like calling React "Facebook JS." Post-rename: **Razem** = the framework (the submodule, `engine/`, the component protocol, affordances, stores, reconciliation, faithful projection, parity tests); **QMS Workflow Engine** = the application to be built with Razem (not yet implemented — all current `pages/` entries are demos/galleries). Rename queued in Forward Plan for execution before the first real QMS workflow ships.

**Engine quality pass — 3 backlog items completed (Session-2026-04-18-003):** (1) **Callable-preservation diagnostic**: `_callable_fields` tuple on Component subclasses declares callable-only fields; `from_descriptor()` sets `_missing_callables` after fresh construction; `_base_state()` surfaces warnings in serialized output. Applied to Computation, Action, DynamicChoiceForm. (2) **Action-dispatch registry**: `_actions = {}` class attribute maps action names → handler method names; base `handle()` dispatches via `getattr`; 20 component classes migrated, 89 if/elif branches eliminated. `None` key handles forms whose affordance bodies omit `action`. Fixed latent bug where `handle_action()` bypassed the registry for structural actions. (3) **Megafile split**: page.py split 1152→631 via `PageMutationsMixin` (493 lines in `page_mutations.py`); tableform.py split 1248→993 via `TableFormActionsMixin` (270 lines in `tableform_actions.py`). navigation.py at 693 left intact. Wiki intro rewritten with faithful-projection/HATEOAS framing, framework/QMS distinction. 72/72 parity tests pass.

**Wiki article expansion + affordances() + auto-keys (Session-2026-04-18-002):** Wiki article (`/wiki`) expanded with architecture framing paragraph, 4 inline SVG diagrams (request lifecycle, reconciliation, component tree, faithful projection), "The component model" subsection defining what a component is (state + affordances + is_complete = program), mutation boundary documentation, and 6 code/pseudocode examples. `affordances()` promoted to first-class public method on `Component` — returns the complete state-dependent affordance list; `_serialize_full()` now delegates to it instead of building inline. Component `key` field made optional: auto-generates `{form}-{8-char-hex}` via UUID at construction when not provided; explicit `key=` still works unchanged; 8 subclasses updated with `super().__post_init__()`. 72/72 parity tests pass.

**Class taxonomy refactor (Session-2026-04-18-001):** The flat `*Component` suffix replaced with role-specific suffixes across 26 classes. Forms (`*Form`) produce State: TextForm, NumberForm, DateForm, BooleanForm, ChoiceForm, CheckboxForm, MultiForm, ListForm, SetForm, TableForm, DictionaryForm, DynamicChoiceForm. Containers are unsuffixed: Page, Navigation, Group, Repeater, Switch, Visibility. Derivations are standalone nouns: Computation, Score, Validation. Display: InfoDisplay. Imperative: Action. Wrapper: Historizer. App: RubiksCubeApp. Runner: TableRunner (unchanged). Module files renamed to match (`engine/textform.py`, `engine/page.py`, `engine/computation.py`, etc.). The heuristic `form` property (which derived type names via `removesuffix("Component").lower()`) replaced with an explicit `form` class attribute on every subclass — registry type names are now declared, not derived. All registry type names preserved for backwards compatibility with stored data (e.g., `Computation.form = "computed"`, `Historizer.form = "history"`). 91 files updated (25 renames + 42 Python + 49 HTML/MD). 72/72 parity tests pass.

**Eigenform → Component rename (Session-2026-04-17-002):** The base class was renamed from `Eigenform` to `Component`, and all 25 concrete subclasses from `*Form` to `*Component`. Propagated through module filenames, the `eigenforms/` template directory (now `components/`), the `eigenform.js` static asset (now `component.js`), CSS prefixes (`ef-` → `c-`), DOM data attributes (`data-ef-` → `data-c-`), and action-protocol names (`add_eigenform` → `add_component`, etc.). The `*Component` suffix was subsequently replaced by the class taxonomy refactor above. 72/72 parity tests pass.

**Learning Portal (Session-2026-04-17-002):** New `/learn` route with eight progressive tutorial lessons covering the engine, grouped into **Fundamentals** (1–5: Hello Component, The Core Loop, Where Data Lives, Composing Pages, Humans and Agents) and **Deep Dives** (6–8: Affordances/Rendering/Parity, Reconciliation and the Descriptor, Mutation Mechanics). Each lesson has a clear learning objective, concrete code examples, pointers to live demo pages, "Try it" callouts, a "What you learned" takeaways block, and prev/next navigation. Shared chrome (breadcrumb, header, nav buttons, code/callout styling) factored into `app/templates/learn/_lesson_base.html`. Landing page presents a lesson-card grid with group headers and pointers to `/framing`, `/readme`, `/portal` Component Gallery as follow-on reference material. Routes: `/learn` + `/learn/<slug>` via `_LEARN_LESSONS` dict in `app/routes.py`. Sidebar link added (pen icon). All 9 pages return 200; parity tests unaffected.

**Wiki page (Session-2026-04-17-002, expanded Session-2026-04-18-002):** Single-page hypothetical Wikipedia-style article at `/wiki`. Wikipedia visual idiom: Linux Libertine / Georgia serif titles with horizontal rules, infobox on right with alternating blue section bands, TOC box, two-column footnote references, categories footer with pill-style tag links. Content sections: History (YAML prototype → clean-room rebuild → framing passes → rename), Architecture (framing intro, component model subsection defining the program analogy + mutation boundary, core loop, three trees, HATEOAS), Features (component types, faithful projection, affordance flotation, mutable pages, error boundaries), Design philosophy, Terminology definition list, Comparison matrix vs React / Phoenix LiveView / Svelte, Limitations (pulled from `/deepdive`), See also, References, External links. All 12 references point at real in-project docs — no fabricated reception. Session-002 added: 4 inline SVG diagrams (request lifecycle, reconciliation, component tree, faithful projection), 6 code/pseudocode examples, component model section, mutation boundary documentation, affordances() as first-class operation. Sidebar link added (fleur-de-lis icon).

**Fractal complexity plan is complete.** All five phases (Switch → Registry → Structural Persistence → Structural Actions → Self-Modifying Pages) are implemented and tested.

**Morphdom integration (Session-2026-04-16-003):** Vendored `morphdom-umd.min.js` v2.7.4 (12KB) into `app/static/`, included in `page.html` before `component.js`. New `_cSwap(html)` helper in `component.js` calls morphdom in place of the prior innerHTML swap, with `onBeforeElUpdated` hook that skips morphing the currently-focused INPUT/TEXTAREA/SELECT so users mid-typing aren't disturbed. Both POST-driven swaps (`_cPost`) and SSE-driven reloads now go through `_cSwap`. Browser-side wins: window scroll, nested-scroll positions, `<details>` state, CSS transitions, input focus, caret position, in-progress text all preserved across POSTs (the prior explicit scrollY save/restore kludge becomes unnecessary on the morphdom path). Server-side unchanged. Graceful fallback to innerHTML+scrollY if morphdom isn't loaded. Wire bandwidth unchanged (still full re-rendered subtree per POST) — payload reduction would be a separate, server-side change.

**Deep Dive page (Session-2026-04-16-003):** Added `/deepdive` — a self-referential page where the engine analyzes itself (rendered by itself). Composed of one Navigation in tabs mode wrapping seven InfoComponents covering: literal characterization, lifecycle, what works, aspiration, the ambition-vs-delivery delta, code-quality findings, and prioritized recommendations. Page is bound directly (fixed scope `deepdive`, url_prefix `/deepdive`) — no InstanceRegistry entry. Routes `/deepdive` and `/deepdive/<path>` in `app/routes.py`; sidebar link in `app/templates/base.html`. Audit findings highlighted: action dispatch is unstructured (88 `if action == ...` across 20 files; Page._handle has 11 elif branches), sibling references are string-typed without validation, `_set_my_config` checks names but not value types, no concurrency model (last-write-wins), mutable-structure builder is sleek-theme-only. Recommended next passes: action registry, architecture doc, typed SiblingRef, config-value validation, megafile splits.

**Stateless-server overrides refactor (Session-2026-04-16-003):** Eliminated all parallel-state sidecar keys (`__config`, `__label`, `__instruction`) that competed with the structure descriptor. The on-disk `__structure` in the parent container is now the single source of truth for every per-child seed-time field (label, instruction, mode, multiline, min_length, etc.). Base helpers `_get_my_descriptor` / `_set_my_field` / `_set_my_config` / `_apply_descriptor` formalize the mutation API. `from_descriptor` deepcopies the matched seed and applies the descriptor's scalars before returning, so the descriptor wins over seed defaults — no need for runtime override layers. Page `__structure` was moved from scope=binding-scope to scope=self.key to align with Navigation/Group convention so children can locate their entry via `self._scope`. Containers now write `__structure` unconditionally (no `editable=True` gate) so children's descriptor entries always exist for `_set_my_*`. Legacy data is migrated automatically on bind: `_migrate_legacy_overrides` folds any leftover `__config`/`__label`/`__instruction` sidecars into the descriptor and deletes them. Trivial `effective_label`/`effective_instruction` shims removed; call sites read `self.label`/`self.instruction` directly. Per-form sweep across textcomponent/numbercomponent/datecomponent/booleancomponent/dictionarycomponent/multicomponent/listcomponent/navigationcomponent.

**Navigation mode switcher UX (Session-2026-04-16-003):** Replaced the four generic `Mode: X` blue buttons with a proper segmented pill control inside the edit toolbar. Active mode = blue accent (`#1a2a3c`/`#3b82f6`/`#60a5fa`, semibold); inactive = neutral gray pill with hover lift. Mode affordances marked `_chrome_rendered=True`; the segmented control is rendered directly in `sleek/navigation.html` from `self.mode`.

**Schematic canvas refinement (Session-2026-04-16-002):** Tree guide lines now connect each container header to its children (L-shaped `::before` at the row-center of each child + continuation `::after` spine for non-last children). Outer box borders on leaf and container blocks removed — only the left accent stripe remains, reading as the node's identity; the tree guide itself carries the "belongs to this parent" signal. Sharp rectangles throughout (no block border-radius) for schematic feel.

**Store resilience (Session-2026-04-16-002):** Fixed recurring `JSONDecodeError` on 0-byte JSON files caused by Windows `write_text` truncate-then-write races during Flask dev-reloader restarts. Both `Store._save` and `InstanceRegistry._save` now use atomic write-temp-then-rename. Both `_load` paths tolerate empty files gracefully.

**Page Builder UI (Session-2026-04-14-004):** Mutable pages have an inline schematic editor between the page header and the rendered components. Two-panel layout: type palette (left, 220px, draggable items) + schematic canvas (right, recursive block diagram showing nesting). Leaf blocks are compact bars; container blocks visually wrap their children. Drag from palette to canvas inserts at position; drag between blocks reorders; drag into a container's child zone reparents. Ctrl+click for multi-select grouping. The actual rendered page appears below the builder — same layout as non-mutable pages. Server-side `add_component` now accepts `position` for numeric index insertion.

**Sleek theme UX polish (Session-2026-04-14-003):** One-click component creation (no key/label required), auto-generated keys (`type-N`) and labels, container drop-target fix for empty groups, eject-from-group button on nested tiles, drag-out-of-group support.

**What's running now:** Flask app at `http://127.0.0.1:5000` with 18 pages:
- **page-1**: TextForm + TextForm + CheckboxForm (basic components)
- **page-2**: TabForm with 3 tabs (Document Title, Scope, Impact Areas)
- **page-3**: RubiksCubeApp (arbitrarily complex component, conditional affordances)
- **page-4**: ChainForm wizard (4-step sequential form with auto-advance)
- **example-table**: TableForm (dynamic columns, stable row IDs, agent-reviewed API)
- **page-6**: MultiForm + ChoiceForm + CheckboxForm + 2x ListForm (change request form)
- **math-test**: TextForm + ChoiceForm + CheckboxForm + TabForm (6-tab scavenger hunt) + ChainForm (4-clue chain)
- **upgraded-math-test**: All questions wrapped in outer ChainForm (one at a time)
- **visibility-experiments**: ChoiceForm controlling Visibility children (Simple/Advanced/Expert)
- **quiz-portal**: 3 quizzes (Geography/Science/History) in nested TabForms, Score grading per quiz
- **vendor-assessment**: Vendor Qualification Assessment composing all 23+ component types
- **weird-experiments**: Playground exercising Validation, DynamicChoiceForm, Action, Repeater
- **switch-demo**: Switch with ticket type driving BugReport/FeatureRequest/Question compositions
- **mutable-demo**: Mutable structure page — add/remove/reorder components at runtime
- **survey-builder**: Self-modifying page — Action generates questions that materialize from registry
- **component-gallery**: Interactive tutorial covering all 33 component types across 10 tabbed sections
- **control-flow-gallery**: Control flow demos (SequenceForm, Fork/Merge, Routing, Historizer)
- **page-builder**: Mutable page for composing component structures from the registry, with embedded Component Reference Menu
- **component-reference**: Component Reference Menu — type documentation for agents (5-tab reference with Overview, Data, Containers, Reactive, Special)

**Component architecture** — 24 component classes (post Score/DynamicChoiceForm removal; earlier consolidations include RankForm→ListForm, MemoForm→TextForm, RangeForm→NumberForm, TabForm+ChainForm+SequenceForm+AccordionForm→Navigation, KeyValueForm→DictionaryForm):

Data forms:
- `TextForm`: free-form string input. Single-line by default; `multiline=True` for textarea. Optional `min_length`/`max_length` validation. Complete when non-empty (and meets min_length if set).
- `CheckboxForm`: multi-select with N/A mode. Complete when any checked or N/A.
- `ChoiceForm`: single selection via radio buttons. Complete when valid option selected.
- `MultiForm`: groups FieldDescriptors under single affordance. Complete when all fields filled.
- `ListForm`: ordered list with add/edit/remove/reorder + N/A. Fixed items, ordering constraints (static + dynamic), topological sort enforcement. Complete when items > 0 or N/A.
- `SetForm`: unordered collection of unique items. Add/remove by value, duplicates rejected. Complete when non-empty.
- `TableForm`: dynamic columns + rows with stable IDs. Inline editing for cells, headers, add/remove. Typed columns: fixed_columns accepts Component instances, cells become bound components with compound scopes and path-based routing.
- `NumberForm`: numeric input with min/max/step constraint. `slider=True` for range slider UI with optional `unit` label. Complete when not None.
- `DateForm`: ISO 8601 date or datetime with optional bounds. Complete when not None.
- `BooleanForm`: binary yes/no toggle with custom labels. Complete when not None.
- `DictionaryForm`: dynamic key-value pairs (renamed from KeyValueForm). Edit/remove by key (not internal ID). Key rename via new_key. Complete when at least one entry with key+value.
- `InfoDisplay`: read-only text display, no interaction affordances, always complete. Edit mode embeds a multiline TextForm for content editing. `text` accepts `str | dict` — dict auto-converts to "key: value" lines on bind.

Container forms:
- `Page`: top-level container with Reset Page (recursive clear). Persistence boundary. Optional mutable_structure for Phase D/E. Feedback banner for action results.
- `Tabs`: free access, one child visible at a time. Classic tabbed interface.
- `Sequence`: gated access, in order. `auto_advance=True` for automatic progression (replaces old chain mode), `False` (default) for manual Back/Next. Faithful projection.
- `Accordion`: free access, all children visible with expand/collapse. Collapsed sections omitted from output (faithful projection).
- `Visibility`: wraps child with conditional visibility. Supports value, list, or callable predicates.
- `Group`: named container for reusable compositions. Supports parameterization via subclassing.
- `Repeater`: stamps template components per dynamic entry. Compound scopes, stable IDs, add/remove.
- `Switch`: selects between named alternative subtrees based on sibling value. Faithful projection.

Sibling-reading forms:
- `Computation`: read-only derived display from arbitrary compute function over sibling values. Optional store_result for cross-component dependencies. `engine/helpers.py::graded(answer_key, **kwargs)` factory constructs a Computation preconfigured for answer-key quiz grading (replaces the former `Score` class).
- `Validation`: cross-field validation rules. Pending/pass/fail. Can block page completion.

Imperative:
- `Action`: imperative button with preconditions, confirmation, side effects. Can return structural_actions for Phase E.

Reactive fields (SiblingBind):
- Any component field may hold a `SiblingBind(sibling_key, fn)` in place of a literal — the field resolves from the referenced sibling's current value at serialize time. Replaces what other frameworks expose as per-type `Dynamic*` variants. Currently wired on `ChoiceForm.options` (replaces the former `DynamicChoiceForm`) and `NumberForm`'s `min_val`/`max_val`/`step`. Stale detection is type-local: ChoiceForm flags a stored value missing from resolved options (plus a Clear affordance); NumberForm flags a stored value outside resolved bounds.

Wrapper forms:
- `Historizer`: wraps a component with append-only change history. Lazy detection on serialize — compares child state to last snapshot, appends if different. Timeline browsing with read-only historical views. History is never editable or clearable.

Runner forms:
- `TableRunner`: reads a sibling TableForm and presents its rows as a gated sequential workflow. Only typed columns are executable; text columns provide row labels. Row ordering constraints become execution gates.

Showcase:
- `RubiksCubeApp`: full Rubik's Cube. Conditional affordances based on solved state.

**Infrastructure (Phases B-E):**
- **Component Type Registry** (`engine/registry.py`): explicit mapping of type names to classes. 29 registered names (24 classes + 5 aliases for Navigation modes and the DictionaryForm/keyvalue alias). Custom types register under their own names.
- **Structural Persistence**: `to_descriptor()` on all types serializes tree structure. `from_descriptor()` reconstructs from descriptors + seed. Page stores `__structure` in the store.
- **Structural Actions**: `mutable_structure=True` pages support add/remove/move/rebuild_from_seed. Surgical data cleanup on removal.
- **Self-Modifying Pages**: Action can return `structural_actions` that Page applies, reshaping the page in response to user interaction.

**Key design patterns:**
- **children property**: base Component returns []. Containers override. Enables generic traversal.
- **Unified bind()**: base bind() deepcopies + calls _bind_children(). Containers override _bind_children() only.
- **Page is the persistence boundary**: Page.bind() takes data_dir and creates its own Store; children inherit it
- **Scope = parent key**: containers pass scope=self.key when binding children. Siblings share scope.
- **Batch actions**: handle() checks for {"action": "batch", "actions": [...]}. Subclasses implement _handle().
- **Universal clear**: base serialize() appends Clear affordance when has_data is True. base handle() intercepts {"action": "clear"}.
- **Base helpers**: `_base_state()` returns common state fields; `_error(msg, *, action, body)` eliminates per-file error helpers; `render_inline_button()` renders delegated action buttons.
- **First-class affordances()**: public `affordances()` method on Component returns the complete state-dependent action list. `get_affordances()` is the subclass hook for type-specific affordances; base `affordances()` adds Clear, Edit/Execute/Undo/Discard, and Batch. `_serialize_full()` delegates to `affordances()`.
- **Auto-generated keys**: `key` is optional on all components. When omitted, auto-generates `{form}-{8-char-hex}` via UUID at construction. Generate-once: stable across deepcopy/bind. Explicit `key=` required only for `depends_on` targets.
- **Affordance body templates**: fillable placeholders (`<value>`, `<true | false>`) + per-affordance instructions
- **is_complete**: required on all components (NotImplementedError). Green border when complete, gray when incomplete.
- **Conditional affordances**: affordance lists change based on state (Rubik's solved/unsolved, CheckboxForm normal/N/A mode)
- **Faithful projection**: TabForm/ChainForm/AccordionForm/Switch hide non-visible components from both JSON and HTML. HTML has no browser-side validation — server is sole authority.
- **Structured errors**: error message + failed_action echoed in response, valid alternatives listed
- **Feedback banner**: Page captures action results as one-shot feedback (success/error), rendered as colored banner, visible in both JSON and HTML
- **Content negotiation**: single URL serves JSON (default) or HTML (when Accept: text/html). No `/view` suffix.
- **Path-based component access**: URLs mirror containment hierarchy (e.g., `/pages/page-2/tabs/title`)
- **RESTful API**: GET /pages/{key} → page, GET /pages/{key}/{path} → component, POST /pages/{key} → page action, POST /pages/{key}/{path} → component mutation
- **Two-tier serialization**: `_serialize_full()` produces internal dict (with form, key, render_hints) for HTML rendering. `serialize()` strips agent-noise fields. render() uses `_serialize_full()` for HTML, `serialize()` for "See JSON" button. Containers override `_serialize_full()`.
- **Jinja2 templates**: All components render via Jinja2 templates in `app/templates/components/`. `render_from_data()` calls `render_template()` with serialized state + component instance. Shared `_edit_header.html` partial replaces 6 duplicated edit-mode label/instruction forms. `engine/templates.py` provides standalone Jinja2 env with `render_aff()`, `render_btn()`, `render_dep_line()`, CSS constants, `tojson` filter. `render_template()` post-processes output to collapse 3+ consecutive newlines (eliminates blank lines from false conditionals). Environment uses `trim_blocks=True` and `lstrip_blocks=True`.
- **Event delegation**: Zero inline JavaScript in Python. All actions use `data-c-post`/`data-c-submit`/`data-c-change` attributes. Single global `app/static/component.js` (~60 lines) handles fetch+reload. Eliminates the XSS class structurally — one escaping context (HTML `escape()`) instead of three (Python/HTML/JS).
- **CSS extraction**: `app/static/style.css` with `ef-` prefixed semantic classes. `CSS_CONFIRM`/`CSS_REMOVE`/`CSS_ARROW` class constants replace inline style strings. ~40% of inline styles extracted.
- **Parity test**: `tests/test_parity.py` verifies every affordance URL in `serialize()` appears as `data-c-*` attribute in `render()` for all 18 pages. Replaces runtime RuntimeError with CI-time enforcement (shift-left). 20 tests, all passing.
- **Event delegation**: All interactive elements use `data-c-*` attributes. Single global `component.js` (~75 lines) handles fetch+swap. Scroll position preserved via explicit `scrollY` save/restore. SSE handler debounced 500ms after same-tab POSTs to prevent redundant swaps.
- **View selector dropdown**: 2-option dropdown (Human View, JSON) on every component. Agents use JSON via content negotiation (`Accept: application/json`). Hidden by default in CSS; only the `debug` theme reveals it.
- **Theme infrastructure**: Themes are selected via the `c-theme` cookie and applied by `before_request` → `engine/templates.set_theme()`. Theme state is held in a `ContextVar` (thread-safe under `threaded=True`). `render_template()` tries `{theme}/{template_name}` first, falls back to the default template. `<body data-theme="X">` is server-rendered (no FOUC). `THEME_NAMES` + `THEME_CSS` + `DEFAULT_THEME` in `app/routes.py`; footer `<select>` for switching. Seven themes shipped (default, sleek, debug, liquid-glass, paper, chat, task). Retired the `operator-view`/`supervisor-view` distinction entirely — model is now `data + theme = output`.
- **Theme-aware wrapper**: `engine/component.py::render()` delegates to `wrapper.html` with context: `classes`, `form`, `key`, `uid`, `label`, `instruction`, `editable`, `edit_mode`, `undo_count`, `url`, `inner`, `json_str`, `is_container`, `data` (full `_serialize_full()` output — themes introspect child state for progress bars, per-type idioms, etc.). `.c-container` class appended to container wrappers so per-form CSS selectors can collapse. `_CONTAINER_FORMS` set identifies container types. `Page._serialize_full()` preserves `form`/`key` on children so themes can dispatch per-type.
- **Sleek theme**: Dark UI inspired by VS Code / GitHub Dark Dimmed. `sleek.css` with navy palette (#1e2a3a page, #363b42 cards, #22272e titlebar). Blue accent (#2563eb/#3b82f6/#60a5fa), red focus (#ff6b6b), amber chrome (#d29922). Card-based data components with black borders and always-visible titlebars; containers transparent with 16px vertical spacing. Navigation layout: Page > Navigation = vertical sidebar (#1e1e1e bar, #2b3035 content), all others = horizontal tabs (#1e1e1e bar, #424850 content matching Group). Navigation titlebar always visible (chrome conditional on editable). Titlebar bordered (#555d66 top/sides, rounded corners). Instruction region between titlebar and nav bar (#1e1e1e background, #444 top separator). Horizontal tabs: subtle #444 border on top/sides with rounded corners. Vertical sidebar tabs: #444 bottom separators, top border on nav bar. Group: label bar with inline chrome, #424850 content panel, full-width content. No nesting-context special cases (Group dissolve removed). Page padding 12% left/right. Page separator below header.
- **LNARF compliance**: JSON is canonical, HTML is faithful projection (verified by parity test), view selector dropdown is human-only (exempt)
- **HATEOAS**: every component carries affordances, POST returns full page state
- **SSE**: `/pages/{key}/stream` pushes updates on POST
- **Stateless server**: Server holds no components or pages in memory between requests. `discover_pages()` returns unbound seed definitions at startup; `bind_page()` produces a transient bound page per request from seed + store. Server is a pure function: `(seed + store + request) → response`. SSE subscriber registry is connection state only (queues, not components).
- **Instance spawning**: Page seeds are templates. Users spawn named instances of any seed type via `POST /instances`. Multiple instances of the same type coexist. `InstanceRegistry` (`app/registry.py`) wraps `data/instances.json` — tracks instance ID, type, label, created_at. Instance IDs are 8-character hex UUIDs (`uuid.uuid4().hex[:8]`) — counter-based IDs were replaced on Apr 13. `POST /instances/<id>/delete` removes instance + data file. Index page is a launcher: seed catalog with "New Page" buttons + instance list with open/delete. Auto-migration adopts legacy `data/{seed_key}.json` files as instances on startup. Instance label propagated to bound page per-request.
- **Config validation**: `_add_component()` validates config keys against type's dataclass fields before persisting. Invalid config returns structured error with valid fields. `validate_config()` in registry.py.
- **Resilient bind**: `bind()` and `_rebuild()` catch reconstruction failures from corrupt `__structure`, fall back to seed. Mutable page reset clears structure entirely.
- **Type registry**: `GET /types` returns config schema per type (field names, types, optional flag). `describe_types()` in registry.py introspects dataclass fields.
- **Compact responses**: Child POST returns targeted component state, not full page. `GET /pages/{id}?depth=shallow` returns labels + completion only. Mutable page affordances collapsed from O(N) to O(1) parameterized remove/move.
- **Affordance flotation**: Separable affordances (Clear, Edit, Batch) float from components at any nesting depth to Page level during agent-facing serialization. Affordances tagged with `_floatable` merge key in `_serialize_full()`. `_collect_floatable()` recursively walks `component`, `components`, `sections` keys. Page groups by merge key and emits parameterized compound affordances with structured `targets` dict (full URL → label). Children retain only type-specific affordances. HTML rendering unaffected (flotation is agent-tier only). ~61% reduction in affordance blocks on flat pages; deeply nested pages (component-gallery) also benefit.
- **Navigation affordance collapse (O(N)→O(1))**: Container navigation affordances (tab switch, section toggle, step jump) collapsed from one-per-child to a single parameterized affordance with an options dict (`tabs`, `sections`, or `steps` mapping key→label). Applies to Navigation (all modes), TableRunner. HTML templates render navigation buttons directly from context data via `render_btn()`. `SwitchTabAffordance` and `ToggleSectionAffordance` deleted.
- **Embedded Page**: Page.bind() accepts both `Path` (top-level) and `Store` (embedded child). Embedded pages derive `data_dir` from parent store path, create independent Store files at `{parent_scope}__{child_key}.json`, and nest URL prefix under parent. Full routing support via `find_component` path traversal. Enables reuse of page seeds across standalone and embedded contexts.
- **Page definitions**: one file per page in `pages/` directory, auto-discovered. Key from definition. Seeds are templates — define page types, not page instances.
- **Store file sync**: Store checks file mtime on every access. External deletes clear cache; external edits reload.
- **Computation ordering**: when store_result=True, must appear before Visibility that depends on its result (serialization is sequential).
- **Named compositions**: Group enables reusable, parameterized component groups via subclassing. Subclass gets own form type identity.
- **Compound scopes**: Repeater uses `key/entry_id` scopes. Store treats scope as opaque string, so nesting works naturally.
- **Structural descriptors**: to_descriptor() auto-extracts serializable config. Containers add children. from_descriptor() reconstructs with seed for callables.
- **Seed preservation**: Page._seed holds unbound components for callable matching during _rebuild().
- **ListForm constraints**: ID-based ordering constraints (static must_follow + dynamic add/remove). Stable topological sort enforcement. Transitive cycle detection. Inline constraint UI per item.
- **OrderedCollection**: Reusable ordering engine extracted from ListForm. Manages stable IDs, fixed items, must_follow constraints, cycle detection, topological sort. ListForm wraps one (items). TableForm wraps two (rows + columns).
- **TableForm reordering**: move_row_up/down, move_col_left/right with inline arrow buttons. Fixed rows/columns. Row/column ordering constraints. Legacy state auto-migration. Inline constraint UI (row: green pills, column: blue pills). Row controls in borderless column outside data grid.
- **TableForm typed columns**: fixed_columns accepts `str | Component`. Component entries become typed columns — each cell is a bound component with compound scope (`table_key/row_id`), path-based URL routing (`table/row_id/col_id`), and RowGroup routing nodes. set_cell guards typed columns; set_row skips them. Serialization includes nested component state. is_complete checks typed cell components.
- **TableForm fixed_rows**: seeds row metadata AND cell data on first access. Enables pre-populated table definitions.
- **Edit mode infrastructure**: `editable: bool = False` on base Component. `set_mode` affordance with `edit`/`execute` modes. Pencil icon (✏) enters edit mode, play icon (▶) returns to execution. Edit mode: dashed border on container, label/instruction become inline editable inputs with `font: inherit` and position-matched margins. **All seed-time field overrides (label, instruction, mode, multiline, min_length, etc.) live in the parent container's `__structure` descriptor entry — the on-disk single source of truth.** Mutations flow through base helpers `_set_my_field` (top-level fields) and `_set_my_config` (config dict fields), which update the descriptor in place AND `setattr` on self so the runtime instance reflects the change before next bind. `from_descriptor` deepcopies the matched seed and applies the descriptor's scalars before returning. `_chrome_rendered` flag prevents duplicate affordance rendering. `_get_edit_affordances()` extensible by subclasses. Type-specific config (NumberForm min/max/step/slider/unit, BooleanForm true/false labels, TextForm multiline/min_length/max_length, DateForm include_time/min_date/max_date, DictionaryForm key_label/value_label, MultiForm fields list) all persisted in the descriptor's `config` dict. ChoiceForm/CheckboxForm embed a child ListForm for options/items editing — visible in edit mode (faithful projection), routable via standard children. Undo stack (`{key}.__undo`) with snapshot-based restore; initial snapshot (`{key}.__snapshot`) for discard. Snapshot captures self's descriptor entry; restore writes it back and re-applies. Chrome buttons: ↩ undo (conditional on depth > 0), ✕ discard (red, restores snapshot and exits edit mode). Child ListForm handle wrapped to push undo on parent. ListForm edit mode: `allow_constraints` toggle, fixed item toggle (📌 pin per item), fixed constraint toggle (📌 pin per constraint pill). `relax_fixed` on OrderedCollection allows editing/removing fixed items in edit mode. Static constraints demotable via `fixed: false` stored entries; `effective_must_follow` excludes demoted statics from enforcement; `all_must_follow` includes them for display. Demoted constraints visible in both modes (gray unpinned pill), removable in execution mode via `not is_effectively_fixed` check. JSON serialization includes demoted constraints with `"active": false`. `remove_constraint` on static constraints always demotes (never strips demotion entry). All item/constraint mutations push undo; snapshot includes item value for full discard. Legacy `__config`/`__label`/`__instruction` sidecar entries auto-migrated into the descriptor on first bind via `_migrate_legacy_overrides`.
- **Edit/execution mode distinction**: TableForm structural operations (add/remove/rename columns, reorder, constraints) are edit-mode activities. Execution mode = structure frozen, only typed cell components are interactive. Text columns are authoring-only. TableRunner enforces this distinction.
- **BUTTON_GAP**: shared constant in affordances.py. Transparent border matches button box height. Used by tablecomponent, listcomponent, rankform, keyvalueform.
- **Dependency visibility**: `render_dependency_line()` in component.py. All sibling-reading components render "Depends on: /path/to/sibling" with full URL paths. Applied to Switch, Visibility, Computation, Validation (per-rule), Action, and any component with a SiblingBind-valued field. Makes the shadow dependency graph visible in the UI.
- **Mutable page UI**: Two-layer editing interface. (1) **Add Component**: card-based type picker with 5 collapsible categories, per-type Unicode icons, category accent colors, radio-as-card selection. `TYPE_CATALOG` in registry.py; `AddComponentAffordance` with structured `type_catalog` in agent JSON. (2) **Structural editor**: tile-based page blueprint showing component tree with drag-and-drop reorder (including intra-container), reparent (drag onto container), multi-select grouping, ungrouping, and nested removal. Recursive tree helpers (`_pluck_from_tree`, `_find_siblings_list`, `_sync_container_structure`, etc.) enable all operations at any nesting depth. Per-component margin controls (▲/▼/🔓/🗑) retained alongside structural editor.
- **Container edit mode**: Container components (Group, Navigation) support edit mode with structural operations: add/remove/reorder children, toggle child editability (✏ pencil toggle per child). Structural persistence via `__structure` in child scope. Undo/discard via `Store.snapshot_scope`/`restore_scope`. `_reconstruct` applies `editable` from descriptor after seed matching. All containers delegate to `super()._serialize_full()` for base edit mode infrastructure. Edit mode rendering: inline label/instruction editors, type/key/label add toolbar, per-child control bars. Navigation (tab switch, step focus, section toggle) works in both modes. Editability is a parent-controlled property — containers toggle child `editable` via structural descriptors.

**Terminology:**
- **Component** = a form that preserves its identity under transformation (serialize, render, handle, recompose). "Eigen" as in eigenvector — identity-preserving — not "self-contained." Revised from original meaning after theoretical analysis (Session-2026-03-30-001).
- **Classes** = 24 types across data, container, sibling-reading, imperative, wrapper, runner, and showcase categories (reactive behavior is a cross-cutting mechanism via `SiblingBind`, not a class category)
- **Seed** = the Python page definition; the genome
- **Structure** = the stored component tree; the expressed organism
- **Structural action** = a mutation that reshapes the component tree at runtime

**CR-110** is IN_EXECUTION (v1.1). EI-1-4 Pass. Remaining EIs (5-7) will need to be scoped to reflect the rebuild.

**26 component classes (29 registered names). 11 page seeds. Full site shell with 10 routes (added `/components` reference taxonomy). Stateless page discovery — no restart needed when pages change.**

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

**Clean-Room Rebuild — Component Architecture** (Mar 25). Deleted all engine code. Built new foundation from scratch. Coined "Component" (self-contained, self-rendering, self-sufficient). Ten component types across data forms (TextForm, CheckboxForm, ChoiceForm, MultiForm, ListForm, TableForm), container forms (Page, TabForm, ChainForm), and showcase (RubiksCubeApp). Key patterns: bind() produces independent copies, is_complete required on all forms, conditional affordances, faithful projection, N/A mode for CheckboxForm/ListForm, recursive Page reset, structured error responses. TableForm agent-reviewed through two iterations. MultiForm reduces agent round-trips by grouping fields under a single affordance. ListForm has inline up/down/remove controls. 6 demo pages exercising all types.

**State Isolation + Render-from-Serialize + URL Overhaul + Primitive Expansion** (Mar 26). Per-page state files. Page definitions with auto-discovery. Content negotiation. Path-based component URLs. Render-from-serialize architectural fix. Score for quiz grading. Quiz Portal page. 10 new component primitives (NumberForm, DateForm, BooleanForm, RangeForm, MemoForm, RatingForm, RankForm, KeyValueForm, Computation, AccordionForm). Computation with store_result for cross-component dependencies. Visibility callable predicates. Vendor Assessment page composing all 23 types with 3-level container nesting and derived computed scores. 11 pages total.

**Expressiveness Expansion + Fractal Complexity Architecture** (Mar 27). Five new component types addressing expressiveness gaps: Validation (cross-field validation), DynamicChoiceForm (conditional options), Action (imperative side effects), Repeater (dynamic repeated structure), Group (named parameterized compositions). Weird Experiments page exercising all new types. Architectural plan for dynamic fractal complexity: collapsing the boundary between structure and data so user interactions can reshape the component tree itself. Biology metaphor: genome (Python types), expression (store), environment (user POSTs). Five-phase plan: Switch → Registry → Structural Persistence → Structural Actions → Self-Modifying Pages.

**Fractal Complexity — Complete Implementation** (Mar 28, session 001). All five phases of the fractal complexity plan implemented. Switch (Phase A): N-way structural selection based on sibling value. Component Type Registry (Phase B): explicit name→class mapping, 29 built-in types. Structural Persistence (Phase C): to_descriptor/from_descriptor round-trip, __structure in store, seed-based reconstruction with callable preservation. Structural Actions (Phase D): mutable pages with add/remove/move/rebuild_from_seed, surgical data cleanup. Self-Modifying Pages (Phase E): Action structural_actions flow up to Page, enabling pages that reshape themselves in response to user interaction. Survey Builder demo. README for qms-workflow-engine. 29 component types, 15 pages.

**Gallery, Feedback, Faithful Projection, Store Sync, UI Polish** (Mar 28, session 002). Component Gallery page: interactive tutorial covering all 29 types across 8 tabbed sections (16 pages total). Universal Clear affordance on all data components. Server-side validation: NumberForm/RangeForm/MemoForm reject invalid values with structured errors instead of silently accepting. Faithful projection enforcement: removed browser-side validation so humans see same errors as agents. Page multi-message feedback banner: errors accumulate per-target, success is singular, dismiss affordance per error. Store file sync: mtime-based cache invalidation. CheckboxForm/RankForm: explicit Done confirmation prevents ChainForm premature auto-advance; CheckboxForm N/A removed (Done with nothing checked = none apply). Condensed move affordances: ListForm/RankForm use two parameterized affordances (Move Up/Down) listing valid items. KeyValueForm: inline edit fields, duplicate key rejection, condensed affordances. ListForm: inline add/edit rows with green +/✓ buttons. Live tooltip updates codebase-wide: all input buttons show actual POST body on hover.

**Module Reorganization + Agent JSON Cleanup** (Mar 29). One component per module: extracted TextForm/CheckboxForm from base, renamed all 27 modules to consistent `*form.py` convention. Two-tier serialization: `_serialize_full()` (internal, for HTML) and `serialize()` (agent-facing). Agent JSON no longer includes `form`, `key`, `render_hints`, or `_rendered` — components are self-describing through instructions and affordances. NumberForm affordance now includes integer constraint in instruction text.

**ListForm Expansion + SetForm + KeyValueForm Simplification** (Mar 29, session 001). ListForm: fixed_items (immutable seed items), must_follow ordering constraints (ID-based, static + dynamic), stable topological sort enforcement, transitive cycle detection, inline constraint UI with per-item add dropdown and remove buttons. SetForm: 30th component type, unordered unique collection. KeyValueForm: API simplified to key-based edit/remove, internal IDs hidden from agent. Consistent layout polish: remove buttons on left, pill badges for IDs, aligned columns across all collection forms. Gallery: dedicated Lists tab with 4 use cases.

**OrderedCollection Extraction + TableForm Unification** (Mar 29, session 002). Extracted `OrderedCollection` utility from ListForm — reusable ordering engine (stable IDs, fixed items, must_follow constraints, cycle detection, topological sort). ListForm refactored to delegate to one OC (zero API change). TableForm refactored to wrap two OCs (rows + columns), gaining: move_row_up/down, move_col_left/right with inline arrows, fixed_columns/fixed_rows, row/column ordering constraints. Legacy state auto-migration. AddConstraintAffordance moved to affordances.py for shared use. Inline constraint UI for both axes (row: green pills in control column, column: blue pills in headers). Row controls moved to borderless column outside data grid. BUTTON_GAP constant for consistent button/gap alignment. Gallery: Tables tab with 5 demos (basic, fixed columns, row constraints, column constraints, full-featured). Fixed _current_states() seeding bug for fixed_columns.

**TableForm UI Overhaul + Configuration Panel** (Mar 29, session 003). Comprehensive TableForm rendering redesign. Column headers: pill badge IDs centered between move arrows (3-column grid), editable inputs with ✓ confirm buttons, remove buttons on label row. Row controls: dedicated bordered columns for remove (−), up (▲), down (▼), and prerequisite (☑) — all shaded #f0f0f0. Prerequisite UI split into ☑ button column (custom button-styled select overlay) and "Prerequisites" column (auto-appears when any prereq exists, pills use ID badge style, vertical layout). Horizontal scroll via overflow-x wrapper. Uniform font sizes (removed per-element overrides). Auto-seed one empty row when columns exist. Add_row affordance body includes column key placeholders. box-sizing: content-box on all inline button styles fixes alignment across ListForm and TableForm. Configuration panel above the table with checkbox toggles for auto-chain rows/columns — when enabled, each row/column automatically depends on the previous one, maintained across add/remove/move operations.

**Typed Columns + Constraint UI + SequenceForm + Edit Mode + TableRunner + Workflow Builder** (Mar 29, session 004). TableForm typed columns: fixed_columns accepts Component instances alongside strings. Cell components use compound scopes (table_key/row_id). RowGroup routing node. fixed_rows now seeds cell data. ListForm constraint UI unified with TableForm (checkbox button overlay, monospace pills). SequenceForm: gated sequential container without auto-advance (intermediate between TabForm and ChainForm). Edit mode infrastructure: editable flag on base Component, pencil icon toggle, label overrides in store, _chrome_rendered for affordance dedup. TextForm edit mode with inline label editor. TableRunner: new Runner category — reads sibling TableForm, presents rows as gated sequential workflow. Only typed columns are executable; text columns provide row labels; ordering constraints become execution gates. Workflow Builder page: 6-tab tool composing 14 component types for designing workflows with stage gates, parallel paths, conditional branches, merge gates, and acceptance criteria. Gallery: SequenceForm in containers tab, TableRunner in tables tab with pre-populated Design/Build/Test source table.

**Theoretical Analysis + Dependency Visibility + Historizer + Control Flow Gallery** (Mar 30, session 001). Rigorous examination of component concept prompted by TableRunner introduction. Found: "eigen" (self-contained) was a special case — eroded gradually across Score, Computation, Visibility, DynamicChoiceForm, Switch, TableRunner. Real invariant: HATEOAS-complete interaction node. Revised component meaning to "identity-preserving under transformation" (eigenvector reading). Further: component is a *program* — state + instruction set (affordances) + halt condition (is_complete). Agent is the runtime. Runners reframe as interpreters. Identified `depends_on` as a shadow dependency graph invisible in the UI — coupling without containment. Implemented `render_dependency_line()`: all sibling-reading components now render "Depends on: /path/to/sibling" with full URL paths (6 types updated). Historizer: new wrapper type with append-only change history, lazy detection on serialize, timeline browsing. Control Flow Gallery page. AuditForm attempted (Historizer + mandatory reason per change) — required monkey-patching child's handle(), which was the first inter-component behavior modification. Rejected as architecturally wrong and deleted. Open question: first-class interception mechanism needed in routing layer.

**Control Flow Gallery + Page Builder** (Mar 31, session 001). Control Flow Gallery expanded: SequenceForm demo (3-step gated workflow), Fork/Merge demo (TabForm inside SequenceForm gives parallel-branch-then-merge for free), Routing demo (Switch inside SequenceForm gives conditional branching with state-preserving route switching). Workflow Builder replaced with Page Builder — generic mutable Page with type dropdown toolbar, per-component ▲/▼/✕ controls, editable=True on dynamically added components. Page mutable HTML overhauled.

**Reverted bases.py abstraction** (Mar 31, session 002). The 7-class base hierarchy (ScalarForm, SelectionForm, etc.) added 251 lines of indirection without sufficient value. Reverted all engine/ changes from that commit, restoring each form's own _handle() and is_complete. Net -145 lines. Page Builder and Control Flow Gallery preserved.

**Edit mode expansion + RatingForm deletion** (Mar 31, session 003). Full edit mode for TextForm, NumberForm, BooleanForm, ChoiceForm, CheckboxForm, ListForm. Same-shape principle: edit mode preserves layout, fields become inline editable inputs with `font: inherit` and position-matched margins. Base infrastructure: `effective_instruction`, `set_mode` replacing `toggle_edit`, pencil/play icons. Type-specific config editing via `__config` store pattern (NumberForm, BooleanForm, ListForm). ChoiceForm/CheckboxForm refactored: child ListForm manages options/items, visible in edit mode via faithful projection. ListForm: fixed items fully editable in edit mode via `relax_fixed` on OrderedCollection; 📌 pin toggles per item and per constraint to mark fixed/unfixed; static constraints demotable via `fixed: false` stored entries. Undo/discard: snapshot-based undo stack with `_push_undo()` before each edit mutation (including all item/constraint mutations in ListForm), initial snapshot for discard-all. Child ListForm handle wrapped to push undo on parent. Chrome buttons: undo (↩, conditional), discard (✕ red). RatingForm deleted — replaced with NumberForm(integer=True). 32 component types.

**Rendering layer modernization** (Apr 1, session 003). External architectural review prompted re-evaluation of three foundational assumptions: JSON-for-agents, JSON→HTML derivation, runtime parity enforcement. Implemented three-step modernization: (1) Event delegation — replaced all inline JavaScript (100+ `fetch()` calls across 30 files) with `data-c-*` attributes and a single 60-line delegation script, structurally eliminating XSS vulnerability class. (2) CSS extraction — moved repeated inline styles to `app/static/style.css` with semantic `ef-` classes, 418→252 inline styles. (3) Parity test + Jinja2 templates — wrote `tests/test_parity.py` (20 tests verifying JSON↔HTML affordance alignment for all 18 pages), removed runtime RuntimeError accounting, migrated all 32 components from f-string HTML to Jinja2 templates in `app/templates/components/`. Shared `_edit_header.html` partial eliminates 6 duplicated edit-header methods. Browser-tested: zero behavioral regressions.

**HTMX migration proof of concept** (Apr 1, session 004). Decision to abandon JSON as agent-facing representation in favor of HTML/HTMX. Integrated HTMX 2.0.4 + json-enc extension. Replaced full page reloads with partial DOM swaps. Migrated TextForm and ListComponentX to native HTMX templates — templates encode the state machine directly via `hx-post`/`hx-vals`, eliminating Affordance objects from the rendering path. Established dual template architecture: agent templates (naked semantic HTML with `data-field`/`data-item-id` attributes, zero styling) and human templates (styled HTMX with CSS classes and layout). Four-option view selector dropdown (Human View, Agent View, Agent HTMX, JSON) replaces the old toggle button. Fixed latent `render_inline_button()` bug where CSS class names were placed in `style=` attribute instead of `class=` — affected all components using `render_btn()`. htmx-lab test page with TextForm + two ListComponentX variants (simple + constrained/editable). 21 parity tests passing across 19 pages.

**TableComponentX — HTMX-native TableForm** (Apr 2, session 001). TableComponentX subclass with dual templates. Agent template demonstrates the O(1) vs O(N) affordance divergence between agent and human views: read-only data grid + parameterized affordance forms (one form per action type with `<select>` dropdowns listing valid IDs), directly mirroring JSON affordance structure for minimal agent context usage. Human template reproduces the full interactive TableForm layout with inline editing, constraint dropdowns, and arrow buttons. Two HTMX Lab demos: simple table (fixed columns) and constrained table (fixed rows, row constraints, auto-chain). 34 component types, 19 pages.

**ChainFormX + SequenceFormX + agent template conventions** (Apr 3, session 001). ChainFormX and SequenceFormX migrated to HTMX-native (44 component types: 33 base + 11 X variants). Both added to HTMX Lab with demo data. Comprehensive agent template quality pass across all 12 agent templates: fixed Jinja2 `&#34;` escaping in data attributes; added `hx-vals` with `<placeholder>` body templates to every `<form>` and `<button>` so agents see exact POST body shape; added `<div data-component="{key}" data-type="{form}">` bounding divs via `_wrap_agent_html()` with proper indentation for nested components; added `_affordance_hints(data)` to base Component threading affordance instruction text into agent templates as visible `<p data-field="instruction">` elements; standardized `<input>` attribute ordering. Research confirmed LLMs can infer POST bodies from forms but reliability degrades with complexity — `hx-vals` chosen as pragmatic explicit approach that keeps HTML human-usable.

**Container edit mode** (Apr 1, session 002). Edit mode for all 5 container components: Group, TabForm, ChainForm, SequenceForm, AccordionForm. Each supports add/remove/reorder children, toggle child editability (parent-controlled ✏ toggle), undo/discard via Store.snapshot_scope/restore_scope. Structural persistence via `__structure` in child scope. `editable` round-trips through to_descriptor/from_descriptor (base Component and registry updated). Containers delegate to `super()._serialize_full()` for base edit mode infrastructure. Edit mode rendering: inline label/instruction editors, type/key/label add toolbars, per-child control bars. Navigation (tab switch, step focus, section toggle) works in both modes. Gallery Container Forms tab: all 5 demos set to editable=True. 11 component types now have full edit mode (6 data + 5 container).

**HTMX excision + X variant removal + stateless server + instance spawning + agent usability fixes** (Apr 4, sessions 001-002). Session 001: HTMX fully excised — deleted htmx.min.js, json-enc.js, removed all hx-* attributes, converted 12 human templates to data-c-* event delegation. All 11 X variant forms deleted (Python files, human templates, agent templates). HTMX Lab page deleted. Registry trimmed from 44 to 33 component types. View selector simplified to 2 panes (Human View, JSON). 20 parity tests passing. Session 002: Stateless server refactor — server no longer holds components or pages in memory between requests. Server is a pure function: (seed + store + request) → response. Instance spawning — page seeds become templates, users spawn named instances via the Agent Portal launcher. Three agents independently tested the API by building workflows (Bug Report, Employee Onboarding, Incident Response), surfacing 11 usability issues. All addressed: config validation before persistence (P0), resilient bind/rebuild on corrupt structure (P0), instance URLs in listings (P1), label propagation (P1), batch affordance surfaced (P2), `GET /types` schema endpoint (P2), expanded config examples (P2), compact child POST responses (P2), shallow GET (P2), collapsed O(N)→O(1) mutable page affordances (P2), checkbox "done" clarification (P3).

**Affordance Flotation** (Apr 4, session 003). Separable affordances (Clear, Edit, Batch) float from components at any nesting depth to Page during agent-facing serialization. Phase 1: affordances tagged with `_floatable` merge key in `_serialize_full()`. Page collects from direct children via `_serialize_full()` (preserving tags), groups by merge key, strips from children, emits parameterized compound affordances with structured `targets` dict and generic instructions. Phase 2 (same session): recursive `_collect_floatable()` walks `component`/`components`/`sections` keys to collect from arbitrary depth. Targets changed from last-URL-segment to full URL paths for correct multi-level routing. Lead feedback incorporated: no `_chrome_rendered` on merged affordances, dedicated `targets` dict (not instruction-only), generic merged instructions. HTML rendering unaffected — flotation is agent-tier only. ~61% reduction on flat pages (49→19 on Employee Onboarding); nested pages (component-gallery) collect from TabForm→Group→data forms. Research confirmed this pattern is novel — no existing hypermedia format has affordance flotation. Closest precedents: Hydra class-level `supportedOperation`, MCP community tool consolidation. Broader affordance option normalization identified as future initiative.

**Navigation Affordance Collapse + Batch Body Cleanup** (Apr 5, session 001). O(N)→O(1) collapse of container navigation affordances across 5 forms: TabForm (`tabs` dict), AccordionForm (`sections` dict), ChainForm (`steps` dict), SequenceForm (`steps` dict), TableRunner (`steps` dict). Each emits a single parameterized affordance with an options dict instead of one affordance per child. HTML templates updated to render navigation buttons directly via `render_btn()` from context data. Deleted `SwitchTabAffordance`, `ToggleSectionAffordance`, `_render_tab_button()`, `_render_accordion_toggle()`. Stripped `_chrome_rendered` from agent JSON. Batch affordance body template cleaned up: `[{"action": "...", "...": "..."}]` → `["<action_body_1>", "<action_body_2>", "..."]` with instruction referencing sibling affordances. ~230 lines reduced from agent JSON across flotation + navigation collapse + batch cleanup.

**InfoDisplay + Component Reference Menu + Embedded Page + Page Builder** (Apr 5, session 001 continued). InfoDisplay: 34th component type — read-only text display, no affordances, always complete. `text` accepts `str | dict` for structured key-value display. AccordionForm: added `default_expanded` config field (defaults `True`, sections start collapsed when `False`). Component Reference Menu: new page (`component-reference`) documenting all 34 types across 5 tabs (Overview + 4 type categories). Overview tab explains component concepts, composition patterns, and config/JSON configurability. Type entries use AccordionForm sections with `default_expanded=False` — 199 lines JSON initially, ~19 lines per expanded type. Floated affordance HTML fix: compound affordances marked `_chrome_rendered` (agent-only, not rendered in HTML). Simplified Add Component: removed config/after from required body — agent flow now matches human flow (add with defaults → edit to configure). Embedded Page: `Page.bind()` handles both top-level (`Path`) and embedded (`Store`) binding. Embedded pages get independent Store files (`{parent_scope}__{child_key}.json`), nested URL prefixes, and full routing support via `find_component` path traversal. Page Builder embeds the Component Reference Menu as first child with independent state. 20 pages, 34 component types, 21 parity tests passing.

**Component Type Consolidation + Template Fixes + Gallery Polish** (Apr 5, session 002). Removed 3 redundant component types: RankForm (→ ListForm with fixed_items), MemoForm (→ TextForm with multiline/min_length/max_length), RangeForm (→ NumberForm with slider/unit). TextForm expanded: `multiline`, `min_length`, `max_length` fields with validation, textarea render hints, template support. NumberForm expanded: `slider`, `unit` fields with range_input render hints. Fixed Batch affordance HTML leak: 6 templates (date, range, action, dynamicchoice, history, tablerunner) rendered `_chrome_rendered` affordances as visible buttons — added `_rendered` filter. Fixed MultiForm missing `render_from_data()` override (fell through to base f-string renderer). Gallery cleanup: all edit-mode components set editable, removed redundant TableForm from collections tab, reordered demos. Component reference page and README updated. 31 component types, 20 pages, 21 parity tests passing.

**Container Unification + InfoDisplay Edit Mode + DictionaryForm Rename** (Apr 5, session 004). Merged TabForm, ChainForm, SequenceForm, AccordionForm into Navigation — single class with `mode` field ("tabs", "chain", "sequence", "accordion"). Two orthogonal axes: unlock policy (free vs gated) + projection (one-at-a-time vs all-visible). ~62% line reduction (1,730→624 lines + 4→1 templates). Registry aliases for backwards-compatible descriptor resolution. InfoDisplay: added edit mode with embedded multiline TextForm child (same pattern as ChoiceForm/CheckboxForm). Suppressed Batch affordance (no interaction affordances to batch). Gallery: new Display Forms tab. KeyValueForm renamed to DictionaryForm. 28 component types, 20 pages, 21 parity tests passing.

**Supervisor/Operator View + Theme Infrastructure + Sleek Theme** (Apr 5, session 005). Page-level Supervisor/Operator View toggle: Supervisor shows full surrounding borders and all chrome, Operator suppresses view toggles/JSON and enables theme selection. Edit chrome (pencil/undo/discard) visible in both views. Component wrapper migrated from inline styles to CSS classes with `data-form` attribute selectors for container exclusion. Theme infrastructure: `set_theme()`/`get_theme()` in templates.py with fallback resolution (themed subdirectory → default). Themes are additive — subdirectory + optional CSS, override only desired templates. Sleek theme: dark UI (GitHub Dark Dimmed palette) with card-based layout, window-style titlebars, VS Code-style tab navigation with active-tab continuity. SVG chrome icons replaced with Unicode characters using `currentColor`. Navigation template gained CSS classes (`ef-nav-bar`, `ef-nav-tab`, `ef-nav-content`, etc.) for reliable theme targeting. Active child content wrapped in `ef-nav-content` div. 21 parity tests passing.

**Sleek Theme Expansion + TableForm Bugfix** (Apr 5, session 006). Sleek ListForm: custom `sleek/list.html` template with row-based layout, numbered ordinals, borderless inline inputs, hover-revealed controls. All `sleek-list__*` BEM classes, zero reliance on `render_btn()`/`ef-btn-*`. Global Sleek button overrides scoped with `:not([class*="sleek-"])` to prevent bleed-through. Sleek TableForm: custom `sleek/table.html` rendering from raw data (col_oc, row_oc, typed_templates, row_groups_by_id, constraint data added to render_from_data context). Dark spreadsheet grid with `border-spacing: 1px` gaps, hover-revealed row/column controls, borderless cell inputs. AccordionForm: migrated toggle div from inline `background: #eee` to `.ef-aff-accordion` class (inline style was blocking all CSS overrides), darkened to `#22272e`, removed blue left accent from section content. TableForm default view bugfix: `render_inline_button()` takes CSS class name but was receiving `STYLE_REMOVE`/`STYLE_ARROW` inline style strings — buttons had no styling. Added `CSS_CONFIRM`/`CSS_REMOVE`/`CSS_ARROW` constants to affordances.py. 21 parity tests passing.

**Theme-Aware Wrapper + Sleek Margin Layout + Navigation Titlebar** (Apr 5, session 007). Sleek page padding (12% left/right). Green→blue palette unification. Feedback banners migrated from inline styles to `.ef-feedback` CSS classes. Tab buttons restored to `render_btn()` in default view. Theme-aware `render()`: extracted component wrapper HTML from Python into `wrapper.html` Jinja2 template with theme fallback (`sleek/wrapper.html`). Each theme controls full output structure — no CSS hiding tricks. Sleek wrapper: data forms get card+titlebar, containers transparent with chrome only, Group gets no titlebar (sidebar handles it), Navigation gets full titlebar with label+instruction+chrome. Vertical tabs: top-level Navigation renders tab bar in left page margin with VS Code design language (dark `#1e1e1e` strip, active tab `#2b3035` merging into content panel). Navigation titlebar extends left to align with tab bar via `calc(-1 * min(10vw, 160px))`; instruction text offset to align with content column. Nested NavigationComponents: horizontal tabs, normal-width titlebar. Group right-margin sidebar: `sleek/group.html` renders label/instruction/affordances in right margin. Page separator below header. Nested Tabs Test page for visual testing. 22 parity tests passing.

**Horizontal/vertical nav simplification + Sleek polish** (Apr 6, session 002). Navigation layout rule: Page > Navigation (direct child) = vertical sidebar, all others = horizontal tabs with bottom-border active indicator. Restructured sleek.css into two-tier nav styles (default horizontal + page>nav vertical override). Group gets independent flex container rules. Navigation instruction moved out of titlebar into separate `.ef-nav-instruction` div (between titlebar and nav bar), enclosed by content border. Data form titlebars always rendered (label visible even when not editable). Group chrome (pencil button) moved into the label bar via dedicated wrapper branch + group template. Container spacing doubled to 16px. Color scheme: nested nav content panels #424850 (matches Group), page-level vertical sidebar #2b3035 (darker). Nested Tabs Test updated with 4 tabs exercising nested tabs/chain/sequence. 22 parity tests passing.

**Stress test + visibility cleanup + border polish + edit mode overhaul** (Apr 7, session 001). Nested Tabs Test rewritten from 14 to 115 components: 6 tabs (Four Modes, Deep Nesting 4 levels, Group Tests, Edge Cases, Reactive Containers with Switch/Visibility, Wide Containers with 8-tab overflow), dual vertical sidebars, bare Page-level InfoDisplay. Group dissolve rule removed — no more nesting-context special cases except Page>Navigation vertical sidebar. Group content panel width fixed (was shrink-wrapping). Navigation titlebar always visible (was conditional on editable). Instruction region: #1e1e1e background matching titlebar, #444 top separator. Titlebar: #555d66 border on top/sides with rounded corners. Horizontal tab elements: subtle #444 border on top/sides with rounded top corners across all states. Vertical sidebar tabs: #444 bottom separators only (no doubling with nav bar border), top border on nav bar. Dark #1e1e1e outer borders on Navigation and Group. Double bottom border fix (content panel border removed). Remaining-affs flush with content panel. Native Sleek edit mode for Navigation (inline tab controls, dark toolbar, vertical sidebar stays in sidebar column) and Group (per-child control bars inside ef-nav-content, wrapper titlebar with play/undo/discard chrome). Comprehensive edit mode CSS: dark overrides for .ef-btn-confirm/remove/arrow, .ef-chrome-btn, .ef-add-toolbar, .ef-empty-state, .ef-aff-accordion, .ef-section-content; attribute-selector overrides for inline-styled elements in default templates. 22 parity tests passing.

**UI Shell Port + Cleanup** (Apr 13, session 001). Strategic refocus: stop side quests, return to main goal of building QMS for Flow State. Ported main-branch site shell into dev branch: base.html with dark sidebar nav, Agent Portal card grid, home page, Quality Manual viewer (markdown TOC + article renderer), QMS dashboard with stage badges, Workspace card list, Inbox placeholder, README as nav page. README rewritten to match current state. Decision: continue on dev branch rather than merging (avoids breaking main). YAML workflows, Template Editor, Workshop, Sandbox all dropped. Cleanup: UUID instance IDs (replacing counter-based), Debug Mode toggle (replacing Supervisor/Operator + theme selector), removed 11 demo page definitions, stateless page discovery (no server restart needed), sleek theme font fix for data form instructions.

**Sleek Edit Mode Unification** (Apr 13, session 002). All data components now render edit mode natively in the sleek theme instead of falling back to default light-themed templates with CSS attribute-selector patches. 8 new sleek templates created (number, boolean, date, choice, checkbox, info, dictionary, multi). 3 existing sleek templates updated to handle edit mode (text_human, list, table). Unified CSS classes: `.sleek-edit-config` config bar, `.sleek-edit-config__toggle` pills, `.sleek-edit-config__field`/`__input`/`__btn` inline config forms, `.sleek-edit-value` value display, `.sleek-edit-child-ef` embedded child container, `.sleek-edit-row` collection rows, `.sleek-list__btn--pin` fixed-item pins. Design pattern: edit header (already styled via `.ef-edit-*`) + config bar + value display + remaining affordances. Execute mode: custom sleek rendering where available, `{% include "default.html" %}` fallback otherwise. 11 parity tests passing.

**Mutable Page Polish + Icon Overhaul + Escaping Fixes** (Apr 14, session 001). Fixed double-escaping bugs: `html.escape()` on wrapper context values (label, url, json_str) produced plain `str` that Jinja2 auto-escaped again — removed redundant `escape()` calls. Added `ensure_ascii=False` to JSON pane for real Unicode. Created `sleek/page.html` template for mutable Page — dark toolbar, margin-positioned controls. Mutable pages now force `editable=True` on seed components (was only set on dynamically added ones). Fixed `from_descriptor()` to sync `editable` flag from descriptor onto matched seed (was only setting True, never False). Added `toggle_editable` action to Page with affordance, handler, and feedback. Icon vocabulary overhaul: pencil (✏) for edit mode, padlocks (🔓/🔒) for toggle-editable, wastebasket (🗑) for delete, ✕ for discard — 8 templates updated. Fixed pre-existing bug where default templates passed inline styles as CSS class names via `render_btn()`. New `ef-icon-btn` class: 24×24 squares, 14px font, `--active`/`--danger` variants. All icon buttons consistent across both themes. 11 parity tests passing.

**Add Component UI + Structural Editor** (Apr 14, session 002). Add Component UI overhauled: flat 31-type dropdown replaced with card-based type picker — 5 collapsible categories (Input/Collections/Containers/Reactive/Display & Actions), 25 filtered types with Unicode icons, category accent colors (blue/green/purple/amber/teal), radio-as-card selection via CSS `:has(:checked)`. `TYPE_CATALOG` in registry.py as canonical source. `AddComponentAffordance` carries structured `type_catalog` dict in agent JSON. Default theme gets `<optgroup>`-categorized dropdown. Structural editor: tile-based page blueprint panel showing the component tree as uniform cards with drag-and-drop reorder, multi-select grouping, reparenting (drag onto container), ungrouping, and nested removal. HTML DnD API with zone detection (insertion line between tiles, green highlight on container tiles). All structural operations now work at any nesting depth: `group_components` finds shared-parent siblings, `ungroup_component` splices children into parent, `reparent_component` moves between containers with store sync, `move_component` supports intra-container reorder, `remove_component` searches recursively. Recursive tree helpers: `_pluck_from_tree`, `_find_container_children`, `_find_parent_key`, `_find_siblings_list`, `_sync_container_structure`. 11 parity tests passing.

**Universal POST-body tooltips** (Apr 16, session 001). Every clickable element that POSTs a JSON body now shows that body on hover — enforced once in JS rather than requiring every template to use `render_btn()`. `_efSyncTooltips()` in `component.js` runs on load and after each fetch+swap, synthesizing `title` attributes on `[data-c-post][data-c-body]` (static-body buttons) and `[data-c-add][data-c-palette-type]` (palette one-click add). Live drag tooltip: `_efDragCtx` stashed on dragstart (dataTransfer.getData() blocked during dragover), `_efShowDragTooltip()` renders a floating monospace tooltip tracking the cursor during drag with the exact POST body that would fire on release — updates live as the user moves between insertion positions, reparent targets, and container drop zones. `.ef-drag-tooltip` CSS in sleek.css.

**Theme system refactor + six new themes** (Apr 19–20, session-2026-04-19-004). Retired `operator-view`/`supervisor-view` distinction; moved to `data + theme = output`. `ContextVar` for thread-safe theme state, `.c-container` class consolidation, `THEME_NAMES` registry, server-rendered `<body data-theme>` (no FOUC). Two engine generalizations: `wrapper.html` now receives `data=data` (themes can introspect child state); `Page._serialize_full()` no longer strips `form`/`key` on children (themes dispatch per-type idioms). Six new themes: **debug** (supervisor-view-as-theme), **liquid-glass** (CSS-only Apple-frosted, proved the refactor), **paper** (document typography, completed forms collapse into inline prose), **chat** (conversational Q&A with avatars, chips, green ✓ badges), **task** (theatrical stage with per-container-type idioms: Tabs = Marquee Carousel, Sequence = Milestone Trail with pulsing gold station, Group = organic Huddle blob; data forms as spotlit Performers; deep indigo canvas with radial spotlights). First pass at Task theme was a flat task-queue list — rejected as "stylistic variant, non-innovative" — rebuilt as theatrical stage with fundamentally different per-type visual primitives. Bug fix along the way: paper/chat text-and-number templates added a hidden `<input name="action" value="set">` that fell through the action registry (registry uses `None` for set); POSTs silently no-opped from those themes. 79/79 parity tests pass throughout.

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
| `engine/component.py` | Component base (children, bind, batch, two-tier serialize, affordances(), auto-key, to_descriptor, has_data, clear) |
| `engine/textform.py` | TextForm — free-form string, optional multiline/min_length/max_length |
| `engine/checkboxform.py` | CheckboxForm — multi-select with Done confirmation |
| `engine/affordances.py` | Affordance (pure data), render_affordance_html utility, all affordance subclasses, disabled_button |
| `engine/store.py` | JSON file store, one file per page, scoped by component key, delete() for surgical removal, mtime-based file sync |
| `engine/registry.py` | ComponentRegistry (register/lookup/available), from_descriptor(), lazy default with 28 types + aliases |
| `engine/page.py` | Page — persistence boundary, find_component, structural persistence, mutable structure, feedback banner |
| `engine/page_mutations.py` | PageMutationsMixin — structural mutations (add/remove/move/group/ungroup/reparent component), tree helpers, handle_action routing |
| `engine/navigation.py` | Navigation — unified container (tabs/chain/sequence/accordion modes), faithful projection |
| `engine/rubikscubeapp.py` | RubiksCubeApp + RotateAffordance — complexity showcase |
| `engine/tableform.py` | TableForm — inline editing, add/remove, batch support, typed columns (RowGroup, compound scopes), fixed_rows cell seeding |
| `engine/tableform_actions.py` | TableFormActionsMixin — 17 action handlers for TableForm (add/remove/rename column, add/set/remove row, move, constraints, auto-chain) |
| `engine/tablerunner.py` | TableRunner — executes a TableForm as a gated sequential workflow |
| `engine/historizer.py` | Historizer — wraps component with append-only change history, lazy detection, timeline browsing |
| `engine/infodisplay.py` | InfoDisplay — read-only text display, embedded TextForm in edit mode, always complete |
| `engine/choiceform.py` | ChoiceForm — single selection via radio buttons |
| `engine/listform.py` | ListForm — ordered list, fixed items, ordering constraints, topological sort |
| `engine/setform.py` | SetForm — unordered unique collection, add/remove by value |
| `engine/multiform.py` | MultiForm — groups FieldDescriptors under single affordance |
| `engine/visibility.py` | Visibility — conditional visibility (value, list, or callable) |
| `engine/switch.py` | Switch — N-way structural selection based on sibling value |
| `engine/score.py` | Score — read-only grading from answer key |
| `engine/numberform.py` | NumberForm — numeric input with min/max/step/integer/slider/unit |
| `engine/dateform.py` | DateForm — ISO 8601 date/datetime with bounds |
| `engine/booleanform.py` | BooleanForm — binary yes/no toggle |
| `engine/dictionaryform.py` | DictionaryForm — dynamic key-value pairs (renamed from KeyValueForm) |
| `engine/computation.py` | Computation — derived display from siblings, optional store_result |
| `engine/validation.py` | Validation — cross-field rules, pending/pass/fail, blocks completion |
| `engine/dynamicchoiceform.py` | DynamicChoiceForm — options from sibling value, stale detection |
| `engine/action.py` | Action — imperative button, preconditions, confirmation, side effects, structural_actions |
| `engine/repeater.py` | Repeater + EntryGroup — dynamic repeated structure, compound scopes |
| `engine/group.py` | Group — named compositions, parameterizable via subclassing |
| `app/__init__.py` | Flask app factory |
| `app/registry.py` | InstanceRegistry — tracks spawned page instances in `data/instances.json` |
| `app/routes.py` | Routes + SSE + content negotiation + instance management + manual/QMS/workspace/inbox |
| `app/manual.py` | Quality Manual markdown rendering (TOC builder, link rewriter, renderer) |
| `app/templates/base.html` | Shared layout — dark sidebar nav (Home, Portal, QMS, Workspace, Inbox, Manual, README) |
| `app/templates/home.html` | Landing page with hero + info cards |
| `app/templates/portal.html` | Agent Portal — card grid grouping instances by seed type |
| `app/templates/page.html` | Component page wrapper (extends base, SSE + view/theme toggles) |
| `app/templates/manual_*.html` | Quality Manual TOC index + article viewer with sidebar TOC |
| `app/templates/qms.html` | QMS document dashboard with stage badges |
| `app/templates/workspace.html` | Active document cards |
| `app/templates/inbox.html` | Review/approval queue (placeholder) |
| `app/templates/readme.html` | README rendered as styled HTML page |
| `app/templates/components/` | Per-type Jinja templates (one per component type) |
| `app/templates/components/sleek/` | Sleek theme template overrides (wrapper, navigation, group, list, table, text) |
| `app/templates/components/paper/` | Paper theme overrides (9 templates) — document typography, prose-collapse on complete |
| `app/templates/components/chat/` | Chat theme overrides (10 templates + `_ask.html` partial) — dialogue Q&A with bubbles |
| `app/templates/components/task/` | Task theme overrides (10 templates) — theatrical stage with per-container-type idioms |
| `app/static/sleek.css` | Sleek theme — VS Code dark palette, card layout |
| `app/static/debug.css` | Debug theme — full borders, visible JSON pane (former supervisor view) |
| `app/static/liquid-glass.css` | Liquid Glass — Apple-frosted cards over pastel gradients (CSS-only) |
| `app/static/paper.css` | Paper theme — document typography, left-border accents |
| `app/static/chat.css` | Chat theme — pastel gradient canvas, bubble/chip primitives |
| `app/static/task.css` | Task theme — deep indigo stage, gold spotlight, per-container-type idioms |
| `pages/` | Seed definitions (page types), auto-discovered. Key = type identifier. |
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

1. **Build real QMS workflows as component compositions** — CR creation, review workflows, document lifecycle pages. This is the primary goal: making the QMS usable.
2. **Wire QMS/Workspace/Inbox to real data** — Connect to qms-cli or QMS document store
3. **Review and clean up demo pages** — Determine which seeds in `/portal` are valuable vs gallery/experiment cruft

### Before First QMS Workflow Ships

4. **Framework rename: `qms-workflow-engine` → Razem** — Decided Session-2026-04-17-003. The framework is general-purpose and should be named separately from its first application. Scope:
   - GitHub repo rename: `qms-workflow-engine` → `razem` (and update remote URL)
   - `.gitmodules` path + submodule path in pipe-dream root (`qms-workflow-engine/` → `razem/`)
   - `CLAUDE.md` references (multiple mentions of `qms-workflow-engine` submodule and paths)
   - Wiki (`app/templates/wiki.html`) — **LANDED** Session-2026-04-17-003 (rewritten as if rename occurred; see session notes for detail).
   - Framing (`app/templates/framing.html`) — rewrite hero subtitle/thesis ("The QMS Workflow Engine is a Python framework..." → "Razem is..."), update §1 Thesis prose, update §8 Pass 4 history
   - README (`README.md` in the framework) — retitle, rewrite opening thesis, update doc-pointer references
   - Lesson prose — Lessons 1 and 5 explicitly reference "the engine" by name in a few places; sweep for "QMS Workflow Engine" → "Razem"
   - Deep Dive (`pages/deepdive.py`) — intro sentence references the framework
   - Preserve "QMS Workflow Engine" as the eventual application name (or rename the application too — separate decision)
   - Effort: one focused session. Low technical risk; mostly text substitution + repo admin.

5. **Class taxonomy refactor** — **LANDED** Session-2026-04-18-001. See §1 for full details. TBD items resolved: ActionComponent → Action, HistoryComponent → Historizer. Heuristic `form` property replaced with explicit class attributes per Lead direction. Change-log entry added to `docs/architecture.md` §6.

### Future Refactors (post-workflow)

6. **Split `Navigation` into descriptive subtypes** — **LANDED** Session-2026-04-19-001. Three subclasses: `Tabs` (free access, one visible), `Sequence` (gated, `auto_advance` flag replaces chain vs sequence distinction), `Accordion` (free access, all visible). `Navigation` base class retains shared machinery. Mode switching removed from edit mode. All page definitions, CSS selectors, registry, templates, and mutable page infrastructure updated.

### After Workflows Are Working

7. **Merge dev into main** — Dev branch preserved until confirmed working
8. **CR-110 remaining EIs** — Update to reflect the rebuilt engine
9. **SDLC-WFE-RS rewrite** — Requirements spec needs full rewrite for component architecture

### Engine Backlog (post-workflow cleanup)

Cross-referenced from Wiki / Framing §8 / Deep Dive / Lessons 6-8. Items surfaced across multiple docs but not yet scheduled. All are engine-quality improvements that should follow the primary workflow-building effort.

**Convergent unscheduled items** (flagged in 3+ docs):

| Item | Effort | Source |
|------|--------|--------|
| **Action-dispatch registry** — **LANDED** Session-2026-04-18-003. `_actions` dict per class, base `handle()` dispatches via `getattr`. 20 classes migrated, 89 if/elif branches eliminated. Simpler than originally scoped: plain `dict[str, str]` (action → method name), no rich ActionSpec. Middleware/logging/replay remain possible future additions on top of the registry. | Done | Wiki Limitations §1; Framing §8 "still open" #4; Deep Dive rec #1 |
| **Callable-preservation diagnostic** — **LANDED** Session-2026-04-18-003. `_callable_fields` tuple on 3 classes (Computation, Action, DynamicChoiceForm); `from_descriptor()` sets `_missing_callables`; `_base_state()` surfaces warnings. | Done | Wiki Limitations §2; Framing §4 "What's still open"; Lesson 7 callout |
| **Concurrency model** — last-write-wins on simultaneous writers to same component; no optimistic concurrency or conflict detection. Fine for single-user; broken for collaboration. | Medium | Wiki Limitations §4; Deep Dive §5 #4 |

**Deep Dive findings not yet cross-referenced elsewhere:**

| Item | Effort | Source |
|------|--------|--------|
| **Move showcase/runner demos to `engine/_examples/`** — RubiksCubeApp (400 lines) and TableRunner ship in the production registry and appear in the builder's type-picker. Should live alongside `pages/` demos, not engine primitives. README still lists them as "Showcase" / "Runner Forms" production categories. | Small | Deep Dive rec #7 |
| **Delete `_migrate_legacy_overrides` with kill-date comment** — runs in the bind hot path on every request, doing store reads + descriptor walks + deletes. Once existing instances are migrated (finite event), this is overhead with no value. | Trivial | Deep Dive rec #8 |
| **Split megafiles along (orchestration / structural mutation / content mutation / rendering) axes** — **LANDED** Session-2026-04-18-003. Page split via `PageMutationsMixin` (1152→631+493); TableForm split via `TableFormActionsMixin` (1248→993+270). Navigation at 693 left intact. Mixin pattern preserves single-class API while separating concerns. | Done | Deep Dive findings §6; rec #5 |
| **Promote mutable-structure schematic editor out of `sleek/page.html`** — the most ambitious feature is gated behind a stylesheet choice. Default theme has no visual editor. Either build in default or move the editor into the engine. Lesson 8 doesn't flag this theme coupling. | Medium | Deep Dive §5 #5; rec #6 |

**Consistency nits from the rename (Session-2026-04-17-002):**

| Item | Effort | Source |
|------|--------|--------|
| **Rename `form` class attribute** — lowercase `form = "text"` registry-type identifier is inconsistent with `Component` PascalCase. Candidates: `type`, `component_type`, or leave. Cosmetic. | Small | 2026-04-17-002 follow-on #1 |
| **Rename branch `dev/content-model-unification`** — no longer accurate post-rename; historical and not breaking. Rename at next major checkpoint. | Trivial | 2026-04-17-002 follow-on #2 |

**Correctly parked** (do not action without a concrete use case):

- **Context primitive** — no ancestor-to-descendant channel equivalent to React Context. Parked across Wiki Limitations §3, Framing §6, Lesson 5. Shape is clear (typed provider at container level + `_context_get(ClassRef)` accessor validated at bind like SiblingRef); the pain point isn't. Most likely earned when user/permissions arrive with QMS workflows.

**Pre-existing items (not from this review):**

- First-class interception mechanism for containers
- Affordance flotation future phases
- Agent integration testing
- Performance / stress testing with large pages
- Error-boundary expansion — `serialize_safely()` (JSON parity), bind-error scoping, `_handle()` partial-mutation scoping (Framing §8)

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

**Framing design plan — all three passes LANDED** (Session-2026-04-17-001). See `/framing` page and `docs/architecture.md` change log for details.
- **Pass 1 (Naming)**: `docs/architecture.md` reference doc; `from_descriptor` docstring rewrite naming "reconciliation" and surfacing callable-preservation as a first-class limitation; `reconcile = from_descriptor` module alias.
- **Pass 2 (Typed composition)**: `SiblingRef` str-subclass value type with `expects=` assertion; 7 sibling-reading components coerce on construction; `Page._validate_sibling_refs()` raises `SiblingRefError` with actionable diagnostics at bind time; `_validate_field_value` at `_set_my_field`/`_set_my_config` boundary (handles simple types, `X|None` both `typing.Union` and PEP 604, `Literal[...]`); `Navigation.mode` and `FieldDescriptor.type` tightened to `Literal`.
- **Pass 3 (Error boundaries)**: `Component.render_safely()` on base; `_error_boundary.html` template (theme-agnostic, traceback in Flask debug mode); defensive fallback to inline HTML if template fails; 18 child-render sites across 10 modules swapped to `render_safely()`. Scope deliberately excluded: `serialize_safely()`, bind-error scoping, `_handle()` error scoping — parked.

**Parity-test hardening — LANDED** (Session-2026-04-17-001). The test suite grew from 12 tests (one forward-parity per page plus two smoke tests) to 72 tests across 9 categories. Closed all 10 audit findings that could be addressed without consolidating `_chrome_rendered` semantics (that remains open as a future engine cleanup). See `tests/test_parity.py` for the full suite and the change log below for per-test coverage.

Follow-on work not included (deliberately scoped out):
- Alternate-state parity (post tab-switch, post set_mode) — requires richer fixturing.
- Handler-existence check — would require POSTing each declared action through the test client and asserting no "unknown action" response. Integration-level concern.
- `_chrome_rendered` owner consolidation — test works around the scattered semantics but does not fix them. Separate engine refactor.

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

**Dev branch has full site shell but no real QMS workflows yet.** The component engine and UI are complete, but no actual QMS document workflows exist — all page seeds are demos/galleries. This is the critical gap.

**SDLC-WFE-RS needs full rewrite.** v1 requirements don't apply to the rebuilt engine.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**qms-workflow-engine submodule pointer** should be kept current with pushes.
