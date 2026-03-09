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

## The Form Is Not the Workflow Step

### The Revelation

Consider the Initiation stage of the current "Create Change Record" workflow. The UI
presents a form: title, purpose, affects_code, submodule. The user fills it out and
submits. But there is no explicit *instruction* — no directive that says "Describe the
change you're proposing. The title should be action-oriented and concise. The purpose
should articulate *why* this change is needed, not *what* it changes."

The instruction is entirely implicit. A human infers it from field labels and layout
convention. An agent has no access to it at all.

This reveals a fundamental conflation: **the form is being treated as the workflow step.**
But they are categorically different things:

- **The form** is a data structure — fields with names, types, and validation rules. It
  is a noun. It answers: "What information exists here?"
- **The workflow step** is a directive — an instruction to an actor to perform an action,
  which may include filling out a form. It is a verb. It answers: "What should you do,
  and how should you do it?"

The form says: `title [String], purpose [Text], affects_code [Boolean]`.
The workflow step says: "Describe the proposed change. The title should be action-oriented
and concise (e.g., 'Add particle collision detection' not 'Changes to physics engine').
The purpose should explain *why* this change is needed — what problem it solves or what
capability it adds. The scope fields will capture *what* changes; don't duplicate that
here."

### Why This Matters

Without explicit instructions, the workflow is just a database schema with sequencing.
The process knowledge — the part that makes it possible for someone unfamiliar with the
document type to produce quality output — lives only in the designer's head.

This is the **context gap** identified in P5 (Guidance is layered), but now understood at
a more granular level. P5 identified three guidance channels (canvas, authoring,
execution). This insight sharpens the execution channel: every stage node needs an
**instruction** that is distinct from (and more important than) its field list.

The instruction is what makes the workflow a *workflow* rather than a form wizard. It
encodes:

1. **What to do** — the action the actor must perform
2. **How to do it well** — quality criteria, common pitfalls, examples
3. **What "done" looks like** — completion criteria that the gate will evaluate
4. **What context matters** — which other stages or documents are relevant

### Implications for the Sandbox

Each stage node in the graph builder needs two distinct property groups:

1. **Fields** — the data slots (what we already have: name, type, editability)
2. **Instruction** — the directive to the actor (what to do, how, and when it's done)

The instruction is the primary artifact of the stage. The fields are secondary — they are
the *materials* the actor works with while following the instruction. A stage could
theoretically have an instruction with no fields (e.g., "Review the document for
completeness and route for approval") or fields with no meaningful instruction (though
this is a design smell — it means the process knowledge hasn't been captured).

### Relationship to Templates and Workflows

This further clarifies the template/workflow separation:

- **Template** defines the form: field names, types, validation rules, rendering hints.
  It is reusable across workflows.
- **Workflow** defines the process: which fields appear at which stage, in what order,
  with what instruction, gated by what conditions. It is the process knowledge layer.

The same template (e.g., "Change Record fields") could be used by different workflows
(e.g., "standard CR process" vs. "fast-track CR process") with different instructions
at each stage. The form is the same; the process of filling it out differs.

### Worked Example: The Implementation Plan Stage

The "Implementation Plan" stage of the CR workflow was initially confusing to model. It
felt like a special case — a complex sub-page with its own table builder, column types,
prerequisite logic, and sequential execution. Should it be a pointer to a sub-workflow?
A separate page-level entity?

The "form is not the step" insight resolves this cleanly. The Implementation Plan is
just a stage with:

**Instruction:**
> Complete the implementation plan table. Each row is an Execution Item (EI) — a discrete,
> verifiable unit of work. For SDLC-governed changes, the required EIs (baseline commit,
> RS update, implementation, qualification, RTM update, merge, pointer update, post-exec
> commit) have been pre-loaded and cannot be removed. You may add additional EIs as needed.
> Each EI must have a clear task description that specifies a verifiable action. Set
> prerequisites where execution order matters. Use the sequential column execution toggle
> if all EIs in a column must complete before the next column begins.

**Fields:** The plan table (columns, rows, cell values, table properties).

**Gate (preceding edge):** Change classification is complete — `affects_code` and
`submodule` fields are filled, which determines which template EIs get auto-loaded.

The key insight is that by the time the actor reaches this stage, the preceding gate has
already resolved the conditional logic. The classification decisions (Is this a code
change? Which system? SDLC-governed?) were made in earlier stages. The gate ensured
that the correct template EIs were stamped in as **protected rows** before the actor
arrived. So the instruction doesn't need conditional branches — it can be specific and
direct, because the workflow has already narrowed the context.

This is the constraint machine working as designed: earlier stages constrain later stages.
The actor at the Implementation Plan stage cannot accidentally omit required EIs because
they were structurally injected by the workflow, not manually added by the actor. The
instruction tells the actor what to *do*; the protected rows ensure they can't *undo*
what the process requires.

### The Plan Table Is a Workflow Graph

A further observation: the Implementation Plan table is literally another way of
rendering a workflow graph. The mapping is direct:

| Table Concept | Graph Concept |
|---------------|---------------|
| Row (EI) | Node |
| Prerequisite column | Edge (dependency) |
| Sequential column execution | Global topological constraint on edge structure |
| Cell values (outcome, date, performed_by) | Field values on the node |
| Audit trail per cell | Execution history per field |
| Cascading revert on modification | Re-evaluation of downstream node states |

The CR workflow is therefore **recursive**: the outer graph (Initiation → Classification
→ Implementation Plan → Review → ...) contains a stage whose *form* is itself a graph
in tabular notation. The table builder is not a separate system — it is a specialized
renderer for a nested workflow graph.

This has concrete design implications:

1. **One engine, two renderers.** The same graph engine that runs the outer CR workflow
   can run the inner EI graph. The table UI is just a different visual projection of
   the same data structure — rows instead of nodes, columns instead of edge layout.

2. **Compile to nested YAML.** The "compile to source" step can emit the plan as a
   nested graph definition within the parent workflow, not a bespoke table format.
   The source representation is uniform.

3. **Execution semantics are inherited.** The audit trail and cascading reverts aren't
   special table logic — they are the sub-graph's execution semantics. When a node's
   field value changes after downstream nodes have already been filled, the engine
   re-evaluates the dependency chain. This is what any workflow engine does when an
   upstream state changes; the table just makes it visible as "cascading revert."

4. **The Sandbox can author both levels.** A workflow designer could build the outer CR
   process graph in the Sandbox, then drill into the Implementation Plan stage and build
   the inner EI graph — using the same tools, same node/edge/gate primitives, same
   instruction properties. The table view is an alternative rendering mode, not a
   different authoring paradigm.

### One Format for All Tables

If a table is a graph and a graph compiles to YAML, then the YAML workflow format
naturally becomes the representation for *all* tables — not just implementation plans.
Any tabular data in any document type (risk assessments, test matrices, requirement
traceability) is a graph definition.

This means:
- **Table templates** are workflow templates. A "standard EI table" template defines
  protected rows and columns the same way a workflow template defines protected nodes
  and fields.
- **Table instances** are workflow instances. A filled-in plan table is an executed
  sub-graph with field values, audit history, and state.
- **Table authoring, execution, and review** are the same lifecycle phases as the
  parent workflow — because they *are* workflow phases, just rendered as rows and columns.

The YAML format we design for workflow definitions will therefore serve triple duty:
top-level process graphs, nested sub-graphs (tables), and their templates. There is no
separate "table schema" format. This eliminates an entire category of bespoke
serialization — the current `plan_columns` / `plan_rows` / `table_properties` JSON
structure in the CR data files is a one-off encoding that would be replaced by the
uniform graph YAML.

### Table Features Are Graph Features

If tables are graphs, then the special behaviors we built for the plan table are not
table-specific — they are *graph execution semantics* that we discovered in a tabular
context. They belong on the engine primitives, available to all nodes:

| "Table Feature" | Actual Graph Primitive |
|-----------------|----------------------|
| **Audit trail per cell** | Field-level change history on any node |
| **Cascading revert** | Downstream state re-evaluation when an upstream field changes |
| **Non-executable column** | Read-only field category (set at authoring time, never filled during execution) |
| **Executable column** | Writable field category (filled by the actor during execution) |
| **Auto-executed column** | Computed field category (value derived from other fields or system state) |
| **Sequential column execution** | Topological constraint: all fields in category N must be complete before category N+1 becomes writable |

These aren't features we *add* to nodes — they are features we *stop restricting* to
tables. Every node in every workflow gets:

- **Field-level audit trail**: Who changed what, when, and from what prior value.
  Currently only the plan table tracks this. It should be universal.
- **Cascading re-evaluation**: If a field value changes after downstream nodes have
  been completed, the engine flags affected nodes for re-execution. The plan table
  does this as "cascading revert"; the general case is dependency-aware state
  invalidation.
- **Field execution categories**: Fields are classified as non-executable (read-only
  context set during authoring), executable (writable during execution), or
  auto-executed (computed by the engine — e.g., timestamps, derived values, counts).
  This replaces the ad-hoc editability flags currently set per-stage in the workflow
  YAML.
- **Category sequencing**: Execution categories can be ordered — all fields in
  category A must be filled before category B becomes writable. This generalizes
  "sequential column execution" from a table toggle to a graph-level constraint.

The result: the engine has one set of execution semantics. The table renderer and the
graph renderer both project the same underlying behavior. No special cases.

### Relationship to the Constraint Machine

This deepens the constraint machine model (see `workflow-as-constraint-machine.md`).
The constraint machine doesn't just restrict *what* actions are available — it provides
*instructions* for what the actor should do with those actions. The agent interaction
model becomes:

1. **Query current state** → receive instruction + permitted fields + current values
2. **Follow the instruction** → fill fields according to the directive
3. **Request transition** → engine evaluates gate (which encodes "what done looks like")

The instruction is what makes the constraint machine *usable*, not just *enforceable*.
Without it, the machine constrains but does not guide. With it, the machine is both
the guard rail and the road map.

---

## Edge Cases: Minimum Templates and Minimum Workflows

Examining the extremes of the design space clarifies what templates and workflows
actually are — and how they relate (or don't).

### Minimum Template: The Memo

What is the simplest possible template? A set of fields with no special conditions,
no conditional edges, no complex stage gates. Just data slots.

The accompanying workflow would be the **baseline document lifecycle**: create the
document → fill out the fields → submit for review → approval → release. The only
gates are the standard ones: "all required fields filled" before review, "reviewer
approved" before release.

This is simpler than any existing non-executable document in the QMS. A memo, a
notice, a simple record — anything where the value is in the captured information,
not in a complex process of producing it. The template defines what to record; the
baseline workflow provides the minimum governance wrapper.

This suggests the engine should provide a **default workflow** that any template can
inherit: the standard create → fill → review → approve → release lifecycle. Most
simple document types would use this default and only define their fields. Custom
workflows are for when the process of filling out the document is itself complex
enough to need stages, gates, and instructions.

### Minimum Workflow: The Decision Tree

What is the simplest possible workflow? Here, the more interesting question is: does
a workflow need a template at all?

**No.** Not every workflow needs to produce a document. Some workflows exist purely
for their *effects* — routing a decision, providing guidance, triggering actions. The
value is in the execution path, not in a recorded artifact.

Examples of template-less, document-less workflows:

- **Help Desk decision tree**: "Is your issue about X? → Yes → Do A. No → Is it
  about Y? → ..." The workflow guides the actor through a branching decision, but
  no document is created. The value is in reaching the right answer.
- **How to check your inbox**: A guidance workflow with pure instruction nodes. No
  fields to fill, no data to record. The workflow *is* the instruction manual,
  presented as an interactive walkthrough rather than a static document.
- **How to perform a review**: Step-by-step guidance for a reviewer — what to check,
  what to look for, how to record findings. The review itself is recorded on the
  parent document; the guidance workflow produces no artifact of its own.
- **Onboarding sequence**: A workflow that walks a new agent through setup tasks,
  each node containing instructions and a "done" acknowledgment. The value is in
  the orchestrated sequence, not in a final document.

### Implication: Workflows Will Proliferate

This reveals an asymmetry in the design space. Templates are relatively rare — they
correspond to document types, and organizations have a bounded set of those.
Workflows are potentially abundant. Every process, procedure, decision tree, guidance
sequence, and instructional walkthrough is a workflow.

If the QMS currently encodes process knowledge in SOPs (which are being phased out),
the natural successor is not "SOP content pasted into a UI page" — it is a
**workflow** that makes the process interactive, stage-gated, and executable by
agents. The SOP's static prose becomes a workflow's instruction nodes. The SOP's
implicit decision points become explicit conditional edges. The SOP's assumed context
becomes gate preconditions.

This means the Sandbox — the workflow authoring tool — is not just for building
document-type processes. It is the **primary authoring environment for all process
knowledge in the organization.** Workflows are the unit of reusable process
intelligence, and they will be created far more often than templates.

The engine should treat the template association as optional. A workflow can:
- **Reference a template**: Standard case — the workflow governs how a document of
  that type gets created and progressed.
- **Reference no template**: The workflow is standalone — guidance, decision tree,
  orchestration sequence. Execution produces effects and/or history, not a document.
- **Reference multiple templates**: Advanced case — a workflow that produces multiple
  documents (e.g., a CAPA workflow that creates both an Investigation report and a
  Corrective Action plan).

---

## Next Steps

1. Resolve open questions (Q1-Q5) through discussion
2. Define the revised data model (what changes in graph.py, template.py)
3. Define the revised CLI surface (what commands exist)
4. Implement
