# Session-2026-04-14-003

## Current State (last updated: 2026-04-14)
- **Active work:** One-click add + drag eject — complete
- **Blocking on:** Nothing
- **Next:** Build real QMS workflows as eigenform compositions

## Progress Log

### One-click add eigenform UX overhaul
Streamlined the add eigenform flow so users don't need to specify keys or labels upfront.

**Server-side (`pageform.py`):**
- `_add_eigenform()`: key and label are now optional. Key auto-generates as `{type}-{n}` (e.g., `text-1`, `navigation-2`), incrementing to avoid collisions. Checks all keys at every depth via `_all_keys_in_tree()`.
- Label auto-generates as title-cased type name (e.g., "Text", "Dynamic Choice"). Special-case: `dynamicchoice` → "Dynamic Choice".
- Feedback message now shows label + key: "Added Number (number-1)."
- Generated key/label written back to body dict so `handle()` feedback has access.

**Sleek theme (`sleek/page.html`):**
- Replaced form+radio+footer with direct `<button>` cards. One click = eigenform created.
- Removed key/label input fields and submit button entirely.
- New `data-ef-add` attribute on cards triggers JS handler.

**Regular theme (`page.html`):**
- Key/label fields remain but marked "(auto)" with placeholder "auto-generated".

**JS (`eigenform.js`):**
- New `data-ef-add` click handler sends `{action: "add_eigenform", type: "<type>"}`.

**CSS (`sleek.css`):**
- Removed dead radio/footer/input/btn styles. Cards now `<button>` with `:active` state instead of `:has(:checked)`.

**Affordance (`pageform.py`):**
- Updated `AddEigenformAffordance` instruction text: key/label described as optional.

**Tests:** 11/11 parity tests passing. Manual testing confirmed auto-generation, uniqueness, duplicate rejection, explicit key override, and sleek HTML rendering.

### Container drop-target fix
- `sleek/page.html`: `--container` class and nest `<div>` now gated on `tile.is_container` (type-based) instead of `tile.children` (data-based). Empty containers are now valid drop targets.
- `pageform.py`: `_build_tile()` adds `is_container` flag from `Eigenform._CONTAINER_FORMS`.

### Eject from group (de-nesting)
**Server (`pageform.py`):**
- `_move_eigenform`: top-level move branch now uses `_pluck_from_tree()` to find and extract eigenforms from any depth. Syncs source container's `__structure` after plucking.

**Template (`sleek/page.html`):**
- Nested tiles (`depth > 0`) get an eject button (↗) that fires `move_eigenform` with `position: 999` (clamped to end).

**CSS (`sleek.css`):**
- Eject button: hidden by default, appears on hover, blue tint.

**Tests:** 11/11 parity tests passing. Manual testing confirmed reparent into group, eject back to top level, drag-out-of-group via move_eigenform.
