# Session-2026-04-16-003

## Current State (last updated: ongoing)
- **Active work:** NavigationForm UX polish (mode switcher) + diagnosis of descriptor/config drift
- **Blocking on:** Nothing
- **Next:** Awaiting Lead direction (drift fix is queued as a small follow-on)

## Progress Log

### Session opened
- Read prior session notes, QMS-Policy/START_HERE/Glossary, SELF.md, PROJECT_STATE
- QMS inbox empty; CR-110 still IN_EXECUTION

### NavigationForm mode switcher (sleek theme)
**Lead feedback:** "the generic buttons to switch modes for NavigationForms is very ugly."

Previously: four separate `SimpleButtonAffordance`s (`Mode: tabs (current)`, `Mode: chain`, etc.)
fell through `_render_button` and stacked at the bottom of the edit panel as generic blue
buttons — discoverable but visually disconnected from the dark theme.

**Approach:**
- Marked the four mode affordances `_chrome_rendered = True` in
  `navigationform.py::_get_edit_affordances` so the strict guard in `Eigenform.render()`
  doesn't complain when the template doesn't iterate them in the bottom affordance loop.
- Rendered a dedicated segmented control inline in `sleek/navigation.html`'s edit block,
  inside the existing `.sleek-edit-toolbar` row (alongside the +Add form, right-aligned
  via `justify-content: space-between`).
- Active mode = filled blue pill (`#1a2a3c` bg, `#3b82f6` border, `#60a5fa` text, semibold).
  Inactive = neutral gray pill with hover lift.
- The active pill is a `<span>` (no click); inactive pills are real `<button data-ef-post>`
  fired by the existing `eigenform.js` event delegator.

**Files changed:**
- `qms-workflow-engine/engine/navigationform.py` — set `_chrome_rendered=True` on mode affs
- `qms-workflow-engine/app/templates/eigenforms/sleek/navigation.html` — segmented control markup
- `qms-workflow-engine/app/static/sleek.css` — `.sleek-edit-toolbar` flex layout +
  `.sleek-mode-switcher` / `.sleek-mode-pill` styles

**Smoke test:** Bound a NavigationForm in edit mode under `sleek` theme; rendered output
contains exactly one `--active` pill and three clickable `<button data-ef-post>` pills;
execution mode unaffected.

### Diagnosis: descriptor/config drift (open item #2 from prior session)
Reported the issue to Lead. Summary:
- `__config` is the runtime-effective override; `_bind_children` always re-applies it
  AFTER seed reconstruction, so runtime behavior is correct.
- The drift is purely cosmetic: the parent's `__structure` descriptor for a
  NavigationForm child still carries the old `mode`/`default_expanded` values from
  whenever the parent last wrote its structure. Stale data in stored state, not
  incorrect runtime behavior.

**Lead correction:** The on-disk representation of a page/workflow MUST be the single
source of truth (stateless server principle). Don't make `__config` the canonical
location; eliminate it entirely. The structure descriptor (`__structure`) is canonical;
all runtime overrides flow into it.

### Cross-cutting refactor: __structure as single source of truth
Authorized as part of CR-110.

**Architectural change:** Removed parallel state (`__config`, `__label`, `__instruction`)
that competed with the structure descriptor. After this refactor, all per-eigenform
seed-time fields (label, instruction, mode, multiline, min_length, etc.) live exclusively
in the parent container's `__structure` descriptor entry for that child.

**Base helpers added** (`engine/eigenform.py`):
- `_get_my_descriptor()` — locate self's entry in parent's `__structure`.
- `_set_my_field(name, value)` — mutate top-level descriptor field (label, instruction,
  editable). Also updates `self.{name}` so the runtime instance reflects the change
  before the next bind.
- `_set_my_config(name, value)` — mutate config-level field (mode, multiline, etc.).
- `_apply_descriptor(desc)` — apply scalar fields from a descriptor onto self;
  subclasses override for non-scalar fields.
- `_migrate_legacy_overrides()` — called from `bind()`, folds legacy
  `__config`/`__label`/`__instruction` entries into the descriptor and deletes the
  sidecar keys; re-applies the folded descriptor to self so the runtime catches up.

**`from_descriptor` patched** (`engine/registry.py`): on the seed-match path, now
deepcopies the seed and applies the descriptor's scalars before returning. Eliminates
the seed-vs-descriptor divergence root cause.

**`set_label`/`set_instruction` migrated** (`engine/eigenform.py`): write into
descriptor, no more sidecar reads. `effective_label`/`effective_instruction` collapse
to trivial pass-throughs (kept as a stable read-side API).

**Snapshot/restore migrated** (`engine/eigenform.py`): base snapshot captures self's
descriptor entry (deepcopied); restore writes it back AND re-applies. Per-form
snapshot overrides now retain only the non-descriptor state they care about
(NavigationForm: `__children_scope`; ListForm: `__value`).

**Per-form sweep** — removed `_effective_config`, replaced sidecar reads/writes with
direct `self.{field}` access and `_set_my_config(field, value)`:
- `engine/textform.py` — multiline, min_length, max_length
- `engine/numberform.py` — min_val, max_val, step, slider, unit
- `engine/dateform.py` — include_time, min_date, max_date
- `engine/booleanform.py` — true_label, false_label
- `engine/dictionaryform.py` — key_label, value_label
- `engine/multiform.py` — fields (overrides `_apply_descriptor` to convert dicts back
  to `FieldDescriptor` instances)
- `engine/listform.py` — allow_constraints
- `engine/navigationform.py` — mode, default_expanded; removed the `__config` read
  in `_bind_children` (descriptor application via `from_descriptor` covers it now)

**Containers always write `__structure`** — removed the `if self.editable:` gate in
`engine/groupform.py` and `engine/navigationform.py`. Children's descriptor entries
must always exist for `_set_my_*` to find them.

**PageForm scope alignment** (`engine/pageform.py`): PageForm previously wrote
`__structure` at scope=binding-scope (instance ID), but its children are bound at
scope=self.key. That mismatch meant children couldn't locate their descriptor entry
via `self._scope`. Changed PageForm to write `__structure` at scope=self.key,
consistent with NavigationForm/GroupForm convention. Updated all related reads/writes
in PageForm (`_get_structure`, `_save_structure`, `_rebuild`, `_rebuild_from_seed`,
reset handler).

**Smoke tests:**
- Direct: mutate mode + label + multiline, rebind from disk, all overrides survive,
  no `__config`/`__label`/`__instruction` sidecars present. ✓
- Legacy migration: pre-write store with sidecar keys, bind, runtime reflects
  migrated values, sidecars deleted, descriptor updated. ✓
- Parity test: 11/11 passing. ✓
- Real Flask instances (4 live page instances copied from `data/`): all render JSON
  and HTML with 200 OK. ✓

### Deep Dive page (/deepdive) — engine self-analysis
Lead asked for a thorough explanation of "what this is all about" — emphasizing that the
page should be grounded in what the code IS, not what its docs claim, and should surface
any delta between aspiration and delivery. Plus a code-quality audit.

**Approach:** Spawned two parallel Explore agents (engine architecture + page composition
patterns), both instructed to ignore docstrings/READMEs and read code only. Verified
load-bearing claims independently (88 `if action == ...` across 20 files; PageForm 1064
lines, TableForm 1192, NavigationForm 665; `_set_my_config` does no value-type validation;
PageForm has zero awareness of `depends_on` edges).

**The page:** `pages/deepdive.py` — a PageForm wrapping a NavigationForm in tabs mode,
seven InfoForm sections. Self-referential by construction (the engine analyzing itself,
rendered by itself). Sections:
1. What this is (literal characterization, no marketing)
2. The lifecycle (seed → bind → reconstruct → handle → serialize/render)
3. What works well (descriptor-as-truth, atomic writes, parity test, …)
4. The aspiration (HATEOAS affordances, faithful projection, mutable structure)
5. The delta (5 honest gaps: action dispatch, string sibling refs, no value validation,
   no concurrency model, mutable structure theme-coupled)
6. Code-quality audit (megafiles, NavigationForm-as-four-classes, scoping inconsistency,
   from_descriptor callable loss, migration cruft in hot path, demos in production registry)
7. Recommendations (action registry, architecture doc, typed sibling refs, config validation, …)

**Routes:** `/deepdive` (page) and `/deepdive/<path>` (eigenform actions). Bound directly
without InstanceRegistry — fixed scope and url_prefix. Sidebar link added to `base.html`.

**Verification:** All 7 tab labels render; tab-switching POST returns 200; section content
visible after navigation; sidebar link wired; 12/12 parity tests pass (was 11 — auto-discovered
the new page).

### Morphdom integration for in-place DOM diffing
Lead asked about React after reading the deepdive page; I argued React would be a misfit
(state-location divergence; AI/replayability properties depend on server-side truth) but
flagged morphdom-style diffing as a near-pure win at near-zero cost. Lead said implement.

**What:** Vendored `morphdom-umd.min.js` v2.7.4 (12KB) from unpkg into `app/static/`.
Inserted `<script>` for it in `app/templates/page.html` before the existing `eigenform.js`
include. Added `_efSwap(html)` in `app/static/eigenform.js` — wraps the html string in a
matching `id="page-content"` div and calls `morphdom(root, ..., {onBeforeElUpdated: ...})`.
The `onBeforeElUpdated` hook returns false when the from-element is the currently-focused
INPUT/TEXTAREA/SELECT, so a user mid-typing is never disturbed. Both `_efPost` (in
eigenform.js) and the SSE-driven page reload (in page.html) now go through `_efSwap`.

**Graceful fallback:** if `typeof morphdom === 'undefined'`, `_efSwap` falls back to the
prior innerHTML+scrollY save/restore. So if the static asset fails to load the page still
works.

**What's gained (browser-only):** window scroll, nested-scroll, `<details>` open state,
CSS transitions in flight, input focus, caret position, in-progress unsubmitted text
all preserved across POSTs. The previous explicit `var scrollY = window.scrollY; ...
window.scrollTo(0, scrollY);` kludge becomes unnecessary on the morphdom path.

**What's NOT gained:** wire bandwidth is unchanged — server still returns the full
re-rendered subtree. Reducing payload would require a separate, server-side change
(POSTs return only the targeted eigenform's HTML, parallel to what the JSON path
already does).

**Verification:** 12/12 parity tests pass. `test_client` smoke: `/deepdive` GET returns
HTML with morphdom included BEFORE eigenform.js; static asset served (200, 12165 bytes);
POST tab switch returns 200; subsequent GET reflects the switched tab. Browser-side
behavior (focus preservation, scroll, etc.) cannot be tested from `test_client` —
requires a live browser.

### Cleanup follow-on: deleted effective_label/effective_instruction shims
After the descriptor refactor these properties just returned `self.label`/`self.instruction`
unchanged — pure indirection. Deleted them and inlined every call site to read the
attribute directly. This is the readable end-state: no two-name confusion, no shim
that hints at an override mechanism that no longer exists.

`_effective_items` (CheckboxForm), `_effective_options` (ChoiceForm), `_effective_text`
(InfoForm) kept — they are legitimate computed views over embedded child eigenforms,
not sidecar shims.

Files touched in cleanup: `engine/eigenform.py`, `engine/navigationform.py`,
`engine/checkboxform.py`, `engine/choiceform.py`, `app/routes.py`.

Re-verified: 11/11 parity tests pass; all 4 live Flask instances render JSON+HTML 200.
