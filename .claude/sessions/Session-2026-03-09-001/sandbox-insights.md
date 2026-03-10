# Agent Portal Sandbox: Themes and Take-aways

*Session-2026-03-09-001*

---

## Themes

### Same Data, Two Renderers

The core experiment: an AI agent and a human observer consume identical JSON. The agent reads it raw; the human sees a styled projection. Neither view is privileged — both are renderings of the same source. This is the interaction model for agent-driven workflows.

### Affordances as Complete API Calls

The agent doesn't interpret a UI or guess at endpoints. Every action it can take is spelled out as a fully-formed request (method, URL, body). The agent picks one and sends it verbatim. The set of available affordances *is* the agent's action space — nothing more, nothing less.

### Declarative Over Procedural

We started with hardcoded Python building fields and affordances per-stage. By the end, both are driven entirely from YAML. The Python is a generic interpreter that knows about types (text, boolean, select, computed) and evaluation rules (visible_when, proceed gates) — it knows nothing about Change Records specifically. A different YAML file could define a completely different workflow.

### 1:1 Projection as a Central Pillar

The rendered view must faithfully project every key in the raw JSON. Nothing hidden, nothing added. A human looking at the rendered view should be able to infer what the source data is. This constraint keeps the renderer honest and prevents the "two truths" problem where the agent sees one thing and the human sees another.

This is not a nice-to-have. It is the foundational constraint of the entire engine.

If an agent is operating inside a workflow — filling fields, advancing stages, selecting options — and a human cannot see exactly what the agent sees, in a form they can instantly interpret, then the human has lost control. Not in a dramatic, science-fiction sense. In the mundane, practical sense: they cannot debug a stuck workflow, they cannot verify that the agent made the right choice, they cannot design a new workflow with confidence that the agent will experience it the way they intended.

The principle is simple: **whatever the agent sees, the human can also see and understand, via a dedicated projection that adds no information and hides none.** The raw JSON is the single source of truth. The rendered view is a bijective map from that truth into something a human can parse at a glance. The agent's action space — the full set of affordances — is visible, enumerable, and comprehensible.

This makes everything else possible:

- **Workflow authoring** becomes tractable because the author can preview exactly what the agent will experience at every state. The YAML definition produces a concrete, visible artifact — not an abstract graph that you have to simulate in your head.

- **Debugging** becomes tractable because when an agent does something unexpected, you can look at the state it was in, the affordances it was offered, and the one it chose. The entire decision context is right there, rendered in a form you can read.

- **Trust** becomes tractable because the human is never in the dark about what the agent is doing. The observer view is not a summary, not a log, not a post-hoc report. It is a live, faithful projection of the agent's actual reality.

- **Control** becomes tractable because the affordance model makes the agent's action space explicit and bounded. The agent cannot do anything that isn't in the affordance list. The human can see that list. The YAML author defines that list. The chain from intent to constraint to visibility is unbroken.

### The Visualizability Breakthrough

Everything clicked once we focused on visualizability. The past few weeks of work on the workflow engine — abstract graph definitions, YAML compilation, CLI-based execution — were not wrong in their goals, but they were doomed in their approach. They were trying to achieve the functionality we built today with no way to see it.

A workflow engine that operates in markdown files and CLI output is hopelessly complex. Not because the underlying logic is complex — the CR workflow we built today has conditional field cascades, stage gates, lifecycle tracking, and a full affordance model, and it's 230 lines of YAML. The complexity was in the *invisibility*. When you can't see the state, can't see the affordances, can't see the agent's view, you're building blind. Every design decision is speculative. Every debugging session is archaeology.

The web UI changed this overnight. The moment we could *see* the agent's JSON and its rendered projection side by side, the design decisions became obvious. Field structures, affordance shapes, visibility rules — these aren't things you reason about in the abstract. You look at them, and you know whether they're right.

This is why the previous iterations felt stuck: they were solving the right problem in a medium that made it impossible to evaluate the solution. The shift from "define workflows as data" to "define workflows as data *that you can see*" is the difference between theory and engineering.

### Instruction as a Universal Key

The `instruction` key appears at every level — page-level stage instructions, field-level guidance. Same key, same meaning, different scope. This is the agent's work instruction, wherever it appears.

---

## Take-aways

1. **The workflow definition is the product.** The YAML file *is* the workflow. Fields, visibility rules, stage gates, navigation, actions — all declarative. The Python interpreter and the HTML renderer are generic machinery. To build a new workflow, you write a new YAML file.

2. **Conditional visibility works as data.** The `visible_when` pattern — simple key-value conditions evaluated against current state — handles the cascading field logic (code impact → submodule → SDLC governed) without any workflow-specific code. This is sufficient for real forms.

3. **Affordance generation is derivable.** Given field definitions with types and a stage configuration with gates, the full affordance list can be mechanically produced for any workflow state. No per-stage authoring required.

4. **Pluggable renderers need context-awareness.** A dungeon map renderer is nonsensical for a CR workflow. The `matches(state)` pattern — each renderer declares what data shapes it supports — solves this cleanly. The system auto-falls back to Raw when nothing matches.

5. **WebFetch is wrong for agents consuming APIs.** Its AI summarizer middle-man destroys structured data. `curl` via Bash is the correct tool for an agent that needs to read and act on JSON responses.

6. **The sandbox proved its value.** Building in isolation from the main UI let us iterate fast on the data shape, the rendering model, and the YAML schema without touching production code. The patterns discovered here — the field/affordance/instruction model, the YAML schema, the renderer architecture — are ready to inform the real engine design.

7. **Visibility is not a feature, it is the architecture.** The entire engine design follows from one constraint: the human must be able to see what the agent sees. Everything else — the JSON schema, the 1:1 projection, the affordance model, the YAML definitions — is downstream of that requirement.
