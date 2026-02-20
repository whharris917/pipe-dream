# Vision: The Interaction System as Canonical QMS Interface

*Session-2026-02-20-002. Synthesizes design work from Sessions 2026-02-19-002, 2026-02-19-003, 2026-02-20-001, and 2026-02-20-002.*

---

## 1. The Core Idea

The QMS interaction system (`qms interact`) becomes the exclusive write interface between AI agents and controlled documents. Agents do not edit markdown files. They respond to prompts. Documents are compiled artifacts, not authored ones.

This is the Air Gap pattern applied to document authoring: just as UI tools cannot mutate the data model directly (they must go through Commands), agents cannot mutate documents directly (they must go through interact). The interaction system is the Command Pattern for the QMS.

---

## 2. What This Replaces

**Current model:**

```
checkout → agent edits markdown freehand → checkin
```

The agent has full control over both content and structure. Structural conformance is verified during review. The document file is the source of truth.

**New model:**

```
checkout → template presents prompts → agent responds → engine commits → compile → checkin
```

The template controls structure. The agent controls content. Structural conformance is guaranteed by construction. The response store is the source of truth; the markdown document is a rendered view.

---

## 3. Three Layers

The full vision has three layers. The interaction system is the middle layer and the connective tissue between the other two.

### Layer 1: Intent Decomposition

A user says "I want to add a new feature to my game." The system determines this requires a CR, asks scoping questions, identifies affected domains, and produces a structured change proposal — all through the interaction system's prompt/response protocol.

This layer does not exist yet. It is the translation from natural language intent to QMS-appropriate action. It sits above the interaction system and feeds into it.

### Layer 2: Guided Document Production (The Interaction System)

Templates encode what the QMS needs to know. Prompts extract it. Responses are timestamped, attributable, and traceable. The engine manages project state snapshots (commits) alongside document state. Compiled output flows into the existing review/approval machinery.

This layer is designed (Sessions 2026-02-19 through 2026-02-20) and ready for implementation.

### Layer 3: Execution Dispatch

Pre-approved execution items are dispatched to appropriate agents. Results are captured through interact. Evidence is compiled. Post-review is routed. The interaction system guides execution and captures evidence at each step.

This layer partially exists — agents execute today, but capture and routing is manual. The interaction system formalizes and automates the capture.

---

## 4. The Interaction Protocol

### 4.1 Tag System

Templates are both interaction scripts and output templates. Embedded tags define the state machine:

| Tag | Purpose |
|-----|---------|
| `@prompt: id \| next: id` | Content prompt. Response stored in `{{id}}`. |
| `@gate: id \| type: yesno \| yes: id \| no: id` | Flow-control prompt. Routes only, no compiled content. |
| `@loop: name` / `@end-loop: name` | Repeating block. `{{_n}}` = iteration counter. |
| `@end` | Terminal state. |

Attributes: `next` (unconditional transition), `type: yesno`, `yes`/`no` (conditional transitions), `default` (auto-fill value), `commit: true` (trigger project state snapshot).

### 4.2 Response Model

Every response is an append-only timestamped list:

```
Entry:
  - value:     The response content
  - author:    Who recorded this entry
  - timestamp: When (ISO 8601)
  - reason:    Why amended (omitted for initial entry)
  - commit:    Git commit hash at time of recording (if commit-enabled)
```

Amendments append — they never replace or delete. Superseded entries render with strikethrough. The active entry is always the most recent. This is GMP-style correction: original data preserved, corrections traceable.

### 4.3 Navigation

Two cursor movement primitives beyond normal forward progression:

- **goto** — detour to a completed prompt, amend (with reason), return to prior position
- **reopen** — re-enter a closed loop, add iterations (with reason), return when gate re-closes

All cursor movements are recorded in the audit trail.

### 4.4 Enforcement

- **Prompt-before-response:** The system will not accept a response to a prompt it hasn't presented. Each `--respond` output includes the next prompt, creating a forced dialogue.
- **Sequential only:** No skipping prompts. Forward progress requires responding in order.
- **Amendments require reason:** `--respond` during a goto detour requires `--reason`.
- **Contextual interpolation:** Prompts can reference previous responses (`"You said you're about to: '{{step_action}}'. Before you execute — what do you expect to observe?"`), making autopilot harder.
- **Self-documenting:** Help footer on every output. The agent never needs to recall syntax from memory.

### 4.5 CLI Interface

Single entry point: `qms interact DOC_ID`. Bare command emits status and current prompt. Flags perform actions:

| Flag | Purpose |
|------|---------|
| `--respond "value"` | Respond to current prompt |
| `--respond --file path` | Respond with file contents (terminal output, logs) |
| `--accept` | Accept default value |
| `--reason "text"` | Required for amendments and loop reopenings |
| `--goto prompt_id` | Amend a previous response |
| `--cancel-goto` | Cancel amendment detour |
| `--reopen loop --reason "why"` | Re-enter a closed loop |
| `--progress` | Show all prompts with fill status |
| `--compile` | Generate compiled document |

Full design with examples: `Session-2026-02-20-001/interact-command-design.md`

---

## 5. Atomic Commit Integration

The interaction engine manages the relationship between document state and project state. On prompts marked with `commit: true`, the engine:

1. Stages all changes in the working tree
2. Commits with a system-generated message: `[QMS] CR-090-VR-001 | steps.1 | step_observed`
3. Records the commit hash as metadata on the response

This makes the evidence chain atomic — no gap between observation and project state snapshot. The author never touches git during an interact session.

### 5.1 What This Solves

Without engine-managed commits, the author might:

- Forget to commit
- Have unstaged changes that aren't captured
- Stage selectively and miss files
- Record a commit hash that doesn't match the actual state
- Commit after making additional changes past the observation point

With engine-managed commits, the commit hash on a response is *exactly* the project state when that response was given. Guaranteed by the system, not by author discipline.

### 5.2 When to Commit

Not every prompt needs a commit. Filling in "parent document ID" doesn't change project state. The `commit: true` attribute on prompt tags controls which responses trigger commits:

```html
<!-- @prompt: step_observed | next: step_outcome | commit: true -->
```

Typical commit points: prompts within execution/verification step loops where project state is expected to have changed (observations, outcomes). Identification and metadata prompts do not commit.

### 5.3 Commit Message Format

System-generated, consistent, traceable:

```
[QMS] {DOC_ID} | {loop_name}.{iteration} | {prompt_id}
```

Examples:
```
[QMS] CR-090-VR-001 | steps.1 | step_observed
[QMS] CR-090-VR-001 | steps.2 | step_observed
[QMS] CR-091 | execution.3 | ei_summary
```

### 5.4 Compiled Document Rendering

Because commit hashes are response metadata, compiled documents can render them automatically:

```markdown
### Step 1

**Action:** Run health check against running MCP service
*— claude, 2026-02-20 10:30*

**Expected:** TCP connect succeeds, service reported as alive
*— claude, 2026-02-20 10:31*

**Command:**
    python -c "import socket; s = socket.socket()..."
*— claude, 2026-02-20 10:32*

**Observed:**
    Connection to localhost:8000 succeeded. Service alive.
*— claude, 2026-02-20 10:33 | commit: a1b2c3d*

**Outcome:** Pass
*— claude, 2026-02-20 10:33*
```

The commit hash appears only on commit-enabled responses, linking the observation to the exact project state.

---

## 6. Primary Data Attachment

The `--respond --file path` flag enables attaching raw data — terminal output, log excerpts, test results — directly into document responses. This is preferred over summarizing output in prose.

### 6.1 Evidence Standards

| Practice | Before | After |
|----------|--------|-------|
| Terminal output | "Ran tests, all passed" | `--respond --file /tmp/test-output.txt` (full output attached) |
| Log excerpts | "Health check returned 200" | `--respond --file /tmp/health-check.log` (raw log attached) |
| Command details | "Ran the migration script" | `--respond --file /tmp/migration-cmd.txt` (exact commands) |

### 6.2 Reproducibility Chain

With atomic commits and primary data attachment, a verifier can:

1. Read the VR step in the compiled document
2. Checkout the commit hash recorded on that step
3. Run the exact command documented in `step_detail`
4. Compare their output to the attached output in `step_observed`

Full reproducibility. The VR is a reproducible experiment log, not a narrative claim.

---

## 7. What This Gives the QMS

### 7.1 Structural Conformance by Construction

A template-compiled CR cannot be missing Section 6.8 (Testing Summary). A VR cannot skip the pre-conditions. The template enforces structure; review focuses on content adequacy. QA stops policing document format and focuses entirely on substance.

### 7.2 Content-Level Attribution

Not just "claude checked in this document" but "claude provided this specific answer to this specific prompt at this specific time at this specific project state." Every piece of content is attributable to an author, a moment, and a commit.

### 7.3 Universal Contemporaneous Recording

Every response is timestamped at the time of recording. The system enforces sequential fill — you can't backfill step 3 after completing step 7. The entire QMS document corpus gets ALCOA+ properties (Attributable, Legible, Contemporaneous, Original, Accurate) by construction.

### 7.4 Consistent Quality Floor

Guidance prompts teach the author what good content looks like at every step. A new agent filling out its first CR gets the same coaching as the hundredth. The prompts encode institutional knowledge about what makes a good Change Description, a thorough Root Cause Analysis, or adequate test evidence.

### 7.5 Review Becomes Verification, Not Discovery

Reviewers currently discover structural problems ("you forgot the Testing Summary," "your EI table is missing columns"). With compiled documents, structure is guaranteed. Reviewers verify that content is adequate — the judgment call that humans and AI reviewers are actually good at.

### 7.6 Templates as Procedural Controls

SOPs define what documents must contain. Templates enforce it. The template IS the procedural control, compiled from SOP requirements. When an SOP changes, the corresponding template changes. The enforcement is live, not advisory.

---

## 8. Architectural Implications

### 8.1 The Response Store Is the Source of Truth

The compiled markdown is a view, not the source. The canonical data is the list of prompt responses with their metadata (timestamps, authors, commit hashes, amendment history). This has implications for:

- **Storage:** Responses need a durable home. Likely a new sidecar structure (e.g., `.meta/{TYPE}/{DOC_ID}-responses.json`) or an extension to the existing metadata tier.
- **Versioning:** The response store, not the markdown file, is what gets versioned and archived.
- **Querying:** "What did claude write for the root cause analysis of INV-012?" becomes a structured query against the response store, not a grep through markdown.

### 8.2 Checkout/Checkin Semantics Evolve

- **Checkout** activates the interaction session. The document enters an interactive state.
- **Checkin** compiles the responses into the final document and returns it to the QMS.
- The workspace copy is the response store, not a markdown file being edited.

### 8.3 Template Governance

Templates are already controlled documents. Under this vision, they are executable interaction scripts that define the canonical creation path for every document of that type. Their review bar goes up accordingly:

- A bad prompt in TEMPLATE-CR affects every CR created after it
- Tag syntax changes propagate to every template
- The tag vocabulary must be stable before templates scale

### 8.4 Structured vs. Narrative Content

Some document sections are structured (EI tables, identification fields, signatures) and some are narrative (Change Description, Root Cause Analysis). The interaction system handles both, but with different value propositions:

- **Structured sections:** Full enforcement. The section exists, has the right format, contains required fields.
- **Narrative sections:** The prompt guarantees the section exists and provides guidance. Content adequacy is still a review judgment.

This is the correct division of labor. Structure enforcement is mechanical and should be automated. Content adequacy is judgment and should be reviewed.

---

## 9. Implementation Path

### Phase 1: Engine and VR (first implementation target)

- Implement the template parser and `qms interact` command in qms-cli
- Implement the response store (storage format and location)
- Implement compilation (responses → markdown)
- Adopt TEMPLATE-VR as the first incrementally-built document type
- Validate the engine against real VR creation

### Phase 2: Atomic Commits

- Add `commit: true` attribute support to the template parser
- Implement engine-managed git commits on respond
- Implement commit hash recording in response metadata
- Implement commit hash rendering in compiled output

### Phase 3: Expand to Executable Documents

- Design TEMPLATE-CR for interact-based creation
- Design TEMPLATE-VAR, TEMPLATE-ADD
- Evaluate which sections benefit from guided fill vs. freeform
- Hybrid approach possible: interact for structured sections, freeform for narrative

### Phase 4: Expand to Non-Executable Documents

- Evaluate TEMPLATE-SOP, TEMPLATE-RS, TEMPLATE-RTM
- These are less natural fits (more narrative, less structured) — may remain freehand or adopt a light interact model

### Phase 5: Intent Decomposition (Layer 1)

- Design the concierge layer that translates "I want to add a feature" into the appropriate document type and scoping prompts
- This layer sits above the interaction system and feeds into it
- Requires orchestration intelligence beyond template-driven form-fill

---

## 10. Open Questions

### Storage Location

Where do response lists live? Options:

1. **New sidecar in `.meta/`** (e.g., `.meta/{TYPE}/{DOC_ID}-responses.json`) — natural extension of existing architecture
2. **New tier** (e.g., `.interact/`) — clean separation but adds complexity
3. **Inline in the document** — keeps everything in one file but makes the markdown complex

### Tag Syntax Stability

The tag vocabulary (`@prompt`, `@gate`, `@loop`, `@end-loop`, `@end`) and attribute format should be reviewed before implementation. Once templates are authored against this syntax, changes require CRs to update every template.

### Commit Scope

When the engine commits, what gets staged? Options:

1. **Everything** (`git add -A`) — captures true project state but may include unrelated changes
2. **Scoped to document paths** — cleaner but misses related changes (e.g., code files modified during execution)
3. **Configurable** — template or document-level setting

### SOP Evolution

SOP-004 Section 5 defines pre-execution and post-execution commits. Fine-grained engine-managed commits subsume this pattern. The SOP language may evolve from "commit at start and end" to "the interaction engine manages commits at evidence boundaries."

### Freehand Escape Hatch

Should there be a path for agents or humans to edit documents without interact? Edge cases, migration of existing documents, documents that genuinely don't fit the template model. If so, how is it governed?

### Concurrent Document Work

If multiple interact sessions are active (e.g., a VR and its parent CR), their commits interleave. Git handles this fine, but the commit messages need to clearly identify which document triggered each commit.

---

## 11. Design Artifacts

| Artifact | Location |
|----------|----------|
| Restructured TEMPLATE-VR | `Session-2026-02-20-001/TEMPLATE-VR-restructured.md` |
| `qms interact` command design | `Session-2026-02-20-001/interact-command-design.md` |
| This vision document | `Session-2026-02-20-002/vision-interact-as-canonical-interface.md` |

---

## 12. Summary

The interaction system starts as a document-filling tool and becomes the canonical interface between AI agents and the QMS. Templates encode procedural requirements as executable interaction scripts. The engine manages both document state (responses) and project state (commits), linking them atomically. Compiled documents are rendered views backed by a structured, auditable, reproducible evidence chain.

The QMS evolves from a system that governs documents to a system that governs interactions — and produces documents as a byproduct.
