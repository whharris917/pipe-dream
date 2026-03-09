# The Workflow as a Constraint Machine

## Core Insight

The WFE UI is not a human convenience layer on top of the QMS CLI. It is the **primary process interface** for both humans and agents. The CLI provides document lifecycle operations (create, checkout, checkin, route), but it does not encode the instructional, prompt-guiding, constraint-enforcing layer that governs *how* a document gets populated. That layer lives in the workflow definition, and the UI is its runtime.

## The Three Layers

### 1. Document Lifecycle (QMS CLI)
What the CLI provides:
- Create, checkout, checkin, route, approve, reject, release, close
- Status tracking, audit trail, permission enforcement
- Document identity and versioning

What it does NOT provide:
- What fields exist on a document
- What order they should be filled in
- What guidance accompanies each field
- What conditions must be met before advancing
- What actions are available at each stage
- Who is allowed to do what at each stage

### 2. Process Definition (Workflow Graph)
The workflow graph — what the Sandbox builds — defines the **constraint machine**:
- **Stages** (nodes): Named states with an assigned actor, a set of visible fields, and editability flags per field
- **Transitions** (edges): Legal state changes with optional conditions (gates) and hooks (side effects)
- **Gates** (conditions on edges): Predicates that must evaluate to true before a transition fires (e.g., "all required fields are filled," "plan execution is complete")
- **Hooks** (actions on edges): Automated side effects that fire when a transition occurs (e.g., "assign document ID," "route for review," "lock all fields")
- **Actions** (on review/approval stages): Named choices available to the actor that map to different transition targets (e.g., "Approve" → next stage, "Reject" → return to previous stage)

This is pure structure — no rendering, no presentation. It is the source of truth for what is possible at every point in the process.

### 3. Process Interface (UI / Agent API)
The UI renders the constraint machine for a specific actor at a specific stage. It provides:
- **Visibility enforcement**: Only fields assigned to the current stage are shown
- **Editability enforcement**: Fields marked read-only cannot be modified
- **Guidance**: Contextual prompts, hints, and instructional text that tell the actor *what to do* and *why*
- **Affordance restriction**: Only legal actions are presented — you cannot advance if the gate isn't satisfied, you cannot see actions that aren't yours
- **Structural impossibility of non-compliance**: The interface does not offer what is not permitted

For a human, this renders as HTML with form fields, buttons, and visual indicators.
For an agent, this renders as structured JSON with available fields, their types, current values, and a list of permitted next actions.

**Both renderers enforce the same constraints.** The difference is presentation, not permission.

## Why the CLI Is Not Sufficient for Agents

An agent given only the CLI can:
- Create a document
- Check it out
- Write arbitrary content to it
- Check it in and route it

But it has no structured understanding of:
- What fields the document expects
- What stage it's in and what that means
- What guidance applies to the current task
- What constitutes "complete enough" to advance
- What the gate conditions actually are

The CLI operates on documents as opaque blobs. The workflow engine operates on documents as structured, stage-gated, actor-scoped entities. An agent that only uses the CLI is operating without the process knowledge that the workflow encodes.

This is analogous to giving someone database write access without the application layer — they *can* insert rows, but they have no schema validation, no business rules, no workflow enforcement. The application layer is not optional.

## Implications for the Workflow Sandbox

The Sandbox graph builder is not just a visual authoring tool. It is building an **executable specification** that:

1. **Compiles** to a process definition (the Source tab — YAML or equivalent)
2. **Drives** the UI renderer (which fields to show, what's editable, what actions are available)
3. **Drives** the agent API (same information, structured for programmatic consumption)
4. **Enforces** constraints at runtime (gates block transitions, hooks fire side effects)

The nodes, edges, gates, and hooks in the graph are not documentation — they are the program. The Sandbox is an IDE for process logic.

## The Agent Interaction Model

When an agent (including Claude) works through a workflow-governed process:

1. **Query current state**: "What stage am I in? What fields can I fill? What actions can I take?"
2. **Receive scoped response**: Only the permitted fields, with their types, current values, guidance text, and editability flags
3. **Perform work**: Fill fields within the permitted set, following the guidance
4. **Request transition**: "I want to advance / approve / reject"
5. **Engine evaluates gate**: Either allows the transition (firing hooks) or returns the unmet conditions
6. **Repeat** from the new stage

At no point does the agent have unmediated access to the document. Every interaction is scoped by the workflow engine. This is the screening mechanism: the workflow doesn't trust the agent to follow rules — it makes rule-breaking structurally impossible.

## Relationship to the Recursive Governance Loop

This architecture feeds directly into the QMS's recursive self-improvement property. The workflow definitions are themselves controlled documents. When a process fails, an Investigation analyzes the failure, and a CAPA improves the workflow definition — using the same workflow-governed process. The constraint machine governs its own evolution.

The Sandbox makes this loop tangible: you can see the process, modify it, and the modification itself follows a governed process. The system's ability to improve is not separate from its ability to enforce — they are the same mechanism.
