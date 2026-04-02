# Session-2026-04-01-004

## Current State (last updated: 2026-04-01)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** HTMX migration proof of concept — complete
- **Blocking on:** Nothing
- **Next:** Continue HTMX migration to more eigenforms, or next task from Lead

## Progress Log

### Session Start
- Read SELF.md, PROJECT_STATE.md, previous session notes (Session-2026-04-01-003)
- Read QMS docs (QMS-Policy, START_HERE, QMS-Glossary)
- Previous session completed rendering layer modernization: event delegation, CSS extraction, Jinja2 template migration

### HTMX Integration — Proof of Concept
- Downloaded HTMX 2.0.4 (50KB) and json-enc extension (1KB) into `app/static/`
- Added to `page.html` template
- Replaced `location.reload()` in eigenform.js with fetch+swap on `#page-content`
- Updated SSE handler similarly — no more full page reloads
- Updated `wants_html()` to use `best_match` (protects agent JSON API from `*/*` matching)
- Lead tested: works

### HTMX Native TextForm
- Rewrote `text.html` template with native `hx-post`/`hx-vals` — no affordance objects, no render_aff()
- Added `hx-target="#page-content"`, `hx-swap="innerHTML"`, `hx-ext="json-enc"` on `#page-content` div — all child elements inherit
- Updated `wants_html()` to recognize `HX-Request` header from HTMX
- Updated parity test to find `hx-post` URLs alongside `data-ef-*`
- Lead tested: works

### ListFormX — HTMX Stress Test
- Created `ListFormX` (engine/listformx.py) — subclass of ListForm, same handler logic, HTMX-native rendering
- Created `listx.html` agent template — naked semantic HTMX, no styling
- Registered in eigenform registry, created `htmx-lab` test page with simple list + constrained list (fixed items, ordering constraints, editable)
- Lead tested: works — all features (add, edit, remove, reorder, constraints, edit mode, pin toggles, N/A)

### View Toggle System
- Added `htmx_native` class attribute on base Eigenform (plain class attr, not dataclass field — fixed a bug where dataclass `__init__` overwrote subclass overrides)
- Evolved toggle from two-way (JSON/HTML) → three-way → five-way → four-way dropdown
- Final: dropdown select with Human View | Agent View | Agent HTMX | JSON for HTMX-native eigenforms; Human View | JSON for legacy
- Removed Human HTMX view (no good reason to show it)

### Semantic HTML Cleanup
- Stripped all inline styles from agent templates (text.html, listx.html)
- Added `data-field="label"`, `data-field="instruction"`, `data-field="value"` attributes
- Added `data-item-id`, `data-constraint-after`, `data-fixed` on list elements
- Replaced overlay constraint picker with plain `<select>` in agent view
- Moved add form outside `<ol>` in agent view

### Dual Template Architecture
- Added `render_agent_from_data()` method on base Eigenform (returns None for legacy)
- TextForm and ListFormX override both `render_from_data()` (human template) and `render_agent_from_data()` (agent template)
- Shared `_template_context()` method eliminates context duplication
- Created `text_human.html` and `listx_human.html` — styled HTMX templates
- Agent template IS the reusable core; human template diverges where UX demands it

### Whitespace + Alignment Fixes
- Enabled `trim_blocks=True` and `lstrip_blocks=True` on Jinja2 environment
- Tightened all list templates (list.html, listx.html, listx_human.html) — removed blank lines inside flex containers, added `-%}` whitespace control
- Fixed latent bug in `render_inline_button()`: CSS extraction renamed `STYLE_ARROW` to `CSS_ARROW` (class name) but the function still used `style="{style}"` — changed to `class="{css_class}"`. This affected ALL eigenforms using render_btn().
