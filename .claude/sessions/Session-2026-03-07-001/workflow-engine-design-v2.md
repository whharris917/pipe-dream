# Workflow Engine Design v2
*Session-2026-03-07-001*

---

## 1. Core Principle: Everything Is Graph Execution

There is one verb: **execute**.

The engine executes graphs. It does not know or care what phase a document is in, whether it is authoring or running, or what the output will be used for. That is the caller's concern.

The phase distinction is real — authoring a CR is different from executing a CR — but it lives in *which graph is being run and what it produces*, not in any engine-level mode or behavior switch.

---

## 2. Bedrock Primitives

Three primitives, unchanged:

- **Field** — `{name, type, value?, writable}` — the atomic unit of data within a node
- **Node** — `{id, fields, edges, prompt?}` — a step in a workflow
- **Edge** — `{to, when?}` — a conditional connection from one node to another

Everything else is emergent.

---

## 3. Templates and Instantiation

### 3.1 Templates Are Graphs

A template is a graph definition with some fields designated as **parameters** (must be supplied at instantiation) and others as **constants** (fixed in the template).

### 3.2 Instantiation Is Execution

There is no separate "instantiate" operation. Instantiating a template *is* executing it. During the authoring phase, the agent executes the template — filling in parameter fields, traversing its nodes — and the output is a concrete subgraph that gets embedded into the workflow being constructed.

Template execution is an action of the authoring phase. Its output is the graph that will be executed during the execution phase.

### 3.3 Template Library

Templates are stored as YAML definitions, separate from workflow instances. The library grows organically as reusable patterns are identified. Every common document structure — EI, commit-EI, VAR branch, VR node, review gate — becomes a template.

### 3.4 Recursive Closure

Writing a new template = executing the write-template template. The system describes and extends itself using its own mechanism.

---

## 4. The Execution Item (EI) as the Canonical Node

EIs are the central purpose of the workflow engine. Getting agents to plan and execute EIs correctly — with proper sequencing, prerequisite enforcement, branching, and amendment handling — is the core challenge the engine exists to solve.

### 4.1 EI Field Structure

Every EI has the same internal structure:

| Field | Writable | Set During |
|-------|----------|------------|
| `task_description` | No | Authoring (template parameter) |
| `vr_required` | No | Authoring (template parameter) |
| `execution_summary` | Yes | Execution |
| `outcome` | Yes | Execution |
| `performed_by` | Yes | Execution |
| `date` | Yes | Execution |

### 4.2 Prerequisites = Incoming Edges

There is no explicit "prerequisites" field. The graph topology encodes prerequisites: an EI node becomes ready when all its incoming edges are satisfied. This handles sequential ordering, branching, forks, and join points — everything a flat EI table cannot express.

### 4.3 Outgoing Edges: Conditions Over Topology

Every EI node has the same outgoing edges, regardless of its parameter values. Edge conditions — not the presence or absence of edges — determine which paths are traversed:

| Edge Target | Condition |
|-------------|-----------|
| VAR branch | `outcome == Fail` |
| VR node | `vr_required == True` |
| Next EI | `outcome == Pass` |

If `vr_required` is False, the VR edge is never traversed. If `outcome` is Pass, the VAR edge is never traversed. The topology is invariant; the data drives behavior.

When VR is required, a join point before the next EI waits for both the VR completion and the Pass outcome — AND-join semantics already present in the engine.

### 4.4 The EI Template

Because all EIs have identical structure, the EI subgraph is defined once as a reusable template. Parameters: `task_description`, `vr_required`. Everything else is fixed.

### 4.5 The Commit-EI Template

A specialized EI template with `task_description` fixed as a constant ("Commit and push. Record hash.") and no parameters. Every CR's execution graph begins and ends with a commit-EI instance. The create-CR template instantiates these automatically — the agent is never prompted about them.

---

## 5. The Two-Phase Model

| Phase | Input | Output |
|-------|-------|--------|
| Authoring | Templates | Execution graph (structure complete, execution fields blank) |
| Execution | Execution graph | Filled document (all fields populated) |

Both phases use the same engine operation: execute a graph. The difference is which graph is running.

During authoring, executing the create-CR template includes executing the EI template for each EI the agent defines. Each EI template execution produces a concrete EI node (task_description and vr_required filled; execution fields blank and writable) embedded into the CR's execution graph. The commit-EI nodes are added automatically.

When authoring completes, the CR execution graph is fully defined. Structure is frozen. Execution fields are blank. This graph is what runs during the execution phase.

---

## 6. Graph State: Property, Not Mode

The draft/committed distinction is a property of a graph instance, not an engine mode. The engine executes graphs regardless of their state.

- **Draft:** structural modifications permitted (add/remove nodes and edges)
- **Committed:** structural modifications rejected; writable fields are fillable

The engine imposes no behavioral modes. It executes. Guards on individual operations handle the state rules.

---

## 7. What the Engine Does Not Know

The engine has no knowledge of:

- Document lifecycle (DRAFT, IN_EXECUTION, CLOSED, etc.)
- QMS document types (CR, VAR, VR, INV)
- Authoring vs. execution phase
- What a "good" outcome is
- Who is allowed to do what

All of that lives in the workflow definitions and the system that invokes the engine.

---

## 8. Hooks

Hooks are commands executed automatically at three trigger points:

- **Enter node** — fires when the engine moves into a node; can block entry
- **Exit node** — fires when the engine completes a node; can block exit
- **Traverse edge** — fires before an edge is followed; can block traversal

Hooks are the integration point between the graph execution engine and external state. They handle validation conditions that cannot be expressed as field conditions on edges, and side effects that must occur at specific transition points.

**Example:** A hook on the "route RTM for approval" edge:
1. Queries the database: is the RS referenced by this RTM in an approved state?
2. Queries the database: does the qualified commit hash in this RTM match the current HEAD of the associated CR's execution branch?
3. If either check fails → blocks traversal with an informative error
4. If both pass → traversal proceeds

Hooks are defined in workflow YAML alongside nodes and edges. Hook implementations are separate from the workflow definition — the same workflow can use different hook implementations (mock in sandbox, real QMS in production) without modification.

**What governs whether a transition happens:**

| Layer | Mechanism | Where defined |
|-------|-----------|---------------|
| Field conditions | `when: field==value` on edges | Workflow YAML |
| External validation | Hooks querying/writing external state | Workflow YAML + hook implementations |
| Structural guards | Engine rules (committed graph rejects construction ops) | Engine |

---

## 9. External State and the Mock Database

The engine needs to query information that exists outside the graph — document approval states, version numbers, qualified commit hashes, branch metadata. The engine itself holds none of this; hooks reach out to retrieve it.

For isolated sandbox development (within `qms-workflow-engine/`, no contact with the real QMS), a rudimentary JSON database serves as a mock representation of external state. Hooks read from and write to this database.

**Mock database contents (representative):**
- Document states (DRAFT, IN_REVIEW, EFFECTIVE, etc.)
- Document metadata (version, responsible user, qualified commit hash)
- Branch metadata (current HEAD commit)
- Any external state a workflow needs to reason about

When the engine is eventually integrated with the real QMS, the hook implementations are swapped — the engine and workflow definitions are unchanged. The mock database is a seam, not a dependency.

---

## 10. Bootstrap Strategy

The engine is built and validated through a self-consuming bootstrap process:

**Step 1 — the seed:**
Build the minimal Python engine and hand-author the `create-workflow` workflow in YAML. `create-workflow` is the only artifact that exists outside the bootstrap process — it cannot build itself because it doesn't exist yet.

The minimal Python engine contains:
- Data structures: Field, Node, Edge, Graph (with template/instance distinction)
- YAML I/O
- Execution loop: present prompt → accept response → fill field → evaluate edges → advance
- Template instantiation
- Construction primitives (add/remove nodes, edges, fields)
- Hook dispatch (enter node, exit node, traverse edge)
- Mock database read/write

**Step 2 — eat your own cooking:**
Execute `create-workflow` to build all other workflows: `ei-template`, `commit-ei-template`, `create-cr`, `create-var`, `create-vr`, review gates, approval gates, etc. Each workflow, once built, is immediately available to build the next.

**The feedback discipline:**
If `create-workflow` cannot produce a working downstream workflow — because a prompt is missing, a condition is inexpressible, a hook can't be defined — that is a Step 1 failure. Delete all workflows. Fix the engine or `create-workflow`. Restart. No patches on a broken foundation.

---

## 11. Open Questions

- **Graph as document:** Is the graph the document itself (node fields ARE the document content), or does the graph produce a document as a separate artifact? The former is the more radical and potentially more elegant model; decision pending.
- **Construction as execution:** Are structural modification operations (add node, add edge) themselves graph execution steps — you never call the construction API directly, only execute graphs that modify other graphs? The bootstrap strategy suggests construction primitives exist in Python for Step 1, with the goal of never calling them directly after `create-workflow` exists.
- **Amendment trails:** When an execution field is amended (e.g., outcome changed after downstream EIs have been filled), cascading reverts are needed. Where does the amendment trail live — in the Field model itself (append-only entries), or at the graph level?

---

*This document captures design decisions made in Session-2026-03-07-001. It supersedes the forward plan in Session-2026-03-05-001 for engine architecture.*
