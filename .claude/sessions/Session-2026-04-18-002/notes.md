# Session-2026-04-18-002

## Current State (last updated: session complete — commit requested)
- **Active document:** None (dev branch work, no CR)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Commit + push, then awaiting Lead direction

## Context from Session-2026-04-18-001
- Class taxonomy refactor completed: 26 classes renamed with role-specific suffixes (Form/unsuffixed/Display/Action/Historizer/App). 91 files updated. 72/72 parity tests pass.
- Explicit `form` class attribute replaced heuristic property on all subclasses.
- Razem rename decided but not yet executed.
- CR-110 IN_EXECUTION (v1.1). EI-1-4 Pass.
- Branch `dev/content-model-unification` is active dev branch.

## Progress Log

### [session open] Initialization
- Created session directory, set CURRENT_SESSION
- Read prior session notes (2026-04-18-001), SELF.md, PROJECT_STATE.md
- Read QMS-Policy, START_HERE, QMS-Glossary

### Wiki article improvements (pre-compaction)
- Added architecture framing paragraph, 4 SVG diagrams, component model subsection
- Added 6 code/pseudocode examples throughout wiki
- Defined mutation boundary: component owns self-mutations via _handle(), container owns structural ops
- Fixed figure numbering (Fig 3/4 swap)

### affordances() refactor — EXECUTED
**Code change (`engine/component.py`):**
- Extracted affordance-building logic from `_serialize_full()` into new public `affordances()` method
- Method sits between `get_affordances()` (subclass hook) and `_serialize_full()` (serialization)
- `_serialize_full()` now calls `self.affordances()` instead of building the list inline
- Page._serialize_full() untouched — has its own independent implementation
- 72/72 parity tests pass

**Wiki updates (`app/templates/wiki.html`):**
- Component model section: updated "three operations" → "four operations", added affordances() description
- Simplified TextForm example: added get_affordances() + affordances() inherited note
- Affordances & HATEOAS section: rewritten to lead with affordances() as the public method
- Glossary: "Affordance" entry updated from "dict" to "dataclass", mentions affordances() method

### Auto-generated keys — EXECUTED
**Code changes:**
- `engine/component.py`: Reordered fields (`label` first, `key` second with `None` default). Added `__post_init__` that generates `{form}-{uuid.hex[:8]}` when key is None. Added `import uuid`.
- 8 subclass files: Added `super().__post_init__()` to Action, ChoiceForm, CheckboxForm, Computation, DynamicChoiceForm, InfoDisplay, Switch, Visibility.
- Generate-once-at-construction: UUID assigned at dataclass init, preserved across deepcopy/bind. Seeds are stable.
- Explicit `key=` still works unchanged. Existing page definitions unaffected.
- 72/72 parity tests pass.
- Verified: auto-keys are unique, stable across rebinds, form-prefixed (e.g. `text-dec47f9e`).
