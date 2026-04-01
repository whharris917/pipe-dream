# Session-2026-04-01-001

## Current State (last updated: 2026-04-01)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** Complete — ListForm constraint pin/unpin fix
- **Blocking on:** Nothing
- **Next:** TBD

## Progress Log

### ListForm constraint pin/unpin fix
- **Bug:** Unpinning (demoting) a static ordering constraint in edit mode caused it to disappear from both HTML and JSON in execution mode, with no affordance to remove it
- **Root cause:** `effective_must_follow` deliberately excludes demoted constraints, and both rendering and serialization used it for display
- **Fix (4 changes across 2 files):**
  - `ordered_collection.py`: Added `all_must_follow` property (includes demoted constraints)
  - `ordered_collection.py`: Rewrote `remove_constraint` — static constraints now demote properly instead of stripping the demotion entry (which silently re-enabled the constraint)
  - `listform.py`: `render_from_data` uses `all_must_follow` for pill display in both modes; execution-mode remove button checks `not is_effectively_fixed` instead of `not is_static`
  - `listform.py`: `_serialize_state` uses `all_must_follow` for JSON, with `"active": false` on demoted constraints
- Verified on eigenform-gallery Static Ordering Constraints page
