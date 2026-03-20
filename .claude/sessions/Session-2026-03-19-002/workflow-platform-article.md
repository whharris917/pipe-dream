# The Missing Runtime: A General-Purpose Platform for Agentic Workflows

*Why the agentic AI ecosystem needs a workflow engine, not more workflow applications*

---

## Abstract

The current approach to building AI agent workflows is analogous to building every video game by writing a custom rendering engine from scratch. Each team implements its own state management, its own action dispatch, its own observation layer, its own control flow — because no shared runtime exists. This paper argues that the agentic workflow ecosystem is missing a foundational layer: a general-purpose platform that provides the primitives, runtime, and rendering infrastructure for structured agent-process interaction, allowing workflow designers to focus on process semantics rather than plumbing. We describe such a platform — a declarative workflow runtime with affordance-driven interaction, bijective human-agent observation, and a publish-discover-execute lifecycle — and argue that its relationship to individual agentic workflows is analogous to the relationship between a game engine and a game, between a programming language and a program, between a distribution platform and an application, and between an international standard and a local convention.

---

## 1. The Problem: Every Workflow Is Built From Scratch

The AI agent ecosystem is experiencing a Cambrian explosion of workflow tooling. LangChain, CrewAI, AutoGen, DSPy, and dozens of other frameworks offer mechanisms for chaining agent actions into multi-step processes. But beneath the surface, each of these frameworks — and, more importantly, each application built on them — is solving the same set of infrastructure problems independently:

**State management.** Where is the workflow's current state? How is it persisted? How is it recovered after a crash? Every workflow application implements its own answer.

**Action dispatch.** How does the agent know what it can do next? How are actions validated? How are invalid actions rejected? Every workflow application implements its own answer.

**Observation.** How does a human see what the agent is doing? How do they verify that the agent's actions are correct? Every workflow application implements its own answer — usually a log file, a dashboard built after the fact, or nothing at all.

**Control flow.** How do you express conditional branching? Parallel execution? Convergence? Gates that block progress until criteria are met? Every workflow application implements its own answer, typically by writing Python code that encodes the logic procedurally.

**Feedback.** After the agent acts, what does it learn about the consequences? Every workflow application implements its own answer — or, more commonly, returns a success code and lets the agent figure it out.

This is the state of the art. And it is exactly where the game industry was before game engines, where software development was before high-level programming languages, where mobile software was before app stores, and where international commerce was before standards bodies.

---

## 2. Four Analogies for a Missing Abstraction

### 2.1 What a Game Engine Is to a Game

Before Unreal Engine, Unity, and their predecessors, building a video game meant building a rendering pipeline, a physics system, an input handler, a sound engine, an asset loader, and a scene graph — before writing any game logic at all. Every studio solved these problems independently, often poorly, and the solutions were not reusable. A team that built a first-person shooter could not easily repurpose its engine for a strategy game.

Game engines changed this by identifying the **common substrate** beneath all games: spatial rendering, collision detection, input mapping, audio mixing, asset management. The engine provides these capabilities as a runtime, and game developers write game logic on top of it. The engine does not know or care whether it is running a racing game or a horror game. It provides primitives; the game provides semantics.

The agentic workflow ecosystem is in the pre-engine era. Every workflow application implements its own state management, its own action dispatch, its own observation layer. The infrastructure consumes more engineering effort than the workflow logic it supports. And the infrastructure is not reusable — a workflow built for customer support cannot share its runtime with a workflow built for code review, even though both need the same fundamental capabilities.

A workflow runtime provides the common substrate: state persistence, affordance generation, expression evaluation, topology visualization, feedback computation, real-time observation. Workflow designers write process definitions on top of it. The runtime does not know or care whether it is executing a quality management process or a customer onboarding flow. It provides primitives; the workflow provides semantics.

### 2.2 What a Programming Language Is to a Program

A programming language is not a program. It is a set of primitives — variables, control flow, functions, types — that can be composed to express any computation. The language does not contain the solution to any particular problem; it contains the vocabulary for expressing solutions to all problems within its domain.

Individual agentic workflow applications are analogous to programs written in machine code: powerful, specific, and impossible to reuse or compose. Each one encodes its process logic directly in Python (or JavaScript, or Go), interleaving workflow semantics with infrastructure concerns. To change the process, you change the code. To understand the process, you read the code. To verify the process, you test the code.

A workflow platform provides a **process definition language**: a set of primitives — fields, tables, lists, gates, routers, forks, merges, side effects, visibility conditions — that can be composed to express any structured process. The language is declarative (YAML, not Python), the runtime interprets it, and the semantics are transparent to inspection.

The primitives of this language map to the universal building blocks of structured processes:

| Language Primitive | Process Concept |
|---|---|
| **Field** (text, boolean, select, computed) | A piece of information the agent must provide or the system computes |
| **Table** (typed columns, execution engine) | A structured artifact the agent constructs and executes against |
| **List** (ordered, CRUD operations) | A collection of items the agent manages |
| **Gate** (expression tree) | A condition that must be satisfied before progress |
| **Router** (conditional targets) | An automatic decision point based on current state |
| **Fork** (parallel branches, merge) | Concurrent work streams that converge |
| **Side effect** (conditional field mutation) | Cascading state changes triggered by agent actions |
| **Visibility** (conditional field display) | Context-sensitive interface adaptation |
| **Affordance** (self-describing action) | The agent's action vocabulary at any given moment |

These primitives are domain-agnostic. A gate that requires "title is truthy" is structurally identical to a gate that requires "patient ID is verified." A router that branches on severity is structurally identical to a router that branches on risk tier. A fork that parallelizes verification and testing tracks is structurally identical to a fork that parallelizes legal review and technical review. The semantics differ; the structure is the same.

This is what makes it a language rather than an application: the primitives compose freely, the compositions are inspectable, and the runtime interprets them uniformly regardless of domain.

### 2.3 What an App Store Is to an App

An app store is not an app. It is a **platform** that provides three things:

1. **A runtime contract.** Apps must conform to a defined interface (APIs, permissions model, lifecycle hooks). The platform guarantees that any conforming app will run correctly.

2. **A distribution mechanism.** Apps are published, discovered, and installed through a central registry. Users do not need to know where an app came from or how it was built.

3. **A trust layer.** The platform enforces review, signing, and sandboxing. Users trust the platform, and the platform vouches for the apps.

The workflow platform provides the same three things for agentic workflows:

**Runtime contract.** Every workflow handler implements a defined protocol: `default_data()`, `render_node()`, `process_action()`, `resolve_resource()`. The platform guarantees that any conforming workflow will be discoverable, executable, observable, and auditable. The workflow does not need to implement its own API layer, its own state persistence, its own SSE streaming, or its own feedback computation.

**Distribution mechanism.** Workflows are published as YAML files to a known directory. The platform discovers them at startup (and eventually via hot reload). An agent does not need to know how a workflow was authored; it discovers available workflows through the platform's registry and interacts with any of them through the same affordance protocol.

**Trust layer.** The platform enforces the bijective mapping: every workflow, regardless of who authored it, is rendered through the same observer, evaluated by the same expression engine, and audited through the same feedback mechanism. A custom workflow published by one team is subject to the same observability guarantees as a built-in workflow. The platform does not trust the workflow's logic; it trusts the contract.

The builder workflow extends this analogy further: just as an app store provides development tools for creating apps, the platform provides a meta-workflow (the builder) for creating workflows. An agent can design, validate, and publish a new workflow without writing code, and the published workflow is immediately available through the same platform infrastructure. This is self-service workflow creation within a governed runtime — the platform equivalent of an SDK.

### 2.4 What an International Standard Is to a Local Convention

International standards (ISO, IEEE, W3C) do not tell organizations what to do. They define **what conformance means**: what a quality management system must contain (ISO 9001), what a network protocol must guarantee (TCP/IP), what a web page must structure (HTML). Organizations implement the standard according to their local needs, and the standard provides the shared vocabulary, the interoperability guarantees, and the audit criteria.

Individual agentic workflows are like local conventions: they work within their context, but they are not interoperable, not auditable against a shared framework, and not composable with workflows from other contexts. A customer support workflow built by one team cannot be inspected, governed, or extended by another team's tools, because there is no shared standard for what a "workflow" is, what an "affordance" contains, or what "observation" means.

The workflow platform defines these standards:

**What a workflow is.** A directed graph of nodes, each with typed content (fields, tables, lists), navigation rules (proceed, router, fork), and evaluation criteria (gates, visibility, acceptance). This is a structural definition, not a semantic one — it describes the shape of all workflows without constraining what any particular workflow does.

**What an affordance is.** A self-describing action specification containing a label, a method, a URL, a body template, and parameter constraints. Any agent that can parse this structure can interact with any workflow that produces it. This is interoperability by design: the agent does not need workflow-specific code, documentation, or training.

**What observation is.** A real-time stream of state dictionaries and feedback diffs, rendered by pluggable visual engines. Any observer that can consume this stream can visualize any workflow. This is the audit guarantee: observability is not a feature that each workflow must implement; it is a property of the platform.

**What feedback is.** A structured diff containing the action outcome, cascading effects (new fields, modified fields, new affordances, modified affordances), and error information. Any agent or observer that can parse this structure can understand the consequences of any action in any workflow. This is the transparency guarantee: the agent's decision-making is not opaque; it is structurally documented by the platform.

These definitions function as a standard. A workflow that conforms to them is automatically discoverable, executable, observable, auditable, and interoperable with any agent or observer that speaks the same protocol. A workflow that does not conform cannot participate in the platform — not because it is rejected, but because it cannot be interpreted by the runtime.

---

## 3. Platform Architecture

### 3.1 The Three Layers

The platform separates concerns into three layers that can evolve independently:

```
┌─────────────────────────────────────────────────┐
│              WORKFLOW DEFINITIONS                │
│    YAML files defining process semantics         │
│    (What to do, in what order, under what        │
│     conditions, with what data)                  │
└────────────────────┬────────────────────────────┘
                     │ interpreted by
┌────────────────────▼────────────────────────────┐
│                  RUNTIME                         │
│    Schema parsing, expression evaluation,        │
│    affordance generation, action dispatch,        │
│    feedback computation, state persistence        │
│    (How to execute any workflow)                  │
└────────────────────┬────────────────────────────┘
                     │ consumed by
┌────────────────────▼────────────────────────────┐
│              INTERFACE LAYER                      │
│    Agent API (affordances), Observer UI (SSE),    │
│    Schematic engine (topology), Renderers          │
│    (How to interact with and observe any workflow) │
└─────────────────────────────────────────────────┘
```

**Definitions** are pure data. They contain no code, no side effects, no platform dependencies. They can be authored by hand, generated by the builder workflow, produced by external tools, or composed programmatically. They are the "programs" that the platform executes.

**Runtime** is the interpreter. It parses definitions into typed structures, evaluates expressions, generates affordances, dispatches actions, computes feedback, and manages state. It is workflow-agnostic: it does not know what any particular workflow means, only how to execute its structural primitives. Adding a new workflow requires no runtime changes; adding a new primitive requires a runtime extension but no changes to existing workflows.

**Interface** is the presentation layer. It renders state for agents (via structured API responses) and for humans (via pluggable visual renderers). It streams state changes in real time. It provides topology visualization through a content-agnostic schematic engine. It is both workflow-agnostic and runtime-agnostic: it consumes the page dictionary that the runtime produces, regardless of which workflow produced it or how the runtime evaluated it.

### 3.2 The Primitive Catalog

The platform's expressiveness comes from its primitive catalog — the set of building blocks that workflow definitions can compose:

**Content primitives** define what appears on a node:

- **Text field**: Free-form string input. The agent can enter any value.
- **Boolean field**: Binary choice. The agent selects true or false.
- **Select field**: Constrained choice from enumerated options, optionally dynamic (options change based on other field values).
- **Computed field**: Read-only value derived from other fields. The agent cannot modify it; the runtime evaluates it.
- **Table**: A structured grid with typed columns (free text, choice list, cross-reference, signature, acceptance criteria). Tables have two lifecycle phases: construction (defining structure and content) and execution (filling cells, signing, evaluating criteria).
- **List**: An ordered collection with a typed item schema. Supports add, edit, remove, reorder, and focus operations.

**Control-flow primitives** define how the agent moves through the workflow:

- **Sequential proceed**: Advance to the next node, optionally gated by an expression.
- **Conditional navigation**: Named links to specific nodes, optionally guarded by expressions.
- **Router**: Automatic conditional branching — the runtime evaluates conditions in order and advances to the first matching target. No agent choice involved.
- **Fork**: Parallel branch split — the agent works on multiple independent tracks and can switch between them freely. All branches must complete before the workflow advances to the merge node.
- **Merge**: Implicit convergence point where parallel branches rejoin.

**Evaluation primitives** define conditions used across the system:

- **Leaf conditions**: field_truthy, field_equals, field_not_null, set_membership, table_has_columns, table_has_rows.
- **Composite operators**: AND, OR, NOT — composable into arbitrary expression trees.
- **Application contexts**: proceed gates, field visibility, navigation guards, acceptance criteria, router conditions, fork gates. All use the same expression language and the same evaluator.

**Behavioral primitives** define reactive state changes:

- **Side effects**: When a condition is met, automatically set field values. Enables cascading state changes triggered by agent actions.
- **Dynamic options**: A select field's valid choices change based on another field's current value. Enables context-sensitive interfaces.
- **Option sets**: Named collections of values shared across fields, providing vocabulary reuse within a workflow.

### 3.3 The Affordance Protocol

The affordance protocol is the platform's agent-facing API contract. Every interaction between an agent and a workflow flows through affordances:

1. **The agent requests the current page** (GET). The runtime renders the current node's state, instructions, and affordances.

2. **The agent selects an affordance and acts** (POST to the affordance's URL with the affordance's body template filled in). The runtime validates the action, mutates state, evaluates side effects, and renders the new page.

3. **The agent receives feedback.** The response contains a structured diff describing the outcome (what the action accomplished), effects (what cascaded), and new affordances (what became possible).

4. **Repeat until the workflow completes.**

The protocol is **self-bootstrapping**: the agent does not need prior knowledge of any workflow to interact with it. The first GET response contains all available affordances with their labels, URLs, methods, body templates, and parameter constraints. The agent reads the affordances, selects one, acts, reads the feedback, and proceeds. No documentation, no training data, no workflow-specific prompts.

This is the critical property that makes the platform general-purpose. A new workflow published to the platform is immediately usable by any agent that speaks the affordance protocol. The agent does not need an update, a new plugin, or a new integration. It reads the affordances and acts. The protocol is the integration.

### 3.4 The Observation Contract

The observation contract is the platform's human-facing guarantee:

1. **The observer receives the same page dictionary the agent receives.** Not a summary, not a dashboard view, not a filtered projection — the identical data structure, delivered via Server-Sent Events in real time.

2. **The observer receives every feedback object the agent receives.** Every action, every outcome, every cascading effect is visible to the human observer at the moment it occurs.

3. **The observer's visual rendering is pluggable but structurally faithful.** Different renderers (compact pills, rich cards, raw JSON) present the same information at different levels of detail, but none of them add semantic content that is not in the page dictionary, and none of them omit semantic content that is.

This contract is the platform's answer to the trust problem. Agentic workflows are powerful but opaque — an agent making decisions at machine speed is difficult for a human to audit. The observation contract makes the agent's experience transparent: the human sees what the agent sees, as the agent sees it, while the agent sees it. Trust is not deferred to post-hoc log review; it is available in real time.

---

## 4. What This Enables

### 4.1 Workflow Portability

A workflow definition is a YAML file. It contains no code, no platform-specific imports, no infrastructure dependencies. It can be:

- **Version-controlled** alongside the code it governs.
- **Reviewed** by humans who read YAML, not Python.
- **Validated** by automated tools that check structural conformance.
- **Shared** between organizations that use the same platform.
- **Composed** by combining primitives from multiple existing workflows.
- **Generated** by AI agents using the builder workflow.

This portability is a direct consequence of the platform's separation of definition from runtime. The workflow does not know how it will be executed; the runtime does not know what the workflow means. The YAML file is the complete, portable specification of a process.

### 4.2 Agent Interoperability

Any agent that can parse JSON and make HTTP requests can interact with any workflow on the platform. The affordance protocol eliminates the need for workflow-specific agent code. This means:

- **A general-purpose LLM agent** can navigate a compliance workflow, a customer onboarding workflow, and a code review workflow using the same interaction logic.
- **A specialized agent** can be built for a specific domain (e.g., medical device quality) without implementing any workflow infrastructure.
- **Multiple agents** can interact with the same workflow concurrently (e.g., one agent fills fields while another reviews them), because the platform manages state and the affordance protocol handles concurrency.

### 4.3 Governance as a Platform Feature

When governance is implemented at the platform level rather than the application level, it becomes universal and automatic:

- **Audit trails** are a property of the platform, not a feature each workflow must implement. Every action, every state transition, every feedback object is recorded by the platform.
- **Observation** is a property of the platform. Every workflow is observable through the same visual infrastructure, with the same bijectivity guarantees.
- **Access control** can be implemented at the platform level: which agents can access which workflows, which actions require human approval, which state transitions trigger notifications.
- **Compliance** becomes structural: a workflow that conforms to the platform's definition schema automatically satisfies the platform's observability, auditability, and transparency requirements.

This is the standards analogy in practice. The platform defines what conformance means; the workflow conforms; and the platform's guarantees apply automatically.

### 4.4 Recursive Self-Extension

The builder workflow — a workflow that produces workflow definitions — enables the platform to extend its own capability set without code changes. This is more than a convenience feature; it is a fundamental architectural property.

Consider a platform that can only execute workflows that were hand-authored by developers. Its capability set is bounded by the development team's bandwidth. Now consider a platform where agents can design, validate, publish, and execute new workflows through the platform's own interface. Its capability set is bounded by the space of expressible processes — which, given a sufficiently rich primitive catalog, is effectively unbounded.

The builder workflow also closes the loop on the platform's own evolution. When the platform's primitive catalog is extended (e.g., adding a new field type or a new control-flow construct), the builder workflow is updated to support the new primitive, and agents can immediately begin using it in their workflow designs. The platform's growth is self-accelerating: each new primitive enables new workflows, which surface new requirements for primitives, which drive further platform development.

---

## 5. The Ecosystem Analogy, Revisited

The four analogies from Section 2 are not just rhetorical. They describe a specific architectural role that is currently unfilled in the agentic AI ecosystem:

| Analogy | What it provides | What it enables |
|---|---|---|
| **Game engine** | Rendering, physics, input, audio | Game developers focus on game design, not infrastructure |
| **Programming language** | Variables, control flow, functions, types | Programmers express solutions, not machine instructions |
| **App store** | Runtime contract, distribution, trust | App developers ship to users, not to bare metal |
| **Standards body** | Conformance criteria, interoperability, audit | Organizations implement locally, interoperate globally |

| **Workflow platform** | State, affordances, observation, feedback, topology | Workflow designers define processes; agents execute them; humans observe them — all through the same infrastructure |

The common thread is **abstraction that enables composition**. A game engine does not make games; it makes games *possible to make well*. A programming language does not solve problems; it makes problems *expressible*. An app store does not build apps; it makes apps *distributable and trustworthy*. A standard does not dictate practice; it makes practices *interoperable and auditable*.

A workflow platform does not define processes. It makes processes expressible, executable, observable, auditable, interoperable, and composable — by agents and humans alike, through a shared interface, under a shared governance model.

---

## 6. Why Now

Three converging trends make this platform layer both possible and necessary:

**Agent capability has outpaced agent infrastructure.** Modern LLMs can reason about complex multi-step processes, but the infrastructure for *structuring* those processes — defining valid actions, enforcing constraints, observing progress, auditing outcomes — is primitive. The result is agents that are powerful in isolation but ungovernable in production. The platform provides the missing governance layer.

**Process complexity is increasing.** As organizations adopt AI agents for increasingly complex workflows — regulatory compliance, software development lifecycle, financial auditing, clinical trials — the cost of building bespoke workflow infrastructure for each domain becomes prohibitive. The platform amortizes this cost: build the runtime once, define workflows declaratively, and execute them on a shared infrastructure.

**Trust is the bottleneck.** The primary obstacle to agent adoption in high-stakes domains is not capability but trust. Organizations need to verify that agents are doing what they should be doing, in the order they should be doing it, with the constraints they should be subject to. The platform's bijective observation contract addresses this directly: the human sees what the agent sees, structurally and in real time, as a property of the platform rather than a feature of any individual workflow.

---

## 7. Conclusion

The agentic AI ecosystem is building applications. It should be building a platform.

The distinction matters because applications solve specific problems while platforms solve classes of problems. An application that automates customer support does not help you automate code review. A platform that provides state management, affordance generation, expression evaluation, topology visualization, and bijective observation helps you automate both — and any other structured process you can express in its definition language.

The workflow platform described here is not a framework for writing agent code. It is a runtime for interpreting process definitions. The definitions are data, not code. The runtime is generic, not domain-specific. The interface is self-describing, not documented. The observation is bijective, not approximate. And the governance is structural, not bolted on.

What Unreal Engine did for games — freeing developers to focus on design rather than plumbing — a workflow platform does for agentic processes. What programming languages did for computation — providing composable primitives rather than machine-specific instructions — a workflow definition language does for process specification. What app stores did for software distribution — providing a runtime contract, a trust layer, and a discovery mechanism — a workflow platform does for process deployment. What international standards did for interoperability — defining conformance criteria that enable local implementation and global auditability — a workflow platform does for agent governance.

The platform is the missing layer. And once it exists, the question is no longer "how do we build this workflow?" but "how do we define this process?" — which is the right question, and always has been.
