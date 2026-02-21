# The Interaction System

*Design document. Synthesizes Sessions 2026-02-19-002 through 2026-02-20-003.*

---

## 1. What This Is

The interaction system is a structured authoring framework for QMS documents. Templates define a sequence of prompts. Authors respond to prompts. The engine records responses, manages project state snapshots, and compiles the responses into finished documents.

The system replaces freehand markdown editing for AI agents. Instead of checking out a document, editing it as prose, and checking it back in, agents interact with a template-driven process that controls structure while the author controls content.

### 1.1 The Skill Metaphor

A template is not a form. A form collects data; a template teaches methodology.

When a VR template asks for expected results before actual results, it enforces the scientific method — hypothesis before experiment. When it coaches "frame the objective as a capability, not a mechanism," it's encoding institutional knowledge about what makes good verification evidence. The sequential enforcement isn't bureaucratic; it's pedagogical.

This framing has consequences:

- **Template authoring is methodology design.** The question is not "what sections does this document need?" but "what sequence of questions, asked in what order, reliably produces a good document of this type?"
- **Template review is methodology review.** A bad prompt doesn't produce a missing section; it produces a missing thought.
- **Templates evolve under selective pressure.** If a template consistently produces documents that fail review, the methodology is deficient. The QMS's own feedback mechanisms (INV, CAPA) improve the templates. The system teaches itself to teach better.

### 1.2 What This Replaces

**Current model:**

```
checkout -> agent edits markdown freehand -> checkin
```

The agent controls both content and structure. Structural conformance is verified during review. The markdown file is the source of truth.

**New model:**

```
checkout -> template presents prompts -> agent responds -> engine commits -> compile -> checkin
```

The template controls structure. The agent controls content. Structural conformance is guaranteed by construction. The source file is the source of truth; the compiled markdown is a derived view.

---

## 2. Data Model

### 2.1 The Source File

Every interactive document has a **source file** — a structured JSON record of all prompt responses, amendments, and metadata. This is the authoritative data from which the compiled document is derived.

```json
{
  "doc_id": "CR-090-VR-001",
  "template": "VR",
  "template_version": 3,
  "cursor": "step_expected",
  "cursor_context": { "loop": "steps", "iteration": 2 },
  "metadata": {
    "parent_doc_id": "CR-090",
    "vr_id": "CR-090-VR-001",
    "title": "Verify MCP health check behavior"
  },
  "responses": {
    "related_eis": [
      {
        "value": "EI-3",
        "author": "claude",
        "timestamp": "2026-02-20T10:30:00Z"
      }
    ],
    "objective": [
      {
        "value": "Verify that the health check endpoint returns 200",
        "author": "claude",
        "timestamp": "2026-02-20T10:31:00Z"
      },
      {
        "value": "Verify that service health monitoring detects running and stopped services correctly",
        "author": "claude",
        "timestamp": "2026-02-20T11:15:00Z",
        "reason": "Broadened scope per VR evidence standards"
      }
    ],
    "step_actual.1": [
      {
        "value": "Connection to localhost:8000 succeeded. Service alive.",
        "author": "claude",
        "timestamp": "2026-02-20T10:35:00Z",
        "commit": "a1b2c3d"
      }
    ]
  },
  "loops": {
    "steps": {
      "iterations": 2,
      "closed": false,
      "reopenings": []
    }
  },
  "gates": {
    "more_steps.1": { "value": "yes", "timestamp": "2026-02-20T10:36:00Z" }
  }
}
```

Key properties of the source:

- **Append-only responses.** Each response key maps to a list. The initial response creates a single-entry list. Amendments append — they never replace or delete. The active value is always the last entry.
- **Per-response attribution.** Every entry has author, timestamp, and optional reason (for amendments) and commit hash (for commit-enabled prompts).
- **Cursor state.** The source tracks where the author is in the template's state machine, including loop context. This makes the interaction stateless from the CLI's perspective — each invocation reads the cursor from the source and presents the appropriate prompt.

### 2.2 The VR Step Tuple

For Verification Records, each step in the loop produces four responses:

| Field | Prompt ID | Description |
|-------|-----------|-------------|
| Instructions | `step_instructions.N` | What the author did — action description and exact command |
| Expected | `step_expected.N` | What the author predicted before executing |
| Actual | `step_actual.N` | What was observed — primary evidence (commit-enabled) |
| Outcome | `step_outcome.N` | Pass or Fail with discrepancy note if Fail |

The commit hash on `step_actual` pins the project state at the moment of observation. A verifier can checkout that commit to see the exact code, configuration, and any output files. The actual result references primary evidence rather than summarizing it — raw terminal output, log excerpts, or file paths within the committed state.

### 2.3 Compiled Document

The compiled document is a markdown file derived from the source by:

1. Stripping all template tags and guidance prose
2. Keeping the markdown structure (headings, tables, code blocks)
3. Substituting `{{placeholders}}` with active response values
4. Rendering amendment trails (strikethrough on superseded entries)
5. Showing timestamps and author on all responses
6. Showing commit hashes on commit-enabled responses

The compiled document is what `qms read` returns. It is what reviewers evaluate. It is what gets archived. But it is always reproducible from the source — if the compilation logic changes (template bug fix, rendering improvement), the document can be recompiled from the same source.

---

## 3. File System

### 3.1 Artifacts

An interactive document produces three artifacts at different lifecycle stages:

| Artifact | Location | Lifecycle |
|----------|----------|-----------|
| **Interact session** | `.claude/users/{user}/workspace/{DOC_ID}.interact` | Exists while checked out. Working copy of the source. |
| **Source** | `QMS/.meta/{TYPE}/{DOC_ID}.source.json` | Permanent. Created on checkin. Authoritative record. |
| **Compiled document** | `QMS/{TYPE}/{PARENT_ID}/{DOC_ID}.md` | Permanent. Created on checkin. Derived view. |

During authoring, the `.interact` file in the user's workspace is the live session. It contains the same data structure as the source (responses, cursor, loop state). On checkin, this data moves to `.meta/` as the permanent `.source.json`, and the compiled markdown is generated into the QMS directory.

### 3.2 Checkout Semantics for Interactive Documents

Checkout serves two purposes: establishing responsible user (ownership/locking) and providing a workspace artifact.

For interactive documents, checkout does NOT place an editable markdown file in the workspace. The workspace receives the `.interact` session file — a structured data file that the interaction engine reads and writes. The author interacts with the document through `qms interact`, not through file editing.

**Checkout flow:**

1. Set `responsible_user` in metadata (standard)
2. Lock the document (standard)
3. Initialize `.interact` session file in workspace (new — replaces copying the markdown)
4. If resuming a previously checked-in document, seed the session from the existing `.source.json`

**Checkin flow:**

1. Compile responses into markdown
2. Store compiled markdown in QMS directory
3. Move session data to `.meta/{TYPE}/{DOC_ID}.source.json`
4. Remove `.interact` from workspace
5. Unlock the document (standard)

### 3.3 Reading Interactive Documents

`qms read DOC_ID` always works and always returns a compiled markdown view:

- **If checked out (session active):** Compiles from the `.interact` session file. May be partially filled — empty prompts appear as blank fields.
- **If checked in (source exists):** Compiles from the `.source.json`. This is the complete document.
- **If no source exists:** Falls back to the standard behavior (returns the markdown file directly). This handles non-interactive documents and documents created before the interaction system.

There is no "this document is interactive, use a different command" gate. Read is read.

---

## 4. The Interaction Protocol

### 4.1 Tag System

Templates embed tags in HTML comments that define a state machine:

| Tag | Purpose |
|-----|---------|
| `@prompt: id \| next: id` | Content prompt. Response stored in `{{id}}`. |
| `@gate: id \| type: yesno \| yes: id \| no: id` | Flow-control prompt. Routes only, no compiled content. |
| `@loop: name` / `@end-loop: name` | Repeating block. `{{_n}}` = iteration counter. |
| `@end` | Terminal state. |

Attributes:

| Attribute | Purpose |
|-----------|---------|
| `next: id` | Unconditional transition to next prompt. |
| `type: yesno` | Gate accepts yes or no. |
| `yes: id` / `no: id` | Conditional transitions for yesno gates. |
| `default: value` | Auto-fill value (author can accept or override). |
| `commit: true` | Engine commits project state when response is recorded. |

### 4.2 Prompt Guidance

The prose between tags is guidance text — visible to the author when the prompt is presented, stripped during compilation. This is where the template encodes methodology:

```markdown
<!-- @prompt: step_expected | next: step_actual -->

What do you expect to observe? State this BEFORE executing — not after.
Good verification covers both sides: confirming what should be present
and confirming what should be absent. A step might check that a service
responds correctly, or that an error no longer appears, or that an
unrelated subsystem remains unaffected. All of these are evidence.

**Expected:** {{step_expected}}
```

The guidance is shown once (when the prompt is presented) and is not part of the compiled output. The quality of the guidance determines the quality of the document.

### 4.3 Response Model

Every response is a timestamped, append-only list:

```
Entry:
  - value:     The response content
  - author:    Who recorded this entry
  - timestamp: When (ISO 8601)
  - reason:    Why amended (omitted for initial entry)
  - commit:    Git commit hash (present only on commit-enabled responses)
```

Amendments append — they never replace or delete. Superseded entries render with strikethrough in the compiled output. The active entry is always the most recent. This is GMP-style correction: original data preserved, corrections traceable.

### 4.4 Navigation

Two cursor movement primitives beyond normal forward progression:

- **goto** — detour to a completed prompt, amend (with reason), return to prior position.
- **reopen** — re-enter a closed loop to add iterations (with reason). Iteration counter continues. Cursor returns when the gate re-closes.

All cursor movements are recorded in the source.

### 4.5 Enforcement

- **Prompt-before-response:** The engine will not accept a response to a prompt it hasn't presented. Each `--respond` output includes the next prompt.
- **Sequential only:** No skipping prompts. Forward progress requires responding in order.
- **Amendments require reason:** `--respond` during a goto detour requires `--reason`.
- **Contextual interpolation:** Prompts can reference previous responses, making autopilot harder and coaching more specific.

---

## 5. Atomic Commit Integration

### 5.1 Engine-Managed Commits

On prompts marked with `commit: true`, the interaction engine:

1. Stages all changes in the working tree
2. Commits with a system-generated message
3. Records the commit hash as metadata on the response

The commit hash on a response is the exact project state when that response was given. Guaranteed by the engine, not by author discipline.

### 5.2 Commit Message Format

System-generated, consistent, traceable:

```
[QMS] {DOC_ID} | {loop_name}.{iteration} | {prompt_id}
```

Examples:

```
[QMS] CR-090-VR-001 | steps.1 | step_actual
[QMS] CR-090-VR-001 | steps.2 | step_actual
```

### 5.3 When to Commit

Not every prompt needs a commit. The `commit: true` attribute controls which responses trigger commits. Typical commit points: evidence-bearing prompts within execution loops (observations, outcomes). Identification and metadata prompts do not commit.

### 5.4 Primary Data Attachment

The `--respond --file path` flag attaches raw data — terminal output, log excerpts, test results — directly into responses. This is preferred over summarizing output in prose.

Combined with the commit hash, a verifier can:

1. Read the step in the compiled document
2. Checkout the commit hash recorded on that step
3. Run the exact command documented in instructions
4. Compare their output to the attached output in actual
5. See any referenced files at the exact committed state

---

## 6. CLI Interface

### 6.1 Entry Point

Single command: `qms interact DOC_ID`. Bare invocation emits status and current prompt. Flags perform actions.

### 6.2 Flags

| Flag | Purpose |
|------|---------|
| `--respond "value"` | Respond to current prompt |
| `--respond --file path` | Respond with file contents |
| `--accept` | Accept default value |
| `--reason "text"` | Required for amendments and loop reopenings |
| `--goto prompt_id` | Amend a previous response |
| `--cancel-goto` | Cancel amendment detour |
| `--reopen loop --reason "why"` | Re-enter a closed loop |
| `--progress` | Show all prompts with fill status |
| `--compile` | Generate compiled document |

### 6.3 Output Contract

Every `--respond` output includes:

1. Confirmation of the recorded response (value, author, timestamp, commit hash if applicable)
2. The next prompt (guidance text and placeholder)
3. Help footer with available commands

This forced dialogue ensures prompt-before-response: the agent reads what the system presents, then responds to it.

### 6.4 Typical Agent Session

```bash
# Orient
qms --user claude interact CR-090-VR-001

# Identification
qms --user claude interact CR-090-VR-001 --respond "EI-3"
qms --user claude interact CR-090-VR-001 --accept                          # date (default: today)

# Objective and pre-conditions
qms --user claude interact CR-090-VR-001 --respond "Verify that service health monitoring detects running and stopped services correctly"
qms --user claude interact CR-090-VR-001 --respond --file /tmp/preconditions.txt

# Step 1
qms --user claude interact CR-090-VR-001 --respond "Run health check against running MCP service: python -c \"import socket; ...\""
qms --user claude interact CR-090-VR-001 --respond "TCP connect succeeds, service reported as alive"
qms --user claude interact CR-090-VR-001 --respond --file /tmp/step1-output.txt    # commit: true
qms --user claude interact CR-090-VR-001 --respond "Pass"
qms --user claude interact CR-090-VR-001 --respond yes                              # more steps

# Step 2
qms --user claude interact CR-090-VR-001 --respond "Stop MCP server and re-check: docker-compose stop && python -c ..."
qms --user claude interact CR-090-VR-001 --respond "TCP connect fails, connection refused"
qms --user claude interact CR-090-VR-001 --respond --file /tmp/step2-output.txt    # commit: true
qms --user claude interact CR-090-VR-001 --respond "Pass"
qms --user claude interact CR-090-VR-001 --respond no                               # no more steps

# Summary and signature
qms --user claude interact CR-090-VR-001 --respond "Pass"
qms --user claude interact CR-090-VR-001 --respond "Verified health monitoring across service up/down states. Both positive verification (correct detection) and negative verification (no false positives on stopped service) confirmed."
qms --user claude interact CR-090-VR-001 --accept                          # performer (default: current_user)
qms --user claude interact CR-090-VR-001 --accept                          # date (default: today)
```

---

## 7. The VR Template

The Verification Record is the first document type built on this system. Its template (TEMPLATE-VR v3) encodes the following methodology:

### 7.1 Structure

| Section | Prompts | Purpose |
|---------|---------|---------|
| Identification | related_eis, date | Administrative. Parent is known from creation metadata. |
| Objective | objective | Capability framing. Guidance coaches broad scope. |
| Pre-Conditions | pre_conditions | Environment state for reproducibility. |
| Steps (loop) | instructions, expected, actual, outcome | The evidence chain. Per-step commit on actual. |
| Summary | summary_outcome, summary_narrative | Overall judgment and narrative. |
| Signature | performer, performed_date | Attribution. |

### 7.2 The Step Tuple

Each verification step is four prompts:

1. **Instructions** — what the author is about to do, including exact commands. Combines intent and mechanism in a single field.
2. **Expected** — what the author predicts before executing. Guidance coaches for both positive verification (confirming presence of correct behavior) and negative verification (confirming absence of unintended behavior).
3. **Actual** — what was observed. Primary evidence: raw output, not summaries. Commit-enabled — the engine snapshots project state at this moment.
4. **Outcome** — Pass or Fail with discrepancy note.

The sequencing is methodologically significant: instructions and expected are recorded before execution. The author commits to a prediction, then tests it. Post-hoc rationalization is structurally prevented.

### 7.3 Design Artifact

The full template is in `Session-2026-02-20-003/TEMPLATE-VR-restructured-v3.md`.

---

## 8. Generalization

### 8.1 Beyond VRs

The interaction system is designed to generalize across document types. The VR is the first implementation target because its structure is naturally sequential and evidence-oriented, making it an ideal proving ground.

Future document types follow the same architecture:

| Document | Interactive Sections | Freehand Sections |
|----------|---------------------|-------------------|
| **VR** | All | None |
| **CR** | Identification, scope, impact assessment, EI table | Change description, justification |
| **INV** | Identification, scope, impact, CAPA table | Background, root cause analysis |
| **SOP** | Possibly none — SOPs are highly narrative | — |

Some documents may be fully interactive (VRs), some hybrid (CRs — structured sections guided, narrative sections freehand), and some may remain entirely freehand (SOPs). The architecture supports all three.

### 8.2 The Three-Layer Vision

The interaction system is the middle layer of a three-layer architecture:

**Layer 1: Intent Decomposition** (future). A user says "I want to add a new feature." The system determines this requires a CR, asks scoping questions, identifies affected domains, and feeds structured intent into the interaction system.

**Layer 2: Guided Document Production** (this system). Templates encode methodology. Prompts extract content. Responses are timestamped, attributable, and traceable. The engine manages project state snapshots. Compiled output feeds into the existing review/approval machinery.

**Layer 3: Execution Dispatch** (partially exists). Pre-approved execution items are dispatched to agents. Results are captured through interact. Evidence is compiled. The interaction system guides execution and captures evidence at each step.

### 8.3 What This Gives the QMS

- **Structural conformance by construction.** A compiled CR cannot be missing Section 6.8. A VR cannot skip pre-conditions. Review focuses on content adequacy, not document format.
- **Content-level attribution.** Not "claude checked in this document" but "claude provided this specific answer to this specific prompt at this specific time at this specific project state."
- **Reproducibility.** Commit hashes on evidence-bearing responses create a verifiable chain. Any step can be independently reproduced.
- **Consistent quality floor.** Guidance prompts encode institutional knowledge. A new agent's first VR gets the same coaching as the hundredth.
- **Templates as procedural controls.** The template IS the SOP enforcement, compiled from procedural requirements and made executable.

---

## 9. Implementation Path

### Phase 1: Engine and VR

- Implement the template parser (tag extraction, state machine construction) in qms-cli
- Implement the `qms interact` command with all flags
- Implement the source data model (`.interact` session file, `.source.json` permanent storage)
- Implement compilation (source -> markdown)
- Modify checkout/checkin to handle interactive documents (session file instead of markdown)
- Modify `qms read` to compile from source when available
- Adopt TEMPLATE-VR v3 as the first interactive template
- Validate against real VR creation

### Phase 2: Atomic Commits

- Add `commit: true` support to the template parser
- Implement engine-managed git commits on respond
- Implement commit hash recording in response metadata
- Implement commit hash rendering in compiled output

### Phase 3: Expand to Executable Documents

- Design TEMPLATE-CR for interact-based creation (likely hybrid: interactive for structured sections, freehand for narrative)
- Design TEMPLATE-VAR, TEMPLATE-ADD
- Evaluate which sections benefit from guided fill vs. freeform

### Phase 4: Non-Executable Documents and Beyond

- Evaluate TEMPLATE-SOP, TEMPLATE-RS, TEMPLATE-RTM
- Intent decomposition layer (Layer 1)

---

## 10. Open Questions

### Commit Scope

When the engine commits, what gets staged? Options: everything (`git add -A`), scoped to document paths, or configurable per template. If multiple interact sessions are active, their commits interleave — commit messages must clearly identify which document triggered each commit.

### SOP Evolution

SOP-004 Section 5 defines pre-execution and post-execution commits. Engine-managed commits subsume this pattern. The SOP language may evolve from "commit at start and end" to "the interaction engine manages commits at evidence boundaries."

### Tag Syntax Stability

The tag vocabulary (`@prompt`, `@gate`, `@loop`, `@end-loop`, `@end`) and attribute format should be reviewed before implementation. Once templates are authored against this syntax, changes require CRs to update every template.

### Hybrid Documents

For documents with both interactive and freehand sections (e.g., CRs), the interaction system needs a mechanism to hand off to freehand editing for narrative sections and resume structured interaction afterward. This could be a special tag (`@freehand: section_name`) or a convention where certain sections are simply not tagged.

---

## 11. Design Artifacts

| Artifact | Location |
|----------|----------|
| VR template (v3) | `Session-2026-02-20-003/TEMPLATE-VR-restructured-v3.md` |
| CLI command design | `Session-2026-02-20-001/interact-command-design.md` |
| Vision document (strategic framing) | `Session-2026-02-20-002/vision-interact-as-canonical-interface.md` |
| This document (consolidated design) | `Session-2026-02-20-003/interaction-system-design.md` |
