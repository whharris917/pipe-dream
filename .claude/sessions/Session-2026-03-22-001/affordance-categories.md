# Affordance Framework — Working Draft

## Motivation: A Visual Cortex for the Agent

An LLM agent's most expensive resource is tokens — the equivalent of conscious attention. Every token spent parsing a flat affordance list, figuring out which actions matter, mentally grouping related operations, and tracking what's already been done is a token *not* spent reasoning about the actual domain problem: what should this field's value be, does this workflow structure make sense, is this the right approval decision.

The current API is raw pixel data. Every affordance at equal prominence, flat list, figure it out. The agent's "prefrontal cortex" — its high-level reasoning capacity — is consumed by work that should be handled at a lower level.

This framework is a preprocessing layer — a visual cortex for the agent. Just as the human visual cortex performs salience detection, perceptual grouping, and gaze management *before* conscious awareness, this framework handles those functions for the agent:

- **Salience detection** — the system highlights what needs attention. An empty required field is "bright." A populated optional field is "dim." A terminal action feels different from a text input. The agent doesn't have to compute relevance; it's presented with a pre-organized scene.

- **Perceptual grouping** — affordances that operate on the same object are grouped together, the way a human perceives a form as a coherent entity rather than individual pixels. The agent sees "here is a table and here are things you can do with it," not "here are 9 unrelated actions."

- **Gaze management** — sticky focus and snap-to-next handle saccades (where to look next). The agent's conscious reasoning focuses on *what value to put in the field*, not *which field to fill next*. Just as humans subconsciously know to fill out a form top to bottom, the attention mechanism sequences rudimentary navigation so the agent's higher thinking is free for difficult problems.

- **Pre-action verification** — flow control and terminal actions are perceptually distinct from data entry, the same way a "Submit Order" button feels different from typing in a text field. This is the brain's pause-before-irreversible-action circuit. The framework encodes that distinction structurally.

A well-designed attention layer doesn't just reduce token count — it makes the agent *smarter* at the task. The tokens saved on affordance management are tokens available for domain reasoning.

---

## Core Principle: Object Tree with Focus Controls

Affordances are grouped with their objects. Objects can contain other objects. A composite object does not, by default, expose the affordances of its child objects. The agent controls what's visible through two focus modes.

### The Object Tree

A workflow node's response is an object tree. Each object carries its own affordances and may contain child objects. Examples:

**Field-filling node:**
```
Node
├── Field: title        → [set value]
├── Field: severity     → [set value]
├── Field: description  → [set value]
└── Flow                → [proceed (gated)]
```

**Table construction node:**
```
Node
├── Table (2 columns, 4 rows)              → [add column, add row, remove row(row)]
│   ├── Column: "Step Instructions"         → [rename, set type, remove, set cell(row)]
│   └── Column: "Expected Outcome"          → [rename, set type, remove, set cell(row)]
└── Flow                                    → [proceed (gated)]
```

**2D game node:**
```
Node
├── Player                → [move left, move right, jump]
├── Room                  → []
│   ├── Lever             → [pull, inspect]
│   ├── Door              → [open (requires key), inspect]
│   └── Block             → [push left, push right]
└── Inventory             → []
    └── Key               → [use on door, drop]
```

### Parameterized Affordances vs. Child Objects

The object tree does not need to mirror the data model literally. The dividing line between creating child objects and parameterizing an affordance is whether the items have **distinct types/behaviors** (separate objects) or are **instances of the same thing** (parameterize).

- **Columns** are separate objects because each has a distinct name, type, and behavior (a choice-list column has different affordances than a free-text column).
- **Rows** are *not* separate objects — they're instances of the same structure. Row multiplicity is handled as a parameter on the column's affordances: `set cell(row)` takes a row index.
- **Cells** are *not* separate objects — a cell is just the intersection of a column (the type) and a row (the instance).

This keeps the affordance count stable as rows grow. A table with 2 columns and 100 rows still has 2 column objects with parameterized affordances, not 200 cell objects. The column gives you the *meaning* (what kind of thing you're filling in), the row parameter gives you the *which* (an index into a known set).

**General principle:** Parameterized affordances handle multiplicity *within* an object. The object tree handles multiplicity *across* objects.

### Concrete Example: Current vs. Proposed

A real response from the Create Executable Table workflow (construction node, 2 columns, 4 empty rows) currently returns 9 flat affordances: proceed, add column, add row, rename column, set column type, remove column, set cell, remove row, set property.

Under the object tree with default collapsed children:

**Default view** — the agent sees:
```
Table (2 columns, 4 rows)    → [add column, add row]
Flow                          → [proceed to review]
```
Two objects, three affordances.

**Focus on Table** — reveals columns and properties:
```
Table (2 columns, 4 rows)                  → [add column, add row, remove row(row)]
├── Column: "Step Instructions" (ne-free)   → [rename, set type, remove, set cell(row)]
├── Column: "Expected Outcome" (ne-free)    → [rename, set type, remove, set cell(row)]
└── Properties                              → [set sequential_execution]
```

**Focus by salience ("what's required?")** — the proceed gate requires columns AND rows, both satisfied. The only surfaced affordance is `proceed`. If cell content were required, empty cells would bubble up as `set cell` affordances on their respective columns.

### Default View

By default, the response shows top-level objects with summaries and affordance counts, but does not expand child object affordances. The agent sees the shape of what's available without being flooded.

### Two Focus Modes

**Focus by object** — drill into a specific object to see its affordances and children. "Show me the table" expands the table's own affordances and reveals its children (columns, properties) as summarized objects. This is spatial navigation through the object tree.

**Focus by salience** — cross-cutting query that surfaces high-salience affordances regardless of nesting depth. "Show me what's required to advance" walks the entire tree and bubbles up unfilled required fields, ungated proceed actions, etc. The agent sees exactly what needs doing without manually drilling down through every branch.

These compose: "Show me required affordances within the table" is focus-by-salience scoped to a subtree.

---

## Salience as a Derived Layer

Salience is not a fixed property of an affordance — it's computed from workflow state and varies with context. An affordance's salience answers the question: *how much should this attract the agent's attention right now?*

Salience levels:

1. **Suggested Next Action** — System-computed recommendation. The engine's opinion about what to do right now. Only computable when the workflow has enough structure (gates, requirements) to form an opinion.

2. **Required to Advance** — Blockers. Unfilled fields in a proceed gate, cells needed for acceptance, etc.

3. **Available** — Possible but not blocking. Optional fields, non-required actions.

4. **Modify Populated** — Revision of already-set values. Forward motion vs. adjustment is a meaningful distinction.

5. **Navigation** — Spatial movement. Go back, switch branch, jump. Changes *where you are*.

6. **Flow Control** — Forward commitment. Proceed, fork activation, merge. Advances workflow state.

7. **Terminal Actions** — Restart, submit, publish. High consequence, end the workflow.

8. **Discovery** — Meta-affordances. The focus/inspect links themselves.

**Not all workflows can compute all salience levels.** A puzzle game has no "required to advance" beyond the terminal goal. Its affordances are all "available," organized purely by object anchoring. The framework works with anchors alone — salience is an enhancement, not a requirement.

---

## The Node Scope Insight

Affordance count is also a **workflow authoring** problem, not just an API presentation problem.

If affordances are anchored to objects, and nodes are the unit of focus, then a node with one object naturally produces a focused affordance set. A well-authored workflow with tight, focused nodes *is* an attention mechanism — it reduces affordances at the source.

Both levers are needed:

- **Workflow design guidance:** Prefer focused nodes with one primary object. The builder could warn when a node has too many competing objects. This is the structural solution.

- **The object tree with focus controls:** For inherently complex nodes (review pages, the builder's node_builder, game worlds), the tree structure keeps things navigable. This is the presentation solution.

---

## Focus Modes and Attention Management

### Sticky Focus

The agent can enter **focus mode** on an object. Focus is session-level state: once set, every subsequent GET returns the focused view without needing `?focus=table` each time. The agent says "I'm working on the table now" and stays in that context across multiple actions until it explicitly defocuses or switches focus to another object.

This mirrors how agents actually work — they commit to a subtask, execute multiple actions within it, then pull back out. Without sticky focus, every request must re-declare the focus, adding per-request overhead.

**The defocus affordance is always visible.** When in focus mode, the response always includes an affordance to defocus (return to the default view). This ensures the agent always knows it's in a narrowed view and can escape. Without it, sticky focus could feel like a trap — the agent wouldn't know there's more to see beyond its current scope.

### Snap to Next Required Action

Instead of the agent asking "what's required?" and getting a list, it asks "take me to the next thing that needs doing" and the engine *moves the focus* for it. The engine computes the next required action and focuses on the object that owns it.

- **Table execution:** snap-to-next focuses on the next column of the next row that needs filling.
- **Field-filling:** snap-to-next focuses on the first empty required field.
- **Fork:** snap-to-next focuses on the branch the agent hasn't touched yet.

This is a cursor that the engine controls, not the agent. The agent just says "next" and the engine decides where to point.

### Autonomy Spectrum

These mechanisms form a spectrum of agent autonomy:

| Mode | Who controls focus | Description |
|------|--------------------|-------------|
| **Manual** | Agent | Agent manages its own focus, drills in and out explicitly |
| **Sticky focus** | Agent (persistent) | Agent commits to a subtree, stays there until it defocuses |
| **Snap to next** | Engine | Engine guides attention to the next required action |
| **Auto-advance** | Engine (automatic) | Engine moves focus after each completed action (like routers already do for nodes) |

Each level trades agent control for engine guidance. An experienced agent that knows the workflow might prefer manual. A generic agent encountering a workflow for the first time might prefer snap-to-next. The agent can switch modes at any time.

---

## Design Principles

- The object tree is derived from the engine's existing data model. Fields, tables, columns, lists, providers — these are already distinct objects. No new metadata authoring required.
- Default responses are shallow: top-level objects with summaries. Depth is revealed on demand.
- Parameterized affordances handle instance multiplicity (rows, items). Child objects handle type multiplicity (columns, fields with distinct behaviors).
- `?focus=<object>` drills into a subtree. `?focus=salience:<level>` surfaces cross-cutting results. `?focus=all` returns everything flat (backward compatible).
- LNARF-conforming: the human renderer projects the same tree as collapsible sections. Agent and human see the same structure.
- Framework is workflow-agnostic and primitive-agnostic — works for fields, tables, lists, game worlds, and any future object types.

## Open Questions

- Exact serialization format for the object tree in JSON responses.
- Should "Suggested Next Action" be a separate top-level key or a flag on affordances within the tree?
- How does `show_all_fields` map? Fields from other nodes become children of... what? A "review context" object? Their source nodes represented as read-only children?
- How does the builder's node_builder page map? The focused node is an object, the workflow-level operations (add/select/remove node, option sets, column types) are siblings.
- Interaction with the feedback diff model — does a POST response return a diff against the object tree, or against the flat affordance list?
