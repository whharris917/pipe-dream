# The Agent Portal: Bijective Human-Agent Interfaces for Governed Process Automation

*A Technical Exposition of the Pipe Dream Workflow Engine's Agent Portal and Its Implications for Recursive Quality System Governance*

---

## Abstract

The Agent Portal is a component of the Pipe Dream Workflow Engine (WFE) that establishes a pattern for AI agent interaction with structured processes. At its core lies a principle we term **bijective mapping**: the guarantee that human observers and AI agents perceive identical state, identical affordances, and identical constraints at every point in a workflow's execution. This paper describes the Agent Portal's current architecture — a YAML-driven, affordance-centric workflow runtime — and argues that its interaction patterns constitute the foundational design language for the entire Pipe Dream quality management system. The Agent Portal is not merely a sandbox for workflow development; it is a proving ground for the interface paradigm that will govern all human-agent collaboration within the project.

---

## 1. Introduction

Software quality management systems have traditionally been designed for human operators executing documented procedures. The introduction of AI agents into this loop creates a fundamental interface challenge: how do you ensure that a process governed by an AI agent is auditable, transparent, and trustworthy? The answer is not to build a separate "agent API" alongside a "human UI." The answer is to build one interface that serves both, identically.

The Pipe Dream project pursues two intertwined objectives: **Flow State**, a hybrid CAD and particle physics application, and the **QMS** (Quality Management System), a GMP-inspired governance framework that controls how Flow State — and itself — evolves. The QMS operates recursively: it governs code changes via Change Records, and it governs its own procedural evolution via the same mechanisms. This recursive structure demands that every process action be traceable, auditable, and reproducible — requirements that become significantly harder to satisfy when the primary actor is an AI agent operating at machine speed.

The Agent Portal was built to solve this problem. It provides a unified runtime that interprets declarative workflow definitions and exposes them simultaneously to agents (via a resource-oriented API) and to humans (via a real-time observer UI). The critical architectural decision was not to build the observer as an afterthought or a monitoring dashboard, but to derive both the agent's action space and the human's visual representation from the same source of truth. This is the bijective mapping principle, and it is the central contribution of the Agent Portal's design.

---

## 2. The Bijective Mapping Principle

### 2.1 Definition

A bijective mapping, in this context, is a one-to-one correspondence between the agent's programmatic interface and the human's visual interface such that:

1. **Every element the agent can see, the human can see.** Every field value, every affordance, every gate condition, every lifecycle position rendered by the observer is derived from the same data structure the agent receives via the API.

2. **Every element the human can see, the agent can see.** There is no "hidden" UI state, no visual-only decoration that carries semantic meaning without a corresponding API representation. If the observer shows a lock icon on a proceed gate with the label "table has columns, table has rows," the agent's affordance list reflects exactly the same gate — either the proceed affordance is present (gate passed) or absent (gate blocked).

3. **The mapping is structure-preserving.** The correspondence is not merely informational but structural. The topology of the workflow — its nodes, branches, forks, and convergence points — is represented identically in the API's lifecycle array, the observer's schematic banner, and the YAML definition that generated both. A router node that evaluates three conditions and selects a target produces the same three-way branch in the API response, in the observer's flowchart, and in the spine model's gate segment.

### 2.2 Why Bijectivity Matters

The alternative — building an "agent API" and a "human dashboard" as separate systems — introduces a class of failure modes that are particularly dangerous in a governed process:

**Divergent state.** If the agent's API and the human's UI are backed by different rendering logic, they can disagree about what the current state is. The agent might see a field as editable while the human sees it as locked. This is not a hypothetical risk; it is the default outcome when two interfaces are maintained independently.

**Phantom affordances.** An agent might be offered actions that the human observer cannot see, or vice versa. In a quality system, this is a compliance failure — it means the audit trail does not faithfully represent the process that was actually executed.

**Semantic drift.** Over time, separate interfaces develop separate interpretations of the same underlying concepts. A "proceed" action might mean "advance to the next node" in the API and "advance to the next visible node" in the UI. These subtle divergences compound.

Bijectivity eliminates these failure modes by construction. There is one rendering function. There is one affordance generation algorithm. There is one state object. Both interfaces consume the same output. When a bug is fixed in one, it is fixed in both. When a feature is added to one, it appears in both. The correspondence is not maintained by discipline; it is maintained by architecture.

### 2.3 Implementation: The Single Render Path

The runtime's `render_page()` function produces a single page dictionary containing three sections:

- **`state`**: The current workflow position, field values, lifecycle topology, and fork state.
- **`instructions`**: The current node's guidance text.
- **`affordances`**: The complete list of actions available to the agent, each with a URL, method, body template, and parameter constraints.

The agent receives this dictionary directly via the API. The observer receives it via Server-Sent Events and renders it through a pluggable renderer. Both consumers receive the identical object. The observer does not query a separate endpoint, does not receive a "human-friendly" variant, and does not augment the data with additional state. It renders what the agent sees, nothing more and nothing less.

This is enforced at the architectural level: the observer's SSE stream pushes the same page dictionary that the API returned to the agent. When the agent takes an action, the resulting feedback (outcome, effects, new affordances) is broadcast to all connected observers in the same format. The observer does not "poll" for state — it receives the agent's exact experience in real time.

---

## 3. The Agent Portal: Current Architecture

### 3.1 Declarative Workflow Definitions

Workflows are defined in YAML and interpreted by a unified runtime. A workflow definition specifies:

- **Nodes**: The steps the agent will visit, each with a title, instruction text, and content declarations.
- **Fields**: Typed data entry points (text, boolean, select, computed) with optional visibility conditions, dynamic options, and side effects.
- **Tables**: Structured data with typed columns (free text, choice list, cross-reference, signature, acceptance criteria) and a construction/execution lifecycle.
- **Lists**: Ordered collections with item schemas and CRUD operations.
- **Navigation**: Proceed gates (with expression-tree conditions), conditional go-to links, and terminal actions (submit, restart).
- **Control flow**: Sequential proceed, routers (automatic conditional branching), forks (parallel branches), and merges (convergence).

The YAML format is the single source of truth. The runtime parses it into typed dataclasses, and all subsequent rendering, evaluation, and action dispatch operates on these parsed structures. No workflow logic lives in Python code unless it cannot be expressed declaratively (the builder handler is the sole exception, and it exists precisely to enable agents to author new YAML definitions).

### 3.2 The Affordance Model

The Agent Portal's interaction model is affordance-centric: the system tells the agent what it can do, not what it must do. Each affordance is a self-describing action specification:

```json
{
  "id": 3,
  "label": "Set Severity (current: null)",
  "method": "POST",
  "url": "/agent/create-cr/severity",
  "body": {"value": "<value>"},
  "parameters": {"value": {"options": ["Critical", "High", "Medium", "Low"]}}
}
```

The affordance contains everything the agent needs to act: the HTTP method, the target URL, the body template, and the parameter constraints. For select fields, the valid options are enumerated. For boolean fields, the options are `[true, false]`. For text fields, the body accepts any string. The agent does not need to consult documentation, parse HTML, or reverse-engineer an API. The affordances *are* the API.

Critically, affordances are **derived, not stored**. The runtime generates them fresh on every render by walking the current node's content declarations and evaluating visibility conditions, gate expressions, and navigation guards. An affordance appears if and only if the corresponding action is valid in the current state. This means the affordance list is always consistent with the state — there are no stale buttons, no disabled-but-visible actions, no race conditions between state and UI.

### 3.3 The Feedback Model

After each action, the runtime computes a structured feedback object that describes what happened:

- **Outcome**: The direct result of the action (e.g., "Title was set to 'Fix parser error handling'").
- **Effects**: Cascading changes triggered by the action — new fields that became visible, existing fields whose values changed due to side effects, and affordances that appeared or changed labels.
- **New affordances**: Actions that became available as a result of the state change (e.g., a proceed gate that now passes).

This feedback model serves two purposes. For the agent, it provides a concise summary of the action's consequences without requiring a full state comparison. For the human observer, it highlights what just changed, making it possible to follow the agent's progress at machine speed without reading the full state after every action.

The feedback is computed by diffing the before and after states: comparing field values, comparing affordance lists by URL identity, and identifying new, modified, and removed elements. This diff is the same regardless of who receives it — the agent's API response and the observer's SSE event carry the identical feedback object.

### 3.4 The Expression Language

All conditional logic in the system — proceed gates, field visibility, navigation guards, acceptance criteria, router conditions, fork gates — uses a single expression language evaluated by a unified evaluator. The language supports:

- **Leaf conditions**: `field_truthy`, `field_equals`, `field_not_null`, `set_membership`, `table_has_columns`, `table_has_rows`
- **Composite operators**: `AND`, `OR`, `NOT`

The evaluator returns both a boolean result and a human-readable explanation string (e.g., `"AND(title truthy: True AND severity truthy: False) = False"`). This explanation is available for debugging and audit purposes, though it is not currently surfaced in the observer UI.

The unification of conditional logic under a single evaluator is itself an expression of the bijective principle: there is one way to express conditions, one way to evaluate them, and one way to report their results. A gate condition on a proceed button uses the same syntax and the same evaluator as a visibility condition on a field or an acceptance criterion on a table row.

### 3.5 Topology Visualization

The observer renders workflow structure through a schematic layout engine that converts workflow definitions into a canonical spine model — a recursive data structure with three segment types:

- **Step**: A simple node (rendered as a pill or card).
- **Gate**: A conditional branch point with labeled routes (rendered as a hexagon).
- **Split**: A parallel fork with labeled branches and a merge target (rendered as a double-bar rectangle).

The spine model is content-agnostic: the layout engine positions nodes and draws topology wires without knowing what the nodes contain. Content is injected via a `nodeRenderer` callback, allowing the same engine to produce compact pill-shaped banners (for inline workflow summaries), rich card-based flowcharts (for detailed inspection), and interactive workshop displays (for development and testing).

Interactive collapse/expand is built into the engine as a service: branch points are clickable by default, and the engine handles spine pruning and re-rendering internally. A `focusNode` option auto-collapses all branches not on the path to the current node, producing a contextual summary that shows only the relevant topology. This is used in the workflow banner to give agents and observers a focused view of where they are in a complex workflow.

---

## 4. The Agent Portal as Architectural Prototype

### 4.1 The Current Scope

Today, the Agent Portal hosts a specific class of workflows: document creation (Change Records, Execution Tables), process execution (Deviation Reports, Incident Response), and workflow authoring (the builder). These workflows are self-contained: an agent enters the portal, selects a workflow, interacts with it through affordances, and produces an output (a document, a table, a workflow definition).

The portal currently coexists with the broader WFE UI — a Flask web application with sidebar navigation to other pages (QMS dashboard, Workspace, Inbox, Templates, Quality Manual browser). These other pages are conventional web interfaces: HTML forms, server-rendered pages, and standard HTTP request/response cycles. They are designed for human users and are not accessible to agents through the affordance protocol.

### 4.2 The Long-Term Vision

The Agent Portal is not the final product. It is the prototype for a universal interaction paradigm that will eventually govern every surface of the Pipe Dream QMS.

Consider what the portal has already proven:

- **Declarative process definition** works. Complex, multi-step, branching, parallel workflows can be authored in YAML and interpreted by a generic runtime without custom code.
- **Affordance-driven interaction** works. Agents can navigate structured processes by following self-describing action specifications, without documentation, without screen scraping, without brittle API contracts.
- **Bijective observation** works. Humans can watch agents work in real time, seeing exactly what the agent sees, with no information asymmetry.
- **Feedback-driven progress** works. The structured diff model gives both agents and humans a concise, accurate account of what each action accomplished.

These patterns are not specific to "workflow execution." They are general-purpose interaction patterns that apply to any structured process. And in a quality management system, *everything* is a structured process.

**Checking your inbox** is a structured process: query pending tasks, filter by role, select a task, navigate to the relevant document. Today this is a conventional web page. Tomorrow it will be a workflow node that the agent navigates through affordances — the same affordances the human sees.

**Reviewing a document** is a structured process: read the document, evaluate each section against review criteria, record a recommendation or request updates, provide comments. Today this requires the agent to use CLI commands and the human to read rendered HTML independently. Tomorrow it will be a unified review workflow where the agent's review actions are visible to the human observer in real time, and the human can perform the same review through the same affordance-driven interface.

**Executing a Change Record** is a structured process: for each execution item, perform the work, record evidence, mark pass or fail, create child documents for failures. The execution table engine already implements this within the Agent Portal. The remaining step is to connect it to the QMS document lifecycle so that execution within the portal directly mutates the governed document state.

### 4.3 The Convergence Trajectory

The trajectory is not "build the Agent Portal, then build the rest of the UI." The trajectory is:

1. **Prove the patterns in the portal.** Declarative definitions, affordance generation, bijective rendering, structured feedback. (Complete.)

2. **Harden the patterns through real use.** Gate condition labels, interactive collapse, execution engine, builder parity. (In progress.)

3. **Extend the patterns to adjacent surfaces.** The inbox becomes a workflow. The review process becomes a workflow. Document routing becomes a workflow. Each extension is a YAML definition interpreted by the same runtime, rendered by the same observer, and navigated by the same affordance protocol.

4. **Retire the conventional UI.** When every QMS operation is expressible as a workflow, the sidebar navigation becomes a workflow selector. The "QMS Dashboard" page becomes the default workflow's initial node. The entire application is a single runtime interpreting a graph of interconnected workflow definitions.

This is not a rewrite. It is a gradual subsumption. Each new workflow definition replaces a bespoke page with a governed, observable, agent-navigable process. The existing Flask routes do not need to be deleted; they simply become unnecessary as the portal absorbs their functionality.

### 4.4 Implications for Agent Autonomy

The convergence trajectory has a profound implication for agent autonomy within the QMS. Today, the orchestrating agent (Claude) interacts with the QMS through a CLI tool — a text-based command interface that was designed for human developers and adapted for agent use. The CLI works, but it is semantically impoverished: it accepts commands and returns text output, with no structured feedback, no affordance discovery, and no real-time observation.

When the QMS operations are expressed as portal workflows, the agent's interaction with the quality system becomes first-class:

- **The agent discovers what it can do** by reading affordances, not by consulting documentation or remembering CLI syntax.
- **The agent receives structured feedback** after every action, not raw text output that must be parsed.
- **The human observes the agent's work** in real time through the same visual interface, not by reading session logs after the fact.
- **The audit trail is automatic** — every action is a POST to a resource endpoint, every state transition is persisted, every feedback object is a structured record of what happened and why.

This is a qualitative shift in the relationship between the agent and the governance system. The agent moves from being a *user* of the QMS (invoking external tools) to being a *participant* in the QMS (navigating governed workflows through a native interface). The bijectivity guarantee ensures that this shift does not compromise human oversight — the human sees everything the agent sees, in the same structure, at the same time.

---

## 5. The Recursive Dimension

The Pipe Dream QMS is governed by a recursive loop: process failures become inputs to process improvement, and the improvement process is itself governed by the same mechanisms. The Agent Portal adds a new dimension to this recursion.

The builder workflow — itself an Agent Portal workflow — allows agents to author new workflow definitions. This means the system can extend its own process repertoire without code changes. An agent can:

1. Identify a process gap (e.g., "there is no formal workflow for security review").
2. Use the builder workflow to design and publish a security review workflow.
3. Execute the new workflow through the same portal.
4. Observe the results, identify improvements, and iterate on the definition.

Each iteration is governed by the same QMS mechanisms: the workflow definition change is authorized by a Change Record, reviewed by technical and quality units, and approved before deployment. The builder does not bypass governance; it operates within it.

This recursive capability — the system using itself to extend itself, under its own governance — is the ultimate expression of the bijective principle. The process of building a workflow is itself a workflow. The process of improving the process is itself a process. And at every level, the human and the agent see the same thing.

---

## 6. Design Principles Codified

The Agent Portal's architecture codifies several principles that will carry forward as the paradigm extends:

### 6.1 Affordances Over Documentation

The system tells the agent what it can do, structurally, in every response. The agent never needs to consult external documentation to determine its next valid action. This eliminates an entire class of errors (stale documentation, misremembered syntax, invalid action sequences) and makes the agent's behavior fully deterministic given the same state.

### 6.2 Derived State Over Stored State

Affordances, visibility, gate evaluations, and lifecycle positions are all computed from the current data on every render. Nothing is cached, nothing is stale, nothing can diverge from the underlying truth. This is more expensive computationally but eliminates consistency bugs by construction.

### 6.3 Structured Feedback Over Raw Output

Every action produces a typed diff — not a success message, not a status code, but a structured account of what changed, what cascaded, and what became possible. This makes agent decision-making transparent and human observation practical even at high interaction speeds.

### 6.4 Topology as a First-Class Concept

Workflow structure is not merely a visual convenience; it is a semantic property that the runtime reasons about. Forks create parallel execution contexts. Routers evaluate conditions and select paths. Gates block progress until criteria are met. The topology is the process, and the process is the topology. The spine model ensures that this structure is faithfully represented in every rendering context — from a compact inline banner to a full interactive flowchart.

### 6.5 Content Agnosticism in Rendering

The schematic engine does not know what nodes contain. The affordance generator does not know what workflows are about. The expression evaluator does not know whether it is evaluating a proceed gate or a visibility condition. Each system operates on the structure of its input, not on its semantics. This separation allows new content types, new workflow patterns, and new rendering formats to be added without modifying existing systems.

---

## 7. Conclusion

The Agent Portal is, in its current form, a workflow sandbox — a space where agents interact with structured processes through self-describing APIs while humans observe through synchronized visual interfaces. But its significance extends far beyond its current scope. The patterns it has proven — declarative definition, affordance-driven interaction, bijective rendering, structured feedback, recursive self-extension — constitute the design language for a new kind of quality management system: one where human oversight and agent autonomy are not in tension but are architecturally unified.

The bijective mapping principle is the load-bearing idea. It is the guarantee that makes agent autonomy compatible with human governance. When the human can see exactly what the agent sees — the same fields, the same gates, the same affordances, the same topology — trust is not a matter of faith but of observation. The agent's actions are not opaque API calls logged in an audit trail that someone might read later; they are visible, structured, real-time events rendered through the same interface the human would use to perform the same process.

As the Agent Portal's patterns extend to encompass inbox management, document review, execution tracking, and eventually the full QMS lifecycle, the distinction between "the Agent Portal" and "the application" will dissolve. What will remain is a single interaction paradigm — declarative, affordance-driven, bijectively observable — applied uniformly to every governed process in the system. The Agent Portal is not a feature of Pipe Dream. It is the prototype for what Pipe Dream will become.
