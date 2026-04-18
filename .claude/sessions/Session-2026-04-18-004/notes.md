# Session-2026-04-18-004

## Current State (last updated: session start)
- **Active document:** None (continuing dev branch work)
- **Current EI:** N/A
- **Blocking on:** Awaiting user direction
- **Next:** TBD

## Context from Previous Sessions
- 003: Engine quality pass completed — callable-preservation diagnostic, action-dispatch registry (20 components migrated, 89 if/elif eliminated), megafile split (page.py 1152→631, tableform.py 1248→993). Wiki intro rewritten. 72/72 parity tests pass.
- Razem rename queued but not executed.
- Class taxonomy refactor (001) already landed.

## Observations at Session Start
- `prompt.txt` open in IDE contains current wiki intro with two alternative new paragraphs (`<new>` and `<alternate new>`) addressing impedance mismatch / faithful projection / affordance floating. Likely source of today's task — may need to choose/merge/refine.
- Working tree clean except CURRENT_SESSION + settings.local.json.

## Progress Log

### [session start] Session initialization
- Read CLAUDE.md, SELF.md, QMS-Policy, START_HERE, QMS-Glossary, PROJECT_STATE (first 150 lines), previous session notes.
- Created Session-2026-04-18-004 folder and updated CURRENT_SESSION.
- Inspected `prompt.txt` in IDE (wiki intro with two candidate new paragraphs on agent/human impedance mismatch).

### Wiki intro rewrite
- Reviewed Lead's two candidate paragraphs in `prompt.txt` (`<new>` and `<alternate new>`). Identified duplication with existing ¶2 (faithful projection/parity suite), a technical error in `<alternate new>` ("DOM tree" vs "component tree"), and placement issue (both fired before affordance was defined).
- Produced single synthesized paragraph (~115 words) covering impedance mismatch + affordance flotation, placed as new ¶4 between HATEOAS (¶3) and declarative/imperative (¶5).
- Written to `wiki-intro-proposal.txt` at project root.
- Applied to `qms-workflow-engine/app/templates/wiki.html` lines 301–303.

### Doc alignment pass — README / Framing / Wiki / Learn
Brought four documents into alignment with recent code changes (class taxonomy, `affordances()`, auto-keys, `_actions` registry, `_callable_fields` diagnostic, megafile split):

- **README.md** — Fixed stale `pagecomponent.py` → `page.py`; added `page_mutations.py` and `tableform_actions.py` to file layout; added `affordances()` to core-protocol bullet list; noted dispatch-via-registry in `handle(action)` description; documented optional `key=` + auto-generation; rewrote "Type names are derived..." paragraph to describe explicit `form` class attribute + alias support.
- **framing.html** — Rewrote Pass 4 description to cover the full two-step rename (Eigenform→Component; *Component→role-specific suffixes); added Pass 5 section ("Harvest") covering action registry + callable diagnostic + megafile split; trimmed "what's still open" to remove items that have landed (callable diagnostic, action dispatch); reframed the callable issue as "root fix" remaining open.
- **wiki.html** — Updated History ¶ that said "four framing passes" to describe the full sequence including Pass 4 role-suffix refactor and Pass 5 harvest; replaced Limitations bullet about "88 if/elif branches" (no longer true) with updated "Callable-preservation reconciliation gap" bullet describing the diagnostic as visible-but-not-root-fixed.
- **Learning Portal** — `lesson_1_hello.html`: "TextComponents" → "TextForms". `lesson_2_loop.html`: rewrote "4. Handle" section to describe `handle()` dispatching via `_actions` registry; updated code example; fixed step-by-step walkthrough. `lesson_3_data.html`: updated mutations-through-_handle() sentence to describe registry dispatch. `lesson_6_affordances.html`: updated "writing a new affordance" instructions (step 4 now describes registry entry rather than if-branch). `lesson_7_reconciliation.html`: updated warning callout to reflect that the silent failure is now visible via `_callable_fields` + `_missing_callables`. `lesson_8_mutation.html`: fixed `_handle()` references to `handle()` for Page; corrected Action code example (`on_trigger` → `action_fn`, signature `lambda state` → `lambda context, store, scope`); updated takeaways.

Verified: parity tests 72/72 pass after all edits.

### Lesson 1 iterative polish
- Lead flagged false Accept-header-in-address-bar instruction; replaced with real `curl` commands. JSON is the engine default; no header needed for agent view.
- Added actual serialized JSON dump (generated via bind + serialize on a temp dir) showing the Page/TextForm/CheckboxForm shape, with "Things to notice" bullets.
- Fixed `CheckboxForm(options=...)` → `items=` in both code examples (would have raised TypeError if readers ran them).
- Removed `key=` from all child components in both examples; added new "When keys matter" section explaining auto-generation + the two reasons to specify explicitly (stable URLs, cross-component references).
- Added "Extracting children for legibility" section showing the variable-substitution refactor pattern.
- Corrected a false claim that Page keys appear in the URL (they don't — URL uses the auto-generated 8-char hex instance_id).

### New Components page
- Added `/components` route in `app/routes.py` with a `_COMPONENT_TAXONOMY` data structure: 7 categories × 25 classes, each entry with (class name, form attribute, description, completion rule).
- Created `app/templates/components_taxonomy.html`: hero intro defining what a component is, jump-to TOC chip bar, one card per category with per-class rows.
- Added sidebar link in `base.html` (icon ⚉) between README and Deep Dive.
- Smoke test confirms all 25 class names render, 7 category sections present, active-highlight works on the `/components` page.

### Score removal
- Created `engine/helpers.py` with `grade(answer_key)` (returns compute_fn) and `graded(answer_key, **kwargs)` (returns Computation with depends_on derived from answer_key). Semantics preserved: case-insensitive string compare, dict-exact, callable predicate.
- Migrated `pages/quiz_portal.py` (3 Score→graded) and `pages/component_gallery.py` (1 Score→graded).
- Deleted `engine/score.py` and `app/templates/components/score.html`.
- Removed Score from `engine/registry.py` (import + class list + describe_types entry). Registered names: 31 → 30.
- Updated docstrings in `engine/component.py`, `engine/validation.py`, `engine/computation.py`.
- Updated public docs: `README.md` (class count 26→25, removed row, updated Computation description), `app/routes.py` _COMPONENT_TAXONOMY (removed Score entry from Derivations), `app/templates/wiki.html` (two mentions), `app/templates/framing.html` (three mentions incl. the Score example in the callable-problem callout → now uses a width/height area example), and learning portal lessons 1, 3, 4, 7.
- `pages/deepdive.py` updated to drop Score from its sibling-reference list.
- Unit-tested grade() compute_fn end-to-end (all-correct / partial / empty cases).
- Parity tests 72/72 pass. All 11 static pages (/components, /portal, /readme, /wiki, /framing, /learn, 4× lessons, /deepdive) return 200 with no Score residue.

### DynamicChoiceForm → SiblingBind generalization
- Created `engine/sibling_bind.py`: `SiblingBind(key, fn, expects=None, default=None)` wraps a field value that resolves from a sibling's current state at serialize time. `__deepcopy__` preserves the callable (mirrors Computation.compute_fn). `as_sibling_ref()` yields the equivalent SiblingRef for bind-time validation.
- Extended `Component._sibling_refs()` base implementation to auto-discover refs from any dataclass field whose value is a SiblingBind — subclasses get free bind-time validation for reactive fields.
- Added `Component._resolve_field(name)` helper — returns literal or SiblingBind-resolved value; the one call site to migrate when wiring a field as reactive.
- **NumberForm**: `min_val`, `max_val`, `step` now reactive-capable. `_serialize_state`, `get_affordances`, and `_do_set` all read through `_resolve_field`. Stale flag set when stored value falls outside resolved bounds.
- **ChoiceForm**: `options` now either a literal list (editable in-place via the `ListForm` child as before) or a SiblingBind (reactive, no in-place editing). New `_current_options` property routes to the right source. Stale flag + Clear affordance when the stored value isn't in the resolved options. Replaces DynamicChoiceForm's full semantics.
- Created `pages/reactive_demo.py` as the validation surface: Tier ChoiceForm drives a NumberForm's max bound. End-to-end test confirms: bounds resolve correctly per tier, out-of-bound values rejected at action time, stale flagged when tier changes make stored value out-of-bounds, missing-sibling caught at bind time with SiblingRefError.
- Migrated `pages/component_gallery.py`: continent→country demo now uses `ChoiceForm(options=SiblingBind("continent", fn))` instead of DynamicChoiceForm. End-to-end test confirms options update, stale detection, Clear affordance cycle.
- Deleted `engine/dynamicchoiceform.py` and `app/templates/components/dynamicchoice.html`. Removed from registry (imports + register list + describe_types entry). Registered names: 30 → 29.
- Extended `from_descriptor` callable-preservation diagnostic: when the seed has SiblingBind-valued fields that the fresh instance doesn't (post-rename/move), they're added to `_missing_callables`. Unit-tested across seed/no-seed/wrong-key-seed paths.
- Updated docs: README (class count 25→24, ChoiceForm row mentions reactive options, NumberForm/bounds, new "Reactive fields" section, ordering-constraints bullet generalized, Dynamic Forms → Imperative section), wiki (history paragraph + limitations bullet updated, DynamicChoiceForm→SiblingBind framing), framing (reactive-types table row removed, six→five sibling-reading types with SiblingBind mention), components taxonomy page (ChoiceForm/NumberForm descriptions updated, new reactive-fields paragraph in hero, Dynamic category → Imperative), lessons 3/4/7 all updated, deepdive.py self-analysis text updated. Historical session logs left intact.
- Final sweep: 79/79 tests pass. All static pages return 200. No DynamicChoice references in user-facing pages (only intentional historical markers in two module docstrings and one architecture.md session log).

## Current State (last updated: end of session)
- **Active document:** None (dev branch work)
- **Next:** TBD
