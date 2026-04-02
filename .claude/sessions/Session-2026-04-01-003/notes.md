# Session-2026-04-01-003

## Current State (last updated: 2026-04-01)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** Rendering layer modernization — Steps 1-2 COMPLETE, Step 3 in progress
- **Blocking on:** Nothing
- **Next:** Continue Step 3 template migration (27 remaining eigenforms), then Step 4

## Progress Log

### Session Start
- Read SELF.md, PROJECT_STATE.md, previous session notes (Session-2026-04-01-002)
- Read QMS docs (QMS-Policy, START_HERE, QMS-Glossary)
- Previous session completed container edit mode for all 5 container eigenforms
- CR-110 EI-1-4 Pass; remaining EIs (5-7) need scoping for the rebuild

### External Feedback: HTMX Migration Proposal
- Received external architectural proposal (prompt.txt) suggesting migrating eigenform HTML rendering to HTMX
- Performed independent evaluation against actual codebase (eigenform.py, affordances.py, routes.py)
- **Valid points identified:** XSS bugs in URL/value escaping (affordances.py:218,254; eigenform.py:415), wasteful location.reload() pattern, brittle inline onclick handlers
- **Rejected:** Jinja2 template extraction (breaks render-from-serialize invariant), "HTML as primary API" (agents use JSON), test-suite parity replacing runtime enforcement (downgrade)
- Drafted response acknowledging bugs, defending core architecture, outlining targeted fixes
- Lead sent the response; received constructive reply accepting the correction
- Sender proposed: event delegation with data-* attrs, partial DOM swaps, XSS fixes
- Evaluated proposals: event delegation sound but underscoped (25 renderers, not 15-line fix); partial DOM swaps complicated by cascading effects; XSS fixes unambiguously correct

### XSS Bug Fixes
- Added `_js_sq()` helper in `affordances.py` — escapes `\`, `'`, `"`, `\n`, `\r` for JS-in-HTML-attribute context
- Applied to ALL URL embeddings in fetch() calls (25 render functions in affordances.py + _chrome_btn in eigenform.py)
- Fixed radio option value: `escape(opt)` → `_js_sq(opt)` (escape() doesn't protect JS string context)
- Fixed form field keys/values in JS builders (_render_multi_field, _render_text_input_add, _render_parameterized)
- Fixed tooltip JS strings: `escape(endpoint)` → `_js_sq(endpoint)` in all oninput/onchange handlers
- Replaced manual checkbox key escaping (line 232) with `_js_sq()` for consistency
- Imported `_js_sq` in eigenform.py for _chrome_btn
- Verified: all 18 pages render without errors, _js_sq unit tests pass

### Step 1: Event Delegation — COMPLETE
- Created `app/static/eigenform.js` — thin delegation script (~60 lines) handling 3 protocols:
  - `data-ef-post` + `data-ef-body`: static-body clicks (buttons)
  - `data-ef-submit`: form submissions (body from named fields)
  - `data-ef-change` + `data-ef-key`/`data-ef-field`/`data-ef-template`: checkboxes, radios, selects
- Updated `app/templates/page.html` to load eigenform.js
- Rewrote all 19 render functions in `affordances.py` — zero inline JS remains
- Rewrote `render_inline_button()` (43 call sites across 12 modules) — all migrated automatically
- Rewrote `_chrome_btn` in `eigenform.py`
- Migrated inline JS in 16 eigenform modules (textform, listform, choiceform, checkboxform, numberform, booleanform, setform, keyvalueform, rubikscubeform, tabform, accordionform, groupform, stepform, chainform, pageform, tableform, repeaterform)
- Removed `_js_sq()` helper — no longer needed (data attributes use standard HTML escaping)
- Dropped all `oninput` tooltip updaters (dynamic tooltip previews → static tooltips)
- Kept client-only JS: "See JSON" toggle in eigenform.py, range slider display update
- Verified: all 18 pages render OK, zero `fetch()` calls in Python, zero `_js_sq` references

### Step 2: CSS Extraction — COMPLETE
- Created `app/static/style.css` with semantic CSS classes (`ef-` prefix, BEM-lite)
- Updated `page.html` to include stylesheet
- Rewrote `affordances.py`: `STYLE_CONFIRM`→`CSS_CONFIRM`, `STYLE_REMOVE`→`CSS_REMOVE`, `STYLE_ARROW`→`CSS_ARROW`
- `render_inline_button()` signature: `style: str` → `css_class: str` (default `CSS_CONFIRM`)
- `BUTTON_GAP` now uses `class="ef-btn-gap"` instead of inline style
- Extracted shared patterns: wrapper (.ef-wrap), chrome (.ef-chrome), affordance buttons, edit-mode forms, list/collection styles, constraint pills, container toolbars/control bars, feedback banners
- Updated all 26+ eigenform modules to use CSS classes
- Inline styles: 418 → 252 (166 extracted, 40%). Remaining 252 are context-specific (Rubik's cube colors, history timeline, dynamic conditional styles, table column layouts)
- Verified: all 18 pages render OK, zero STYLE_* references remain

### Step 3: Parity Test + Template Migration — IN PROGRESS
- **Parity test** (`tests/test_parity.py`): 20 tests, all passing. Verifies every affordance URL in serialize() appears as data-ef-* attribute in render() for all 18 pages.
- **Runtime accounting removed**: Deleted the RuntimeError post-render check and _chrome_rendered mechanism from eigenform.py render(). Kept mark_rendered() and _rendered flag for double-rendering prevention. Chrome affordances marked in render() before render_from_data() call.
- **Jinja2 environment** (`engine/templates.py`): standalone Jinja2 env with FileSystemLoader, autoescape=True, render_aff() global, CSS class constants, tojson filter.
- **Shared partial** (`_edit_header.html`): editable label + instruction forms, replaces 6 duplicated _render_edit_header() methods.
- **TextForm migrated**: first eigenform moved to Jinja2 template (`text.html`). 88 lines of f-string Python → 40 lines clean Python + readable HTML template. All 20 parity tests pass.
- **All 32 eigenforms migrated** to Jinja2 templates via 3 parallel agents
- 31 templates + 1 shared partial (_edit_header.html) in app/templates/eigenforms/
- Fixed 2 stale inline fetch() calls (eigenform.py chrome btn, tableform.py constraint dropdown) that agents reverted
- engine/templates.py expanded: render_btn, render_dep_line, BUTTON_GAP globals added by agents
- Final state: zero fetch() in Python, 20/20 parity tests pass, all 18 pages render
- Browser-tested by Lead: external behavior fully retained, no regressions
