# Session-2026-04-14-001

## Current State (last updated: 2026-04-14)
- **Active work:** UI polish pass on mutable PageForm and icon buttons — complete
- **Branch:** dev/content-model-unification (qms-workflow-engine submodule)
- **Status:** All changes done, tests passing, ready for commit
- **Blocking on:** Nothing
- **Next:** Build real QMS workflows as eigenform compositions

## Progress Log

### JSON pane double-escaping fix
- `eigenform.py:459`: Removed `escape()` wrapper on `json_str` — `html.escape()` returns plain `str`, Jinja2 auto-escape was escaping it again, producing `&amp;quot;` in the browser
- Added `ensure_ascii=False` to `json.dumps()` so Unicode chars (em dashes etc.) render directly instead of `\u2014`

### Label/URL double-escaping fix
- Same root cause: `escape()` on `label` and `url` in wrapper context was double-escaped by Jinja2 auto-escape
- Removed redundant `escape()` calls, letting Jinja2 handle it

### Sleek page template
- Created `sleek/page.html` — mutable PageForm now renders with dark theme classes (`sleek-edit-toolbar`, `sleek-edit-child__bar`, `sleek-edit-btn`) instead of light-themed inline styles
- Per-eigenform structural controls moved to right margin via absolute positioning (`sleek-page-child__controls`)

### Mutable page: seed eigenforms now editable
- `pageform.py`: On mutable pages, seed eigenform descriptors get `editable=True` forced on (first-bind and rebuild-from-seed)
- `registry.py`: `from_descriptor()` now syncs `seed.editable = bool(desc.get("editable"))` instead of only setting True — was the bug preventing toggle-off

### Toggle Editable affordance on PageForm
- Added `toggle_editable` action to PageForm: affordance (with editable/locked status), handler, feedback message, guard for non-mutable pages
- `child_items` now includes `editable` flag for templates
- Both `page.html` and `sleek/page.html` render padlock toggle button per eigenform

### Icon vocabulary overhaul
- Toggle editable: pencil → padlock (🔓 unlocked / 🔒 locked)
- Delete/remove: ✕ → wastebasket 🗑
- Enter edit mode: ✏ pencil (unchanged)
- Discard changes: ✕ (unchanged)
- Updated 8 templates (page, group, navigation × default + sleek)

### Icon button sizing fix
- New `ef-icon-btn` class in `style.css`: 24×24 squares, 14px font, flexbox centered, with `--active` and `--danger` variants
- Fixed pre-existing bug: default templates were passing inline styles as `class=` attribute values via `render_btn` — buttons had no styling at all in debug mode
- Updated all 3 default templates to use proper CSS classes
- Sleek buttons (`sleek-edit-btn`) bumped from 20×20/10px to 24×24/14px
- Chrome buttons (`ef-chrome-btn`) given explicit font-size/line-height
- Wastebasket icon 20% larger (17px) via `--danger` modifier, neutral color (not red)
