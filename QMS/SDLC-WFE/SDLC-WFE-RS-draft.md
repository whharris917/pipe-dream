---
title: Workflow Engine Requirements Specification
revision_summary: Cornerstone requirements — graph primitives, lifecycle, construction,
  navigation, rendering, persistence, CLI
---

# SDLC-WFE-RS: Workflow Engine Requirements Specification

## 1. Purpose

This document specifies the functional requirements for the QMS Workflow Engine (`qms-workflow-engine/`), a graph-based DAG execution engine for orchestrating AI agent workflows.

These requirements serve as the authoritative specification for workflow engine behavior. Verification evidence demonstrating compliance with each requirement will be documented in SDLC-WFE-RTM when the system is ready for qualification.

---

## 2. Scope

This specification covers:

- Graph primitives (Slot, Node, Edge)
- DAG construction and validation
- Workflow execution (scheduling, slot-filling, edge evaluation)
- Workflow definition storage and loading
- Agent tool surface (construction and execution modes)
- Rendering (graph state to agent-readable view)

This specification does not cover:

- Integration with the existing QMS CLI or document control system
- User interface or visual rendering
- Performance characteristics
- Deployment or infrastructure

---

## 3. System Overview

*This section provides context for understanding the requirements. It is informative, not normative — the requirements in Section 4 are the authoritative specification.*

### 3.1 What the Workflow Engine Does

The workflow engine executes directed acyclic graphs (DAGs) where each node represents a step in a workflow and edges define the flow between steps. Nodes contain typed slots that hold data. Edges may have conditions that control which paths are taken.

### 3.2 Bedrock Primitives

The engine is built on three primitives:

- **Slot** — `{name, type, value?, writable}` — the atomic unit of data within a node
- **Node** — `{id, slots, edges, prompt?}` — a step in a workflow containing slots and outgoing edges
- **Edge** — `{to, when?}` — a conditional connection from one node to another

Everything else — prompts, schemas, gates, templates, documents — is emergent from these three.

### 3.3 Execution Model

The engine operates in two modes:

- **Construction mode** — modify graph structure (add/remove nodes, edges, slots)
- **Execution mode** — fill slots, evaluate edges, advance through the DAG

During execution, the scheduler evaluates node readiness (all required input slots filled), activates ready nodes, evaluates outgoing edges when a node completes, and handles fork/join semantics. Multiple true outgoing edges all fire (fork). Downstream nodes with multiple incoming edges wait for all active incoming paths (AND-join).

### 3.4 Storage

Workflow definitions are stored in YAML. Definitions (templates) are separate from instances (active executions with filled slot values).

---

## 4. Requirements

*Requirements are added incrementally as development proceeds. Each requirement is atomic, testable, and identified by `REQ-WFE-NNN`.*

### 4.1 Graph Primitives

**REQ-WFE-001:** A Slot shall have a name, a type, an optional value, and a writable flag.

**REQ-WFE-002:** A Node shall have a unique identifier, a collection of Slots, and a collection of outgoing Edges.

**REQ-WFE-003:** An Edge shall have a target Node reference and an optional condition.

**REQ-WFE-004:** The graph shall enforce the acyclic invariant: no sequence of edges may form a cycle.

**REQ-WFE-005:** Every graph shall have exactly one home node that serves as the universal navigation root.

### 4.2 Graph Lifecycle

**REQ-WFE-006:** A graph shall have a lifecycle state: draft or committed.

**REQ-WFE-007:** A new graph shall be created in draft state with a home node.

**REQ-WFE-008:** A draft graph shall be committable, which freezes its structure and makes it immutable.

**REQ-WFE-009:** A committed graph shall be checkable-out, which produces a draft copy for editing.

**REQ-WFE-010:** Construction operations shall be rejected on a committed graph.

### 4.3 Construction Operations

**REQ-WFE-011:** The engine shall support creating a new node in a draft graph.

**REQ-WFE-012:** The engine shall support deleting a node from a draft graph, including removal of all edges referencing the deleted node.

**REQ-WFE-013:** The engine shall prevent deletion of the home node.

**REQ-WFE-014:** The engine shall support adding a slot to a node in a draft graph.

**REQ-WFE-015:** The engine shall support removing a slot from a node in a draft graph.

**REQ-WFE-016:** The engine shall support creating an edge between two nodes in a draft graph.

**REQ-WFE-017:** The engine shall reject creation of an edge that would violate the acyclic invariant.

**REQ-WFE-018:** The engine shall support removing an edge from a draft graph.

### 4.4 Navigation

**REQ-WFE-019:** The engine shall maintain a current node context representing the user's position in the graph.

**REQ-WFE-020:** The engine shall support navigating to a connected node by following an outgoing edge from the current node.

**REQ-WFE-021:** The engine shall support jumping directly to the home node from any position.

### 4.5 Rendering

**REQ-WFE-022:** The engine shall render the current node showing its identifier, its slots (with names, types, and values), and its outgoing edges (with targets and conditions).

**REQ-WFE-023:** The rendered view shall indicate whether the graph is in draft or committed state.

### 4.6 Persistence

**REQ-WFE-024:** The engine shall save a graph to a YAML file preserving all nodes, slots, edges, the home node identity, and the lifecycle state.

**REQ-WFE-025:** The engine shall load a graph from a YAML file, restoring the full graph structure and lifecycle state.

### 4.7 CLI Entry Point

**REQ-WFE-026:** The engine shall provide a command-line entry point that creates or loads a graph and positions the user at the home node in construction mode (if draft) or read-only mode (if committed).

---

## 5. Environmental Assumptions and Exclusions

### 5.1 Assumptions

- Python 3.10+ runtime environment
- No external service dependencies (self-contained library)
- YAML available for workflow definition storage

### 5.2 Exclusions

- Network communication or API hosting
- Persistent database storage (filesystem only)
- Real-time performance guarantees

---

**END OF DOCUMENT**
