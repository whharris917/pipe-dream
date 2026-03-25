# Workflow Engine Content Model Unification

## Context

The engine has empirically discovered its core abstraction — the Element Library documents element types delivered in an ordered content array with per-element affordances. But the code doesn't express this yet: fields, field groups, lists, and tables live in 4 parallel structures in the schema, are delivered in 3 different shapes in the response, and are rendered through 2 different dispatch mechanisms in JS.

This refactor crystallizes what the system already knows it wants to be: **one content array, one element protocol, one dispatch loop.**

### Guiding Principles
- **LNARF**: Lossless, Non-Additive, Representationally Free
- **Faithful Projection**: Human and agent views are lenses on the same data
- **HATEOAS**: Every element carries its own affordances; agents discover actions from responses
- **Fractal Composability**: Same protocol at every level (element → node → workflow)

---

## What is an Element?

An element is an object that has internal state, can render itself inline wherever it is inserted on a page, can expose affordances as POSTable endpoints that mutate its internal state, and can include those affordances as interactive controls in its rendering. An element is — all by itself — a mini HATEOAS-compliant, LNARF-compliant application.

The element protocol:
```python
render_state(data) → dict    # always produces state
get_affordances(ctx) → list  # may be empty (valid response, not a protocol violation)
```

### The protocol constrains interface, not complexity

The protocol says nothing about how rich the state is, how many affordances there are, or how elaborate the rendering gets. It only says: you have state, you can render it, you can expose actions that mutate it.

A `text_field` is an element: its state is a string, it renders as a text input, it exposes one affordance (set value). A `table` is also an element: its state is a 2D grid with typed columns, it renders as an interactive table, it exposes many affordances (add column, set cell, etc.). A hypothetical `rubiks_cube` would also be an element: its state is a configuration matrix, it renders as an interactive cube, it exposes rotation affordances. All three implement the same protocol. The difference is internal complexity, not kind.

This means the element taxonomy is **open, not closed**. The seven types defined below are the types the workflow engine currently needs. Any future element type that implements `render_state` and `get_affordances` drops into the content array and the renderer dispatches it — no changes to the protocol, the content assembly loop, or the affordance framework.

### Affordance minimization

Good element design minimizes the affordance surface. The rubik's cube could naively expose 12 affordances (clockwise + counterclockwise for each of 6 faces), but a better design adds a perspective rotation and exposes only 2 affordances for the facing side — fewer affordances, same capability.

This is exactly the design pressure that produced `multi_field`. A naive "collect three values" would be three separate `text_field` elements — three affordances. `multi_field` compresses that to one. The principle is general: when multiple actions can be unified without loss of capability, they should be.

Not every element produces affordances at every moment. A `text_field` hidden by `visible_when` returns an empty list. A `text_display` always returns an empty list — it has the capacity but never the occasion. The protocol is uniform; the affordance count is a runtime property, not a type-level constraint.

### Nesting and independence

Elements can nest. A parent element can contain child elements. The key constraint is: **nesting does not change the child's identity or protocol.** A child element inside a parent is still a full element — it still implements `render_state` and `get_affordances`. The parent doesn't demote it, suppress its affordances, or absorb it.

The parent-child relationship is **delegation, not absorption.** A parent element renders its own state, declares its own affordances, and then delegates to its children to render theirs. The child's affordances appear in the response alongside the parent's. The child doesn't know or care what contains it.

Consider a hypothetical `collapse` element: it has state (open/closed), it renders a toggle control, and it exposes an affordance (toggle visibility). When open, it delegates to its child element — which could be any element — to render. The child retains full element identity.

Or consider a "clearable container" that exposes a "clear all" affordance. It reaches down and resets each child's state. The children don't know they're clearable — the container does. The affordance belongs to the container, not to the children.

This pattern requires that **container elements validate what they accept.** A clearable container knows how to reset a `text_field` (set to null) and a `boolean_field` (set to false), but may not know how to reset a `table`. The container declares what child types it accepts, and validation enforces this at definition load time — a `ValueError` at parse time, just like a missing instruction.

### Nesting vs. composition

Two patterns for elements with internal structure:

- **Nesting** (e.g., collapse, clearable container): parent contains child *elements*. Children retain full element identity and their own affordances. Parent delegates rendering and affordance generation to children.
- **Composition** (e.g., multi_field): single element with internal *value descriptors*, not child elements. Internal parts have no element identity, no affordances. One affordance for the whole unit.

Both are valid. The distinction matters: nested children are elements all the way down; composed internals are not.

### Current scope

The seven element types in this refactor do not nest — multi_field uses composition (value descriptors, not child elements), and the other six are leaf elements. But the protocol and content model support nesting, and the implementation should not preclude it. Future container element types (collapse, clearable group, sub-workflow) can use nesting when the need arises.

---

## Element Taxonomy

Seven element types currently implemented:

| Element | Values | Affordances | Nature |
|---------|--------|-------------|--------|
| `text_field` | 1 | 1 (set value) | Single free-form string |
| `boolean_field` | 1 | 1 (set value) | Single true/false |
| `choice_field` | 1 | 1 (set value) | Single selection from options |
| `text_display` | 1 | 0 (read-only) | Computed/derived text value |
| `multi_field` | N | 1 (set all values) | Compound: multiple values, single affordance |
| `table` | N×M | Many (structural ops) | Columns, rows, properties |
| `list` | N | Many (add/edit/remove) | Ordered items with schema |

### The multi_field distinction

A `multi_field` is NOT a container of child elements. It is a **composed element** — a single element that collects multiple values through a single affordance. The things inside it are **value descriptors** (called `fields`), not elements. They have:
- A key, type, label, instruction, and current value (for rendering)
- NO affordance of their own (not even a suppressed one — the concept doesn't exist)
- NO independent element identity

The utility of `multi_field` is that it produces **fewer affordances than the sum of its parts**. An agent sees one action ("Set Basic Information") instead of three separate field-setting actions. This is a deliberate reduction in affordance surface, not a visual grouping.

The renderer can share visual utilities (a text input looks the same inside a multi_field as it does for a standalone text_field), but the affordance system treats the multi_field as a single unit.

A multi_field validates its value descriptors at load time: it accepts `text`, `boolean`, and `choice` descriptor types. Nesting an arbitrary element inside a multi_field is not valid — that's what container elements (nesting pattern) are for.

### Type naming conventions

- `*_field` suffix → settable (produces affordances that mutate its value): `text_field`, `boolean_field`, `choice_field`, `multi_field`
- `*_display` suffix → read-only (renders state, no affordances): `text_display`
- No suffix → structural: `table`, `list`

The suffix carries meaning: if you see `_field`, you know there's an affordance. If you see `_display`, you know there isn't. The pattern is extensible — `boolean_display`, `choice_display` could exist if needed, but `text_display` covers the current use case.

### Legacy type aliases

The compat layer normalizes old type names to new:
- `text` → `text_field`
- `boolean` / `toggle` → `boolean_field`
- `select` / `choice` → `choice_field`
- `computed` / `indicator` → `text_display`
- `group` → `multi_field`

---

## Target State

### Definition format: Python-native

YAML is eliminated as the definition format. Workflows are defined as **Python dataclass instances** and persisted as **JSON** for storage and builder output.

**Why:** YAML required a normalization layer (compat.py) that translated YAML quirks into canonical form — `requires` → `gate` expansion, `options_ref` → `options_from`, key injection, type alias mapping, content synthesis from parallel dicts. This translation pipeline existed solely to bridge the gap between "what the author wrote in YAML" and "what the engine needs." With Python-native definitions, the definition IS the canonical form. No translation, no normalization, no compat layer.

**Two definition paths:**
1. **Hand-authored workflows** — Python modules that construct `WorkflowDef` directly. Type-safe, IDE-assisted, validated at construction time.
2. **Builder-published workflows** — Serialized to JSON, loaded via `WorkflowDef.from_json()`. The builder constructs a `WorkflowDef` in memory and persists it.

### Python definition (hand-authored)
```python
from engine.runtime.schema import (
    WorkflowDef, NodeDef, ElementType as E,
    TextField, BooleanField, ChoiceField, TextDisplay,
    MultiField, ValueDescriptor, ListElement, TableElement,
    ProceedDef, NavigationDef,
)

create_cr = WorkflowDef(
    workflow_id="create-cr",
    workflow_title="Create Change Record",
    workflow_description="Author a new Change Record for review and approval.",
    option_sets={"submodules": ["flow-state", "qms-cli", "qms-workflow-engine"]},
    nodes={
        "initiation": NodeDef(
            id="initiation",
            title="Initiation",
            instruction="Provide the document title, classify code impact, and state the purpose.",
            content=[
                MultiField(
                    key="initiation",
                    label="Basic Information",
                    instruction="Provide a short descriptive title, classify whether this change affects code, and state the purpose.",
                    fields=[
                        ValueDescriptor(key="title", type="text", label="Document Title",
                                        instruction="A short, descriptive title."),
                        ValueDescriptor(key="affects_code", type="boolean", label="Code Impact",
                                        instruction="Does this change affect code?"),
                        ValueDescriptor(key="purpose", type="text", label="Purpose",
                                        instruction="What problem does this CR solve?"),
                    ],
                ),
                BooleanField(
                    key="affects_submodule",
                    label="Affects Submodule",
                    instruction="Does it affect a controlled submodule?",
                    visible_when={"type": "field_equals", "key": "affects_code", "value": True},
                ),
                ChoiceField(
                    key="submodule",
                    label="Submodule",
                    instruction="Which controlled submodule is affected?",
                    options_from="submodules",
                    visible_when={"type": "field_equals", "key": "affects_submodule", "value": True},
                ),
            ],
            proceed=ProceedDef(
                label="Proceed to Change Definition",
                gate={"op": "AND", "conditions": [
                    {"type": "field_truthy", "key": "title"},
                    {"type": "field_truthy", "key": "purpose"},
                ]},
            ),
        ),
        # ... more nodes
    },
)
```

### JSON persistence (builder output / state files)
```json
{
  "workflow_id": "create-cr",
  "workflow_title": "Create Change Record",
  "nodes": {
    "initiation": {
      "id": "initiation",
      "title": "Initiation",
      "instruction": "...",
      "content": [
        {
          "type": "multi_field", "key": "initiation",
          "label": "Basic Information", "instruction": "...",
          "fields": [
            {"key": "title", "type": "text", "label": "Document Title", "instruction": "..."},
            {"key": "affects_code", "type": "boolean", "label": "Code Impact", "instruction": "..."}
          ]
        },
        {"type": "boolean_field", "key": "affects_submodule", "label": "Affects Submodule",
         "instruction": "...", "visible_when": {"type": "field_equals", "key": "affects_code", "value": true}}
      ],
      "proceed": {"label": "Proceed to Change Definition", "gate": {"op": "AND", "conditions": [...]}}
    }
  }
}
```

`WorkflowDef.from_json(path)` and `WorkflowDef.to_json(path)` handle serialization. The JSON shape mirrors the dataclass structure exactly — no normalization needed.

### Response (runtime)
```json
{
  "state": {
    "workflow": "...",
    "node": "...",
    "node_title": "...",
    "content": [
      {
        "type": "multi_field", "key": "initiation",
        "label": "Basic Information", "instruction": "...",
        "fields": [
          {"key": "title", "type": "text", "label": "Document Title",
           "value": null, "instruction": "..."},
          {"key": "affects_code", "type": "boolean", "label": "Code Impact",
           "value": null, "instruction": "..."}
        ],
        "affordance": {
          "id": 1, "label": "Set Basic Information",
          "method": "POST", "url": ".../set_fields",
          "body": {"title": "<value>", "affects_code": "<value>"},
          "parameters": {
            "title": {},
            "affects_code": {"options": [true, false]}
          }
        }
      },
      {
        "type": "boolean_field", "key": "affects_submodule", "label": "Affects Submodule",
        "value": null, "affordance": {"id": 2, "method": "POST",
        "url": ".../affects_submodule",
        "body": {"value": "<value>"},
        "parameters": {"value": {"options": [true, false]}}}
      },
      {
        "type": "list", "key": "issues", "label": "Issues",
        "instruction": null, "items": [...],
        "affordances": [{"id": 3, "label": "Add Issues item", ...}, ...]
      },
      {
        "type": "table", "key": "table", "columns": [...], "rows": [...],
        "properties": {...}, "summary": "2 columns, 3 rows",
        "affordances": [...]
      }
    ],
    "completed_nodes": [...],
    "definition": {...}
  },
  "instructions": "...",
  "affordances": [/* flat projection: all content affordances + flow control affordances */]
}
```

Key design points:
- multi_field's `fields` array items have **no `affordance` key** — only the multi_field itself has an affordance
- Every content item has a `key` for identity and diffing
- Affordance shape uses `body` + `parameters` (matching the existing code convention)
- The top-level `affordances` array is a **flat projection** built by walking `state.content` and collecting all embedded affordances, then appending flow control affordances

### JS Rendering (projection)
```javascript
// Single dispatch loop over content array
var _elementRenderers = {
  'text_field':     _renderTextField,
  'boolean_field':  _renderBooleanField,
  'choice_field':   _renderChoiceField,
  'text_display':   _renderTextDisplay,
  'multi_field':    _renderMultiField,    // owns all rendering for its fields
  'table':          _renderTable,
  'list':           _renderList,
};

function renderContent(contentItems, ctx) {
  return contentItems.map(item => {
    var render = _elementRenderers[item.type] || _renderUnknownElement;
    return render(item, ctx);
  }).join('');
}
```

`_renderMultiField` uses shared visual utilities (text input, boolean toggle, choice dropdown) but backs every control with the multi_field's single affordance — not with per-field affordances.

---

## Design Specifications

These address specific implementation questions surfaced by adversarial audit.

### Schema dataclasses — element types

Each element type gets its own dataclass. All share a base protocol but carry type-specific fields:

```python
@dataclass
class TextField:
    type: str = "text_field"  # or use an enum
    key: str
    label: str
    instruction: str | None = None
    default: Any = None
    visible_when: dict | None = None
    side_effects: list[dict] | None = None
    grouped: bool = False  # True when inside a multi_field

@dataclass
class MultiField:
    type: str = "multi_field"
    key: str
    label: str
    instruction: str
    fields: list[ValueDescriptor]  # NOT elements

@dataclass
class ValueDescriptor:
    key: str
    type: str  # "text", "boolean", "choice" — short names, NOT element types
    label: str
    instruction: str | None = None
    options: list[str] | None = None
    # ... other field-like properties for rendering
```

`NodeDef.content` is `list[TextField | BooleanField | ChoiceField | TextDisplay | MultiField | TableElement | ListElement]` — a union of concrete element types.

### `from_json` / `to_json` serialization

`WorkflowDef.from_json(path)` reads JSON, dispatches each content item by `type` to the appropriate element dataclass constructor. `WorkflowDef.to_json(path)` serializes via `dataclasses.asdict()`. The JSON shape is a direct mirror of the Python structure — no normalization step.

For backward compatibility during migration, `WorkflowDef.from_yaml(path)` remains temporarily, performing YAML loading + the old compat normalization + construction. Removed in Phase 4.

### Visibility and the content array

Invisible elements (where `visible_when` evaluates false) are **omitted from the content array** — same behavior as today for fields. This means:
- Content array length changes between renders (elements appear/disappear)
- Diffing by `key` handles this naturally: a key absent in one render and present in another is a `new` or `removed` item
- For multi_field value descriptors: if a descriptor's `visible_when` is false, it is omitted from the multi_field's `fields` array AND from the multi_field's affordance `parameters`. The multi_field itself remains visible as long as it has at least one visible descriptor. If all descriptors are hidden, the multi_field is omitted entirely.

### multi_field member fields and individual settability

Multi_field member fields are **not individually settable via `set_field`**. The `_set_field` action handler rejects keys that belong to a multi_field. The only way to set them is via `set_fields` (the multi_field's affordance). This is enforced by:
- `all_fields` returns all field definitions (including multi_field members) for lookup purposes
- Each field carries `grouped: bool` (set True for multi_field members)
- `_set_field` checks `grouped` and returns an error directing the agent to use `set_fields`

### List and table action handler lookup

`NodeDef` gains `content_by_key(key)` and `content_by_type(type)` helper methods that walk the content list. Action handlers use these instead of the old `node.lists` / `node.table` attributes:
- `_list_action` uses `node.content_by_key(list_key)` to find the list element
- Table actions use `node.content_by_type("table")[0]` to find the table element

### show_all_content merging

When `show_all_content` is true, `node_content()` returns a merged array:
- Walk all nodes in definition order, collect their content items
- Deduplicate by `key` — first occurrence wins
- Multi_field membership is respected: if field `X` is standalone in node A but grouped in node B, the first occurrence determines the treatment

### Feedback diffing

**Pre-existing issue:** The current `_compute_feedback()` reads `state.get("fields")` but the renderer never sets `state["fields"]` — it builds `state["content"]` instead. Feedback field diffing is currently non-functional. This refactor fixes it:

- Walk `state.content` before and after the action
- Build `{key: item}` dicts from both
- `outcome`: the content item whose key matches the acted field
- `effects.new`: keys present in after but not before (appeared via `visible_when`)
- `effects.modified`: keys present in both where the value changed
- `effects.removed`: keys present in before but not after (disappeared)
- multi_field: diff by the multi_field's `key`, comparing its `fields` array values
- table/list: diff by `key`, comparing summary or item count

### Top-level affordances array (flat projection)

Built by:
1. Walking `state.content` and collecting `item.affordance` (singular) or `item.affordances` (plural)
2. Collecting flow control affordances (proceed, navigation, fork, branch switch, actions)
3. Assigning sequential IDs across the combined list

Affordances flow **outward** (from elements into the top-level array) rather than being generated flat and partitioned back.

### `_serialize_definition` and the flowchart

- `_serialize_definition()` includes content element summaries (type + key + label) instead of field arrays
- `_serialize_definition_topology()` is unaffected (only uses proceed/router/fork)

### Provider state in response

`state["providers"]` is **removed**. Provider data delivered only via read-only content elements. Raw provider cache is internal.

### Builder output format

The builder constructs a `WorkflowDef` in memory during the authoring session. On publish:
- `WorkflowDef.to_json()` writes to `data/custom_workflows/{id}.json`
- Discovery at startup scans for both `.py` modules (hand-authored) and `.json` files (builder-published)
- Builder emits standalone fields (no multi_field grouping — deferred)

---

## Key Design Decisions

**Python-native definitions, JSON persistence.** No YAML, no compat layer. The definition IS the schema. Builder outputs JSON; hand-authored workflows are Python modules.

**Flow control stays at node level.** Proceed, navigation, router, fork, and actions are NOT elements in the content array. Their affordances go directly into the top-level `affordances` array.

**Execution tables are tables with execution state.** Not a separate element type. `execution: true` on the node triggers execution mode.

**`show_all_fields` becomes `show_all_content`.** Merges content from all nodes, deduplicating by key.

**multi_field uses `fields` key for its value descriptors.** They are not elements.

**Every content item has a `key`.** Required for identity, diffing, and action routing.

**Affordance shape uses `body` + `parameters`.** Matching existing code convention.

**Affordance anchoring is per-element.** Atomic fields → singular `affordance`. multi_field → singular `affordance`. Table/list → plural `affordances`. Flow control → top-level only.

**Provider exposed fields become content elements.** `state.providers` removed.

**Value descriptor types vs element types.** Inside multi_field: short names (`text`, `boolean`, `choice`). In content array: full names (`text_field`, `boolean_field`, etc.).

---

## Phases

### Phase 1: Schema Rewrite
**Goal:** Replace the fractured schema with a unified content model. Python-native element dataclasses. JSON serialization.

**Files:**
- `engine/runtime/schema.py` — Major rewrite:
  - Element dataclasses: `TextField`, `BooleanField`, `ChoiceField`, `TextDisplay`, `MultiField`, `ListElement`, `TableElement`
  - `ValueDescriptor` dataclass for multi_field internals
  - `NodeDef.content: list[Element]` replaces `fields`, `field_groups`, `lists`, `table`
  - `NodeDef.content_by_key(key)` and `content_by_type(type)` helpers
  - `WorkflowDef.from_json(path)` / `to_json(path)` — JSON round-trip
  - `WorkflowDef.all_fields` and `node_content()` walk content list
  - Each field-like element carries `grouped: bool`
  - Keep `from_dict()` temporarily (needed for YAML loading until Phase 3)
  - Remove `FieldGroupDef` (replaced by `MultiField`)
- `engine/runtime/compat.py` — Add content synthesis for old-format YAML:
  - `_normalize_content()`: synthesize `content` from `fields`/`field_groups`/`lists`/`table`
  - Type alias mapping: `text` → `text_field`, `toggle`/`boolean` → `boolean_field`, etc.
  - This is a **temporary bridge** — removed in Phase 4 when YAML support is dropped

**Verify:** Load all 11 YAMLs via the compat bridge. Assert `node.content` is populated correctly. Assert `all_fields` returns same fields as before. Assert `content_by_key` works. Write one workflow as a Python module, load it, confirm identical behavior.

---

### Phase 2: Renderer + Affordances + JS (The Switch)
**Goal:** Python renderer builds state from content. JS dispatches on element type.

**Blast radius mitigation:** Verify Python output via curl/Agent mode first, then update JS. Sequential testing within one commit.

**Python files:**
- `engine/runtime/renderer.py` — Rewrite `render_page()`:
  - Single loop over `node_content(node.id)`, dispatching by element type
  - Per-element render functions: `_render_field()`, `_render_multi_field()`, `_render_table()`, `_render_list()`, `_render_text_display()`
  - Affordances generated inline per-element
  - Top-level affordances built by walking content + flow control sources
  - Remove `_build_fields()`, partition/reattach block, `state["providers"]`
  - Update `_serialize_definition()` for content summaries
- `engine/runtime/affordances.py` — Simplify:
  - Per-element functions: `field_affordance()`, `multi_field_affordance()`, `table_affordances()`, `list_affordances()`, `execution_affordances()`
  - `flow_control_affordances()` for proceed/navigation/fork/actions
  - Remove monolithic `get_node_affordances()`, all `_field_label`/`_table_anchor` tags, `FieldGroupSource`
- `engine/runtime/actions.py`:
  - Guard grouped fields in `_set_field`
  - List/table lookup via `content_by_key()` / `content_by_type()`
- `app/app.py`:
  - Rewrite `_all_affordances()` to walk `state.content`
  - Rewrite `_compute_feedback()` to diff by `key` (fixes pre-existing bug)

**JS files:**
- `app/static/renderers/human-renderer.js`:
  - `_elementRenderers` registry replacing `_sectionRenderers`
  - New renderers: `multi_field`, `table` (from content item), `list`, `text_display`
  - Updated: `text_field`, `boolean_field`, `choice_field`
  - Remove old `_sectionRenderers['table']`, `['execution_table']`, `['content']`
  - Update `_wfClassifyAffordances`, `_structuralKeys`, feedback highlighting

**Verify:** Every workflow in Agent + Human mode. All action types. Feedback highlighting. SSE. curl response shape validation.

---

### Phase 3: Definition Migration
**Goal:** Convert YAML files to Python modules and JSON. Update builder.

**Files:**
- `data/workflows/` (new directory):
  - `create_cr.py`, `create_executable_table.py` — hand-authored Python modules for built-in workflows
  - Builder-published workflows remain as JSON in `data/custom_workflows/`
- `data/agent_create_cr.yaml` etc. — **deleted** (replaced by Python modules)
- `engine/builder.py`:
  - `_publish()` outputs JSON via `WorkflowDef.to_json()`
  - Builder's internal state model unchanged
- `app/app.py` — Update workflow discovery:
  - Scan `data/workflows/*.py` for hand-authored Python definitions (import and register)
  - Scan `data/custom_workflows/*.json` for builder-published definitions (load via `from_json`)
  - Remove YAML discovery path
- `engine/runtime/__init__.py` — Remove `yaml.safe_load()` import and YAML loading code

**Verify:** All workflows load and run. Builder publish → load round-trip works. No YAML files remain in the load path.

---

### Phase 4: Cleanup + Documentation
**Goal:** Remove all YAML infrastructure. Update documentation.

**Files:**
- `engine/runtime/compat.py` — **deleted entirely**. No YAML normalization needed.
- `engine/runtime/schema.py` — Remove `from_dict()` classmethods (no longer needed). Remove old attributes (`fields`, `field_groups`, `lists`, `table`) if any backward-compat shims remain. Clean up type aliases.
- `engine/runtime/renderer.py` — Remove dead code paths
- `engine/runtime/affordances.py` — Remove dead source classes
- `engine/utils.py` — Remove `field()` helper if unused
- `app/static/renderers/human-renderer.js` — Remove dead rendering functions
- `app/templates/workshop_elements.html` — Update Element Library
- `docs/ENGINE.md` — Rewrite for Python-native definitions and unified content model
- 11 old YAML files — **deleted** (if not already in Phase 3)

**Verify:** Full regression. Confirm no YAML imports or compat references remain in codebase.

---

## Files Summary

| File | Phase | Change |
|------|-------|--------|
| `engine/runtime/schema.py` | 1 | Major rewrite: element dataclasses, content list, JSON serialization |
| `engine/runtime/compat.py` | 1, 4 | Temporary YAML bridge in Phase 1; deleted in Phase 4 |
| `engine/runtime/renderer.py` | 2 | Content-driven assembly, inline affordances |
| `engine/runtime/affordances.py` | 2 | Per-element functions, remove monolithic collector |
| `engine/runtime/actions.py` | 2 | Grouped field guard, content-based lookup |
| `engine/runtime/__init__.py` | 3 | Remove YAML loading |
| `app/app.py` | 2, 3 | Feedback/affordance rewrite; update discovery |
| `app/static/renderers/human-renderer.js` | 2 | Element-type dispatch, new renderers |
| `engine/builder.py` | 3 | JSON output via `to_json()` |
| `data/workflows/*.py` | 3 | New: hand-authored Python definitions |
| `data/custom_workflows/*.json` | 3 | Builder output format (was YAML) |
| 11 YAML files | 3-4 | Deleted |
| `app/templates/workshop_elements.html` | 4 | Update Element Library |
| `docs/ENGINE.md` | 4 | Rewrite documentation |

## Risks and Mitigations

**Risk:** `show_all_content` merging produces different ordering than `show_all_fields`. **Mitigation:** Deduplicate by key, first occurrence wins. Test with Change Definition node in Create CR.

**Risk:** Builder has no multi_field concept. **Mitigation:** Builder emits standalone fields. multi_field authoring deferred.

**Risk:** Feedback diffing was already broken. **Mitigation:** This refactor fixes it properly.

**Risk:** Affordance IDs are not stable across renders. **Mitigation:** Agents should use `url` as the stable identifier. Document this.

**Risk:** Phase 2 blast radius (Python + JS simultaneously). **Mitigation:** Verify Python via curl first, then JS. Single commit, sequential testing.

**Risk:** Python module discovery is more complex than YAML glob. **Mitigation:** Use a simple registry pattern — each module registers its `WorkflowDef` at import time, or use `importlib` with a known directory.

**Risk:** JSON definitions are less readable than YAML for debugging. **Mitigation:** Python modules are the human-readable format. JSON is machine-readable persistence. Use `json.dumps(indent=2)` for readable output.

## Verification (end-to-end)

After each phase:
1. **Agent mode**: `curl GET /agent/{wf_id}/{inst_id}` — confirm response shape
2. **Human mode**: Load each workflow in browser — confirm visual rendering
3. **Actions**: Test set_field, set_fields (grouped guard), proceed, go_back, list ops, table ops, cell_action
4. **Builder**: Create → publish (JSON) → load → execute a workflow
5. **SSE**: Confirm live updates in observer mode
6. **Feedback**: Confirm structured diff works (previously broken — verify it now works)
7. **Python definition**: Load a hand-authored `.py` workflow, confirm identical behavior to JSON-loaded
