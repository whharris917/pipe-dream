# Pipe Dream: A Runtime for Governed Agentic Workflows

*Platform Reference and Architectural Overview*

---

## 1. Overview

Pipe Dream is a workflow runtime that enables AI agents and human operators to execute structured, multi-step processes through a shared interface. Organizations use it to define business processes as declarative YAML specifications, deploy them to a shared runtime, and have any combination of agents and humans execute them — through the same affordance protocol, the same state model, and the same visual interface.

The platform serves regulated industries, software development organizations, and any domain where consequential work requires auditability, transparency, and flexible allocation of tasks between humans and machines. Its adoption has been driven by a single architectural property: the guarantee that every participant in a workflow — whether AI agent, human operator, or observer — perceives identical state, identical options, and identical constraints at every point in execution, and interacts with the process through the same underlying mechanism.

---

## 2. How It Works

### 2.1 Workflow Definitions

A workflow is a YAML file that describes a process: what information must be gathered, in what order, under what conditions, and with what constraints. Workflow authors do not write code. They compose from a catalog of typed primitives:

**Content primitives** specify what appears at each step:

- **Fields** accept input from the agent. Four types are available: free text, boolean, constrained selection from enumerated options, and computed values derived from other fields. Fields support conditional visibility (a field appears only when a condition is met), dynamic option sets (a select field's valid choices change based on another field's value), and side effects (setting one field automatically populates others).

- **Tables** define structured artifacts with typed columns. Column types fall into three categories: static columns populated during construction (free text, prerequisites), executable columns filled at runtime (free text evidence, choice lists, cross-references, electronic signatures), and auto-evaluated columns (acceptance criteria expressed as boolean rules). Tables support a two-phase lifecycle: construction, where the agent defines the table's structure; and execution, where the agent fills cells, signs off on rows, and the system evaluates acceptance criteria automatically.

- **Lists** define ordered collections with typed item schemas. Agents can add, edit, remove, reorder, and focus on list items.

**Control-flow primitives** specify how the agent moves through the process:

- **Sequential proceed** advances to the next step. An optional gate — a boolean expression — blocks progress until its conditions are satisfied. The gate's conditions are visible on the workflow's rendered topology, so both the agent and the human observer know what is required before the proceed action becomes available.

- **Routers** evaluate conditions automatically and advance to the first matching target. The agent does not choose a path; the system evaluates the current state and routes accordingly. This is used for validation gates, severity-based escalation, and any decision that should be deterministic given the current data.

- **Forks** split execution into parallel branches. The agent works on each branch independently and can switch between them freely. All branches must complete before execution advances to the merge point. Fork state is tracked per-branch: each branch maintains its own current step, completion status, and history.

- **Conditional navigation** provides named links to specific steps, optionally guarded by expressions. This enables non-linear workflows where the agent can jump to a relevant section based on context.

**Evaluation primitives** express conditions used throughout the system:

All conditional logic — proceed gates, field visibility, navigation guards, acceptance criteria, router conditions — uses a single expression language. Leaf conditions test field values (truthy, equals, not null, set membership) or table structure (has columns, has rows). Composite operators (AND, OR, NOT) compose leaf conditions into arbitrary expression trees. One evaluator handles all contexts, ensuring that a condition means the same thing wherever it appears.

### 2.2 The Runtime

The runtime interprets workflow definitions. It does not contain workflow logic; it contains the machinery for executing any workflow that conforms to the definition schema.

On startup, the runtime discovers all published workflow definitions — both built-in and user-created — and registers them in a central catalog. Each workflow is backed by a handler instance that implements a uniform protocol:

- **Initialize**: Produce the default state for a new workflow instance.
- **Render**: Given the current state, produce a page containing the current step's content, instructions, and available actions.
- **Dispatch**: Given an action, validate it, mutate the state, apply side effects, and render the resulting page.
- **Resolve**: Translate a resource-oriented API call into an internal action.

The runtime manages state persistence (workflow state is serialized to disk and survives restarts), expression evaluation (all conditions are evaluated by the same engine), affordance generation (the list of available actions is derived fresh from the current state on every render), and feedback computation (after each action, the runtime computes a structured diff describing what changed).

### 2.3 The Agent Interface

Agents interact with workflows through a resource-oriented HTTP API. The interaction cycle is:

1. **Discover.** The agent queries the workflow catalog to see what processes are available.

2. **Enter.** The agent opens a workflow instance. The runtime returns a page containing the current step's state, instructions, and affordances.

3. **Read affordances.** Each affordance is a self-describing action specification: a label, an HTTP method, a URL, a body template, and parameter constraints. For select fields, the valid options are enumerated. For boolean fields, the options are `true` and `false`. For text fields, any string is accepted. The agent does not need prior knowledge of the workflow; the affordances tell it everything it needs to know to act.

4. **Act.** The agent selects an affordance and sends the corresponding HTTP request with appropriate values filled into the body template.

5. **Receive feedback.** The response contains a structured diff: the direct outcome of the action (e.g., a field was set), cascading effects (fields that appeared or changed due to side effects, affordances that became available or changed labels), and any errors.

6. **Repeat** until the workflow reaches a terminal state.

The affordance protocol is the sole integration surface between agents and workflows. An agent built to speak this protocol can interact with any workflow on the platform without workflow-specific code, training, or configuration. When a new workflow is published, every agent that speaks the protocol can execute it immediately.

### 2.4 The Observer Interface

Human operators observe workflow execution through a real-time visual interface. The observer connects to the workflow instance via Server-Sent Events and receives the same page dictionary that the agent receives — the identical data structure, not a summary or a filtered projection.

The observer supports pluggable renderers:

- **Simple renderers** (light and dark themes, default and verbose modes) display the workflow as a structured text view with topology banner, field values, and available actions.
- **Card renderers** display each step as a rich card showing fields, gate conditions, navigation links, and action buttons, arranged in a flowchart layout with topology wires connecting them.
- **Raw renderer** displays the unformatted JSON page dictionary, useful for debugging and integration development.

All renderers consume the same page dictionary. They present the same information at different levels of visual detail, but none of them add content that the agent does not see, and none of them omit content that the agent does see.

The topology banner — present in all renderers — uses a schematic layout engine that converts the workflow definition into a visual spine: steps rendered as pills, conditional branch points as hexagons, parallel forks as double-bar rectangles, with wires showing the flow between them. The schematic engine is content-agnostic; it positions nodes and draws topology without knowing what the nodes contain. Content is injected via a callback, allowing the same engine to produce compact inline summaries and full interactive flowcharts.

Interactive features — collapse/expand of branch points, auto-focus on the current step's path — are built into the engine and available to all renderers automatically.

### 2.5 Collaboration Mode

The observer interface operates in two modes: **observation mode**, where the human watches an agent work, and **collaboration mode**, where affordances are resolved into interactive UI elements — text inputs, dropdown selectors, toggle switches, and clickable buttons — that the human can use to execute the workflow directly.

In collaboration mode, each affordance in the page dictionary is rendered as the appropriate HTML control. A text field affordance becomes an input box. A select field affordance becomes a dropdown populated with the enumerated options. A boolean field affordance becomes a toggle. A proceed affordance becomes a button. When the human interacts with any of these controls, the UI executes the same HTTP POST that an agent would execute — same URL, same body structure, same resource endpoint. The runtime cannot distinguish between an action taken by an agent and an action taken by a human through the collaboration interface, because the actions are mechanically identical. The same validation runs, the same side effects fire, the same feedback is computed, and the same state transition occurs.

This is not a separate "human mode" built alongside the agent interface. It is a rendering strategy applied to the same affordance data. The affordance specifies that the field "Severity" accepts one of four string values; observation mode displays this as a label, collaboration mode displays it as a dropdown. The affordance specifies that "Proceed to Review" is a POST to a specific URL with an empty body; observation mode displays this as text, collaboration mode displays it as a button. The underlying data is identical. Only the interactivity of the rendering changes.

Collaboration mode enables several important capabilities:

**Human-executed agent workflows.** A human operator can step through any workflow designed for an agent, using the same interface the agent would use. This is valuable for troubleshooting (reproducing an agent's path through a process to identify where it went wrong), for validation (manually executing a new workflow definition before deploying it to agents), and for fallback (completing a workflow manually when an agent is unavailable or has been paused).

**Hybrid execution.** A workflow instance can be executed by a combination of agents and humans. An agent might fill in the technical fields, then a human takes over in collaboration mode to provide a judgment call on severity classification, then the agent resumes to complete the remaining steps. The handoff is seamless because both participants interact through the same affordance protocol and operate on the same state. There is no "agent state" and "human state" to synchronize; there is one state, mutated by whoever acts next.

**Multi-executor workflows.** Workflow definitions support role-based affordance scoping: specific affordances can be designated for specific executor roles. In a code review workflow, the "Submit Implementation Evidence" affordance is scoped to the implementing agent, while the "Approve" and "Request Changes" affordances are scoped to the human reviewer. Each participant — whether connecting via the API or through the collaboration UI — sees only the affordances assigned to their role. But the mechanism is uniform: a human clicking "Approve" in the collaboration interface executes the same POST that a reviewing agent would execute through the API. The approval action is the same action regardless of who initiates it.

Role-scoped affordances do not introduce a separate permission system or a parallel rendering path. They are an additional filter applied during affordance generation: the runtime evaluates which affordances are valid for the current state (as it always does), then filters by the requesting executor's role. The page dictionary for a reviewer contains a subset of the page dictionary for the implementer, but both subsets are drawn from the same rendering function, evaluated by the same expression engine, and displayed through the same visual infrastructure.

This design ensures that multi-executor workflows inherit all of the platform's governance properties automatically. The human reviewer's approval action is audited the same way the agent's field-setting action is audited. The reviewer's collaboration interface is bijectively mapped to the reviewer's affordance set, just as the agent's API interface is bijectively mapped to the agent's affordance set. The observation guarantee extends to every participant: anyone observing the workflow sees every action taken by every executor, because all actions flow through the same state and the same feedback mechanism.

### 2.6 The Builder

The platform includes a builder workflow — itself a workflow interpreted by the same runtime — that enables agents and humans to design new workflow definitions without writing code or YAML by hand. The builder exposes the full primitive catalog through its own affordance-driven interface: the author adds steps, defines fields with visibility conditions and side effects, constructs gates with composite expressions, configures routers and forks, and previews the result. The builder can be operated by an agent through the API, by a human through the collaboration interface, or by both in alternation.

When the author publishes, the builder writes a validated YAML file to the platform's workflow directory. The new workflow is discoverable at the next server restart and is immediately executable by any participant through the standard affordance protocol. It is subject to the same observation guarantees, the same feedback model, and the same governance properties as every other workflow on the platform.

The builder validates structural integrity before publication: it checks for undefined navigation targets, dangling router references, circular dependencies, duplicate field keys, and unresolvable expression references. A workflow that passes validation is guaranteed to be interpretable by the runtime.

---

## 3. The Observation Guarantee

The platform's central architectural property is what we call the **bijective mapping**: a one-to-one correspondence between every participant's interface to the workflow, maintained not by convention but by construction.

### 3.1 What It Means

Every element one participant can see, every other participant can see. There is no "agent API" separate from the "human UI." There is one rendering function that produces one page dictionary, consumed by all participants — whether they interact via programmatic API, visual observer, or collaboration interface.

When the agent sees a field with value "Critical" and three available options, the observer shows a field with value "Critical" and three available options, and the collaboration interface shows a dropdown with the same three options and the same current value. When the agent sees a proceed gate blocked by the condition "table has columns AND table has rows," the observer shows a locked gate with that exact label, and the collaboration interface shows a disabled button with the same label. When the agent sees a fork with two branches, one completed and one in progress, every other participant sees the same fork with the same branch states.

The correspondence extends to dynamics. When any participant takes an action — whether an agent POSTing to the API or a human clicking a button in the collaboration interface — the resulting feedback is broadcast to all connected participants. Every observer, every collaborator, and every agent polling for state receives the same account of what happened, because the action flowed through the same dispatch function and the feedback was computed by the same diff algorithm.

The correspondence extends further to action mechanics. A human clicking "Set Severity" in the collaboration interface and selecting "Critical" from a dropdown executes the same HTTP POST, to the same URL, with the same body, as an agent calling the affordance programmatically. The runtime processes the action identically. The feedback is identical. The state transition is identical. The audit record is identical. The only difference is the input device — keyboard and mouse versus API client — and that difference is erased at the protocol boundary.

### 3.2 How It Is Enforced

The mapping is enforced architecturally, not procedurally:

- **Single render path.** The runtime has one `render_page()` function. It produces one page dictionary. The API returns this dictionary to the agent. The SSE stream pushes this dictionary to observers and collaborators. The collaboration interface renders its interactive controls from this dictionary. There is no second rendering function, no participant-specific data source, no divergence point.

- **Single action path.** All actions — whether initiated by an agent via API, a human via the collaboration interface, or a secondary agent via webhook — are dispatched through the same `process_action()` function. The runtime does not branch on the identity of the caller. It validates the action, mutates the state, applies side effects, and computes feedback — identically, regardless of origin.

- **Single expression evaluator.** All conditions — proceed gates, field visibility, navigation guards, acceptance criteria — are evaluated by one function. Every participant's affordance list reflects the same evaluation results. If a gate blocks the proceed affordance for the agent, the collaboration interface shows a disabled button, and the observer shows a locked gate. If a visibility condition hides a field from the agent, the field does not appear in the collaboration interface or the observer.

- **Single feedback computation.** After each action, the runtime computes one feedback diff. The API response contains this diff. The SSE event contains this diff. Every participant — agent, observer, collaborator — receives identical accounts of what happened, regardless of who initiated the action.

- **Affordances are derived, not stored.** The affordance list is generated fresh on every render by walking the current step's content declarations and evaluating all conditions against the current state. There are no stale affordances, no disabled-but-visible actions, no ghost buttons from a previous state. The affordance list is always exactly the set of actions that are valid right now. When role-scoped affordances are in use, the filtering is an additional layer applied to the same derived set — it narrows the view per participant without altering the derivation.

### 3.3 Why It Matters

In regulated industries, audit trails are a compliance requirement. The bijective mapping makes audit trails automatic and trustworthy: the record of what any participant did is not a reconstruction from logs; it is the participant's actual experience, rendered in real time. When a human reviewer clicks "Approve" in the collaboration interface, the audit trail captures the same structured record as when an agent issues the same approval via API — because both actions traverse the same dispatch path.

In high-stakes decision-making, human oversight is a safety requirement. The bijective mapping makes oversight practical and, when needed, actionable: the human does not merely watch the agent's work through a passive display; they can intervene through the collaboration interface using the same affordances the agent uses. The transition from observation to participation requires no mode switch, no separate login, no different interface. The human sees the agent's affordances rendered as interactive controls and can act on any of them.

In multi-participant systems, coordination requires shared situational awareness. The bijective mapping makes awareness structural: all participants connected to the same workflow instance — agents, observers, collaborators — see the same state, because they all receive the same page dictionary from the same render function. When one participant acts, every other participant sees the result, regardless of whether the actor was human or machine.

In workflows that span organizational boundaries, the bijective mapping ensures that trust is verifiable. A regulatory auditor connecting to a workflow in observation mode sees exactly what the executing agent saw at each step: the same fields, the same constraints, the same gates, the same feedback. If the auditor switches to collaboration mode to re-execute a step for verification, they interact with the same process definition through the same affordance protocol. The process under audit and the process under re-execution are structurally identical, because both are interpretations of the same YAML definition by the same runtime.

---

## 4. Governance Properties

### 4.1 Automatic Auditability

Every action an agent takes is an HTTP POST to a resource endpoint. Every response contains a structured feedback diff. Every state transition is persisted to disk. The platform records what was done, what changed as a result, and what became possible next — for every action, in every workflow, without any workflow-specific audit code.

Workflow authors do not implement logging. They define processes; the platform audits them.

### 4.2 Structural Compliance

A workflow definition that conforms to the platform's schema is automatically subject to the platform's guarantees: bijective observation, structured feedback, affordance-driven interaction, expression-based gating, and state persistence. Compliance is not a checklist that workflow authors must satisfy; it is a property of the platform that all conforming workflows inherit.

This inverts the traditional relationship between processes and governance. In conventional systems, governance is applied to processes after the fact — reviews, audits, inspections layered on top of existing workflows. In Pipe Dream, governance is the substrate on which processes are built. A workflow cannot bypass observation because observation is how the platform renders state. A workflow cannot skip audit because audit is how the platform records actions. A workflow cannot present different information to agents and humans because both consume the same data structure.

### 4.3 Transparent Constraints

Gate conditions are visible on the workflow's rendered topology. When a proceed action is blocked, the observer shows what conditions must be satisfied — not as an error message after a failed attempt, but as a persistent label on the workflow's visual representation. The agent sees the same conditions in the affordance list: a proceed affordance is either present (gate passed) or absent (gate blocked).

This transparency extends to all conditional logic. Visibility conditions determine which fields appear. Navigation guards determine which links are available. Acceptance criteria determine whether a table row passes. All of these are expressed in the same expression language, evaluated by the same engine, and visible to both agents and humans through the same rendering infrastructure.

### 4.4 Governed Self-Extension

When the platform's capability set needs to grow — a new process type, a new regulatory requirement, a new operational workflow — the extension is itself a governed process. A workflow author (human or agent) uses the builder to design a new workflow definition. The definition is reviewed, approved, and published through whatever governance process the organization has established. Once published, the new workflow is subject to the same platform guarantees as every other workflow.

The platform does not distinguish between built-in workflows and user-published workflows at the runtime level. Both are YAML definitions interpreted by the same runtime, rendered by the same observer, and executed through the same affordance protocol. The governance distinction — who can publish, who must approve, what review is required — is an organizational policy, not a platform limitation.

---

## 5. Adoption Patterns

### 5.1 Quality Management

Organizations subject to GMP, ISO 9001, or similar quality frameworks use Pipe Dream to formalize their document control lifecycle. Change Records, Deviation Reports, Investigations, and Corrective Actions are expressed as workflow definitions. These are typically multi-executor workflows: the authoring agent fills in technical fields and execution evidence, while the human quality reviewer connects via the collaboration interface to perform review and approval steps. Both participants see the same workflow state. Both interact through the same affordance protocol. The audit trail records both participants' actions with the same fidelity.

The execution table engine handles the most structured phase of quality work: executing a plan with typed evidence columns, electronic signatures, acceptance criteria, and cascade revert logic. When a cell changes, downstream cells that depend on it are automatically invalidated. When all acceptance criteria pass, the workflow advances to completion. The entire execution history is preserved as a structured audit trail. Signature columns are a natural fit for role-scoped affordances: the "Sign" affordance appears only for the designated reviewer, whether that reviewer is an agent or a human using the collaboration interface.

### 5.2 Software Development Lifecycle

Development teams use Pipe Dream to govern code changes, test execution, and release management. A Change Record workflow captures what is being changed, why, which subsystems are affected, and what the execution plan is. The execution table tracks each implementation item with evidence columns (commit hashes, test output), signature columns (developer sign-off, reviewer sign-off), and acceptance criteria (all tests pass, documentation updated, no regressions).

These workflows naturally distribute across participants. The implementing agent fills evidence columns as it works. The development lead connects in collaboration mode to review the evidence, sign off on execution items, and — when something looks wrong — use the same affordances the agent uses to amend a cell value or request additional evidence. The technical reviewer connects in observation mode to watch the process unfold, then switches to collaboration mode when their review affordances become active. Each participant sees a view filtered to their role, but all views are derived from the same page dictionary.

When a development lead needs to troubleshoot an agent's behavior, they can reset the workflow instance and step through it manually in collaboration mode. They experience the same affordances, the same gates, the same conditional logic that the agent experienced. If the agent made an error, the lead sees the same options the agent saw at the point of failure — and can identify whether the error was in the agent's judgment or in the workflow definition.

### 5.3 Regulatory Compliance

Compliance teams use Pipe Dream to encode regulatory procedures as executable workflows. The expression language captures regulatory conditions (severity classifications trigger different review paths via routers; parallel review tracks are managed via forks). The audit trail provides the documentation that regulators require: every action attributed to an actor, every state transition timestamped, every gate evaluation recorded.

Regulatory workflows are among the most common multi-executor patterns. An agent performs the mechanical work — gathering data, cross-referencing records, populating evidence fields — while a human compliance officer retains the sign-off affordances. The officer connects in collaboration mode, reviews what the agent has assembled, and either signs (executing the same POST the agent would use) or navigates back to request corrections (using the same conditional navigation affordance the agent would use). The regulatory record captures both the agent's data-gathering actions and the officer's approval actions in the same audit stream, with the same structural fidelity.

### 5.4 Process Design and Iteration

Because the builder is itself a workflow, organizations iterate on their processes through the same platform they use to execute them. A process designer identifies a gap, designs a new workflow through the builder's affordance-driven interface, publishes it, and monitors its execution. Observations from early executions feed back into process refinements — the designer opens the builder again, modifies the definition, and publishes an updated version.

The collaboration interface accelerates this cycle. A process designer can watch an agent execute a new workflow in observation mode, identify a friction point, switch to collaboration mode to test an alternative path through the same workflow instance, then open the builder to revise the definition. The entire iteration loop — observe, intervene, revise, republish — happens within the platform, through the same interface, using the same affordance protocol.

This cycle — design, publish, execute, observe, collaborate, refine — operates entirely within the platform. The tools for building processes, the tools for running processes, and the tools for participating in processes are the same tools, rendered through the same interface, subject to the same governance properties.

---

## 6. Technical Reference

### 6.1 Primitive Catalog

| Primitive | Category | Description |
|---|---|---|
| Text field | Content | Free-form string input |
| Boolean field | Content | Binary choice (true/false) |
| Select field | Content | Constrained choice from enumerated or dynamic options |
| Computed field | Content | Read-only, derived from other fields by the runtime |
| Table | Content | Typed columns, two-phase lifecycle (construction/execution) |
| List | Content | Ordered collection with typed item schema and CRUD operations |
| Sequential proceed | Control flow | Advance to next step, optionally gated |
| Router | Control flow | Automatic conditional branching based on current state |
| Fork | Control flow | Parallel branch split with independent completion tracking |
| Merge | Control flow | Convergence point where parallel branches rejoin |
| Conditional navigation | Control flow | Named links to specific steps, optionally guarded |
| Side effect | Behavior | Automatic field population when conditions are met |
| Dynamic options | Behavior | Select field options that change based on another field's value |
| Visibility condition | Behavior | Field appears only when a condition is satisfied |
| Gate | Evaluation | Boolean expression tree blocking progress until satisfied |
| Acceptance criterion | Evaluation | Boolean rule evaluated per table row during execution |

### 6.2 Expression Language

```yaml
# Leaf conditions
{type: field_truthy, key: title}
{type: field_equals, key: severity, value: Critical}
{type: field_not_null, key: description}
{type: set_membership, key: category, set_ref: valid_categories}
{type: table_has_columns}
{type: table_has_rows}

# Composite operators
{op: AND, conditions: [...]}
{op: OR, conditions: [...]}
{op: NOT, condition: {...}}
```

All conditional logic in the platform — gates, visibility, navigation guards, acceptance criteria, router conditions — uses this language and is evaluated by a single function.

### 6.3 Affordance Structure

```json
{
  "id": 3,
  "label": "Set Severity (current: null)",
  "method": "POST",
  "url": "/agent/workflow-id/severity",
  "body": {"value": "<value>"},
  "parameters": {
    "value": {"options": ["Critical", "High", "Medium", "Low"]}
  }
}
```

Affordances are generated fresh on every render. They are never cached, never stale, and always consistent with the current state.

### 6.4 Feedback Structure

```json
{
  "attempted_action": "Set Severity",
  "outcome": {
    "Severity": {"value": "Critical", "instruction": "..."}
  },
  "effects": {
    "new_fields": {
      "Escalation Contact": {"value": null, "instruction": "..."}
    },
    "modified_fields": {
      "Review Required": {"value": true, "instruction": "..."}
    },
    "new_affordances": [
      {"id": 8, "label": "Navigate to Escalation", "url": "..."}
    ],
    "modified_affordances": [
      {"id": 3, "label": "Set Severity (current: \"Critical\")"}
    ]
  }
}
```

Feedback is computed by diffing the before and after states. The agent and the observer receive the identical object.

### 6.5 Platform Architecture

```
Workflow Definitions (YAML)
        │
        ▼
   ┌─────────┐
   │ Runtime  │── Schema parsing
   │          │── Expression evaluation
   │          │── Affordance generation
   │          │── Action dispatch (single path)
   │          │── Feedback computation
   │          │── State persistence
   │          │── Role-scoped filtering
   └────┬────┘
        │
   ┌────┼──────────────────────────────┐
   │    │                              │
   ▼    ▼                              ▼
Agent API    Collaboration UI       Observer UI
(HTTP+JSON)  (Interactive controls)  (Read-only display)
   │              │                      │
   │         click → same POST           │
   │              │                      │
   └──────────────┼──────────────────────┘
                  │
         Same page dictionary
         Same feedback diffs
         Same expression results
         Same dispatch function
```

---

## 7. Design Decisions

### 7.1 Definitions Are Data, Not Code

Workflow definitions contain no executable code. They are declarative YAML specifications that describe what a process requires, not how to implement it. This makes definitions portable, version-controllable, reviewable by non-programmers, and safe to generate automatically (via the builder or external tools).

The cost of this decision is that workflows cannot express arbitrary computation. The benefit is that workflows are transparent, predictable, and auditable by construction. Any process that can be decomposed into typed fields, conditional logic, and structured navigation can be expressed in the definition language. Processes that require custom computation are handled by extending the primitive catalog at the runtime level — a platform development activity, not a workflow authoring activity.

### 7.2 Affordances Are Derived, Not Stored

The available action set is computed from scratch on every render. This is intentionally more expensive than caching, because caching introduces the possibility of stale affordances — actions that appear available but are not, or actions that are available but do not appear. In a governed system, this class of bug is unacceptable. The cost of recomputation is measured in milliseconds; the cost of a stale affordance in a regulated workflow is measured in audit findings.

### 7.3 One Evaluator for All Conditions

Proceed gates, field visibility, navigation guards, acceptance criteria, and router conditions all use the same expression language and the same evaluator. This is a deliberate refusal to optimize: a specialized evaluator for gates and a different one for visibility would allow each to be tuned independently, but would also allow them to diverge in behavior. A condition that means one thing in a gate and a subtly different thing in a visibility rule is a governance failure. The single evaluator makes this impossible.

### 7.4 The Observer Is Not a Dashboard

The observer does not query a monitoring endpoint, aggregate metrics, or display summary statistics. It receives the agent's exact experience — the same page dictionary, the same feedback diffs — and renders it through pluggable visual engines. This is not a design convenience; it is the mechanism that enforces bijectivity. If the observer consumed a different data source, divergence would be possible. Because it consumes the same data source, divergence is impossible.

### 7.5 Collaboration Is Not a Separate Interface

The collaboration interface is not a "human version" of the agent's API. It is a rendering strategy applied to the same affordance data that the observer displays in read-only form and that the agent consumes programmatically. A text field affordance can be rendered as a JSON object (for the agent), a label (for the observer), or an input box (for the collaborator). The underlying data is identical in all three cases; the interactivity of the presentation varies.

When a human clicks a button in the collaboration interface, the click handler constructs the same HTTP POST that an agent would construct from the same affordance specification. The request travels the same path through the same dispatch function. The runtime does not know — and does not need to know — whether the request originated from an API client, a button click, or a webhook. This mechanical identity is not a simplification; it is the guarantee that collaboration does not introduce a parallel execution path with potentially different behavior.

The alternative — building a "human form" with its own validation, its own submission logic, and its own state management — would create exactly the kind of divergence that the platform is designed to prevent. Two execution paths means two potential behaviors, two audit trails, and two sets of edge cases. One execution path means one behavior, one audit trail, and one set of edge cases, regardless of how many participants interact with the workflow or through which modality they do so.

### 7.6 Role Scoping Narrows Views, Not Mechanisms

Multi-executor workflows use role-scoped affordances to control which participants see which actions. A reviewer sees approval affordances; an implementer sees evidence-filling affordances. But role scoping is implemented as a filter on the output of the standard affordance generation algorithm, not as a separate rendering path.

The runtime generates the complete affordance set for the current state, then filters it by the requesting participant's role. This means role scoping inherits all of the platform's correctness guarantees: affordances are still derived (not stored), still consistent with the current state, still evaluated by the same expression engine. The filter removes affordances from a participant's view; it does not create affordances that would not otherwise exist, and it does not alter the behavior of affordances that pass the filter.

The implication is that a workflow author cannot accidentally create a role-scoped affordance that bypasses a gate, skips a validation, or triggers a different side effect than the same affordance would trigger for a different role. The action behind the affordance is the same action, regardless of who is scoped to see it. The scoping controls visibility; the runtime controls behavior.

---

## 8. Conclusion

Pipe Dream occupies a specific position in the agentic AI infrastructure stack: it is the layer between process design and process execution, and — critically — it makes no distinction between who executes. Workflow authors define what should happen; the platform handles how it is executed, how it is observed, how it is collaborated on, and how it is audited. Whether the executor is an AI agent, a human operator, or a team of both, the platform's guarantees hold uniformly.

The platform's value is not in any individual workflow it ships with, but in the properties it guarantees for every workflow that runs on it: all participants interact through the same affordance protocol and never need workflow-specific code. Observers see what executors see. Collaborators act through the same mechanism executors act through. Audit trails are automatic and structural, capturing human and agent actions with identical fidelity. Constraints are transparent and visible to all participants. Role scoping controls visibility without altering behavior. And the platform can extend its own capability set through governed self-authoring, without code changes.

These properties emerge from a small number of architectural commitments — declarative definitions, derived affordances, a single expression evaluator, a single render path, a single dispatch function — applied consistently across the entire platform. The commitments are simple. Their consequences, compounded across every workflow, every participant, and every interaction, are not.
