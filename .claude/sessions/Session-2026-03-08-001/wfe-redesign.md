# WFE Redesign: First Principles

## The Unifying Insight

A workflow engine for GMP-style document management serves three functions simultaneously:

- **Document generation**: The blank workflow IS the plan
- **Execution guidance**: The workflow directs the executor through each step
- **Evidence recording**: The filled workflow IS the controlled document

These are not three separate systems. They are three views of one artifact at different lifecycle stages.

## Core Principles

### P1: A workflow is a DAG of steps with typed data slots and conditional edges.

Unchanged from v1. Field, Node, Edge, Graph. DAG invariant. Lifecycle (draft/committed).

### P2: Templates define reusable step patterns with enforcement rules.

Instantiation stamps required structure into the graph. Template-originated content
(nodes, fields, edges) is **protected** — authors can add to but not subtract from it.

Import is a first-class operation, not a hook side-effect.

### P3: Execution is filling slots and advancing. The graph gates progression.

Unchanged from v1. Fill fields, evaluate edge conditions, advance.

### P4: The filled graph IS the document. Rendering is a pure function of graph state.

Every node in the graph appears in the compiled output. No scaffold/hidden nodes.
No rendering hints in data primitives (`block`, `scaffold` are eliminated).

Rendering conventions are defined externally (in a render config or by convention on
template_id), not as field attributes.

### P5: Guidance is layered.

Three distinct guidance channels, each with a clear audience:

| Channel | Audience | Purpose | Example |
|---------|----------|---------|---------|
| **Canvas guidance** | Author | How to build this type of document | "This is an SDLC CR. Per SOP-002, import `ei` for each execution item. Minimum: baseline commit, implementation, qualification, post-exec commit." |
| **Authoring guidance** | Author | How to customize this template | "Set vr_required to 'yes' for steps needing behavioral verification. Task descriptions must be specific verifiable actions." |
| **Execution guidance** | Executor | How to perform this step | "Check out SDLC-QMS-RS. Add requirements in REQ-{SYS}-NNN format. Check in when done. Record version and req IDs." |

Canvas guidance lives on the workflow definition (or workflow type).
Authoring guidance lives on the template.
Execution guidance lives on the instantiated node.

---

## What Changes from v1

### Eliminated

| Concept | Why |
|---------|-----|
| Meta-workflows (`create-cr`, `create-workflow`, `create-template`) | Authoring is guided by canvas/template prompts, not by executing a separate workflow |
| `scaffold` flag on nodes | Every node appears in compiled output; no hidden authoring-only nodes |
| `block` flag on fields | Rendering hints belong in render configuration, not in data primitives |
| `build_node_chain` hook | Template import is a first-class engine operation |
| `extend_chain` hook | Adding steps is a construction operation, not a hook side-effect |
| `save_workflow` / `save_template` hooks | File I/O is a CLI concern, not a hook |
| Workspace as hook communication channel | TBD — may still be needed for simpler purposes |

### New

| Concept | Purpose |
|---------|---------|
| **Template enforcement** | Template-originated nodes/fields/edges are marked as protected; construction operations refuse to delete them |
| **Canvas prompt** | Top-level guidance on the workflow: what type of document this is, which SOPs apply, which templates to import |
| **Authoring prompt** (per template) | Instructions for the author on how to configure template-originated content |
| **Execution prompt** (per node) | Rich instructions for the executor on how to perform the step |
| **`wfe import <template>`** | First-class CLI command that stamps a template into the graph with enforcement |

### Retained

| Concept | Notes |
|---------|-------|
| Graph primitives (Field, Node, Edge, Graph) | Core is solid |
| DAG invariant + lifecycle (draft/committed) | Unchanged |
| Session + navigation (go, home, advance, fill) | Unchanged |
| Edge conditions (==, !=) | Unchanged |
| Templates + TemplateLibrary | Structure unchanged; gains authoring_prompt and enforcement metadata |
| Compile (graph → markdown) | Retained but simplified; no scaffold filtering, rendering hints move out of fields |
| YAML persistence | Unchanged |
| Hook infrastructure (register, fire, HookContext) | Retained for genuine extension points (validation, external integration) |

---

## Open Questions

### Q1: How does template enforcement work mechanically?

Options:
- **a) Protected flag on nodes/fields/edges**: Each entity has a `protected: bool` flag set
  during instantiation. Construction operations check it.
- **b) Template origin tracking**: Nodes/fields record their `template_id` origin.
  Deletion is blocked if the entity has a template origin.
- **c) Structural diff**: The engine keeps a reference to the original template and
  validates the graph still contains all template-required content.

Leaning toward (b) — it's simple, per-entity, and doesn't require keeping the template
around after instantiation.

### Q2: What is the right granularity for rendering configuration?

If `block` is eliminated from Field, where does the "render this field as a paragraph
body" hint live?

Options:
- **a) In the template definition**: Templates specify rendering hints for their fields.
  The compile step reads the template library.
- **b) In a separate render config file**: A YAML file mapping template_id → field → hint.
- **c) Pure convention**: Fields named `purpose`, `scope`, etc. render as blocks;
  everything else renders inline. No configuration.

### Q3: Do we still need hooks?

With meta-workflows eliminated, the primary hook use cases were:
- `init_target_graph`, `build_node_chain`, `save_workflow` — eliminated (meta-workflow support)
- `validate_field_in_db`, `lookup_entity_props` — genuine validation/enrichment
- `set_workspace`, `pull_from_workspace` — routing logic (may be eliminated with meta-workflows)
- `compile_to_file` — CLI concern

Remaining legitimate hook use cases:
- **Field validation** (is this value in the allowed set?)
- **External integration** (call QMS CLI to route a document)
- **Enrichment** (look up properties from a database)

These are real. The hook system should stay but be much smaller.

### Q4: What replaces the create-cr routing wizard?

The wizard determined which CR template to use based on: affects_code → involves_submodule → which_submodule → SDLC_governed?

Options:
- **a) CLI flags**: `wfe new cr --system flow-state` — the CLI has the routing logic.
- **b) Canvas prompt**: The blank CR tells the author "if SDLC-governed, import from
  cr-sdlc. If non-code, import from cr-non-code." Author follows guidance manually.
- **c) Both**: CLI provides a shortcut; canvas prompt provides fallback guidance.

### Q5: How rich should execution prompts be?

The prompt field currently holds a single sentence. For proper execution guidance, it
needs to hold multi-paragraph instructions. This is a content authoring problem, not
an engine problem — but it affects field type and rendering.

Should prompts:
- Be stored as multi-line text in the YAML?
- Reference external documents (e.g., "See SOP-004 Section 8")?
- Include both a summary (for compiled output) and detailed instructions (for the agent)?

---

## Sketch: What Authoring Looks Like

With the redesign, creating a CR would look like:

```
$ wfe new cr
Created graph 'cr' (DRAFT).

Canvas: This is a Change Record. Per SOP-002:
  - Fill in the Change Overview section (title, purpose, scope, etc.)
  - Import 'ei' template for each execution item
  - For SDLC-governed changes, include: baseline commit, RS update,
    implementation, qualification, RTM update, merge, pointer update,
    post-exec commit
  - See SOP-002 §5 for full requirements

Node: home  [HOME]
Fields: (none)
Edges: (none)

Construct: add node <name> | import <template> [key=value] | ...
```

The author reads the canvas guidance, imports templates, adds fields to the overview
node, wires edges. The engine prevents them from deleting template-required content.

```
$ wfe import ei task_description="Update the RS"
Imported template 'ei' as node ei-a1b2c3d4 (protected).
Authoring: Set vr_required to 'yes' if this step needs behavioral
  verification. Task description is fixed at import.

$ wfe import ei task_description="Implement the change"
Imported template 'ei' as node ei-e5f6g7h8 (protected).
```

Each import shows the template's authoring guidance. The author configures parameter
fields at import time. Template-originated structure is locked.

---

## Sketch: What Execution Looks Like

After authoring is complete and the graph is committed:

```
$ wfe view
=== my-cr (COMMITTED) - execution mode ===

Node: ei-a1b2c3d4
Execution prompt:
  Check out SDLC-QMS-RS via `qms checkout SDLC-QMS-RS`.
  Add requirements for [feature]. Each requirement must follow
  REQ-{SYS}-NNN format. Check in when complete.
  Record the new version number and requirement IDs in execution_summary.

Fields:
  task_description [string, read-only]: 'Update the RS'
  vr_required [bool, read-only]: 'no'
  execution_summary [string, writable]: (empty)
  outcome [string, writable]: (empty)
  performed_by [string, writable]: (empty)
  date [string, writable]: (empty)

Execute: draft | fill execution_summary <value> | fill outcome <value> | advance
```

The execution prompt is rich enough that the agent knows exactly what to do.

---

## Next Steps

1. Resolve open questions (Q1-Q5) through discussion
2. Define the revised data model (what changes in graph.py, template.py)
3. Define the revised CLI surface (what commands exist)
4. Implement
