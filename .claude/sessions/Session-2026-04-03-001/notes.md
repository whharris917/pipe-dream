# Session-2026-04-03-001

## Current State (last updated: 2026-04-03)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** HTMX migration — ChainFormX, SequenceFormX, agent template quality pass
- **Blocking on:** Nothing
- **Next:** Lead testing / next eigenform batch / TableFormX hints+instructions

## Progress Log

### ChainFormX + SequenceFormX (43rd, 44th eigenform types)
- Created `engine/chainformx.py` — subclass of ChainForm with `htmx_native = True`, `_template_context()` shared between templates, `render_from_data()` and `render_agent_from_data()`
- Created `engine/stepformx.py` — subclass of SequenceForm with same pattern, includes `accessible` gating info in step items
- Agent templates (`chainx.html`, `stepx.html`): semantic HTMX with `data-step`/`data-active`/`data-complete` attributes, O(1) parameterized forms for structural ops, nav buttons for Back/Next
- Human templates (`chainx_human.html`, `stepx_human.html`): styled HTMX with progress bars, gating indicators, continue/nav buttons
- Registered both in `engine/registry.py` — 44 eigenform types total (33 base + 11 X variants)
- Added both to HTMX Lab page with demo data (Setup Wizard chain, Gated Workflow sequence)

### Agent template quality pass (all 12 agent templates)
- **Jinja2 escaping fix**: `{{ ' data-active="true"' if ... }}` → `{% if %} data-active="true"{% endif %}` to prevent `&#34;` in attributes (chainx, stepx, tabx)
- **hx-vals on all forms**: every `<form>` and `<button>` in agent templates now has `hx-vals` showing the complete POST body shape with `<placeholder>` templates (e.g., `hx-vals='{"value": "<value>"}'`). Agents no longer need to infer body structure from HTML form encoding. Applied to all 12 agent templates including ListFormX and TableFormX.
- **Bounding div**: `render_agent()` and the "Agent HTMX" view pane now wrap output in `<div data-eigenform="{key}" data-type="{form}">` with proper indentation. Added `_wrap_agent_html()` helper to base Eigenform.
- **Affordance instructions**: Added `_affordance_hints(data)` to base Eigenform — builds `action → instruction` lookup from serialized affordance data. Threaded through `_template_context()` in all 12 X forms. Agent templates display instructions as `<p data-field="instruction">` after forms/buttons. ListFormX shows add/na/clear/clear_na instructions. Data forms show set/clear/done instructions.
- **Consistent attribute ordering**: standardized `<input>` attributes to `type` before `name` across agent templates.

### Design decisions
- Research on agent HTML POST inference: LLMs can infer from forms but reliability degrades with complexity. `hx-vals` approach chosen as pragmatic middle ground — explicit body templates while keeping HTML human-usable.
- Bounding div uses `data-eigenform` (not `id` or `data-field`) to avoid collisions and maintain semantic distinction.
- Instructions displayed directly (not tooltips) per Lead preference.
- Tooltip revert: `title="POST ..."` on buttons was added then reverted per Lead preference.
