# Session-2026-04-18-001

## Current State (last updated: class taxonomy rename complete)
- **Active document:** None (no CR for this — engine-internal refactor on dev branch)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Awaiting Lead direction (commit when requested)

## Context from Session-2026-04-17-003
- Razem naming decided, Wiki rewritten with new name. Rename not yet executed in code.
- Class taxonomy rename decided (28 classes → role-suffixed names), not yet executed.
- Navigation-split queued as post-workflow refactor.
- CR-110 IN_EXECUTION (v1.1). EI-1-4 Pass. Remaining EIs (5-7) need re-scoping.
- Branch `dev/content-model-unification` is active dev branch (submodule `qms-workflow-engine`).
- 72/72 parity tests pass.

## Progress Log

### [session open] Initialization
- Created session directory, set CURRENT_SESSION
- Read prior session notes (2026-04-17-003), SELF.md, PROJECT_STATE.md
- Read QMS-Policy, START_HERE, QMS-Glossary

### Class taxonomy rename — EXECUTED
TBD decisions resolved by Lead:
- ActionComponent → **Action** (not ActionButton)
- HistoryComponent → **Historizer** (not HistoryWrapper)

**Phase 1: File renames** — 25 `git mv` operations in `engine/`:
- 12 Forms: `*component.py` → `*form.py`
- 6 Containers: `*component.py` → unsuffixed (`page.py`, `navigation.py`, `group.py`, `repeater.py`, `switch.py`, `visibility.py`)
- 3 Derivations: `computedcomponent.py` → `computation.py`, `scorecomponent.py` → `score.py`, `validationcomponent.py` → `validation.py`
- 1 Display: `infocomponent.py` → `infodisplay.py`
- 1 Imperative: `actioncomponent.py` → `action.py`
- 1 Wrapper: `historycomponent.py` → `historizer.py`
- 1 App: `rubikscubecomponent.py` → `rubikscubeapp.py`

**Phase 2: Bulk class + import rename** — Python script updated 42 .py files:
- All class names (TextComponent → TextForm, PageComponent → Page, etc.)
- All import paths (engine.textcomponent → engine.textform, etc.)

**Phase 3: Explicit form mapping** — Per Lead's direction, replaced heuristic `form` property with explicit class attributes:
- Removed `Component.form` property that derived name via `removesuffix("Component").lower()`
- Base property now raises NotImplementedError if subclass forgets to declare
- Added `form = "text"`, `form = "page"`, `form = "computed"`, `form = "history"`, etc. to all 26 classes
- Updated `_type_name()` in registry.py to read `cls.form` directly
- Key non-obvious mappings: Computation.form = "computed", Historizer.form = "history"

**Phase 4: HTML/MD docs** — Script updated 49 template and documentation files:
- All Jinja templates (default + sleek), lessons, framing, wiki, README, docs/architecture.md

**Phase 5: Changelog** — Added entry to docs/architecture.md §Change log explaining:
- The rename categories and rationale
- Why `*Form` reintroduction is a refinement, not a reversion

**Verification:**
- 72/72 parity tests pass
- Flask app starts, 31 types registered, 10 seeds discovered
- Zero stale references to old class names or module paths (verified via grep)
- All registry type names preserved (text, page, computed, history, etc.) — backwards-compatible with stored data
