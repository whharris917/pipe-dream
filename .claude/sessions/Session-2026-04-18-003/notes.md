# Session-2026-04-18-003

## Current State (last updated: end of session)
- **Active document:** None (dev branch work, no CR)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Razem rename or first real QMS workflow

## Context from Session-2026-04-18-002
- Wiki article expanded with architecture framing, 4 SVG diagrams, component model subsection, mutation boundary docs, 6 code examples
- `affordances()` promoted to first-class public method on Component
- Auto-generated keys: `key` field now optional, auto-generates `{form}-{8-char-hex}` via UUID
- 72/72 parity tests pass
- Class taxonomy refactor landed in 001; Razem rename queued but not executed

## Progress Log

### Wiki intro rewrite
- Reviewed Lead's proposed wiki intro rewrite in `prompt.txt`
- Identified 6 issues (stale class names, promotional tone, missing framework/QMS distinction, etc.)
- Produced revised 7-paragraph intro incorporating: faithful projection, HATEOAS, declarative vs imperative components, workflow-engine-replacement architecture, framework/QMS distinction, ACI positioning
- Two follow-up edits: "Python framework" → "framework"; "simultaneously" → "collaborative use"
- Deleted untracked `debug_page.html` (stale HTML snapshot artifact)

### Engine quality backlog — 3 items completed

#### 1. Callable-preservation diagnostic
- Added `_callable_fields: tuple[str, ...]` class attribute to Component base
- Computation: `_callable_fields = ("compute_fn",)`
- Action: `_callable_fields = ("action_fn", "precondition_fn")`
- DynamicChoiceForm: `_callable_fields = ("options_fn",)`
- `from_descriptor()` in registry.py checks after fresh construction, sets `_missing_callables` on instance
- `_base_state()` includes warnings in serialized output when callables are missing
- Visibility and Score correctly excluded (polymorphic fields, not exclusively callable)

#### 2. Action-dispatch registry
- Added `_actions = {}` class attribute to Component base (plain class attr, not dataclass field — avoids mutable default error)
- Base `handle()` dispatches via `self._actions.get(action)` → `getattr(self, method_name)(body)`, falls back to `_handle()`
- Base `_handle()` changed from `raise NotImplementedError` to `return self.serialize()`
- Solved "no action in body" pattern: simple data forms use `None` as dict key since `body.get("action")` returns `None`
- 20 component classes migrated (89 if/elif branches eliminated):
  - Small files: textform, booleanform, numberform, dateform, checkboxform, choiceform, setform, dynamicchoiceform, action, rubikscubeapp, historizer, repeater, tablerunner, multiform, dictionaryform, group, computation
  - Large files: navigation (8 actions), listform (13 actions), page (10 actions), tableform (17 actions)
- 4 `_handle()` overrides remain (correct — delegation patterns): component.py base, historizer, switch, visibility
- Removed 4 no-op `_handle()` overrides: score, validation, RepeaterEntry, RowGroup
- Fixed latent bug: `page.py handle_action()` called `self._handle(sa)` for structural actions — now correctly calls `self.handle(sa)` to go through the registry
- 72/72 parity tests pass throughout

#### 3. Megafile split
- **page.py**: 1152 → 631 lines. Structural mutations extracted to `page_mutations.py` (493 lines) as `PageMutationsMixin`. Contains: 8 `_do_*` wrappers, `_add_component`, `_remove_component`, `_move_component`, `_toggle_editable`, `_group_components`, `_ungroup_component`, `_reparent_component`, `handle_action`, 5 recursive tree helpers (`_pluck_from_tree`, `_find_container_children`, `_find_parent_key`, `_find_siblings_list`, `_all_keys_in_tree`), `_clear_component_data`, `_find_component_recursive`, `_sync_container_structure`.
- **tableform.py**: 1248 → 993 lines. 17 action handlers extracted to `tableform_actions.py` (270 lines) as `TableFormActionsMixin`.
- **navigation.py**: 693 lines — under threshold, not split.
- Mixin pattern: `Page(PageMutationsMixin, Component)`, `TableForm(TableFormActionsMixin, Component)`. Clean MRO, no circular imports.
- Static method recursive calls updated to reference mixin class name instead of `Page`.
- 72/72 parity tests pass.
