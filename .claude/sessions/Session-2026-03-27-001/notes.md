# Session-2026-03-27-001

## Current State (last updated: mid-session)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current EI:** Rebuild continuation — eigenform expansion
- **Blocking on:** Nothing
- **Next:** SwitchForm (Phase A of fractal complexity plan), then registry + structural persistence

## Progress Log

### Scope rules discussion
- Discussed Python-like scope rules for eigenforms (closed scopes, explicit parameter passing)
- Explored Django ORM analogy — eigenforms as persistent objects with identity
- Drafted Django code for Math Quiz page; decided current DSL is more elegant
- Key insight: the gap isn't persistence model, it's the boundary between structure and data

### Five new eigenform types built

**ValidationForm** (engine/validation.py)
- Cross-field validation via ValidationRule (name, depends_on, check_fn, message)
- Rules are pending/pass/fail; pending when dependencies are None
- block_completion flag controls whether failures block page completion

**DynamicChoiceForm** (engine/dynamic_choice.py)
- Options computed from sibling value via options_fn or static_options lookup
- Stale detection: if selected value no longer in options, marked stale (not auto-cleared)
- Reuses SelectAffordance from choice.py

**ActionForm** (engine/action.py)
- Imperative button with preconditions, optional two-step confirmation
- action_fn receives (context, store, scope) — can write to other eigenforms
- writes_to declares side-effect targets (documentation, not enforced)
- DisabledAffordance for greyed-out state; added _render_disabled_button to affordances.py

**RepeaterForm** (engine/repeater.py)
- Container stamping template eigenforms per dynamic entry
- Compound scopes (key/entry_0) — works with existing Store
- Inner EntryGroup class enables find_eigenform routing
- min_entries/max_entries, stable IDs, add/remove with scope cleanup

**GroupForm** (engine/group.py)
- Simplest container: named group of eigenforms, no special behavior
- Enables parameterized compositions via subclassing
- Subclass gets its own form type identity (class name → form field)

### Weird Experiments page updated
- Exercises all new types: number multiplier, cross-field validation, dynamic choice + action with confirmation, repeater with team members
- 11 eigenforms on the page

### Fractal complexity architecture discussion
- Identified the key boundary: structure is code (frozen), values are data (mutable)
- Vision: collapse that boundary — structure becomes mutable data
- Biology metaphor: genome (Python types), expression (store), environment (user POSTs)
- Drafted plan with 5 phases: SwitchForm → Registry → Structural Persistence → Structural Actions → Self-Modifying Pages
- Plan saved to session folder

### Totals
- 28 eigenform types (was 23)
- 12 pages (was 11)
