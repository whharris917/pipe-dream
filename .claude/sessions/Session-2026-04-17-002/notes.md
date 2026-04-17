# Session-2026-04-17-002

## Current State (last updated: /wiki landed, all pushed)
- **Active document:** CR-110 IN_EXECUTION (engine vocabulary cleanup + documentation expansion, no new CR required)
- **Current EI:** None specific
- **Blocking on:** Nothing — all work this session landed and pushed to origin
- **Next:** TBD — awaiting Lead direction
- **Commits this session:** 4 submodule commits (rename, /learn × 2, /wiki), 4 corresponding root commits

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

### Rename committed and pushed
- Staged engine/, app/, pages/, tests/, docs/, README.md in submodule (excluding untracked `.claude/`).
- Submodule commit `7543631`: "Session-2026-04-17-002: Rename Eigenform → Component throughout engine" — 103 files changed, git detected all renames at 80-98% similarity.
- Pushed submodule to `dev/content-model-unification`.
- PROJECT_STATE vocabulary refreshed: class names, module paths, `_efSwap`→`_cSwap`, `_efPost`→`_cPost`, `data-ef-`→`data-c-`, plus new §1 entry documenting the rename.
- Root commit `f345527`: "Session-2026-04-17-002: Eigenform → Component rename landed" — submodule pointer, PROJECT_STATE, session notes.
- Pushed root to `main`.

### Learning Portal — fundamentals (complete)
Lead asked for a new /learn page with subpages in a tutorial/lesson format. Built infrastructure + five progressive lessons covering the engine's mental model.
- **Landing page** (`app/templates/learn.html`): hero, intro card, lesson grid with numbered cards linking to each lesson. Next-step callout pointing at /framing, /readme, /portal Component Gallery.
- **Shared chrome** (`app/templates/learn/_lesson_base.html`): breadcrumb, lesson number label, title + italic objective, body styles for h2/h3/p/ul/code/callouts/code-blocks, takeaways section, prev/next nav, lesson-chip component for takeaway tags. Each lesson extends this base and overrides `{% block lesson_content %}`.
- **Lesson 1 — Hello, Component** (`/learn/hello`): build the smallest possible page from scratch, understand PageComponent + TextComponent, see the JSON/HTML duality, add a CheckboxComponent.
- **Lesson 2 — The Core Loop** (`/learn/loop`): four-stage request cycle (Define → Bind → Serve → Handle), statelessness, hot reload, concrete walkthrough of "Alex clicks Save."
- **Lesson 3 — Where Data Lives** (`/learn/data`): props / state / derived with concrete rule of thumb, mutation APIs, Store layout example with __structure alongside state.
- **Lesson 4 — Composing Pages** (`/learn/compose`): containers, NavigationComponent's four modes from one class, keys and scope, sibling-reading components with `depends_on` and SiblingRef, RepeaterComponent and GroupComponent subclassing.
- **Lesson 5 — Humans and Agents** (`/learn/humans-and-agents`): affordance anatomy, HATEOAS loop, faithful projection invariant, parity test sketch, controlled vs uncontrolled state boundary, pointers onward to /framing /readme /portal /deepdive.
- Sidebar nav added with Learning Portal entry (pen icon) between Framing and the bottom of the nav.
- Routes: `/learn` (index) and `/learn/<slug>` (dispatches via `_LEARN_LESSONS` dict).
- All 6 pages return 200; unknown slugs 404; parity still 72/72.
- Submodule commit `d68dc56`, root `a6b235d`. Both pushed.

### Learning Portal — deep dives (complete)
Lead asked for more lessons, specifically flagging "Affordance Generation, Rendering, and Parity Testing" as required. Added three deep-dive lessons filling in the mechanics.
- **Lesson 6 — Affordances, Rendering, and Parity Tests** (`/learn/affordances`): Affordance dataclass hierarchy, per-component generation, two-tier serialization (`_serialize_full` vs `serialize`), render_aff / render_btn helpers, the five `data-c-*` URL-carrying attributes, affordance flotation as a Portal pattern with structured `targets` dicts, 72 parity tests across 9 categories broken down by what each checks, how to add a new affordance type.
- **Lesson 7 — Reconciliation and the Descriptor** (`/learn/reconciliation`): three-tree mental model (seed / descriptor / bound), `__structure` as on-disk canonical, from_descriptor's deepcopy-seed-apply-scalars algorithm with concrete Store JSON example, callable-preservation silent failure mode explained, SiblingRef with `expects=` validation at bind time, field-type validation at `_set_my_field` / `_set_my_config` boundary, what reconciliation does NOT do.
- **Lesson 8 — Mutation Mechanics** (`/learn/mutation`): prop vs structural mutation axes, `_set_my_field` / `_set_my_config` as the two mutation APIs, edit mode pencil pattern with per-component undo via snapshots, mutable_structure=True pages with all seven structural actions (add/remove/move/reparent/group/ungroup/rebuild), surgical state cleanup on remove, self-modifying pages via `ActionComponent.structural_actions`, a "mutation matrix" table showing what changes go where.
- **Landing page regrouped** into Fundamentals (1-5) and Deep Dives (6-8) with labeled group headers.
- **Lesson 5's next-link updated** to point at Lesson 6 (previously ended the portal).
- **Gotcha during dev:** Lesson 6 shows Jinja template syntax in code examples (`{{ render_aff(affordance) }}`). Jinja tried to evaluate it — 500 on first render. Fixed by wrapping the example block in `{% raw %}...{% endraw %}`.
- Submodule commit `7bdff09`, root `67d5dd4`. Both pushed.

### Wiki page (complete)
Lead asked for a "hypothetical Wikipedia page" on the engine. Built as a single static HTML template mimicking the Wikipedia visual idiom.
- **Content**: lead paragraph, History, Architecture (core loop, three trees, HATEOAS), Features (component types, faithful projection, affordance flotation, mutable pages, error boundaries), Design philosophy, Terminology (definition list), Comparison matrix vs React/Phoenix LiveView/Svelte, Limitations pulled from /deepdive, See also, References, External links.
- **Visual treatment**: Linux Libertine / Georgia serif titles with horizontal rules under h1 and h2, sans-serif body, infobox on right with alternating blue section bands, TOC box with centered head, two-column footnote-style references, categories footer with pill-style tag links, "Retrieved from" italic footer.
- **References**: pointers to actual in-project docs (/framing, /learn/*, /readme, /deepdive, docs/architecture.md change log). No fabricated reception or third-party coverage — the article leans on internal documentation as its citation base, keeping the hypothetical-article conceit honest.
- **Infobox** covers Developer, Initial release (March 25, 2026 as Eigenform engine), Stable release, Repository, Written in Python, Engine stack (Flask, Jinja2, morphdom), Platform, Website, plus Key Concepts section and Parity section.
- Sidebar nav Wiki entry added (fleur-de-lis icon).
- /wiki returns 200 (41KB rendered).
- Submodule commit `6226602`, root `962ee5a`. Both pushed.

## Artifacts
- Branch: `dev/content-model-unification` (submodule qms-workflow-engine), commits `7543631` → `d68dc56` → `7bdff09` → `6226602` pushed to origin.
- Main branch of root: commits `f345527` → `a6b235d` → `67d5dd4` → `962ee5a` pushed to origin.
- Temporary scripts (`rename_to_component.py`, `fix_articles.py`, `_rename_project_state.py`) created during work and deleted before commit.
