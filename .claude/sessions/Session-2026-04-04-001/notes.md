# Session-2026-04-04-001

## Current State (last updated: 2026-04-04)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** Agent template cleanup complete
- **Blocking on:** Nothing
- **Next:** Lead testing / next eigenform batch / further agent template refinements

## Progress Log

### Agent template cleanup pass (all 12 agent templates)
- **HTML entity fix**: Replaced `&#9650;`/`&#9660;`/`&#10003;` in ListFormX agent template with plain text (`Up`/`Down`/`Save`) — entities rendered as literal `&#9660;` in agent view
- **Enumerated options in hx-vals**: Per Lead suggestion, select-based placeholders now list valid options inline (e.g., `<Low | Medium | High | Critical>` instead of generic `<value>`). Applied to ChoiceFormX, TableFormX (12 forms), ChainFormX, SequenceFormX, TabFormX, AccordionFormX
- **Affordance hint escaping fix**: `_affordance_hints()` in base Eigenform now wraps instruction strings in `Markup()` so Jinja2 preserves `<value>` placeholders instead of escaping to `&lt;value&gt;`
- **Hidden input removal**: Stripped all `<input type="hidden">` from all 11 agent templates (~59 lines removed). These were redundant with `hx-vals` under json-enc. Also removed dead `onchange` JS handlers from TableFormX constraint removal forms
