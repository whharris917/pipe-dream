# Session-2026-04-16-002

## Current State (last updated: session end)
- **Active work:** Schematic canvas refinements + NavigationForm mode editability + Store resilience
- **Blocking on:** Nothing
- **Next:** Awaiting direction from Lead

## Progress Log

### Session opened
- Read previous session notes (Session-2026-04-16-001)
- Read SELF.md, QMS-Policy, START_HERE, QMS-Glossary, PROJECT_STATE

### Schematic canvas refinements (sleek.css)
Goal from Lead: "make the canvas a visually pleasing, intuitive schematic of the page."

Proposed six directions ranked by impact. Lead selected #1 (tree guide lines).

**Tree guide lines (`.blk__children`):**
- Each child in a container now draws its own L-shaped guide connecting to the parent's spine.
- `::before` pseudo-element: top-left L (vertical + horizontal stub with rounded inner corner at 4px radius). Horizontal arm lands at 20px from top, aligning with the block header's icon center.
- `::after` pseudo-element: continuation spine to the next sibling (non-last children only). Extends into the 5px gap.
- Increased `.blk__children` left padding from 14px to 22px to make room.
- Guide color `#4a5058` — one step brighter than neutral border tone.

**Border reduction (Lead follow-up: "indentation is meaningful now"):**
- Stripped outer borders on `.blk--leaf` and `.blk--container`. Kept the left accent stripe (3px, category-colored) as the node's identity.
- Removed `.blk__head` bottom border and top-corner radius.
- Selection still works via existing `box-shadow: 0 0 0 1px` (now reads as an outline).

**Nested-group bug + follow-up fix (Lead: "nested groups don't link up properly"):**
- Root cause: I'd added `overflow: hidden` to `.blk--container` to clip the header background against the parent's rounded corners. But `overflow: hidden` also clips the container's own `::before` pseudo-element (positioned at `left: -14px`, outside the container's box), erasing the nested L-guide.
- Fix: removed `overflow: hidden` AND removed `border-radius: 5px` from `.blk` base entirely. Sharp rectangles are more schematic-appropriate and eliminate the header-bg-overflow problem without piecemeal patching.

### NavigationForm mode editability (engine/navigationform.py)
Lead observation: "NavigationForms' edit mode doesn't allow the mode to be switched."

**Infrastructure:**
- Added `_effective_config` property returning store override or seed defaults for `mode` and `default_expanded`.
- Modified `_bind_children` to apply `__config` override to `self.mode` and `self.default_expanded` at bind time, before any logic that reads mode. Chose this over an `_effective_mode` refactor to avoid touching every read site.
- Extended `_snapshot_edit_state` / `_restore_edit_state` to include `__config` alongside the existing `__children_scope`.

**Affordances:**
- Initial attempt: single parameterized `Set Mode` affordance with `body={"action": "set_mode", "mode": "<tabs|chain|sequence|accordion>"}`. Appeared in serialized state but Lead couldn't see buttons.
- Investigation: affordance was rendering via `_render_parameterized` fallback (text input + submit) — technically visible but not discoverable.
- Replaced with four explicit `SimpleButtonAffordance`s, one per mode. Current mode gets `(current)` suffix. These render as proper buttons via `_render_button` path.

**Namespace collision bug:**
- Discovered base Eigenform's `handle()` intercepts `action == "set_mode"` at line 483 for the edit↔execute chrome toggle (`mode == "edit"` / `mode == "execute"`). It returns unconditionally, so my `_handle`'s `set_mode` branch never fired.
- Renamed my action to `set_nav_mode`. Updated affordance bodies and handler to match.
- Chrome path (exit edit mode) verified still works.

**Handler behavior:**
- `_set_nav_mode` validates mode against valid list, writes to `__config`, clears `self.value` (mode-specific shape: step key for tabs/chain/sequence, dict for accordion — old value would be invalid in new mode).

### Store resilience (engine/store.py, app/registry.py)
Recurring `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` — 0-byte JSON files.

**Root cause:** `write_text` on Windows truncates-then-writes. Flask dev-reloader kills and respawns the process on any `.py` edit. During that truncate-to-write window (tiny but non-zero) the file is 0 bytes — and we hit it while I was editing code during a running server.

**Fix:**
- Atomic writes: `_save` now writes to `{path}.tmp` and uses `Path.replace()` (atomic on Windows and POSIX). Applied to both `Store._save` and `InstanceRegistry._save`.
- Defensive load: `_load` treats empty files as the default empty state (`{}` for Store, `{"_counters": {}, "instances": {}}` for InstanceRegistry). Applied to both.

**Data recovery:**
- `data/instances.json` was wiped to 0 bytes during one of these races (second occurrence). All four instance data files (`bd4b13d1.json`, `27c1258c.json`, `98296e6b.json`, `096a45ff.json`) were intact.
- Reconstructed `instances.json` from the prior state captured in a system-reminder snapshot. Note: this is runtime data, not committed.

## Files changed
- `qms-workflow-engine/app/static/sleek.css` — tree guides, border reduction, sharp rectangles
- `qms-workflow-engine/engine/navigationform.py` — mode config + `set_nav_mode` affordance/handler
- `qms-workflow-engine/engine/store.py` — atomic writes, empty-file tolerance
- `qms-workflow-engine/app/registry.py` — atomic writes, empty-file tolerance

## Open items raised but not actioned
- `default_expanded` (accordion-only) has `_effective_config` entry but no edit affordance yet. One-liner following the same pattern when wanted.
- Descriptor/config drift: a NavigationForm embedded in a mutable parent has its current (possibly overridden) mode exported by `to_descriptor()`. Config override in `__config` wins at bind time so runtime behavior is correct, but the two representations can diverge.
- Mode buttons use the generic `_render_button` path — readable but don't match the sleek dark theme. If desired, add explicit mode-switcher markup inside `sleek/navigation.html`'s edit block instead of letting them fall through.
- The sharp-rectangle look is a canvas aesthetic decision that leaked into the leaves. If leaves should stay slightly rounded (2-3px) while containers go sharp, revisit.
