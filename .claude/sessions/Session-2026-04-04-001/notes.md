# Session-2026-04-04-001

## Current State (last updated: 2026-04-04)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** Agent template redesign complete
- **Blocking on:** Nothing
- **Next:** Lead testing / remaining HTMX migration / agent integration testing

## Progress Log

### Agent template cleanup pass (all 12 agent templates)
- **HTML entity fix**: Replaced `&#9650;`/`&#9660;`/`&#10003;` in ListFormX agent template with plain text (`Up`/`Down`/`Save`) — entities rendered as literal `&#9660;` in agent view
- **Enumerated options in hx-vals**: Per Lead suggestion, select-based placeholders now list valid options inline (e.g., `<Low | Medium | High | Critical>` instead of generic `<value>`). Applied to ChoiceFormX, TableFormX (12 forms), ChainFormX, SequenceFormX, TabFormX, AccordionFormX
- **Affordance hint escaping fix**: `_affordance_hints()` in base Eigenform now wraps instruction strings in `Markup()` so Jinja2 preserves `<value>` placeholders instead of escaping to `&lt;value&gt;`
- **Hidden input removal**: Stripped all `<input type="hidden">` from all 11 agent templates (~59 lines removed). These were redundant with `hx-vals` under json-enc. Also removed dead `onchange` JS handlers from TableFormX constraint removal forms

### Agent template redesign — pure semantic markup (all 12 agent templates)
- **Design decision**: Agent templates should NOT be human-usable. Stripped all form controls (`<form>`, `<input>`, `<select>`, `<textarea>`, `<label>`) from all 11 agent templates. Agent view is now pure semantic markup: state display + annotated action endpoints.
- **`data-affordance` wrapper divs**: Each action is wrapped in `<div data-affordance="action_name">` containing the button + its instruction. Enables unambiguous parsing — agent queries `div[data-affordance="set"]` to get the complete action unit.
- **Edit mode removed**: Edit mode is a human-view concern. Agent templates no longer render edit mode at all.
- **Consistent null values**: All `data-field="value"` elements use empty content for null/unset state instead of magic strings (`None`, `Not set`, `Selected: None`).
- **ChoiceFormX options field**: Added `<p data-field="options">` listing valid options as text.
- **ListFormX O(1) affordances**: Per-item buttons collapsed into single parameterized affordances with enumerated IDs (matching the TableFormX pattern).

### Bug fixes
- **`_affordance_hints` dict.clear collision**: `hints.clear` in Jinja2 resolved to `dict.clear()` method instead of the `"clear"` key. Fixed by returning `SimpleNamespace` instead of `dict`.
- **Scroll position lost on swap**: Page scrolled unexpectedly after interactions. Root cause: SSE `onmessage` handler did raw `innerHTML` swap with no scroll control. Fixed with explicit `scrollY` save/restore on both eigenform.js swaps and SSE swaps. Also added 500ms debounce to suppress SSE reloads after same-tab POSTs.
- **Feedback banner HTML escaping**: `target_label` built via Jinja2 string concatenation caused `Markup.__radd__` to escape the HTML literal. Fixed by using inline template tags instead.
- **Feedback banner duplicate path**: Success message included path (`set → path`) AND template appended it as `target_label`. Fixed message to just the action name.

### HTMX excision
- **Decision**: HTMX removed entirely. It was providing minimal value — just fetch+swap on buttons, which eigenform.js already does. Agent view reverts to JSON (the clearer machine-readable format). HTML is for humans only.
- **Infrastructure**: Deleted `htmx.min.js`, `json-enc.js`. Removed all `hx-*` attributes from `page.html`. Removed `HX-Request` check from routes.
- **12 human templates**: Converted `hx-post`/`hx-vals` → `data-ef-post`/`data-ef-body`/`data-ef-submit`/`data-ef-change` (eigenform.js delegation).
- **eigenform.py**: Removed `htmx_native`, `render_agent_from_data`, `render_agent`, `_wrap_agent_html`, `_affordance_hints`. View selector simplified to 2 panes (Human View + JSON).
- **routes.py**: Removed `agent_view` query param, all `render_agent()` calls.
- **pageform.py**: Removed `render_agent` method.

### X variant removal
- **Deleted 11 X form Python files** (ListFormX, TableFormX, ChoiceFormX, CheckboxFormX, NumberFormX, BooleanFormX, MemoFormX, TabFormX, AccordionFormX, ChainFormX, SequenceFormX)
- **Deleted 11 X human templates** and all 12 agent templates
- **Deleted HTMX Lab page** (pages/htmx_lab.py + data/htmx-lab.json)
- **Registry**: trimmed from 44 to 33 eigenform types
- **Tests**: 20 passing (lost 1 HTMX Lab parity test with page deletion)
