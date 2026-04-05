# Session-2026-04-05-002

## Current State (last updated: 2026-04-05T16:32Z)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** Eigenform type consolidation — removed 3 redundant types
- **Blocking on:** Nothing
- **Next:** Lead direction

## Progress Log

### Eigenform Type Consolidation

**RankForm removed** — redundant special case of ListForm.
- Deleted `engine/rankform.py` and `app/templates/eigenforms/rank.html`
- Removed from registry
- Replaced with `ListForm(fixed_items=..., allow_constraints=False)` in vendor_assessment and eigenform_gallery
- Removed RankForm demo from Selection Forms tab in gallery
- Removed from README, eigenform reference

**MemoForm removed** — merged into TextForm.
- Expanded TextForm with `multiline: bool`, `min_length: int | None`, `max_length: int | None`
- TextForm `_handle()` now validates length constraints; `_serialize_state()` includes new fields when set
- TextForm `get_affordances()` uses `TextAffordance` (textarea render hints) when multiline/length constraints present
- Template renders `<textarea>` and pre-wrap display in multiline mode
- Deleted `engine/memoform.py` and `app/templates/eigenforms/memo.html`
- Removed from registry
- All usages replaced with `TextForm(multiline=True, ...)`
- Eigenform reference updated

**RangeForm removed** — merged into NumberForm.
- Expanded NumberForm with `slider: bool`, `unit: str | None`
- NumberForm `get_affordances()` emits `range_input` render hints when slider mode
- Template renders slider-style display (value+unit, "Not set" placeholder) when `data.slider`
- Deleted `engine/rangeform.py` and `app/templates/eigenforms/range.html`
- Removed from registry
- All usages replaced with `NumberForm(slider=True, unit=..., ...)`
- Eigenform reference updated (also cleaned up stale rank entry)

### Template Fixes

**Batch affordance HTML leak fixed** — 6 templates were rendering `_chrome_rendered` affordances (like Batch) as visible buttons because they iterated all affordances without checking `_rendered`.
- Fixed: `date.html`, `range.html`, `action.html`, `dynamicchoice.html`, `history.html`, `tablerunner.html`
- Added `{% if not aff._rendered %}` guard to affordance rendering loops

**MultiForm missing template override** — MultiForm had no `render_from_data()` override, falling through to the base class f-string renderer which renders all affordances unconditionally. Added override to route through `multi.html` (which already had the `_rendered` filter).

### Gallery Cleanup

- Fixed "gear icon" → "pencil icon" in TextForm demo instruction
- Moved TextForm (multiline) below original TextForm
- Moved NumberForm (slider) below original two NumberForms
- Removed TableForm from Multi-Field & Collection Forms tab (dedicated tables tab exists)
- Made all edit-mode eigenforms editable: top-level TabForm, all 10 section GroupForms, and all directly-declared data form demos of types with edit mode support

### Final State
- **31 eigenform types** (was 34: removed RankForm, MemoForm, RangeForm)
- **20 pages**
- **21/21 parity tests passing**
