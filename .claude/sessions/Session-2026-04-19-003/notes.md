# Session-2026-04-19-003

## Current State (last updated: committing)
- **Active document:** None
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Browser-verify all changes

## Progress Log

### Inspect panel Data view fix
Right-click > Data was always showing `{}` for leaf components. The bug: `storeData[s.key]` looked up the component's own key as a top-level scope key, but leaf component data lives under the parent's key as scope (e.g., `storeData["simple-values"]["text-demo"]`, not `storeData["text-demo"]`). Fix: extract scope from URL — the second-to-last path segment is the parent key. Applied in both initial load and live-refresh paths.

### TextForm rendering consistency
Standardized TextForm rendering across Debug Mode and Sleek Theme (single-line and multiline):
- **Consistent pattern:** "Value: <current value>" read-only display, followed by a blank input/textarea for new value entry
- **Debug Mode:** Added "Value:" display before the form, blanked the input (was pre-populated for multiline but not single-line)
- **Sleek Theme:** Added plain "Value:" display before the form, removed pre-populated values from input/textarea, removed the styled `sleek-text__value` block (blue left-border strip) — now uses a plain `<p>` like NumberForm
- Removed `placeholder="{{ label }}"` ghost text from sleek input/textarea
- Added POST tooltip (`title` attribute) to sleek Save button and input/textarea fields

### Universal ghost-style Clear buttons
Made all Clear buttons across all components render with the same ghost style as TextForm's Clear in the sleek theme:
- Added `css_class` parameter to `_render_button()` in `affordances.py`
- `render_affordance_html()` detects `body.action == "clear"` and passes `c-btn-clear` class
- Sleek CSS: `.c-btn-clear` styled as ghost button (transparent bg, gray text, subtle border)
- Fixed CSS specificity: the blanket `button[data-c-post]:not([class*="sleek-"])` blue rule was overriding — added `:not(.c-btn-clear)` exclusion

### Live form tooltips
POST tooltips on form submit buttons now update dynamically as the user types:
- New `_cSyncFormTooltip(form)` builds body from current `FormData` and sets `title` on submit button and all named inputs
- `_cSyncTooltips()` now covers `form[data-c-submit]` in addition to static-body buttons and palette add
- `input` event listener on document updates form tooltips live
- Universal: applies to TextForm Save, NumberForm set, edit mode config forms, etc.

### Files changed
- `engine/affordances.py` — `_render_button()` css_class param, clear detection in renderer
- `app/static/component.js` — Data view scope fix, form tooltip sync
- `app/static/sleek.css` — `.c-btn-clear` ghost style, specificity fix
- `app/templates/components/text_human.html` — consistent Value:/blank input pattern
- `app/templates/components/sleek/text_human.html` — consistent Value:/blank input, no placeholders, POST tooltips

### Tests
79/79 pass throughout
