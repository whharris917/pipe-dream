# The Tool-Free QMS

## Context

This document captures an insight from Session-2026-02-27-001 that extends the frontmatter-driven interaction design to its logical endpoint: the QMS does not require a CLI. The entire system can be reduced to file edits and file moves — literal paper-pushing.

---

## The Observation

If the frontmatter-driven interaction design is taken to its limit, every QMS operation reduces to one of three primitive file operations:

1. **Read** a file (check inbox, see current prompt)
2. **Edit** a file (fill in frontmatter, write inline responses)
3. **Move** a file (put it in your outbox)

No CLI commands. No MCP tools. No API. No special protocols. The process is the documents and the conventions they encode.

---

## CLI Commands as File Operations

Every existing CLI command maps to a file operation:

| CLI Command | File Operation | What Makes It Happen |
|---|---|---|
| `qms create {TYPE}` | Copy template into workspace | Template is the starting point |
| `qms checkout {DOC}` | Document appears in inbox/workspace | Routing puts it there |
| `qms checkin {DOC}` | Move document to outbox | Outbox triggers processing |
| `qms route --review` | Move finished document to outbox | Document state (all fields complete) + outbox = "route for review" |
| `qms route --approval` | Move reviewed document to outbox | Document state (reviewed) + outbox = "route for approval" |
| `qms interact --respond` | Edit the document, move to outbox | Same cycle as everything else |
| `qms review --recommend` | Reviewer moves document to their outbox | Review decision is in the document |
| `qms approve` | Approver moves document to their outbox | Approval decision is in the document |
| `qms inbox` | List files in inbox folder | `ls` |
| `qms status {DOC}` | Read the document's frontmatter | `cat` |

The CLI is a convenience layer that validates and logs these operations. The process itself doesn't require it.

---

## The Infrastructure: One Mail Clerk

The only piece of infrastructure needed is the equivalent of a mail clerk — something that watches outbox folders and performs the routing:

1. **Pick up** documents from outboxes
2. **Validate** the document state (are required fields populated? is the tier 3 sequence respected?)
3. **Record** the transaction (timestamps, audit trail, amendment history)
4. **Route** the document to the next inbox (based on document state and workflow conventions)
5. **Render** the next view (re-render the Jinja2 template with updated data)

This could be a daemon, a cron job, a filesystem watcher, or even another AI agent whose sole job is checking outboxes. The mail clerk is stateless — it reads the document, does its job, and forgets. If it crashes, the documents are still in the outboxes. A new mail clerk picks them up.

The current QMS CLI is this mail clerk, but it runs synchronously on user invocation rather than asynchronously on file events. The distinction is operational, not architectural.

---

## The Pre-Computer Analogy (Completed)

The paperwork principle from the frontmatter-driven interaction design now extends to the full system:

| Pre-Computer Office | Tool-Free QMS |
|---|---|
| Blank form from the supply cabinet | Template in `QMS/TEMPLATE/` |
| Form on your desk | Document in your inbox/workspace |
| Filling in the form | Editing frontmatter + inline responses |
| Putting it in your outbox tray | Moving document to outbox folder |
| Mail clerk picks it up | Daemon/watcher/agent processes outbox |
| Routing slip determines destination | Document state determines next inbox |
| Carbon copy for the files | `.audit/` JSONL trail |
| Filing cabinet | `QMS/.source/` + `QMS/.meta/` |
| Signature on the form | Review/approval recorded in document metadata |
| Stamp with date and initials | Per-response timestamps in `.meta/` |
| Supervisor's inbox | Reviewer/approver's inbox folder |
| "Return to sender" slip | Rejection with comment — document returns to author's inbox |

Every row has a direct correspondence. The system is not *inspired by* pre-computer paperwork — it *is* pre-computer paperwork, implemented with files instead of paper.

---

## Agent Implications

### Zero-Knowledge Participation

An agent does not need to know:
- The `qms` CLI API
- MCP tool schemas
- Command-line argument syntax
- HTTP endpoints
- Authentication protocols

An agent needs to know:
- How to read a file
- How to edit a file
- How to move a file

These are the three most primitive operations any agent can perform. The barrier to participation is essentially zero. A new agent — even one from a completely different model family, even one with no prior context about this project — can participate in the QMS by reading the document on its desk, following the prompt, and putting the result in the outbox. The document itself contains all the instructions.

### Self-Describing Workflows

The rendered document IS the instruction manual for the current step. The agent doesn't need a task tracker, a workflow engine, or a coordinator to tell it what to do. It reads the document. The document says "set `step_outcome` to Pass or Fail." The agent does that. The agent doesn't need to understand the workflow — it just needs to follow the current prompt.

This is how paper-based organizations scaled: each worker only needed to understand their form, not the entire process. The process emerged from the forms moving between desks.

### Crash Resilience (Reinforced)

The tool-free model strengthens the crash resilience argument. If the system crashes:
- Documents in inboxes are still in inboxes
- Documents in outboxes are still in outboxes (the mail clerk re-processes them)
- Documents being edited are still in the workspace (the agent re-reads and continues)
- No session state, no connection state, no in-memory state of any kind

Recovery is not a feature. It is the default behavior. There is nothing to recover because nothing was ever at risk.

---

## Architectural Implications

### The CLI Becomes Optional

The CLI remains useful for:
- **Validation**: Catching errors before they reach the mail clerk
- **Convenience**: Combining read + edit + move into a single command
- **Feedback**: Immediate response ("checkin successful") vs. asynchronous processing
- **Power users**: Batch operations, scripting, integration with other tools

But it is not architecturally necessary. The CLI is syntactic sugar over file operations, not a load-bearing component.

### The MCP Server Becomes Optional

If the CLI is optional, the MCP server (which wraps the CLI) is doubly optional. It exists to make the CLI accessible to agents that prefer tool-calling over shell commands. But an agent that can read/edit/move files doesn't need it.

### The Outbox Convention

The key new convention is the outbox. Currently, the QMS has:
- `QMS/.source/` — canonical source files
- `QMS/.meta/` — metadata sidecars
- `.claude/users/{user}/workspace/` — per-user workspace (inbox + editing surface)

The tool-free model adds:
- `.claude/users/{user}/outbox/` — per-user outbox (completed work awaiting processing)

Moving a document from workspace to outbox is the universal "I'm done with this step" signal. The mail clerk (daemon/watcher) picks it up, processes it, and routes the next view to the appropriate inbox.

### Progressive Enhancement

The system can be implemented progressively:
1. **CLI-only** (current): All operations via explicit commands
2. **CLI + outbox**: Outbox as alternative to explicit route/checkin commands
3. **Outbox-only**: CLI removed, mail clerk handles everything
4. **Distributed**: Multiple mail clerks, multiple agent workspaces, same convention

Each layer adds capability without removing the previous one. An agent using the CLI and an agent using the outbox can coexist in the same QMS instance.

---

## Relationship to Other Design Documents

- **Frontmatter-driven interaction** (`frontmatter-driven-interaction.md`): The tool-free QMS is the logical extension. That document eliminated the interaction engine; this one shows that the CLI itself is optional.
- **CR-107 (Unified Document Lifecycle)**: The tool-free model is fully compatible. Source files, `.meta/` sidecars, Jinja2 rendering, living schema authority — all preserved. The CLI is replaced by file operations + mail clerk, but the data model is unchanged.
- **The Paperwork Principle**: This document completes the analogy. The frontmatter-driven design showed that the document is the state. This document shows that the process is just paper-pushing.

---

## Open Questions

### 1. Outbox Semantics

When a document lands in the outbox, how does the mail clerk know what action to take? Options:
- **(a) Infer from document state.** If all fields are populated and status is DRAFT, route for review. If status is REVIEWED, route for approval. The document's state is unambiguous.
- **(b) Explicit action field.** The document's frontmatter includes an `action` field (e.g., `action: route_review`). The user sets it before moving to outbox. More explicit, but adds a field that exists only for routing.
- **(c) Filename convention.** `CR-108.review.md` vs `CR-108.approve.md`. Simple, but fragile.

### 2. Conflict Resolution

What if two agents edit the same document simultaneously? In the CLI model, checkout locks prevent this. In the tool-free model, there's no lock — anyone can read and edit any file in their inbox. Options:
- **(a) Keep checkout locks.** The mail clerk checks locks before processing outbox items. This reintroduces state management, but it's minimal.
- **(b) Optimistic concurrency.** The mail clerk detects conflicts (document changed since the agent's copy was created) and rejects the outbox submission, returning the document to the agent's inbox with a conflict notice.
- **(c) Accept it.** For a single-agent system (which this currently is), conflicts don't arise. Solve this when multi-agent concurrency becomes real.

### 3. Mail Clerk Implementation

What form should the mail clerk take?
- **(a) Filesystem watcher daemon.** Watches outbox folders, processes on file events. Real-time but requires a running process.
- **(b) Cron job.** Periodically scans outboxes. Simple but introduces latency.
- **(c) The CLI itself.** `qms process-outbox` command, run manually or by a hook. Keeps the CLI relevant and avoids a new daemon.
- **(d) An AI agent.** An agent whose workspace IS the set of all outboxes. It reads, validates, routes. The ultimate paper-pushing worker.
