# Vision: Guided Agent Orchestration (v2)

**Session:** 2026-02-25-001

---

## Vision Statement

The QMS governs work through document lifecycles, but the knowledge required to navigate those lifecycles is currently scattered across SOPs, templates, and policy documents. An agent starting a CR today must internalize thousands of lines of context to know what steps to take, in what order, and what constitutes compliant execution. This context cost is the central bottleneck — it wastes tokens, invites errors of omission, and makes every new agent session a cold start.

The solution is a system that meets agents where they are in the workflow and tells them exactly what they need to know *right now*. At each stage gate, the system enforces preconditions programmatically and surfaces a concise, targeted prompt: what just happened, what's required next, and what the common mistakes are at this specific transition. The agent never reads an SOP. It receives the distilled, decision-relevant subset at the moment it matters.

The purpose of this machinery is not compliance for its own sake — it is to get agents into the vault as fast as possible. Once the paperwork is filed, the reviews are in, and the execution branch is cut, the blast doors seal and the agent has total creative freedom. Anything it does is contained, reversible, and controlled. If it succeeds, the result is a clean line on the EI table. If it causes rampant destruction, a single git command rolls it back, a VR documents what happened, and the catastrophic failure becomes a cheap learning opportunity. The guardrails exist so that the space inside them can be fearless.

A complementary goal is the elimination of SOPs as a document class. If the CLI enforces a mechanism, prescribing that same mechanism in prose is redundant and a maintenance burden. The authority model reduces to two strands: the CLI (mechanism — what the system enforces) and the Quality Manual (judgment — what to do at points of high degrees of freedom). SOPs are retired and replaced by the guided orchestration system itself: the CLI *is* the procedure, and the Quality Manual tells you how to think when the CLI asks you to choose.

---

## The Breakthrough: No Central Engine

The first iteration of this vision proposed a central workflow engine — a dynamic directed graph that tracks all documents, all actions, all dependencies. That design raised an unanswerable question: where does the engine's responsibility end and the agent's begin?

The answer is: there is no central engine. There is no central graph. There is no elaborate prompt generator.

Instead, the system is built entirely from mechanisms that already exist:

- **Inboxes** deliver actionable items to agents
- **Checkout** locks resources for exclusive use
- **Interactive documents** walk agents through structured prompts
- **Templates** generate compliant documents

The missing piece is not a new runtime — it is a new kind of interactive document that **collapses** the full space of possible workflows down to the agent's specific situation.

---

## The Help Desk Model

An agent doesn't know what to do. They check their inbox. If nothing is there, they "send an email" — they request help. What comes back is an **interactive workflow document**: a `.interact` file loaded with all templates, all possible paths, all prompts (or pointers to them).

The agent interacts with it. Each response eliminates possibilities:

- "Is this a code change?" → eliminates document-only paths
- "Which system?" → narrows to qms-cli, loads its system profile
- "Did an EI fail?" → opens the failure recovery branch
- "What type of failure?" → selects the appropriate recovery template

The interactive document is a **superposition of all possible workflows**. Each prompt collapses it further. What falls out at the end is a **task bundle** — a concrete, fully-specified package:

- The right documents, pre-populated with context from the interaction
- The right permits identified (which systems need write access)
- The right sequence of actions laid out
- Just-in-time guidance attached to each action

The agent accepts the task bundle and executes using existing QMS mechanisms: checkout, edit, checkin, route.

---

## The Agent Experience

### Starting Work

```
> qms inbox

  No pending tasks.

> qms help

  Loading workflow navigator...

  What do you need to do?
  (a) Make a change to code or documents
  (b) Handle a failure during execution
  (c) Respond to a review assignment
  (d) Close out completed work

> a

  What kind of change?
  (a) Code change to a governed system
  (b) Document-only change (templates, QMS infrastructure)
  (c) Process improvement

> a

  Which system?
  (a) qms-cli (CLI-18.0, commit 309f217, RS v22.0, RTM v27.0)
  (b) flow-state
  (c) quality-manual

> a

  Does this change add new requirements?
  ...
```

Each answer narrows the path. The system knows what questions to ask because the templates encode the decision tree.

### Receiving a Task Bundle

After the interaction collapses:

```
> Task bundle generated: CR-108

  Title: Add `diff` command to compare document versions
  System: qms-cli (branch: cr-108)
  Permits needed: qms-cli

  Actions:
    1. [mutation]  Create CR-108 (pre-populated)
    2. [gate]      Route for review, wait for approval
    3. [mutation]  Acquire permit on qms-cli, cut branch cr-108
    4. [work]      Update RS with new requirements
    5. [gate]      Wait for RS to reach EFFECTIVE
    6. [work]      Implement the change
    7. [work]      Run tests, push, qualify
    8. [work]      Update RTM with verification evidence
    9. [gate]      Wait for RTM to reach EFFECTIVE
   10. [mutation]  Merge branch, release permit
   11. [gate]      Route for post-review, wait for closure

  Accept this task bundle? (y/n)
```

The agent sees the full plan. Each action has a flavor (mutation, gate, work) so the agent knows what requires their effort and what happens automatically. They accept, and execution begins.

### During Execution

The agent doesn't need to remember the plan. They check what's next:

```
> qms next

  CR-108 / Action 6: implement
  System: qms-cli, branch: cr-108
  Context: RS v23.0 is EFFECTIVE with REQ-DIFF-001 through REQ-DIFF-006.
  Guidance: Run full test suite before marking complete.
  Blocked: Actions 7-11 (waiting on this)
```

### When Things Go Wrong

Action 6 fails. The agent reports the failure:

```
> qms fail

  Action 6 failed. Loading recovery options...

  What happened?
  (a) Implementation didn't work — need to revert and try again
  (b) Implementation revealed a design flaw — need to rethink
  (c) External blocker — can't proceed until something else is resolved

> a

  Recovery plan:
    6a. [mutation]  Revert branch cr-108 to pre-action-6 state
    6b. [mutation]  Create VAR (CR-108-VAR-001)
    6c. [work]      Author VAR: document failure and corrective approach
    6d. [gate]      Wait for VAR pre-approval
    6e. [work]      Retry implementation with corrective approach

  Accept recovery plan? (y/n)
```

The recovery options are themselves interactive — the agent answers a few questions and the appropriate recovery template expands into new actions spliced into their task bundle. No graph engine required. Just another `.interact` that collapses to the right recovery path.

---

## Domain Model

The agent's universe is a single git repo (the **project**) containing any number of governed submodules (**systems**).

| Concept | What it is |
|---------|-----------|
| **Project** | The root repo. Governance infrastructure: QMS documents, metadata, audit trail, agent config. Not itself a system. |
| **System** | A governed submodule. Code or content that changes under CR authorization. Leaf nodes — never nested from the engine's perspective. Each has its own origin/main (the truth). |
| **Document** | A QMS artifact with a lifecycle. In this model, documents shift from driving the process to being **compiled views** of completed work, packaged for human review. |
| **Permit** | Write access to a system, held by an in-execution CR. Derived from document state, not stored. |
| **Task bundle** | The output of a collapsed interactive workflow. A concrete sequence of actions with pre-populated documents and identified permits. |
| **Agent** | The entity performing work actions. |
| **Human** | The entity performing decision actions (approve, reject, choose). |

### The Evolving Role of Documents

As more of the process is absorbed into the interactive workflow and task bundles, documents shift from being the driver of the process to being **compiled review artifacts**. The irreducible function of a document is the **review boundary** — a coherent chunk of work packaged so that a human can look at it and say "this is acceptable."

The template system compiles the relevant actions and their outcomes into a document at the point where human judgment is needed. The reviewer reads a document, exactly as they do today. The machinery underneath is completely different.

---

## Action Vocabulary

Actions are the primitive. Each has a flavor and a fixed schema.

### Action Flavors

| Flavor | Performed by | What it does |
|--------|-------------|--------------|
| **gate** | system | Checks a condition. Passes or blocks. No side effects. |
| **mutation** | system | Changes system state automatically. |
| **work** | agent | Requires creativity and judgment. |
| **decision** | human | Requires human judgment. |

### Verb Catalog (fixed schemas)

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

---

## What Gets Built vs. What Already Exists

| Capability | Status | What changes |
|-----------|--------|-------------|
| Inboxes | **Exists** | Become the primary task delivery mechanism |
| Checkout/checkin | **Exists** | Extends to claiming task bundles and acquiring permits |
| Interactive engine | **Exists** (CR-091, VR authoring) | Generalized to workflow navigation and recovery |
| Templates | **Exists** | New templates for CR/VAR/ADD authoring via interaction |
| Document compilation | **Exists** (Jinja2 compiler) | Extended to compile task bundle outcomes into review documents |
| Workflow navigator | **New** | The master `.interact` that collapses all possible workflows |
| Recovery templates | **New** | Interactive failure-response templates that expand task bundles |
| Permit enforcement | **New** | System-level locking tied to in-execution CRs |
| `qms help` | **New** | Entry point to the workflow navigator |
| `qms next` | **New** | Shows the next ready action from the agent's active task bundle |
| `qms fail` | **New** | Triggers recovery template interaction |

---

## The Exponential Improvement Thesis

We are building neural implants for AI, by AI. The interactive documents are externalized cognition — they hold the decision trees, the recovery patterns, and the compliance knowledge so the agent's context window is free for creative work.

Every novel failure an agent encounters gets encoded as a new recovery template. The next agent that hits the same failure doesn't spend tokens reasoning about recovery — they interact with a few prompts and the right recovery path falls out. The system accumulates intelligence over time without any individual agent needing to carry that knowledge.

This is the mechanism for exponential improvement in AI success rates: the cost of each failure decreases over time because the recovery path is pre-computed. Agents spend their tokens on creative work, not on navigating process. The interactive documents handle process; the agent handles judgment.

---

## Design Principles

1. **An action should fit in your head.** One node, one sentence. If describing an action takes a paragraph, it's actually multiple actions.

2. **Templates should be readable as plain lists.** Not code, not graph notation — a recipe. If you can't read it aloud and have it make sense, it's too clever.

3. **The task bundle should be inspectable at any moment.** The agent can always see what's done, what's next, what's blocked, and why. No hidden state.

4. **Local reasoning works.** You can look at one action and understand it without understanding the full bundle. Its guidance is self-contained.

5. **Start embarrassingly simple.** The prototype handles one CR workflow and one failure recovery path. If that feels natural to use, extend. If it feels like fighting the system, redesign before adding complexity.

6. **Maximize what already exists.** Every new feature should be a composition of existing mechanisms, not a replacement. The inbox, checkout, interactive engine, and template compiler are the foundation — not the scaffolding to be removed later.

7. **Easy and intuitive to build and reason about.** The system must be simpler to work with than the process it replaces. If it's harder to reason about than reading SOPs, we've failed.

---

**END OF DOCUMENT**
