# Workflow Engine: Forward Plan

*Distilled from Session-2026-03-05-001 design discussions*

---

## The Core Idea

A workflow engine that governs all QMS operations — document creation, review, execution, closure — through a single interaction model. The agent navigates a graph of nodes, filling slots at each one. The engine validates and routes. Everything the QMS does today (CRs, INVs, VARs, TPs, ERs, even RTM updates) becomes a workflow: a named subgraph with a start node.

---

## Three Primitives

| Primitive | Shape | Purpose |
|-----------|-------|---------|
| **Slot** | `{name, type, value?, writable}` | A single piece of data on a node |
| **Node** | `{id, slots, edges, prompt?}` | A step in a workflow |
| **Edge** | `{to, when?}` | A connection between nodes |

Everything else — prompts, schemas, gates, templates, documents — is emergent from these three.

## Execution Semantics

- **Fork:** Multiple outgoing edges that evaluate true all fire (parallel activation)
- **Join:** A node waits for all activated predecessors to complete (AND-join)
- **Dead path elimination:** If a predecessor was never activated, it is not waited on
- **Acyclic constraint:** The graph is always a valid DAG — no cycles, no deadlocks

## Two Modes

| | Construction | Execution |
|---|---|---|
| Agent sees | Node schema (slot definitions, edges) | Node prompt (slots to fill) |
| Agent does | Modify structure (add/remove slots, edges, nodes) | Fill slots (provide values) |
| Artifact | The graph definition | Filled slot values |

Both modes share the same mental model: the agent is "at" a node. The mode determines what actions are available.

## Navigation

- The agent always starts at a **home node** — a global navigation root
- **Start nodes** mark the entry points of self-contained workflows
- From home, the agent can: enter construction mode (build a new workflow), begin executing an existing workflow, or inspect completed work
- Workflow identity maps to QMS document types: a CR is a workflow, an INV is a workflow, a VAR is a sub-workflow spawned from within a CR

## Replication (Not Cycles)

When a workflow step needs to repeat an unknown number of times (e.g., defining multiple execution items in a CR), the engine **replicates** the node forward. Each replica is a new node with a fresh ID. The agent chooses "add another" or "proceed" via edge conditions. The graph grows forward, never backward.

## Storage

- **Format:** YAML — human-readable, git-diffable, machine-parseable, LLM-comprehensible
- **Definition vs. instance:** The graph structure (nodes, slots, edges, prompts) is the definition. Filled slot values during execution are the instance. Separate concerns, like an EBR's Master Batch Record vs. execution record.
- **The agent never touches raw YAML.** It uses construction/execution tools. The engine handles serialization.

## Agent Interface

The agent interacts via tool/function calls, not raw text parsing.

**Construction tools:** `add_node`, `add_slot`, `add_edge`, `modify_slot`, `remove_*`, `move_to`, `inspect`, `validate`

**Execution tools:** `respond` (fill slots), `inspect` (view a node), `progress` (see overall status)

**Rendered view at each node** (execution mode):
```
[PROGRESS: 4/12 nodes complete | 2 ready | Branch: main path]

## Current: Observe and Document Symptoms

Gather all observable facts about the problem. Do not jump to conclusions.

### Provide:
- symptoms (text, required): What symptoms are present?
- onset (text, required): When did the problem start?
```

Key properties (from research):
- Show only the current node, not the whole graph
- Natural language for prompts, structured calls for responses
- Slot names should be self-documenting (field naming swings accuracy from 4.5% to 95%)
- Validate immediately; reject invalid responses before advancing
- Collapse completed nodes to outcomes (slot values only)

## Genesis

There is no special meta-workflow. "Create a new workflow" = enter construction mode on an empty graph from the home node. The agent builds nodes, defines slots, wires edges — riding the graph, not writing code. The constructed graph is provisional (DRAFT) until it passes QMS review and approval.

---

## What Comes Next

1. **Define the engine core** — the DAG scheduler that manages node readiness, edge evaluation, fork/join, and dead path elimination
2. **Define the tool surface** — the exact construction and execution tool signatures the agent will call
3. **Build one real workflow** — likely CR, since it's the most exercised document type — in YAML, and execute it manually to validate the model
4. **Build the rendering layer** — the ACI that translates graph state into the focused, progressive-disclosure view the agent sees
