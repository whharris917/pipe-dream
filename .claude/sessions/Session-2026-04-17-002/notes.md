# Session-2026-04-17-002

## Current State (last updated: framing page rewrite complete)
- **Active document:** CR-110 IN_EXECUTION (engine vocabulary cleanup, no new CR required)
- **Current EI:** None specific
- **Blocking on:** Nothing — rename + framing rewrite both landed, tests green
- **Next:** TBD — awaiting Lead direction (commit, review, or next wedge)

## Context carried from 2026-04-17-001
- Framing design plan all three passes LANDED: naming/architecture.md, typed composition (SiblingRef + field-type validation + Literal enums), error boundaries (render_safely across 18 sites).
- Parity test hardening LANDED: 72 tests across 9 categories.

## Progress Log

### Session opened
- Read CURRENT_SESSION (initialized Session-2026-04-17-002), prior session notes (2026-04-17-001), SELF.md, PROJECT_STATE.md.
- Read QMS-Policy, START_HERE, QMS-Glossary.
- Inbox empty.

### Lead discussion: "eigenform" naming
- Lead raised concern that "eigenform" is gaudy/niche and may deter external developers. Claude agreed — the name was path-dependent (coined with original meaning "self-contained" in March, retrofitted to "identity-preserving" later; `architecture.md` §6 already admitted it equated to "Component"). Decision: full rename to Component, including the Form suffix on all concrete subclasses (TextForm → TextComponent, etc.). All under CR-110; no new CR.

### Rename execution (complete)
- **Survey**: 196 `Eigenform`, 825 `eigenform`, 27 `*Form` classes, 596 `ef-` CSS hits, 193 `data-ef-` attributes, 44 templates in `app/templates/eigenforms/`. Submodule on `dev/content-model-unification`, clean tree.
- **Script** (`rename_to_component.py`, deleted after): exact-string substitutions for class names, PascalCase `Eigenform`→`Component`, lowercase `eigenform`→`component`, `\bef-`→`c-`, `data-ef-`→`data-c-`, `(?<=[\._])ef(?=[A-Z])`→`c` for JS identifiers. 98 files content-modified, 28 files renamed, 1 directory renamed.
  - `engine/eigenform.py` → `engine/component.py`
  - 25 × `engine/*form.py` → `engine/*component.py`
  - `app/static/eigenform.js` → `app/static/component.js`
  - `pages/eigenform_gallery.py` → `pages/component_gallery.py`
  - `app/templates/eigenforms/` → `app/templates/components/`
- **Surgical fixes** (Edit): `removesuffix("Form")` → `removesuffix("Component")` at two call sites (`component.py:524`, `registry.py:42`), plus the docstring that described the stripping rule. README line 238 prose. "Register an component" → "Register a component" typo in registry docstring.
- **Article fixups** (`fix_articles.py`, deleted after): `\ban component\b`→`a component` etc. across 18 files. The regex missed cases where HTML tags intervened (e.g., `An <strong>component</strong>`); handled those in framing.html by hand.
- **Prose cleanup**: framing.html §0 Primer — removed the "Eigen as in eigenvector" etymology paragraph (no longer coherent), reworded "The central idea: an component" heading and lead para. architecture.md §6 — dropped the trivial "Component subclass ≈ Component class" row, added a short intro note; added a change log entry for this session.
- **Left alone** (intentional): `form` lowercase class attribute (still holds the registry type name like `"text"`, `"table"`; separate question); "Form submissions" / "Form styles" comments in component.js and style.css (refer to HTML `<form>`, not the class); historical session notes under `.claude/sessions/`; legacy-type comments in registry.py referring to the pre-unification `TabForm` etc. (historical, correct as-is).

### Verification
- `python -m pytest tests/test_parity.py` → **72/72 pass**.
- Flask test client: all 8 top-level routes (`/`, `/portal`, `/framing`, `/deepdive`, `/readme`, `/qms`, `/workspace`, `/inbox`) return **200**.
- Instance smoke test: spawned a `component-gallery` instance via `POST /instances`, fetched `/pages/{id}` in both JSON (7.5KB) and HTML (21.5KB) — both 200. Deletion also 200.
- Remaining `\bForm\b` occurrences in the submodule: 3, all legitimate (the two HTML-form comments + one historical reference in the architecture change log).
- Remaining `Eigenform`/`\beigenform\b` in the submodule: only inside `.claude/sessions/` (historical notes, not touched).

### Framing page rewrite (complete)
Updated `/framing` to match the post-rename reality. Targeted edits:
- **Hero**: new subtitle ("How the engine maps to React conventions, and why"). New thesis paragraph frames the page as documentation of alignment, not prospective design plan.
- **§1 Thesis**: dropped the "concepts are unnamed / three costs" framing. New version names what the engine calls things (Component, Props, State, Derived, reconciliation, portal, faithful projection) and states the payoff as cumulative rather than dramatic.
- **§2 Mapping table**: dropped the trivially self-referential "Component class ≈ Component subclass" row. Updated "Error boundary" row from Absent to Present with notes pointing at `render_safely()`. Updated callout beneath the table.
- **§3 Props/State/Derived**: replaced "No document names this yet" hook with the bug-surface framing from `architecture.md`. Callout now points readers to `docs/architecture.md §1` as authoritative.
- **§4 Reconciliation**: updated section hook to note the `reconcile` alias. Replaced "Concrete actions, small" prospective list with "What shipped" retrospective list (docstring + alias + typed SiblingRef). Added "What's still open" covering the callable-preservation diagnostic follow-on.
- **§5 Error boundaries**: rewrote from "Today vs Proposed" to "Before vs Now" reflecting what landed in Pass 3. Added "Shipped & open" section enumerating scope actually delivered vs parked scope.
- **§8 Design plan → "How we got here"**: retitled as retrospective arc. All four passes now show Landed status. Added Pass 4 (the rename itself) as a new entry. Added "What's still open" list covering callable diagnostic, error-boundary expansion, Context primitive, and the action-dispatch-as-reducer opportunity flagged from `/deepdive`.
- **TOC**: §8 entry updated to "How we got here".

Only remaining `Eigenform`/`eigenform` references in framing.html are in the Pass 4 description itself, which is intentional historical documentation of what was renamed FROM.

### Verification after rewrite
- 72/72 parity tests still pass.
- `/framing` returns 200 (71KB rendered).

### Known follow-ons (not done this session)
1. **`form` attribute.** The lowercase `form = "text"` class attribute (registry type identifier) is now inconsistent with the PascalCase `Component` base. Candidates: `type`, `component_type`, or leave. Not urgent; flagged.
2. **`dev/content-model-unification` branch name.** No longer accurate but historical and not breaking. Could be renamed at next major checkpoint.
3. **Callable-preservation diagnostic.** Planned as a Pass 2 follow-on; still silent today.
4. **Action-dispatch-as-reducer.** 88 branches across 20 files. An `ActionRegistry` with named dispatch would formalize the pattern.

## Artifacts
- Branch: `dev/content-model-unification` (submodule qms-workflow-engine), uncommitted rename changes in working tree.
- No commits yet — waiting for Lead review.
