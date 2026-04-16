# Session-2026-04-14-004

## Current State (last updated: 2026-04-16)
- **Active work:** Builder UI complete and polished
- **Blocking on:** Nothing
- **Next:** Build real QMS workflows as eigenform compositions

## Progress Log

### Builder layout — "MS Paint" for PageForm (initial)
Restructured the mutable page editing UI from a vertical stack into a two-panel workspace.

**Template (`sleek/page.html`):**
- `.builder` grid: `.builder__palette` (left 220px) + `.builder__canvas` (right)
- Palette: compact type list by category, each item draggable with `data-ef-palette-type`
- Canvas: flat list of eigenform cards with tile bars and collapsible rendered content
- Feedback banners extracted into reusable `render_feedback` macro

**Server (`pageform.py`):**
- `_add_eigenform()`: added `position` parameter for numeric index insertion

### Schematic block diagram canvas (v2)
User feedback: canvas should be a visual/schematic representation showing nesting, not flat cards with rendered HTML.

**Template rewrite:**
- Replaced flat `builder__item` cards with recursive `render_block` macro
- Leaf blocks (`.blk--leaf`): compact single-row bars with icon, type, label, key, actions
- Container blocks (`.blk--container`): header bar + `.blk__children` zone visually wrapping nested child blocks
- Empty containers show dashed "drop here" placeholder
- Category-tinted backgrounds on container children zones (purple for containers, amber for reactive)

**CSS (`sleek.css`):**
- Full `.blk` block system replacing `.builder__item` styles
- Leaf vs container differentiation, accent colors, hover-revealed actions
- Drop target highlighting on container blocks

**JS (`eigenform.js`):**
- Complete rewrite of drag/drop/select handlers for `.blk` elements
- `_blkFromDragHandle()` helper for leaf vs container header drag sources
- `_efFindDropZone()` updated to find `.blk__children` zones
- Multi-select via Ctrl+click on block handles

### Inline builder within standard page flow (v3)
User feedback: builder should slot between the page header/feedback and the rendered eigenforms, not replace the standard page layout.

- Unified mutable/non-mutable rendering: both share title → instruction → feedback → eigenforms → page actions
- Builder is an inline section between feedback and eigenforms (mutable pages only)
- Removed duplicate title/instruction from canvas header
- Removed separate preview section — eigenforms render naturally below the builder
- Rebuild from Seed and Reset Page render together at the bottom via `ef-remaining-affs`

### Drag-into-group fix + palette height fix
- **Drag-into-group error:** When dropping into a container's child zone, JS now checks if the item is already a child. If not, sends `reparent_eigenform` instead of `move_eigenform` (which failed with "not found in container").
- **Palette scrollbar:** Removed `overflow: hidden` / flex layout from palette, removed `overflow-y: auto` from scroll area. Palette now sizes to content naturally; grid row matches the taller column. Canvas scrolls internally if needed.

**Tests:** 11/11 parity tests passing throughout all iterations. Non-mutable pages unaffected.
