# Session-2026-04-18-005

## Current State (last updated: workshop drag/drop + layout fixes)
- **Active document:** None
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Further Workshop iteration or other work

## Context from Previous Sessions
- 004: /components page, Score removal, DynamicChoiceForm→SiblingBind generalization, wiki/README/framing/learning portal doc alignment, Lesson 1 iterative polish. 79/79 tests pass. 24 classes, 29 registered names.
- Razem rename queued but not executed.

## Progress Log

### [session start] Session initialization
- Read CLAUDE.md, SELF.md, PROJECT_STATE, previous session notes.
- Created Session-2026-04-18-005 folder and updated CURRENT_SESSION.

### Discussion: SiblingBind and sub-component primitives
- Explored what SiblingBind represents conceptually — "field modifier" framing led to housekeeping proposals (Constraint, Default, EditGuard) that the Lead found uncompelling ("meh").
- Key insight: SiblingBind's significance is enabling new expressiveness (reactive configuration), not reorganizing existing code.
- Better framing: SiblingBind is the first "composable capability" — decoupled reactivity from the type hierarchy.

### Workshop page
- Created `app/templates/workshop.html` — standalone interactive canvas for mocking up Razem pages.
- Added route in `app/routes.py` (`/workshop`).
- Added sidebar link in `base.html` (pencil icon).
- Features: drag-and-drop palette (21 component types, 4 groups), dot-grid canvas, inline component previews (inputs, sliders, toggles, radios, tables, etc.), properties panel, undo/redo (Ctrl+Z/Y), JSON export drawer, container nesting with child drop zones, toast notifications, keyboard shortcuts (Delete, Ctrl+D duplicate).
- Flask server running, /workshop returns 200.

### Workshop v2 — juicy interactive upgrade
Full rewrite of workshop.html with these additions:
- **Live interactive mocks**: all inputs work — text fields accept typing, toggles toggle, radios select, sliders slide, checkboxes check, lists add/remove items, sets add/remove tags, dictionaries edit keys+values, tables have editable cells, action buttons click. State tracked per-component.
- **Completion tracking**: per-card completion ring (green when complete) + global completion percentage in the topbar with animated ring.
- **Slash command palette**: press `/` anywhere on the canvas for a Notion-style fuzzy search popup. Arrow keys to navigate, Enter to insert, Esc to close.
- **Connection wiring mode**: "Connect" toggle in toolbar. Click source component, then target — draws animated SVG bezier curves between them with arrowheads. Connections shown in properties panel. Right-click a connection line to remove.
- **Context menu**: right-click any card for Duplicate, Move up/down, Wrap in Group, Delete — with keyboard shortcut hints.
- **Visual polish**: color-coded left accent bars per card, sectioned properties panel (Identity / Configuration / Connections), completion rings, smoother animations, better type indicators.
- **Keyboard shortcuts**: `/` open palette, `Esc` exit connect mode or deselect, `Delete` remove, `Ctrl+D` duplicate, `Ctrl+Z/Y` undo/redo.
- Verified: /workshop returns 200, all features present in rendered HTML.

### Debugging sweep (continued after compaction)
- **Drag ghost persistence**: Extracted `cleanupDrag()` helper, called from `dragend`, `drop`, and `dragstart`. Fixed orphaned ghost elements.
- **Drop zone layout shift**: Replaced expanding 40px dashed drop zones with thin 3px blue hover lines between cards. Added `ws-dropzone-empty` (full-canvas target for empty state) and `ws-dropzone-tail` (flex:1 target below last card for easy appending).
- **Browser drag ghost**: `setDragImage()` failed on Windows regardless of technique (Image, canvas, offscreen div). Replaced entire HTML5 drag API with mouse-based drag (`mousedown`/`mousemove`/`mouseup`). Removed `draggable="true"` from palette items and cards. Uses `elementFromPoint` hit-testing with pointer-events toggle on the ghost. All drag artifacts eliminated.
- **Card drag threshold**: Card mousedown immediately started drag, preventing click events (broke Connect mode and card selection). Added 5px movement threshold via `cardDragPending` — plain clicks pass through, drag only starts after movement.
- **Independent scroll**: Overrode `.main` and `.content` with `overflow: hidden` and `min-height: 0` to constrain flex children to viewport height. Palette list and canvas now scroll independently.
