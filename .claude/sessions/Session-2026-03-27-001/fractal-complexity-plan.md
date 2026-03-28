# Plan: Dynamic Fractal Complexity

## Vision

Collapse the boundary between structure and data. The eigenform tree becomes mutable state — user interactions don't just fill in values, they reshape the tree itself. Python definitions are the seed (genome); the store holds the living organism (expression); user POSTs are environmental signals (epigenetics).

## Current State

- 28 eigenform types including GroupForm (named compositions) and RepeaterForm (dynamic repetition)
- Structure is frozen at definition time (Python code)
- Values are mutable at runtime (JSON store)
- Compositions are parameterized but static — determined at import, not at interaction

## Architecture

### The Biology Metaphor

| Concept | System Analog | Where It Lives |
|---------|--------------|----------------|
| Genome | Eigenform type registry — all available types and their behaviors | Python classes |
| Gene | A specific eigenform type with its callables (compute_fn, action_fn, etc.) | Python class + config |
| Expression | Which genes are active, in what arrangement, with what parameters | Store (`__structure`) |
| Organism | The live eigenform tree at any moment | Reconstructed from registry + store |
| Environment | User POST actions that trigger structural changes | HTTP requests |
| Epigenetics | Rules governing which structural changes are allowed | Structural action constraints |

### Key Mechanisms

#### 1. Eigenform Type Registry

An explicit, queryable registry mapping type names to classes.

```python
registry = EigenformRegistry()
registry.register("text", TextForm)
registry.register("choice", ChoiceForm)
registry.register("team-member", TeamMember)  # parameterized GroupForm subclass
```

Purpose: reconstruct live eigenform instances from stored structural descriptions. Currently implicit (Python imports) — needs to be explicit so the store can reference types by name.

#### 2. Structural State in the Store

The eigenform tree stored as data alongside values.

```json
{
  "__structure": [
    {"type": "text", "key": "q1", "label": "Question 1", "config": {}},
    {"type": "choice", "key": "q2", "label": "Question 2", "config": {"options": ["A", "B"]}},
    {"type": "team-member", "key": "lead", "config": {"roles": ["Staff", "Principal"]},
     "children": [
       {"type": "text", "key": "name", "label": "Name", "config": {}},
       {"type": "choice", "key": "role", "label": "Role", "config": {"options": ["Staff", "Principal"]}}
     ]}
  ],
  "q1": "user answer",
  "q2": "B",
  "lead": { ... }
}
```

Callables (compute_fn, action_fn, etc.) are NOT stored — they come from the registered type. The store holds scalar configuration only. The registry provides behavior.

#### 3. Seed + Grow Model

- Page definition provides the initial structure (the seed/genome)
- First bind: writes the seed structure to the store
- Subsequent binds: reads structure FROM the store, reconstructs the tree using the registry
- If the Python definition changes (new version), a migration mechanism reconciles

#### 4. Structural Actions

New action types that mutate the tree, not just values:

- **AddEigenform**: Insert a new eigenform into the tree at a specified location
- **RemoveEigenform**: Remove an eigenform (and its children/state) from the tree
- **ReplaceEigenform**: Swap one eigenform (or composition) for another
- **MoveEigenform**: Reorder within a container

These could be built into ActionForm (it already has store access) or be a new primitive.

#### 5. SwitchForm (Immediate Precursor)

Before full structural mutation, a `SwitchForm` provides the 80% case: select between pre-defined compositions based on a sibling value. Like VisibilityForm but for swapping alternatives rather than show/hide.

```python
SwitchForm(key="assessment", depends_on="type", cases={
    "regulatory": RegulatoryAudit("audit"),
    "financial": FinancialReview("review"),
    "operational": OperationalCheck("check"),
})
```

Only the active case exists in the tree. Switching replaces one subtree with another. This is "controlled structural mutation" — the cases are pre-defined, but which one is expressed is dynamic.

## Implementation Phases

### Phase A: SwitchForm (incremental, builds on existing patterns)
- New eigenform type: selects between named alternatives based on sibling value
- Active case is bound and rendered; inactive cases are dormant
- Switching preserves state for previously-visited cases (like TabForm)
- No registry needed — cases are defined in Python

### Phase B: Eigenform Type Registry
- Explicit registry with register/lookup
- Auto-registration from existing eigenform classes
- GroupForm subclasses register with their parameterized configs
- Registry is queryable: "what types are available?"

### Phase C: Structural Persistence
- Store gains a `__structure` key holding the tree description
- PageForm.bind() reads structure from store if present, falls back to Python definition
- Serialization includes structure metadata (not just values)
- Structural changes written atomically alongside value changes

### Phase D: Structural Actions
- ActionForm (or new StructuralActionForm) can add/remove/replace eigenforms
- Structural mutations go through the store, triggering rebind
- Constraints on what mutations are allowed (schema validation)
- Undo for structural changes

### Phase E: Self-Modifying Pages
- Pages that grow in response to user input
- "Add a section" that materializes a composition from the registry
- Workflows where completing one phase unlocks the next phase's structure
- Templates that clone and specialize themselves

## Design Constraints

1. **Callables stay in Python.** The store holds data; Python holds behavior. The registry bridges them.
2. **Seed is always valid.** A page must be renderable from its Python definition alone, even if the store is empty.
3. **Structural changes are auditable.** Every mutation to the tree is traceable (who, when, what changed).
4. **No orphaned state.** Removing an eigenform from the tree clears its stored values.
5. **Backward compatible.** Existing pages with static definitions continue to work unchanged.

## Open Questions

- Should structural state be a separate store/file, or in the same JSON as values?
- How do we handle schema migration when the Python definition evolves?
- Should structural actions be their own eigenform type or a capability of ActionForm?
- What does undo look like for structural changes? (Snapshot? Delta? Command pattern?)
- How does this interact with the QMS — is a structural mutation a controlled change?
