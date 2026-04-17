# Session-2026-04-17-001

## Current State (last updated: session open)
- **Active document:** CR-110 IN_EXECUTION v1.1 (workflow engine)
- **Current EI:** None active
- **Blocking on:** Nothing — awaiting Lead direction
- **Next:** TBD

## Context
- Prior session (2026-04-16-003) finished a major refactor: `__structure` is the single source of truth for eigenform overrides; sidecar keys (`__config`/`__label`/`__instruction`) eliminated and legacy-migrated on bind.
- Morphdom vendored and wired into `_efSwap`; in-place DOM diffing preserves focus/scroll/transitions across POSTs.
- `/deepdive` page added — engine self-analysis with honest ambition-vs-delivery delta.
- NavigationForm mode switcher: segmented pill control in `sleek/navigation.html`.

## Open questions for Lead
- Typed composition discipline (Move 1 SiblingRef + Move 2 field-type validation + Move 3 Literal enums) is queued as Ready backlog. ~1 day as one CR.

## Progress Log

### Parity test audit (parked)
- Audited `tests/test_parity.py`. 13 findings across correctness/coverage/hygiene.
- Key finding: the test claims "agents and humans see the same action surface" but only does JSON⊆HTML, not HTML⊆JSON. Also skips body shape, HTTP method, and has dead-code `_chrome_rendered` handling (defused by `serialize()` popping the flag at engine/eigenform.py:501).
- Missed attributes: `data-ef-add`, `data-ef-url`.
- Parked per Lead direction — do after framing design plan (Passes 1–3). Added to PROJECT_STATE Ready backlog with full findings.

### Parity-test hardening (complete)
Rewrote `tests/test_parity.py` from 12 tests (forward-parity only + smoke) to 72 tests across 9 categories. Each closes a specific audit finding.

**Fixtures/hygiene**:
- `tmp_path_factory` fixture replaces the real `data/` directory. No more state bleed between test runs.

**Extraction helpers**:
- `extract_json_affordances(data)` — recursive walk that reads from `_serialize_full()` (so `_chrome_rendered` flags survive). Walks into parameterization dicts (`targets`, `tabs`, `sections`, `steps`, `options`) and synthesizes one affordance entry per target URL found — this correctly treats O(N)→O(1) compound affordances as legitimately declaring all their per-target URLs.
- `extract_html_actions(html)` — HTMLParser-based extractor scanning FIVE URL-carrying attributes: `data-ef-post`, `data-ef-submit`, `data-ef-change`, `data-ef-add` (palette one-click), `data-ef-url` (builder canvas). Records each action's `data-ef-body` action name for action-level parity.

**Per-page tests (×10 pages = 70 test instances)**:
- `test_serialized_page_has_required_shape` — agent-facing `serialize()` must contain `affordances` (list). Separately asserts internal `_serialize_full()` carries `form="page"` and matching `key`.
- `test_no_empty_url_affordances` — no non-chrome, non-disabled affordance may have empty URL.
- `test_affordance_methods_are_declared` — every affordance with a URL has a non-empty method.
- `test_forward_parity` — JSON ⊆ HTML, excluding `_chrome_rendered` compounds (agent-JSON-only by design per `docs/architecture.md §4`).
- `test_reverse_parity` (NEW) — HTML ⊆ JSON. Every clickable HTML action URL must be declared somewhere in JSON. Closes the one-way-check audit finding.
- `test_action_name_parity` (NEW) — where both sides declare an action name for the same URL, they match. Catches typos like `set_valeu`/`set_value` where URLs match but bodies differ.
- `test_affordance_urls_resolve` (NEW) — every JSON affordance URL routes to a real eigenform via `find_eigenform`. Catches URLs that parity-match but 404 at runtime.

**Pan-page tests (×2)**:
- `test_all_pages_render` — every page renders without exception and produces non-empty HTML.
- `test_all_pages_serialize` — every page serializes to a dict with `affordances`. Dropped the wrong earlier assertion that `form`/`key` live in `serialize()` output — they are deliberately stripped for agent cleanliness.

**Dead-code removal**: the original test had `if aff.get("_chrome_rendered"): continue` reading from `serialize()` — but `serialize()` pops the flag at `engine/eigenform.py:501`, so the skip never fired. The new suite reads from `_serialize_full()` where the flag survives. Forward parity now legitimately excludes floated compounds.

**Injection test**: confirmed the reverse parity fires when a ghost URL is injected into HTML that has no JSON counterpart. Confirmed `find_eigenform` returns `None` for unknown paths.

**Coverage during development**: an intermediate run surfaced a real faithful-projection concern in NavigationForm sequence mode (SwitchForm's `is_complete=True` when its dependency is unset causes HTML to render a step-jump button whose body is not declared as a JSON affordance). After the extractor was taught about parameterization dicts the test no longer flags it as a URL-parity violation — the URLs coincide with the Batch affordance — but the underlying engine quirk (step appears "complete" when it's vacuously complete) remains as an open UX concern. Filed nowhere yet; parity is concerned with surface alignment, not semantics.

**Result**: 72/72 pass.

### Pass 3 of framing design plan — Error boundaries (complete)
- **`Eigenform.render_safely()` on base** — default wraps `render()` in try/except; on exception returns a structured error card via `_render_error_card(ef, exc)`. The card is self-contained (no affordances of its own) — a dead-end placeholder describing what failed. Siblings continue to render normally.
- **`_render_error_card` helper** (in `engine/eigenform.py`) — detects Flask debug mode via `flask.current_app.debug` and conditionally includes `traceback.format_exc()` output. Outside Flask context or in production, only the exception class + message are shown. Defensive try/except around the template rendering itself falls back to a minimal inline HTML card if `_error_boundary.html` fails — nothing can make a page unviewable.
- **`app/templates/eigenforms/_error_boundary.html`** — red-bordered card with: "Render error" badge, eigenform type, key label + code, exception class + message, optional collapsible `<details>` traceback in debug mode, italic sibling-continuity hint at the bottom.
- **`app/static/style.css`** — theme-agnostic `.ef-error-boundary`, `.ef-error-header`, `.ef-error-badge`, `.ef-error-type`, `.ef-error-key`, `.ef-error-body`, `.ef-error-message`, `.ef-error-traceback`, `.ef-error-hint` classes. Red/amber palette (#c74545 badge, #fff5f5 background, #fae0e0 code pills, dark-on-light traceback for readability).
- **18 child-render sites swapped to `render_safely()`** across 10 modules: pageform.py (2), groupform.py (2), navigationform.py (2), repeaterform.py (2), tablerunner.py (1), tableform.py (1), switchform.py (1), visibilityform.py (2), historyform.py (1), checkboxform.py (1), choiceform.py (1), infoform.py (1). Verified via grep-sweep that no `ef.render()` remains outside the base class definition.
- **Integration test**: built a PageForm with 3 TextForm siblings, monkey-patched the middle child's `render()` to raise `RuntimeError`. Bound page rendered without 500; HTML contained `ef-error-boundary` with the exception message, class, and broken key; both good siblings rendered normally; `render_safely()` on the broken child returned the card directly.
- **Parity**: 12/12 pass. All top-level pages (/, /framing, /deepdive, /readme) still serve 200.
- **Deliberately parked for a future pass**: `serialize_safely()` (JSON-side equivalent — an agent-facing error card has no obvious form yet); bind-error scoping (the eigenform tree literally does not exist post-bind-failure, so there is nothing to contain); `_handle()` error scoping (partial-mutation risk on action failure).

### Pass 2 of framing design plan — Typed composition discipline (complete)
- **Move 1 — SiblingRef**: `engine/sibling_ref.py` — `SiblingRef` as a `str` subclass so existing call sites (URL composition, store lookups, JSON serialization, `render_dependency_line`) keep working unchanged. Carries optional `.expects: type | None` for bind-time type assertion. Seven sibling-reading eigenforms (SwitchForm, VisibilityForm, DynamicChoiceForm, ComputedForm, ActionForm, ValidationForm's ValidationRule, ScoreForm) coerce their `depends_on` via `__post_init__` and expose `_sibling_refs()` on the base Eigenform. `PageForm._validate_sibling_refs()` walks the bound tree after bind, builds a scope map, and raises `SiblingRefError` with actionable diagnostics (owner key, scope, missing ref, known sibling keys) on stale refs or type mismatches. Closes the silent-orphan bug.
- **Move 2 — Field-type validation at `_set_my_field` / `_set_my_config`**: `engine/eigenform.py::_validate_field_value` consults the dataclass field annotation via `typing.get_type_hints` (with per-class caching) and rejects mistyped values. Supports simple types (`str`, `int`, `bool`, `float`), `X | None` (both `typing.Union` and PEP 604 `types.UnionType` forms), `Literal[...]`, and is permissive on complex/unknown annotations so it never obstructs unannotated fields. Closes the silent-corruption bug.
- **Move 3 — Literal on enum-like fields**: `NavigationForm.mode: Literal["tabs","chain","sequence","accordion"]` and `FieldDescriptor.type: Literal["text","choice"]`. Combined with Move 2, invalid strings fail at the boundary with a rich error naming the `Literal` args.
- **Docstring hygiene**: architecture.md §3 and docstring for `from_descriptor` already note callable-preservation as the planned Pass 2 fix — that specific scope was NOT addressed in this pass (still a known limitation). Pass 2's SiblingRef validation is a *different* closure: it catches missing sibling keys, which is adjacent to but distinct from the callable-preservation gap.
- **Verification**: parity 12/12 pass, all top-level pages (/, /framing, /deepdive, /readme) serve 200. Ad-hoc integration tests confirm: stale ref → SiblingRefError with actionable message; `expects=` type mismatch → error names both expected and actual types; `_set_my_config("mode", "carousel")` → TypeError citing the Literal args; wrong-type bool config → TypeError.
- **Docs updated**: architecture.md change log lists Pass 2 entries; framing.html timeline shows Pass 1 and Pass 2 as `Landed` (new status pill added).

### Pass 1 of framing design plan — Naming (complete)
- **`docs/architecture.md`** (440 lines) — authoritative reference covering: (1) Props/State/Derived categories with per-type field enumeration and the "props-in-descriptor, state-in-Store, neither-owns-derived" invariant; (2) Keys and scope with the container-by-container scope convention table (and a note on the PageForm alignment from Session-2026-04-16-003); (3) Reconciliation — full algorithm spec for `from_descriptor`, including the callable-preservation limitation with affected fields enumerated, current mitigations, and the planned Pass 2 fix; (4) Affordance flotation (Portal) — motivation, mechanics, floatable markers (`clear`/`edit`/`batch`), and how to add a new floatable type; (5) Controlled vs uncontrolled state boundary with a decision table; (6) Vocabulary map between this codebase and React terms plus the explicit "don't have by design" list.
- **`engine/registry.py` docstring rewrite** — `from_descriptor` now names the operation "reconciliation" in the first sentence and lifts callable-preservation to a first-class "Raises/Limitation" block rather than burying it mid-paragraph. Cross-references `docs/architecture.md` §3.3.
- **`reconcile = from_descriptor` module-level alias** — zero-cost discoverability for contributors who know the React term.
- **`README.md` Documentation section** — links both `/framing` (pedagogical) and `docs/architecture.md` (reference) with a one-sentence summary of each.
- Smoke tested: `reconcile` is `from_descriptor`, descriptor round-trip works via alias, `/framing` and `/readme` still serve 200, parity 12/12.

## Original progress log

### Session opened
- Read CURRENT_SESSION, prior session notes (Session-2026-04-16-003), SELF.md, PROJECT_STATE.md, QMS-Policy, START_HERE, QMS-Glossary.
- Initialized Session-2026-04-17-001.

### Lead discussion: React analogies for eigenforms
- Discussed which React concepts transfer to the engine. Key observation: bind=render, seed args=props, __structure=element tree, from_descriptor=reconciliation, keys=keys, morphdom=DOM diff, affordance flotation=portal — already there, just unnamed.
- Concrete wedges identified: (1) name what we have in docs, (2) typed composition discipline (already queued), (3) error boundaries (new, small, high-value QMS alignment). Park Context until concrete pain. Don't port hooks/JSX/refs.

### /framing page created
- **First attempt (eigenform):** `pages/framing.py` with PageForm + NavigationForm(tabs) + 8 InfoForms. Worked but InfoForm's paragraph-per-line rendering was limiting — no tables, no diagrams, no card grids.
- **Lead feedback:** don't constrain yourself to the engine's own primitives; this page is prose with tables and diagrams, not an interactive form. Write it as HTML.
- **Second attempt (HTML):** deleted `pages/framing.py`; simplified route to `render_template("framing.html")`; created `app/templates/framing.html` with hero, TOC, 19-row mapping table with colored status pills, Props/State/Derived card grid, reconciliation dataflow diagram, error-boundary before/after panels + code sketch, not-borrowing card grid, and Pass-by-pass design plan timeline.
- **Lead feedback round 2:** page assumes too much engine background; needs pedagogical primer for new contributors.
- **Third pass (pedagogical augmentation):**
  - Rewrote hero to introduce "what this engine is" before the thesis pull-quote; added explicit "skip to §1 if you know the codebase; read the primer otherwise" call-out.
  - Expanded TOC to surface the primer as item 0 with a star and distinct color.
  - Inserted new §0 Primer section with its own visual treatment (warm amber border, "★ Primer" pill label, dashed subsection dividers). Sub-sections: The problem the engine solves · The central idea (eigenform + four responsibilities + HATEOAS) · The core loop (4-step horizontal diagram with arrows + cycle-back note) · Key vocabulary (11-entry definition list: Seed, Store, Bind, Descriptor, Key, Scope, Affordance, Faithful projection, HATEOAS, Handle, Container vs leaf) · A minimal example (syntax-highlighted `pages/hello.py` + two-phase walkthrough card: first request + user action) · Type catalog (18-row table covering the main types referenced in later sections, grouped by category).
  - Added inline glosses in the mapping table (morphdom defined; affordance flotation explained; controlled/uncontrolled clarified).
  - Softened §1 Thesis opening with a bridge paragraph tying the primer's vocabulary to the React analogy that follows.
- Page now 67KB rendered (was 45KB). Parity 12/12 pass.
