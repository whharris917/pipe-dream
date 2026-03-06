# The QMS Graph: A Grand Unification

**Author:** Claude (Orchestrator), with Lead
**Date:** 2026-03-05
**Context:** CR-108 Genesis Sandbox — evolved from workflow engine design through a series of increasingly fundamental reframings
**Supersedes:** `workflow-engine-design.md` (same session) — the five-primitive workflow model is subsumed by this design

---

## 1. The Insight

The previous design proposed five primitives (WorkflowTemplate, WorkflowInstance, Step, Gate, Signal) to replace the document-centric model. That design was an improvement, but it still treated templates, instances, and execution as separate concepts mediated by an engine.

The insight that unifies everything: **the entire QMS is a single graph.** Not a collection of templates that produce instances that get executed — a single, traversable, self-modifying graph. Everything the QMS does — document creation, drafting, review, approval, execution, deviation handling, template authoring, SOP revision, even onboarding a new agent — is cursor traversal through this graph.

There are no templates. There are no instances. There are no document types. There is a graph, and there are tickets moving through it.

### What This Replaces

| Old concept | Graph equivalent |
|-------------|-----------------|
| SOP (prose instructions) | A subgraph whose nodes supply the instructions as prompts |
| Template (document blueprint) | A well-known subgraph that tickets enter when creating that document type |
| Document instance (CR-109) | A ticket whose cursor is traversing the CR subgraph |
| Execution item | A node in the graph |
| Gate / prerequisite | An edge condition — the cursor cannot traverse this edge until a condition is met |
| Evidence | A response collected by the ticket at a node |
| Review / approval cycle | A subgraph with reviewer and approver nodes |
| START_HERE.md decision tree | The literal start region of the graph |
| `qms_interact` prompts | The universal node interaction: node presents prompt, agent responds |
| Automated CLI side effects (ID assignment, audit entries, notifications, version increments) | Hooks — `on_enter`, `on_exit`, `on_traverse` actions bound to nodes and edges |
| Bootstrap workflow | The part of the graph that constructs new parts of the graph |

### What Remains

The ten design principles (P1–P10) from the workflow engine design remain valid — they describe properties the graph must have. The research synthesis (BPMN, Temporal.io, ALCOA+, van der Aalst patterns, etc.) remains relevant. The core behavioral requirements (ordering enforcement, evidence validation, deviation handling, audit trails) are unchanged. What changes is the *structure* — from engine-with-primitives to graph-with-cursors.

---

## 2. The Graph

### 2.1 What Is the Graph?

The QMS Graph is a directed graph where:

- **Nodes** are prompts. Each node carries: a prompt (what to present to the agent), an evidence schema (what the response must look like), and rendering metadata (how to display this node in context).
- **Edges** are transitions. Each edge carries: a condition (what must be true to traverse it), and optionally a label (the choice that selects this edge when multiple outgoing edges exist).
- **Subgraphs** are named regions. A subgraph is a connected subset of nodes with a designated entry node and one or more exit nodes. Subgraphs can be nested. What we currently call "SOPs," "templates," and "workflows" are all subgraphs.

The graph is not a tree — it has convergence points, loops (with gates preventing infinite traversal), and cross-references between subgraphs. A ticket in the CR subgraph might need to briefly enter the SDLC subgraph to satisfy a qualification gate, then return.

**Physical representation — two options under consideration:**

**Option A: Two-layer hybrid (Python infrastructure + data templates).**
- **Infrastructure layer (Python code):** Core routing, lifecycle state machines, review/approval cycles, deviation handling. These are the load-bearing walls — rarely changing, needing complex gate logic, benefiting from being testable.
- **Template layer (YAML/JSON data):** Document-type-specific subgraphs — step definitions, evidence schemas, ordering. More frequently changing, primarily declarative, creatable by the construction vehicle (see Section 6).
- The engine loads both layers and merges them into a unified runtime graph. Simple gate conditions live in data. Complex gates are Python code.
- **Tradeoff:** Infrastructure changes require code changes (slower improvement velocity, but more expressive for complex logic). Template changes are data changes (faster, construction-vehicle-compatible).

**Option B: Fully file-based schema (engine is Python, graph is entirely data).**
- **The engine** is Python code — a graph traversal interpreter that reads, evaluates, and renders.
- **The graph** is entirely defined in files (YAML/JSON). Every node, edge, subgraph, and gate binding is data. The file structure IS the graph structure:

```
graph/
  start.yaml
  change-control/
    entry.yaml
    code-cr/
      drafting/
        title.yaml
        scope.yaml
        extension-point.yaml
      execution/
        pre-commit.yaml
        run-ci.yaml
        update-rs.yaml
        merge.yaml
        post-commit.yaml
      review/
        ...
  deviation/
    classify.yaml
    inline-resolution.yaml
    spawn-investigation.yaml
  review-cycle/
    assign-reviewers.yaml
    review.yaml
    synchronization-gate.yaml
  approval/
    approve.yaml
    reject.yaml
```

- **Complex gate conditions** use a named-function registry. The gate *logic* is Python (shipped with the engine). The gate *binding* (which gate applies to which edge) is data:

```yaml
# graph/change-control/code-cr/execution/update-rtm.yaml
node:
  id: code-cr.execution.update-rtm
  prompt: "Update RTM with verification evidence"
  gates:
    - function: rs_is_effective
    - function: qualified_commit_exists
```

```python
# engine/gates.py (the registry — part of the engine, not the graph)
@gate("rs_is_effective")
def rs_is_effective(ticket, context):
    rs_doc = context.find_rs_for(ticket)
    return rs_doc.status == "EFFECTIVE"
```

- **Simple edge conditions** (comparing responses to values) could use inline expressions:

```yaml
edges:
  - to: inline-resolution
    condition: "response.severity == 'minor'"
  - to: spawn-investigation
    condition: "response.severity in ('major', 'critical')"
```

- **Advantages over Option A:**
  - The construction vehicle is universal — ALL graph modifications (including review cycles, deviation handling, the start region) are data changes that go through the same construction vehicle. No privileged layer requiring code changes.
  - The graph is browsable: `ls graph/deviation/` shows the deviation subgraph. `grep -r "prompt:" graph/` finds all prompts. Reviewers and auditors can inspect the QMS without running code.
  - Git diffs of graph changes are human-readable YAML diffs, not code diffs.
  - Each subgraph is a directory, naturally decoupled. Testable in isolation.
  - The bootstrap base case shrinks: only the engine (a small, stable interpreter) requires code changes. The entire graph topology is modifiable through the construction vehicle.
  - Analytics metadata can live as sidecar files alongside graph nodes, extending the existing QMS sidecar pattern.
  - Addresses the ossification risk: improvement velocity is uniform across the entire graph, not split between a fast template layer and a slow infrastructure layer.

- **Tradeoff:** Gate functions that reference external state still require Python code in the engine's registry. Adding a *new type* of gate check requires an engine update. But applying existing gate types to new edges is purely a data change.

Both options are version-controlled in git. Both support the construction vehicle pattern (Option A for the template layer only; Option B for the entire graph). The decision affects how much of the graph is modifiable through the graph's own mechanisms — Option B maximizes this, which strengthens the recursive self-improvement loop but requires a well-designed gate function registry and expression language.

### 2.2 The Start Region

The root of the graph is what START_HERE.md describes today: a decision tree that routes agents to the right place.

```
[START]
  "What would you like to do?"
    → "Make a change"        → [CHANGE_CONTROL entry]
    → "Investigate a problem" → [DEVIATION_MANAGEMENT entry]
    → "Review something"      → [REVIEW entry]
    → "Define a new process"  → [TEMPLATE_AUTHORING entry]
    → "I'm lost"              → [ORIENTATION subgraph]
```

Today this is a markdown file that agents read and interpret. In the graph, it's the literal topology — the agent doesn't interpret anything, they respond to the prompt and the cursor moves.

### 2.3 Subgraph Examples

**The Change Control subgraph** (currently SOP-002 + TEMPLATE-CR):
```
[CHANGE_CONTROL entry]
  "What kind of change?"
    → "Code change"      → [CODE_CR subgraph entry]
    → "Process change"   → [PROCESS_CR subgraph entry]
    → "Document update"  → [DOC_CR subgraph entry]

[CODE_CR subgraph]
  → "Title?" → "Scope?" → "Execution items?"
  → [REVIEW_CYCLE subgraph]
  → [PRE_APPROVAL subgraph]
  → [EXECUTION subgraph]
    → "Pre-execution commit" (gate: auto)
    → "Create execution branch"
    → "Implement changes"
    → "Run CI" (gate: implementation complete)
    → "Update RS" (gate: CI passes)
    → "Update RTM" (gate: RS EFFECTIVE, qualified commit exists)
    → "Merge to main" (gate: RS EFFECTIVE, RTM EFFECTIVE, CI green)
    → "Post-execution commit" (gate: merge complete)
  → [POST_REVIEW subgraph]
  → [CLOSURE]
```

**The Review Cycle subgraph** (currently SOP-001 §9):
```
[REVIEW_CYCLE entry]
  → [ASSIGN_REVIEWERS] (performer: quality)
    "Assign reviewers for this document"
  → [PARALLEL_REVIEW] (one cursor per reviewer)
    Each reviewer: "Read document. Recommend or request updates?"
      → "recommend" → [REVIEW_COMPLETE for this reviewer]
      → "request-updates" → [FEEDBACK node] → back to initiator
  → [SYNCHRONIZATION_GATE] (all reviewers must reach REVIEW_COMPLETE)
  → [REVIEW_CYCLE exit]
```

**The Deviation Handling subgraph** (currently SOP-003 + SOP-004 §9A):
```
[DEVIATION entry]
  "What happened?"
  → "Classify: minor / major / critical"
    → minor: [INLINE_RESOLUTION]
      "Describe the fix" → "Evidence of fix" → [DEVIATION exit]
    → major/critical: [SPAWN_CHILD_WORKFLOW]
      Creates a new ticket for INV/VAR → parent cursor waits at gate
```

### 2.4 Graph Properties

**Deterministic routing.** At every node, the set of outgoing edges is fully defined. The agent never needs to decide "what do I do next" — the graph tells them. If there's a choice, the node presents it as a prompt.

**Gate enforcement.** Edge conditions are evaluated by the engine. If an edge's condition is not met, the cursor cannot traverse it. This is how ordering constraints, prerequisite requirements, and approval gates work. The agent doesn't need to know the gate logic — they see "blocked: waiting on X."

**Subgraph composability.** Any subgraph can reference any other subgraph as a "call" — the cursor enters the called subgraph, traverses it, and returns to the calling subgraph at the exit point. This is how the review cycle, approval cycle, and SDLC qualification chain are reused across document types.

**Self-modification under control.** The graph includes subgraphs for modifying itself (template authoring, SOP revision). These subgraphs route through review and approval gates before changes take effect. The graph governs its own evolution — the recursive governance loop is a topological property, not a philosophical principle.

### 2.5 Hooks: Automated Actions

Gates control whether the cursor *can* move. Hooks control what *happens* when it does. Hooks are commands that the engine executes automatically when the cursor reaches specific points in the graph. The agent does not invoke them — they fire as side effects of traversal.

**Three hook points:**

| Hook | Fires when | Use case |
|------|-----------|----------|
| `on_enter` | Cursor arrives at a node (before prompt is presented) | Assign document ID, create audit entry, check preconditions, prepare context |
| `on_exit` | Cursor leaves a node (after response is collected) | Log response, send signals to other tickets, update external state |
| `on_traverse` | Cursor crosses an edge | Increment version, archive previous version, send notifications, trigger CI |

**Node hooks:**

```yaml
node:
  id: code-cr.execution.run-ci
  prompt: "Run the CI pipeline and provide the results"
  hooks:
    on_exit:
      - command: "python -m pytest --ci"
        on_failure: block
```

**Edge hooks:**

```yaml
edge:
  from: execution.complete
  to: post-review.entry
  hooks:
    on_traverse:
      - command: "qms checkin {ticket.doc_id}"
      - command: "qms route {ticket.doc_id} --review"
```

**Examples of what hooks automate:**

| Agent would normally type... | Hook equivalent |
|-----------------------------|-----------------|
| `qms checkout CR-109` | `on_enter` hook at drafting entry: `qms checkout {ticket.doc_id}` |
| `qms checkin CR-109` | `on_exit` hook at drafting exit: `qms checkin {ticket.doc_id}` |
| `qms route CR-109 --review` | `on_traverse` hook on edge to review subgraph: `qms route {ticket.doc_id} --review` |
| `git checkout -b cr-109/execution` | `on_enter` hook at execution entry: `git checkout -b {ticket.doc_id}/execution` |
| `git checkout main && git merge cr-109/execution` | `on_exit` hook at merge step: `git checkout main && git merge {ticket.branch}` |
| `python -m pytest` | `on_exit` hook at CI step: `python -m pytest --ci` |

**What hooks do NOT handle (engine or CLI responsibilities):**

| Automated behavior | Owner | Why not a hook |
|-------------------|-------|---------------|
| Document ID assignment | Engine | Happens when ticket is created — no agent command equivalent |
| Audit trail entries | Engine | Happens on every cursor movement — intrinsic to traversal |
| Version increment on approval | CLI (`qms approve`) | Already a side effect inside the approve command |
| Archive on supersede | CLI (`qms checkin`) | Already a side effect inside the checkin command |
| Inbox notifications | CLI (`qms route`, `qms assign`) | Already a side effect inside routing commands |

**The boundary principle: hooks operate at the agent-action level.**

A hook can do anything an agent could do by typing a command in a terminal. A hook does NOT replicate logic that already lives inside those commands or inside the engine itself. This prevents the graph from absorbing the CLI — instead, the graph *orchestrates* it.

Three categories of automated behavior, with clear ownership:

| Category | Owner | Examples |
|----------|-------|---------|
| **Graph traversal mechanics** | Engine (Python code) | Cursor movement, gate evaluation, prompt presentation, audit trail entries, ticket creation, document ID assignment |
| **Document lifecycle operations** | QMS CLI (existing commands) | Checkout/checkin (with archive-on-supersede), route (with inbox notifications), approve (with version increment), all internal side effects |
| **Orchestration of agent-level actions** | Hooks (graph data) | Invoking CLI commands and bash commands at specific graph points — automating what an agent would otherwise type manually |

**Valid hooks** (things an agent could type):
```yaml
hooks:
  on_exit:
    - command: "qms checkout {ticket.doc_id}"
    - command: "git checkout -b {ticket.doc_id}/execution"
    - command: "qms checkin {ticket.doc_id}"
    - command: "qms route {ticket.doc_id} --review"
    - command: "python -m pytest"
    - command: "gh pr create --title '{ticket.title}'"
```

**NOT hooks** (these belong to the engine or CLI internals):
- `assign_document_id` — engine responsibility when creating a ticket
- `create_audit_entry` — engine responsibility on every cursor movement
- `archive_previous_version` — already a side effect inside `qms checkin`
- `increment_version` — already a side effect inside `qms approve`
- `send_inbox_notification` — already a side effect inside `qms route` / `qms assign`
- `update_metadata` — already a side effect of various CLI commands

**Why this boundary matters:**
- It keeps the hook vocabulary bounded and predictable (CLI commands + bash commands)
- It prevents the graph from becoming a reimplementation of the CLI
- It preserves the CLI's internal logic (archive, version, audit) without duplication
- It means hooks are testable: you can verify a hook by running the same command manually
- It means ANY command-line tool is hookable — not just QMS commands, but git, CI, testing frameworks, etc.

**Hooks are invisible to the agent.** The agent sees prompts and responds. Hooks fire silently in the background, automating the mechanical command sequences that agents currently must remember. An agent at the "execution complete" node doesn't need to know that `qms checkin` and `qms route --review` just ran — they see the next prompt.

**Hook failure:** If a hook's command fails, the engine must decide: block or continue. Each hook declares its failure mode:

```yaml
hooks:
  on_exit:
    - command: "python -m pytest"
      on_failure: block     # cursor does not advance until tests pass
    - command: "echo 'Step completed' >> log.txt"
      on_failure: log       # cursor advances, failure is logged
```

---

## 3. The Ticket

### 3.1 What Is a Ticket?

A ticket is an object that rides on top of the graph. It does not modify the graph by default — it collects responses as it traverses. Think of it as a train on tracks: it carries passengers (evidence) but takes power from the third rail (prompts from nodes).

A ticket has:

```yaml
ticket:
  id: TICKET-001
  owner: claude                    # who is driving
  cursor: CODE_CR.EXECUTION.step_4 # where in the graph
  state: active                    # active, waiting, completed
  created: 2026-03-05T10:00:00Z

  # Everything collected during traversal
  responses:
    - node: CHANGE_CONTROL.type
      value: "Code change"
      timestamp: 2026-03-05T10:00:05Z
    - node: CODE_CR.title
      value: "Add particle collision detection"
      timestamp: 2026-03-05T10:00:12Z
    - node: CODE_CR.EXECUTION.step_3
      value: { commit: "abc1234", description: "Implemented collision..." }
      timestamp: 2026-03-05T11:30:00Z

  # Child tickets spawned during traversal
  children:
    - TICKET-002  # VR spawned at step 5
```

### 3.2 The Ticket Lifecycle

```
qms start
  → navigation session begins (no ticket yet)
  → start region presents routing prompts
  → agent responds, cursor advances through start region

agent reaches a document subgraph entry (e.g., CODE_CR)
  → CR-109 created (ticket with document identity)
  → cursor placed at first node of the CR subgraph
  → node presents first prompt

agent responds
  → response saved to ticket
  → cursor advances along matching edge
  → next node presents next prompt

... repeat ...

cursor reaches terminal node
  → ticket state = completed
  → ticket is a permanent record (the closed document)
```

### 3.3 Ticket Identity

Every ticket IS a document. There are no bare tickets. The start region is a lightweight navigation session — no ticket, no persistence, no audit trail. The ticket is created at the moment the navigation session enters a document subgraph (CR, INV, VAR, etc.), and it is born with its document identity (CR-109, INV-015).

This means:
- No orphaned tickets from agents who navigate to START and disconnect
- No identity "promotion" — the ticket is CR-109 from the moment it exists
- The start region is disposable routing — "what do you want to do?" with no side effects
- The document IS the ticket, the ticket's collected responses ARE the document's content

### 3.4 The Ticket as Construction Vehicle

For normal traversal, the ticket passively collects responses while the graph supplies prompts. But certain subgraphs give the ticket **write access** to the graph itself:

- **Template authoring subgraph:** The cursor enters a region where each prompt asks "define a step" / "define a gate" / "define an evidence schema." The responses don't just get collected on the ticket — they get laid down as new nodes and edges in the graph.
- **SOP revision subgraph:** The cursor enters a region where existing nodes can be modified, reordered, or removed.
- **Graph maintenance subgraph:** Retiring old subgraphs, archiving unused paths.

In all cases, the modification is gated. The "lay down nodes" operation goes through the same review/approval subgraph as any other change. The construction vehicle has a permit system.

### 3.5 Ticket Properties vs. Node Properties

A critical distinction:

- **Node properties** belong to the graph. They persist across all tickets. They are the "template" — the instructions, the evidence schemas, the gate conditions. Modifying them requires the construction vehicle workflow.
- **Ticket properties** belong to the traversal. They are unique to this ticket. They are the responses, the evidence, the timestamps. They are written freely by the agent during normal traversal.

This replaces the template/instance distinction with something simpler: the graph is shared infrastructure, the ticket is this particular journey through it.

---

## 4. The Third Rail: How Nodes Supply Prompts

### 4.1 Node Anatomy

Every node in the graph has:

```yaml
node:
  id: code-cr.execution.run-ci
  subgraph: code-cr.execution

  # What the agent sees
  prompt: "Run the CI pipeline and provide the results"
  context: "The execution branch has been created and code changes committed."

  # What the agent must provide
  evidence_schema:
    ci_url: { type: url, required: true }
    ci_result: { type: enum, values: [pass, fail], required: true }
    ci_log_summary: { type: text, required: false }

  # Who can respond
  performer: initiator

  # Display
  phase: execution      # grouping label
  ordinal: 4            # position within phase

  # Automated actions (invisible to agent — see Section 2.5)
  # Hooks invoke agent-level commands, not engine internals
  hooks:
    on_exit:
      - command: "python -m pytest --ci"
        on_failure: block
```

### 4.2 What the Agent Sees

When a cursor arrives at a node, the agent sees a rendered view of their ticket — not the raw graph. The rendering shows:

```
CR-109 | Add particle collision detection
Status: IN_EXECUTION | Step 4 of 11

[completed] 1. Pre-execution commit
             Response: commit abc1234 on 2026-03-05
[completed] 2. Create execution branch
             Response: branch cr-109/collision-detection
[completed] 3. Implement code changes
             Response: collision detection module added (commit def5678)
> [active]  4. Run CI pipeline
             Provide: CI run URL, pass/fail result
             Hint: "The execution branch has been created and code changes committed."
  [blocked] 5. Update RS ← waiting on: step 4 (CI must pass)
  [blocked] 6. Update RTM ← waiting on: steps 4, 5
  [blocked] 7. Merge to main ← waiting on: steps 4, 5, 6
  ...

> _
```

The agent types their response. The engine validates it against the evidence schema. If valid, the response is saved to the ticket, and the cursor advances.

### 4.3 Conditional Nodes

Some nodes only activate based on previous responses:

```yaml
node:
  id: inv.immediate-containment
  condition: "responses['inv.classify'].severity in ('major', 'critical')"
  prompt: "Describe immediate containment actions taken"
```

If the condition is false, the cursor skips this node. The agent never sees it. This replaces the current system where agents must read SOP-003 to know that containment is only required for major/critical deviations.

### 4.4 Branching Nodes

Some nodes present choices that determine which edge the cursor follows:

```yaml
node:
  id: deviation.classify
  prompt: "Classify the deviation"
  evidence_schema:
    type: { type: enum, values: [procedural, product] }
    severity: { type: enum, values: [minor, major, critical] }

edges:
  - from: deviation.classify
    to: deviation.inline-resolution
    condition: "response.severity == 'minor'"
  - from: deviation.classify
    to: deviation.spawn-investigation
    condition: "response.severity in ('major', 'critical')"
```

The agent doesn't need to know what happens next. They answer the prompt. The graph routes them.

---

## 5. Concurrent Actors: Delegation, Not Forking

### 5.1 The Problem

Many QMS workflows involve multiple actors: an initiator drafts, QA assigns reviewers, reviewers review, QA approves. A single cursor owned by a single agent can't model this.

### 5.2 The Delegation Model

The initiator doesn't split into multiple selves — they *delegate* to other actors and wait. The model:

- A ticket has one **primary cursor** (the initiator's). This is the driver.
- At delegation nodes, the ticket creates **task cursors** — lightweight, scoped assignments for other actors.
- Task cursors have a narrow scope: "review this document," "approve this document," "assign reviewers."
- The primary cursor waits at a gate until task cursors resolve.
- Task cursors appear in actors' inboxes. Actors advance them by responding.
- When all task cursors resolve, the gate opens and the primary cursor resumes.

```
[REVIEW_CYCLE entry]
  primary cursor pauses at gate

  task cursor created → QA: ASSIGN_REVIEWERS
    QA responds (assigns tu_ui, tu_scene)
    → QA task cursor completes
    → spawns reviewer task cursors

  task cursor created → tu_ui: REVIEW
  task cursor created → tu_scene: REVIEW
    Each reviewer responds (recommend / request-updates)
    → reviewer task cursors complete

[SYNCHRONIZATION_GATE]
  condition: all task cursors resolved
  → primary cursor resumes
```

This preserves the "one driver" model. The ticket belongs to the initiator. Other actors contribute via tasks, not by sharing ownership.

### 5.3 What Actors See

**QA sees (in inbox):**
```
CR-109 | Task: Assign reviewers
  "Assign reviewers for CR-109"
  > _
```

**Reviewer sees (in inbox, after QA assigns):**
```
CR-109 | Task: Review
  "Read document. Recommend or request updates?"
  [Full ticket responses visible for context]
  > _
```

**Initiator sees:**
```
CR-109 | Waiting for review
Your cursor: REVIEW_GATE (blocked)
  Waiting on: tu_ui review, tu_scene review
  [No action available]
```

### 5.4 Inbox as Task Cursor Query

The inbox becomes trivially simple: `qms inbox` returns "all task cursors assigned to me that are awaiting my response." No special inbox infrastructure needed — just a query over active task cursors.

---

## 6. The Construction Vehicle: Graph Modification

The construction vehicle operates at two levels: **permanent modification** (changing the shared graph for all future tickets) and **local extension** (adding ticket-scoped nodes for this ticket only). Both use the same interactive prompting pattern, but they produce different artifacts.

### 6.1 Read-Only Traversal (Default)

Normal ticket operation is read-only with respect to the graph. The ticket collects responses, the graph supplies prompts. 99% of QMS activity is this mode.

### 6.2 Local Extension: Ticket-Scoped Nodes (Instance Drafting)

When an agent creates a CR, the CR subgraph contains template-defined nodes (invariant steps) and **extension points** where the author adds custom steps. The custom steps become **ticket-scoped nodes** — they exist only for this ticket's traversal, not in the permanent graph.

```
CR subgraph (permanent graph):
  [pre-execution-commit]      ← template node, invariant
  [EXTENSION_POINT]           ← "Define your execution items"
  [post-execution-commit]     ← template node, invariant

CR-109 local view after drafting:
  [pre-execution-commit]       source: template
  [implement-collision]         source: author (ticket-scoped)
  [run-ci]                      source: author (ticket-scoped)
  [update-rs]                   source: author (ticket-scoped)
  [update-rtm]                  source: author (ticket-scoped)
  [merge-to-main]               source: author (ticket-scoped)
  [post-execution-commit]      source: template
```

The execution engine sees a uniform sequence of nodes. It doesn't care whether a node is from the permanent graph or ticket-scoped. The cursor traverses them identically.

**The drafting interaction:**

```
CR-109 | Drafting
Template steps (cannot be removed):
  1. Pre-execution commit [auto]
  7. Post-execution commit [auto]

Your execution items (between template steps):
  [none yet]

> Add an execution item?
  Name: _
```

```
> "Implement collision detection"

  What evidence will this step produce?
  > "Commit hash, description of changes"

  Any prerequisites?
  > "No"

Step added. Current plan:
  1. Pre-execution commit [template]
  2. Implement collision detection [you]
  7. Post-execution commit [template]

> Add another?
```

The agent builds their execution plan interactively, seeing the template's invariant steps as fixed scaffolding and their own steps filling in between.

**Mutability rules:**
- **Template nodes** cannot be removed or reordered. They're inherited from the permanent graph.
- **Author nodes** can be added, removed, and reordered during drafting. They're ticket-scoped.
- **At pre-approval**, the ticket's local view is frozen. Both template and author nodes become immutable. Only evidence fields remain writable during execution.

"Pre-approval" has a clean graph meaning: **the ticket's local graph view becomes read-only.**

### 6.3 Permanent Modification: Draft Graph Overlay (Template Authoring)

When the construction vehicle modifies the permanent graph (creating a template, revising an SOP), the new nodes don't go live immediately. They exist as a **draft graph overlay** — a proposed diff, like a git branch.

The flow:

1. Agent enters the template authoring subgraph (authorized by a CR)
2. The engine creates a **draft overlay** — a set of proposed additions/modifications to the permanent graph
3. The agent's prompts ("define step 1," "define step 2") create nodes in the overlay
4. The agent previews the result (the engine renders the subgraph as if the overlay were applied)
5. The authoring CR goes through review/approval
6. Upon approval, the overlay is applied to the permanent graph → version increment

```
[TEMPLATE_AUTHORING entry]
  "What kind of workflow are you defining?"
  → "Investigation" → target_subgraph: inv

  "What is the first step?"
    Step name: _
    → agent responds: "Document the deviation"
    → OVERLAY: create node(id: inv.step-1, prompt: "Document the deviation")

  "Who performs this step?"
    Performer: _
    → agent responds: "initiator"
    → OVERLAY: update node(inv.step-1, performer: initiator)

  "What evidence is needed?"
    Evidence: _
    → agent responds: "Description of what happened, when, affected systems"
    → OVERLAY: update node(inv.step-1, evidence_schema: {description: text, ...})

  "Any prerequisites for this step?"
    → agent responds: "No, this is always first"
    → OVERLAY: create edge(inv.entry → inv.step-1, condition: none)

  "Add another step?"
    → "Yes" → loop
    → "No" → [REVIEW/APPROVAL subgraph for the overlay]
```

During authoring, no other ticket can see the draft nodes. The overlay exists only in the context of the authoring ticket. Upon approval, the overlay merges into the permanent graph — identical to how `git branch` → `git merge` works, and how the current QMS checkout/checkin works.

The responses serve double duty: they're collected on the ticket (as a record of the authoring session) AND they define the overlay (the proposed graph changes). The overlay is stored as ticket data — the authoring ticket's responses include the complete definition of every new node.

### 6.4 Two Levels of Modification — Summary

| Level | What changes | Scope | Approval needed | Example |
|-------|-------------|-------|-----------------|---------|
| **Local extension** | Ticket-scoped nodes added to this ticket's local view | This ticket only | Pre-approval of the ticket itself | Adding custom EIs to a CR |
| **Permanent modification** | New nodes/edges added to the permanent graph via overlay | All future tickets | Full CR review/approval cycle | Creating a new template, revising an SOP |

The agent interacts with both levels through the same prompting pattern. The engine knows which level is active based on the subgraph the cursor is in (drafting region = local extension, template authoring region = permanent modification).

### 6.5 Graph Versioning

Since the graph IS the QMS, modifying it is a controlled change. Permanent graph modifications:

1. Are proposed as a diff overlay (new nodes, modified nodes, new edges, removed edges)
2. Go through the review/approval subgraph (the same one used for documents)
3. Are applied atomically — the graph transitions from version N to version N+1
4. Are recorded in the audit trail

The graph version maps naturally to git: the graph definition files (Python infrastructure + YAML/JSON template data) are version-controlled. "Graph v47" is the graph as defined at a specific git commit. Template changes go through CRs, which produce commits, which produce new graph versions. No separate version tracking infrastructure is needed — git provides it.

### 6.6 Tickets In-Flight During Graph Changes

**Rule: tickets are bound to the graph version at their creation.** TICKET-001, created under graph v47, continues traversing v47 even after v48 becomes effective. This is identical to how the current QMS works: a CR pre-approved under SOP-001 v20.0 continues under v20.0 even if SOP-001 is revised to v21.0 during execution.

New tickets created after the graph update traverse v48. The ticket records which graph version it's bound to, ensuring reproducibility.

---

## 7. How Current QMS Concepts Map to the Graph

### 7.1 Documents

| Current concept | Graph equivalent |
|----------------|-----------------|
| CR-109 | A ticket whose cursor entered the CR subgraph |
| INV-015 | A ticket whose cursor entered the INV subgraph |
| CR-109-VAR-001 | A child ticket spawned by CR-109's cursor at a deviation node |
| SOP-001 v21.0 | Graph version in which the document-control subgraph was last modified |
| TEMPLATE-CR v10.0 | Graph version in which the CR subgraph was last modified |

### 7.2 Lifecycle States

| Current state | Graph equivalent |
|--------------|-----------------|
| DRAFT | Cursor is in the authoring region of a subgraph |
| IN_REVIEW | Cursor has forked into the review subgraph |
| REVIEWED | All review cursors have reached REVIEW_COMPLETE |
| IN_APPROVAL | Cursor has entered the approval subgraph |
| PRE_APPROVED | Cursor has passed the approval gate |
| IN_EXECUTION | Cursor is in the execution region |
| POST_REVIEWED | Cursor has re-entered review subgraph after execution |
| POST_APPROVED | Cursor has passed post-execution approval gate |
| CLOSED | Cursor has reached a terminal node |

The state is not stored as metadata — it is *derived from cursor position*. A ticket is "IN_REVIEW" because its cursor is in the review subgraph. The state IS the position.

### 7.3 The CLI / MCP Interface

The entire CLI simplifies:

| Current command | Graph equivalent |
|----------------|-----------------|
| `qms start` | Begin navigation session (no ticket yet), route through start region |
| `qms interact --respond "..."` | Advance the cursor by responding to the current node's prompt |
| `qms status CR-109` | Query: where is CR-109's cursor? What node is it on? |
| `qms inbox` | Query: which task cursors are assigned to me and awaiting my response? |
| `qms route --review` | Eliminated — the cursor enters the review subgraph automatically when the drafting region is complete |
| `qms checkout / checkin` | Potentially eliminated — the cursor's position in the graph implies editability |
| `qms create CR --title "..."` | Eliminated — `qms start` routes you to CR creation through the start region |

Most commands collapse into variations of `qms start` and `qms respond`. The agent's entire interface is:

1. **Where am I?** → `qms status DOC-ID`
2. **What's being asked of me?** → the prompt at the current node
3. **Here's my answer.** → `qms respond "..."`

### 7.4 The Audit Trail

Every cursor movement is an audit event:

```jsonl
{"ticket": "TICKET-001", "node": "code-cr.execution.step-4", "action": "respond", "performer": "claude", "value": {"ci_url": "...", "ci_result": "pass"}, "timestamp": "2026-03-05T12:00:00Z", "graph_version": "47.0"}
```

ALCOA+ compliance is structural:
- **Attributable:** ticket.owner and cursor.performer
- **Contemporaneous:** timestamp at response time
- **Original:** append-only event log
- **Accurate:** response validated against node's evidence schema
- **Complete:** cursor cannot advance without valid response
- **Consistent:** graph_version pins the rules in effect
- **Enduring:** event log is immutable
- **Available:** any actor can query ticket state

---

## 8. The Rendered View

### 8.1 The Universal View

Regardless of where a cursor is — authoring, execution, review, template creation — the rendered view follows the same pattern:

```
{DOCUMENT_ID} | {Title}
Status: {derived from cursor position} | Step {N} of {M}

[completed] 1. {step name}
             Response: {collected evidence summary}
[completed] 2. {step name}
             Response: {collected evidence summary}
> [active]  3. {step name}
             {prompt from current node}
             Evidence needed: {evidence schema description}
  [blocked] 4. {step name} ← {gate condition description}
  [pending] 5. {step name}

> _
```

This view works for:
- An initiator executing a CR (steps are execution items)
- A reviewer reviewing a CR (steps are review criteria)
- A template author defining a workflow (steps are "define step 1," "define step 2")
- QA assigning reviewers (steps are assignment actions)
- An investigator analyzing a deviation (steps are investigation phases)

One view. Every context. The agent always knows: what's done, what's now, what's next.

### 8.2 Contextual Information

The rendered view can include contextual information drawn from the graph:

- **Hints** from the node: "Remember to include the commit hash from the CI run"
- **Cross-references** from signals: "RS version: 22.0 (EFFECTIVE as of 2026-03-04)"
- **Child ticket status**: "VAR-001: IN_EXECUTION (step 2 of 5)"
- **Gate explanations**: "Blocked: RTM cannot be updated until RS is EFFECTIVE and a qualified commit exists"

The agent never navigates to other documents to check status. The rendered view pulls everything relevant from the graph and presents it in context.

---

## 9. Open Questions — Analysis and Resolutions

### Q1: Graph Storage and Representation — OPEN: Two Options

Two approaches are under consideration (detailed in Section 2.1):

**Option A: Two-layer hybrid (Python infrastructure + data templates).** Infrastructure (review cycles, deviation handling, lifecycle state machines) is Python code. Templates (document-type-specific steps and evidence schemas) are YAML/JSON data. The construction vehicle modifies the template layer; infrastructure changes require code changes. Maps to how the current QMS works (SOPs are "infrastructure," templates are "data").

**Option B: Fully file-based schema.** The engine is Python (a small interpreter). The entire graph — including review cycles, deviation handling, the start region — is YAML/JSON data organized as a directory structure that mirrors graph topology. Complex gate conditions use a named-function registry (logic in Python, binding in data). The construction vehicle can modify ANY part of the graph, not just templates.

**Key tradeoff:** Option A is more conventional and limits blast radius (infrastructure changes require engineering review). Option B maximizes the recursive self-improvement loop (the entire graph is modifiable through the graph's own mechanisms) but requires a well-designed gate function registry and expression language for edge conditions.

**Leaning toward:** Option B, because it strengthens the recursive governance loop, makes the graph browsable/inspectable as files, produces human-readable git diffs, and shrinks the bootstrap base case to just the engine. But this needs validation through prototyping — particularly the expression language for edge conditions and the gate function registry pattern.

### Q2: Ticket Identity — RESOLVED: No Bare Tickets

**Resolution: The start region is a navigation session, not a ticket.**

`qms start` begins an interactive routing session — stateless navigation through the start region. No ticket is created. No audit trail. No persistence. It's just "what do you want to do?"

The ticket is created at the moment the routing produces a decision: "I need a code CR." At that moment, CR-109 is born — a ticket with document identity, cursor position, and audit trail. There are no "bare tickets" in the system.

This means:
- Every ticket IS a document. No exceptions, no orphans.
- The routing session is lightweight and disposable.
- Identity assignment is simultaneous with ticket creation.
- No promotion, no ambiguous pre-document state.

This loses the theoretical elegance of "everything is a ticket" but gains practical cleanliness.

### Q3: Concurrent Cursors — RESOLVED: Delegation Model

Resolved in Section 5. One primary cursor per ticket. Task cursors for delegation to other actors. Child tickets for true parallelism (VARs, child CRs).

### Q4: Graph Versioning — RESOLVED: Git IS the Version

**Resolution: Graph versioning collapses into git versioning.**

The graph definition files (Python infrastructure + YAML/JSON template data) are version-controlled in git. "Graph v47" is the graph as defined at a specific git commit. Template changes go through CRs, which produce commits, which produce new graph versions.

A ticket records the git commit hash it was created under, binding it to a specific graph snapshot. No separate version tracking infrastructure is needed.

Atomic versioning is correct — a single commit represents a single graph state. The commit message and CR record what specifically changed.

### Q5: Documents as Rendered Output — RESOLVED

**Resolution: Markdown is an export format, not the source of truth.**

The canonical representation of a document is: ticket (responses) + graph (structure at bound version). The rendering engine produces:
- A live rendered view (what agents see during interaction)
- A markdown export (for human review, archival, external sharing)
- Potentially other formats (PDF for regulatory, JSON for machine consumption)

This is what CR-107's Jinja2 engine was designed for — it just gets a cleaner input (structured ticket data) instead of a messier one (markdown with frontmatter and metadata sidecars).

### Q6: Relationship to qms_interact — RESOLVED: Direct Evolution

**Resolution: Build the graph engine as an evolution of `qms_interact`.**

The current system already implements: present prompt → collect response → advance → repeat. The additions needed:
1. Graph topology (branching based on responses, convergence points)
2. Gate evaluation (check edge conditions before advancing)
3. Task cursor creation (delegation to other actors)
4. Ticket-scoped nodes (local extension during instance drafting)
5. Draft overlay management (permanent modification during template authoring)

The core loop doesn't change — it gains awareness of topology.

### Q7: Backwards Compatibility — RESOLVED: Clean Break with Bridge

**Resolution: Clean break for new work, bridge period for in-flight documents.**

Existing in-flight documents (CR-108, legacy INVs/VARs) complete under the old system. New work starts on the graph. Historical documents are archived artifacts, not migrated graph traversals.

The bridge period lasts until all in-flight old-system documents reach terminal state. During that time, old CLI commands coexist with graph commands. Once all old documents are closed/retired, the old system can be decommissioned.

### Q8: How Does the Start Region Actually Work? — NEW, OPEN

With Q2 resolved (no bare tickets, start region is a navigation session), a new question emerges: what is the start region, mechanically?

- Is it part of the graph (a subgraph with no ticket)?
- Is it a separate routing layer outside the graph?
- Does it share the same engine (prompt → response → advance) or is it a simpler dispatcher?

**Preliminary thinking:** It should use the same engine for consistency (P10: one interaction model). But it doesn't create audit entries or persist state. It's a "lightweight traversal" mode — same navigation mechanics, no ticket, no persistence. The engine supports two modes: persistent (with ticket) and ephemeral (without).

### Q9: Extension Points in Templates — NEW, OPEN

Section 6.2 introduces extension points where authors add ticket-scoped nodes. But how flexible are these?

- Can the author add steps before the first template step? After the last?
- Can the author add steps between any two template steps, or only at designated extension points?
- Can there be multiple extension points in a single template (e.g., one for implementation, one for verification)?
- Can the author define gates between their custom steps?

**Preliminary thinking:** Extension points are designated positions in the template subgraph. The template author explicitly places them: "authors can add steps here." This gives template designers control over where customization is allowed. Multiple extension points per template are supported. Authors can define ordering between their own custom steps but cannot create gates that reference template steps (to prevent coupling).

### Q10: Evidence Schema Language — NEW, OPEN

Nodes declare evidence schemas. What language describes these schemas?

- Simple type system: `text`, `url`, `commit_hash`, `enum(values)`, `bool`, `date`, `doc_id`
- Compound types: `list(text)`, `{field: type, field: type}`
- Validation rules: `required`, `pattern(regex)`, `references(doc_type, status)`

**Preliminary thinking:** Start minimal. The prototype needs `text`, `enum`, `bool`, and `doc_id`. Compound types and validation rules can be added incrementally. The evidence schema should be expressive enough that the rendered view can generate meaningful prompts ("Provide: commit hash, pass/fail result") but simple enough that template authors can define schemas through the interactive prompting pattern without learning a schema language.

---

## 10. The Three-Sentence Pitch

The entire QMS is a single graph. An agent starts a ticket, which places a cursor on the graph, and the agent advances by answering prompts supplied by each node — like a train taking power from the third rail. The cursor can also lay down new track (with approval), making the graph self-constructing and self-governing.

---

## 11. Relationship to Previous Design Work

### From workflow-engine-design.md

The five primitives (WorkflowTemplate, WorkflowInstance, Step, Gate, Signal) collapse:
- **WorkflowTemplate** → a subgraph
- **WorkflowInstance** → a ticket traversing that subgraph
- **Step** → a node
- **Gate** → an edge condition
- **Signal** → a response on one ticket that satisfies a gate condition on another ticket's edge

The ten design principles (P1–P10) remain valid. The research synthesis remains relevant. The behavioral requirements are unchanged. The structure is simpler.

### From the DocuBuilder Prototype

The prototype's key concepts carry forward:
- **enforce/locked** → node properties (the graph defines what's fixed; the ticket defines what's writable)
- **Sequential execution with cascade revert** → cursor position and graph topology
- **Prerequisites** → edge conditions (gates)
- **Audit trail** → cursor movement log
- **Checkout/checkin** → cursor position implies editability (may be eliminatable)

### From CR-107 (Unified Document Lifecycle)

CR-107's Jinja2 rendering engine becomes the **rendered view generator** — it produces the visual representation of a ticket's state on the graph. The "universal source file" concept maps to the ticket's response collection. The "spectrum model" (static ↔ dynamic content) maps to the node property / ticket property distinction.

### From CR-106 (System Governance)

CR-106's system qualification workflow becomes a subgraph. The qualification gate (RS EFFECTIVE + RTM EFFECTIVE + CI green + qualified commit) becomes a set of edge conditions. The system checkout/checkin model maps to a cursor entering/exiting the system-modification subgraph.
