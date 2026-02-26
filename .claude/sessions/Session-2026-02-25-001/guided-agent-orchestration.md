# Vision: Guided Agent Orchestration

**Session:** 2026-02-25-001

---

## Vision Statement

The QMS governs work through document lifecycles, but the knowledge required to navigate those lifecycles is currently scattered across SOPs, templates, and policy documents. An agent starting a CR today must internalize thousands of lines of context to know what steps to take, in what order, and what constitutes compliant execution. This context cost is the central bottleneck — it wastes tokens, invites errors of omission, and makes every new agent session a cold start.

The solution is a system that meets agents where they are in the workflow and tells them exactly what they need to know *right now*. At each stage gate, the system enforces preconditions programmatically and surfaces a concise, targeted prompt: what just happened, what's required next, and what the common mistakes are at this specific transition. The agent never reads an SOP. It receives the distilled, decision-relevant subset at the moment it matters.

The purpose of this machinery is not compliance for its own sake — it is to get agents into the vault as fast as possible. Once the paperwork is filed, the reviews are in, and the execution branch is cut, the blast doors seal and the agent has total creative freedom. Anything it does is contained, reversible, and controlled. If it succeeds, the result is a clean line on the EI table. If it causes rampant destruction, a single git command rolls it back, a VR documents what happened, and the catastrophic failure becomes a cheap learning opportunity. The guardrails exist so that the space inside them can be fearless.

A complementary goal is the elimination of SOPs as a document class. If the CLI enforces a mechanism, prescribing that same mechanism in prose is redundant and a maintenance burden. The authority model reduces to two strands: the CLI (mechanism — what the system enforces) and the Quality Manual (judgment — what to do at points of high degrees of freedom). SOPs are retired and replaced by the guided orchestration system itself: the CLI *is* the procedure, and the Quality Manual tells you how to think when the CLI asks you to choose.

---

## Domain Model

The agent's universe is a single git repo (the **project**) containing any number of governed submodules (**systems**).

### Concepts

| Concept | What it is | Where it lives |
|---------|-----------|----------------|
| **Project** | The root repo. Governance infrastructure: QMS documents, metadata, audit trail, agent config. Not itself a system. | `/` |
| **System** | A governed submodule. Code or content that changes under CR authorization. Each has its own origin/main (the truth), branches, and potentially its own CI. Systems are leaf nodes — never nested from the engine's perspective. | `/qms-cli`, `/flow-state`, etc. |
| **Document** | A QMS artifact with a lifecycle. Authorizes and tracks changes to systems. | `QMS/` in the project root |
| **Branch** | An execution branch on a system. Scoped to one CR. | Within a system's git history |
| **Permit** | Write access to a system, held by an in-execution CR. Not stored — derived from document state. | Computed |
| **Agent** | The entity performing work actions. | |
| **Human** | The entity performing decision actions (the Lead, reviewers). | |

### Boundary Rules

- Changes to **systems** go through the full permit model: permit acquired, branch cut, work done, branch merged, permit released.
- Changes to the **project root** (templates, agent definitions, QMS infrastructure) are governed by the QMS but don't use the permit/branch/merge model. They're committed directly under CR authorization.
- Systems are always submodules. The project root is never a system. This keeps the model uniform and avoids systems-inside-systems complexity.

---

## Architectural Framing: Three Systems

The redesign comprises three distinct systems that serve a single goal:

### 1. Template System (Jinja2) — Interactive Document Authoring

Generates compliant documents from agent input at key decision points. The agent provides judgment (what is this change? why? what's affected?); the system handles structure, boilerplate, conditional sections, and EI table composition. Product: a plan that is correct by construction.

The three-artifact separation (workflow spec + rendering template + source data) described in the original design discussion (Session-2026-02-22-004) applies here. The workflow spec harvests decisions at high-degree-of-freedom points; the rendering template compiles those decisions into a compliant document. The agent is not walked through every subsection — it is asked for judgment where judgment is needed, and the system handles the rest.

### 2. Interactive Execution System — Project-Scale Orchestration

Knows the state of all open documents, their dependencies, their EIs, their blockers and prerequisites. Tells the agent: "here is your next actionable step, here is what you need to know to do it, here is what's blocking everything else." Not scoped to a single document — scoped to the *project*.

The current VR interaction engine (CR-091) is a single-document prototype of this system. The redesign generalizes it upward: the system doesn't just walk you through VR steps, it walks you through the entire lifecycle — "CR-107 EI-3 is unblocked, RS is EFFECTIVE, here's the branch, go build" and then "you're back, EI-3 passed, EI-4 needs the RTM updated, here's what the RTM currently says about your requirements."

### 3. Permit System — Project-Level Locking

The truth for each governed system is origin/main on GitHub. Various access protections already exist (GitHub authentication, Claude Code permissions, the qms-write-guard hook, read-only container mounts), but none of these enforce the fundamental rule: you cannot modify a controlled system without an in-execution CR that explicitly declares that system as in scope.

The permit system makes this programmatic. A CR's declared target systems become lock acquisitions: when the CR enters execution, the agent gains write access to an execution branch on those systems and only those systems. When the CR closes or rolls back, the lock releases. This is the mechanism that makes the "vault" metaphor real — it's not just that failure is reversible, it's that the blast doors are physically sealed. An agent literally cannot write to a system it doesn't hold a permit for.

This also solves multi-agent coordination: if two CRs try to claim the same system, the conflict is explicit and resolvable rather than a silent race condition. The enforcement chain:

1. **CR authoring** — template system requires declaration of target systems
2. **CR enters execution** — lock acquired on those systems (branch created, write access granted)
3. **Agent works** — write access scoped to *that branch* of *that system*
4. **CR closes / rolls back** — lock released, branch merged or deleted

### Design Principle: Design for Agents

The Quality Manual and templates must not become bloated. Agents cannot reliably retain small but important details buried in large documents. The "read and understand" model is abandoned in favor of **Compliance by Design**: the template system enforces correct plans with correct stage gates, and the execution system provides targeted guidance for entering and leaving the "vaults" — the execution branches where agents work with full creative freedom inside controlled, reversible boundaries.

The Quality Manual is not a document agents read. It is a data source the execution system draws from to compose just-in-time guidance. Agents see the prompt, not the manual.

---

## The Engine: A Dynamic Directed Graph

The three systems above (template, execution, permit) are unified by a single runtime engine: a dynamic directed graph where nodes are **actions** and edges are **dependencies**.

### The Primitive: Actions, Not Tasks

The fundamental unit is the **action** — not the EI, not the task, not the document. An EI is a *subgraph* of actions. A document lifecycle is a larger subgraph. The entire project is one graph.

"Action" is chosen deliberately over "task" because not everything in the graph requires agent work. The graph contains four flavors of action:

| Flavor | Performed by | Examples |
|--------|-------------|----------|
| **gate** | system | "is RS EFFECTIVE?", "are all reviewers done?", "does CI pass?" |
| **mutation** | system | acquire lock, transition document state, cut branch, release lock |
| **work** | agent | write code, author document content, run tests |
| **decision** | human | approve/reject, choose approach, resolve conflict |

A **gate** is a check with no side effects — it passes or blocks. A **mutation** changes system state automatically. **Work** requires agent creativity and judgment. A **decision** requires human judgment.

An EI like "Update RS to EFFECTIVE" decomposes into an action subgraph:

```
checkout RS → edit RS content → checkin RS → route for review
    → [gate: all reviewers done?] → route for approval
    → [decision: approve/reject] → RS is EFFECTIVE
```

Some of these are agent work, some are system mutations, some are gates waiting on external input. They are all first-class nodes in the same graph, with their own preconditions and effects.

### Dynamic Graph Expansion

The graph is not static. It mutates in response to outcomes.

The initial graph is generated from the CR's EI table — the planned work, decomposed into actions. This is the happy path. When an action fails, the system consults its library of **expansion templates** and splices a recovery subgraph into the graph. The recovery subgraph connects back to the parent graph at the appropriate point.

Example: EI-3 (implement feature) fails.

```
Before failure:
    EI-2 ─→ EI-3 ─→ EI-4 ─→ ...

After failure (graph expands):
    EI-2 ─→ EI-3 [FAILED]
                ╰─→ revert branch ─→ create VAR ─→ author VAR
                    ─→ review VAR ─→ approve VAR
                    ─→ retry EI-3' ─→ EI-4 ─→ ...
```

The agent doesn't need to know recovery procedures. It just sees new ready actions appear on the frontier. The graph encodes the recovery knowledge.

### Expansion Templates

Expansion templates are the system's growing library of "what to do when X goes wrong." They are the mechanism by which the system accumulates intelligence over time.

An expansion template is **parameterized**: "on EI failure" always generates the same structural shape (revert → VAR → retry), but parameterized with the specific EI, parent document, failure context, and affected systems.

Example template file:

```yaml
# expansion-templates/ei-failure-var-recovery.yaml
name: EI Failure — VAR Recovery
version: 1

trigger:
  flavor: work
  outcome: failed

steps:
  - action: revert
    system: "{{ system }}"
    to: "pre-{{ ei }}"

  - action: create
    type: VAR
    parent: "{{ document }}"

  - action: author
    document: "{{ var }}"
    guidance: |
      Document what was attempted, what failed, and the
      proposed resolution. Classify as Type 1 or Type 2.

  - action: wait
    document: "{{ var }}"
    until: PRE_APPROVED

  - action: retry
    original: "{{ action }}"
    guidance: |
      Re-attempt with the corrective approach from {{ var }}.

rejoin: "{{ action.next }}"
```

Each action type has a fixed schema — no free-form qualifiers. `revert` always takes `system` and `to`. `create` always takes `type` and `parent`. `wait` always takes `document` and `until`. If a field isn't in the schema, it's an error.

**Open design questions:**

1. **Who creates new templates?** Initially, templates are defined by the Lead/QMS as formalized failure-response patterns (the patterns that are currently described in SOPs and the Quality Manual). Over time, the system may be able to infer new templates from agent behavior — an agent improvises a recovery, the pattern is captured, and it becomes available as a template for future failures.

2. **How deep can expansion nest?** A VAR subgraph could itself contain an action that fails, spawning its own recovery subgraph. The correct model is infinite recursion with practical safeguards (depth limits, cycle detection, escalation to human decision after N nested failures).

3. **Template evolution:** Expansion templates are themselves governed artifacts. When a template produces poor outcomes, that's a process failure that feeds back into template improvement — the recursive governance loop applied to the engine itself.

### The Role of Documents

As the graph absorbs more of what documents currently do — authorization, plan definition, evidence tracking, audit trail — the role of documents shifts. Currently, documents drive the process. In this model, the graph drives the process and documents become **compiled views of the graph**, packaged for human review.

Documents currently serve five roles:

1. **Authorization** — absorbed by the permit system
2. **Plan definition** — absorbed by the action subgraph (the EI table becomes a generated view)
3. **Evidence record** — absorbed by action outcomes recorded on nodes
4. **Audit trail** — absorbed by graph state history
5. **Review boundary** — the irreducible function that remains

The review boundary is what documents are *for* in this model. Someone needs to look at a coherent chunk of work and say "this is acceptable." You can't review a raw graph. You review a narrative: what was planned, what happened, what evidence exists. The template system compiles the relevant subgraph into a document at the point where human judgment is needed.

The process feels the same to the reviewer — they read a document, exactly as they do today. The machinery underneath is completely different.

### Vocabulary

The graph is built from a small set of nouns and verbs.

**Nouns** (the things that exist):

| Noun | What it is |
|------|-----------|
| **document** | A QMS-controlled artifact (CR, VAR, VR, RS, RTM...) |
| **system** | A governed submodule (qms-cli, flow-state, quality-manual) |
| **branch** | An execution branch on a system |
| **permit** | Write access to a system, held by a document |
| **agent** | The entity performing work |
| **human** | The Lead (or any human decision-maker) |

**Verbs** with fixed schemas (grouped by action flavor):

| Verb | Flavor | Required fields | Optional fields |
|------|--------|----------------|-----------------|
| **check** | gate | document, state | |
| **wait** | gate | document, until | |
| **create** | mutation | type, parent | |
| **transition** | mutation | document, to | |
| **acquire** | mutation | system, held_by | |
| **release** | mutation | system | |
| **branch** | mutation | system, from | name |
| **merge** | mutation | system, branch | |
| **revert** | mutation | system, to | |
| **author** | work | document | guidance |
| **implement** | work | system, branch | guidance |
| **test** | work | system | guidance |
| **approve** | decision | document | |
| **reject** | decision | document | comment |
| **choose** | decision | options | guidance |

### The Agent Experience

From the agent's perspective, the graph is invisible. The agent sees one thing: **the next ready action**, with just enough context to execute it.

```
> qms next

  Ready: CR-107 / EI-3 / implement
  System: qms-cli, branch: cr-107
  Context: RS v23.0 is EFFECTIVE with REQ-DIFF-001 through REQ-DIFF-006.
           Target: commands/diff.py (create), qms.py (modify).
  Guidance: Run full test suite before marking complete.
  Blocked: EI-4 (waiting on EI-3), EI-7 (waiting on RTM update)
```

If EI-3 fails:

```
> qms next

  Ready: CR-107 / EI-3-recovery / revert
  System: qms-cli, branch: cr-107
  Context: EI-3 failed. VAR created (CR-107-VAR-001).
           Reverting branch cr-107 to pre-EI-3 state.
  Guidance: Run `git reset --hard <pre-ei3-commit>`. Verify clean state.
```

The agent never reasons about the process. It follows the frontier. The graph does the reasoning.

### The Exponential Improvement Thesis

We are building neural implants for AI, by AI. The graph is externalized cognition — it holds the plan, the context, and the recovery knowledge so the agent's context window is free for creative work.

Every novel failure an agent encounters gets encoded as a new expansion template. The next agent that hits the same failure doesn't spend tokens reasoning about recovery — the graph just expands. The system accumulates intelligence over time without any individual agent needing to carry that knowledge.

This is the mechanism for exponential improvement in AI success rates: the cost of each failure decreases over time because the recovery path is pre-computed. Agents spend their tokens on creative work, not on navigating process. The graph handles process; the agent handles judgment.

### Design Principles

1. **An action should fit in your head.** One node, one sentence. If describing an action takes a paragraph, it's actually multiple actions.

2. **Expansion templates should be readable as plain lists.** Not code, not graph notation — a recipe. "When an EI fails: (1) revert branch, (2) create VAR, (3) author VAR, (4) review VAR, (5) approve VAR, (6) retry." If you can't read it aloud and have it make sense, it's too clever.

3. **The graph should be inspectable at any moment.** `qms status` shows the full graph in human-readable form — what's done, what's ready, what's blocked, and why. No hidden state.

4. **Local reasoning works.** You can look at one action and understand it without tracing the full graph. Its preconditions are listed. Its guidance is self-contained.

5. **Start embarrassingly simple.** The Genesis Sandbox prototype handles one CR with a linear EI chain and one failure expansion. If that feels natural to use, extend. If it feels like fighting the engine, redesign before adding complexity.

6. **Easy and intuitive to build and reason about.** The system must be simpler to work with than the process it replaces. If the engine is harder to reason about than reading SOPs, we've failed.

### Implementation: Genesis Sandbox

The engine will be built in a Genesis Sandbox — a standalone prototype informed by the existing QMS but not constrained by it. The core is a custom dynamic directed graph built on NetworkX (~300-400 lines), with:

1. **NetworkX DiGraph** for graph structure
2. **A topological executor** that walks the ready frontier (all predecessors completed)
3. **An expansion hook**: `on_failure(node, graph) → new subgraph` that splices recovery actions into the graph
4. **Action nodes** carrying their flavor (gate/mutation/work/decision), context, and guidance
5. **JSON serialization** of graph state for persistence
6. **A `next` query** that computes the ready frontier and enriches it with just-in-time guidance

The distributed state model applies: no central orchestrator state on disk. The graph is computed on the fly from QMS document metadata (`.meta/` files). Expansion templates are the only new persistent artifacts.

---

**END OF DOCUMENT**
