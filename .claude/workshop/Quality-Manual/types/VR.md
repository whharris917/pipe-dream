# Document Type: VR (Verification Record)

## Overview

A Verification Record (VR) is an **executable**, **attachment-type**, **interactive** document that records behavioral verification of execution items. See [Child Documents](../07-Child-Documents.md) for the conceptual overview and [Interactive Authoring](../08-Interactive-Authoring.md) for the template-driven authoring system. VRs are unique in the QMS in three ways:

1. **Born IN_EXECUTION**: VRs skip the entire pre-approval lifecycle. They are created directly in `IN_EXECUTION` at version `1.0`.
2. **Attachment type**: VRs are cascade-closed when their parent closes, and can close from any non-terminal status.
3. **Interactive authoring**: VRs are authored via a template-driven prompting engine (`qms interact`), not freehand Markdown editing.

---

## Template Structure

Source: `QMS/TEMPLATE/TEMPLATE-VR.md`

The VR template is an **interactive template** -- it contains embedded `@prompt`, `@gate`, and `@loop` tags that drive the interaction engine rather than being edited directly.

### Frontmatter

```yaml
---
title: '{{title}}'
revision_summary: 'Initial draft'
---
```

### Template Header

```
@template: VR | version: 5 | start: related_eis
```

| Field | Value | Purpose |
|-------|-------|---------|
| name | VR | Template identity |
| version | 5 | Schema version (used for source compatibility) |
| start | related_eis | First prompt in the authoring flow |

### Sections

| # | Section | Prompts | Purpose |
|---|---------|---------|---------|
| 1 | Verification Identification | `related_eis` | Which parent EIs this VR verifies |
| 2 | Verification Objective | `objective` | Capability being verified (not mechanism) |
| 3 | Prerequisites | `pre_conditions` | System state before verification begins |
| 4 | Verification Steps | `step_instructions`, `step_expected`, `step_actual`, `step_outcome`, `more_steps` (loop) | Repeating step cycle |
| 5 | Summary | `summary_outcome`, `summary_narrative` | Overall pass/fail and narrative |

### Prompt Flow

```
related_eis -> objective -> pre_conditions -> [LOOP: steps]
  step_instructions -> step_expected -> step_actual (commit) -> step_outcome -> more_steps (gate)
    yes -> step_instructions (next iteration)
    no  -> summary_outcome -> summary_narrative -> END
```

### Prompt Detail

| Prompt ID | Type | Next | Attributes | Guidance Summary |
|-----------|------|------|------------|------------------|
| `related_eis` | prompt | objective | | Which parent EIs does this VR verify? |
| `objective` | prompt | pre_conditions | | State the CAPABILITY being verified, not mechanism |
| `pre_conditions` | prompt | step_instructions | | System state before verification -- must be reproducible |
| `step_instructions` | prompt | step_expected | loop: steps | What you are about to do (copy-pasteable commands) |
| `step_expected` | prompt | step_actual | loop: steps | What you expect BEFORE executing |
| `step_actual` | prompt | step_outcome | loop: steps, **commit: true** | What you observed (raw evidence, not summary) |
| `step_outcome` | prompt | more_steps | loop: steps | Pass or Fail with discrepancy note |
| `more_steps` | gate (yesno) | yes: step_instructions, no: summary_outcome | loop: steps | More verification steps? |
| `summary_outcome` | prompt | summary_narrative | | Overall Pass/Fail |
| `summary_narrative` | prompt | end | | Brief narrative overview |

The `step_actual` prompt has `commit: true`, meaning the engine performs an automatic git commit when this response is recorded, pinning the project state to the observation moment.

---

## Interactive Authoring System

VRs are authored through a four-layer system of files and engines.

### The Three File Layers

| Layer | File | Location | Purpose |
|-------|------|----------|---------|
| Session | `{DOC_ID}.interact` | User workspace | Live authoring state (JSON). Created on checkout, deleted on checkin. |
| Source | `{DOC_ID}.source.json` | `.meta/{type}/` | Permanent record of all responses. Written on checkin. |
| Compiled | `{DOC_ID}.md` | `QMS/{path}/` | Rendered Markdown. Generated from source + template on checkin. |

### Template Tag Vocabulary

Tags are embedded in HTML comments within the template Markdown.

**Flow tags:**

| Tag | Syntax | Purpose |
|-----|--------|---------|
| `@template` | `@template: name \| version: N \| start: id` | Template header (required, exactly once) |
| `@prompt` | `@prompt: id \| next: id [\| commit: true] [\| default: value]` | Content prompt. Response stored in `{{id}}`. |
| `@gate` | `@gate: id \| type: yesno \| yes: id \| no: id` | Flow-control decision. Routes only, no compiled content. |
| `@loop` | `@loop: name` | Repeating block start. `{{_n}}` = iteration counter. |
| `@end-loop` | `@end-loop: name` | Repeating block end. |
| `@end-prompt` | `@end-prompt` | Guidance boundary marker. Ends guidance text after a prompt/gate. |
| `@end` | `@end` | Terminal state. |

**Attributes:**

| Attribute | Used On | Purpose |
|-----------|---------|---------|
| `next: id` | @prompt | Unconditional transition to next node |
| `type: yesno` | @gate | Gate accepts yes or no |
| `yes: id` / `no: id` | @gate | Conditional routing |
| `default: value` | @prompt | Auto-fill value (author can override). Special values: `today`, `current_user` |
| `commit: true` | @prompt | Engine commits project state when response is recorded |

### Response Model (REQ-INT-008, REQ-INT-009)

Every response is a **timestamped append-only list**, not a scalar. The initial response creates a single-entry list. Amendments append -- they never replace or delete prior entries.

```json
{
  "responses": {
    "objective": [
      {
        "value": "Verify API endpoint returns correct response",
        "author": "claude",
        "timestamp": "2026-02-22T01:15:00Z"
      }
    ],
    "step_actual.1": [
      {
        "value": "Output: 4 constraints satisfied",
        "author": "claude",
        "timestamp": "2026-02-22T01:20:00Z",
        "commit": "abc1234"
      },
      {
        "value": "Output: 5 constraints satisfied (rerun after fix)",
        "author": "claude",
        "timestamp": "2026-02-22T02:00:00Z",
        "reason": "Reran after hotfix applied",
        "commit": "def5678"
      }
    ]
  }
}
```

Entry fields:

| Field | Always Present | Purpose |
|-------|----------------|---------|
| `value` | Yes | The response content |
| `author` | Yes | Who recorded this entry |
| `timestamp` | Yes | When recorded (ISO 8601 UTC) |
| `reason` | Only on amendments | Why the entry was amended |
| `commit` | Only on commit-enabled prompts | Git commit hash at moment of observation |

### Source File Structure (REQ-INT-006)

```json
{
  "doc_id": "CR-091-VR-001",
  "template": "VR",
  "template_version": 5,
  "cursor": "step_expected",
  "cursor_context": { "loop": "steps", "iteration": 2 },
  "metadata": {
    "parent_doc_id": "CR-091",
    "vr_id": "CR-091-VR-001",
    "title": "Verify interactive engine"
  },
  "responses": { ... },
  "loops": {
    "steps": {
      "iterations": 2,
      "closed": false,
      "reopenings": []
    }
  },
  "gates": {
    "more_steps.1": { "value": "yes", "timestamp": "..." }
  }
}
```

### Iteration-Indexed IDs

Prompts inside a `@loop` block get iteration-indexed IDs: `{base_id}.{N}`.

| Source Key | Meaning |
|------------|---------|
| `step_instructions.1` | Step 1 instructions |
| `step_actual.2` | Step 2 actual observation |
| `more_steps.1` | Gate decision after step 1 |

Functions `make_iteration_id(base, N)` and `parse_iteration_id(id)` in `interact_source.py` handle this.

---

## The Interaction Engine (`interact_engine.py`)

The `InteractEngine` class manages the authoring session.

### Core Operations

| Method | Purpose |
|--------|---------|
| `get_current_prompt_info()` | Returns status, guidance, and display ID for the current prompt |
| `respond(value, author, reason, commit_hash)` | Record response to current prompt, advance cursor |
| `respond_gate(value, author)` | Record yes/no gate decision, route accordingly |
| `goto(prompt_id, reason)` | Navigate to a previously-answered prompt for amendment |
| `cancel_goto()` | Cancel amendment mode, return to previous position |
| `reopen_loop_cmd(loop_name, reason, author)` | Reopen a closed loop for additional iterations |
| `get_progress()` | List all prompts with fill status |

### Cursor Management

The engine tracks position via `cursor` (current node ID) and `cursor_context` (loop name, iteration number, goto return info).

- **Sequential enforcement** (REQ-INT-014): Responses must be given in template order. You cannot skip ahead.
- **Amendment mode**: `goto` saves current position, moves to target; after responding, returns automatically.
- **Loop reopening**: Closed loops can be reopened with a reason, starting a new iteration.

### Contextual Interpolation (REQ-INT-015)

Guidance text supports `{{id}}` placeholders that resolve to:
1. `{{_n}}` -- current loop iteration number
2. Metadata fields (e.g., `{{parent_doc_id}}`)
3. Previously recorded responses (e.g., `{{objective}}`)

---

## The Compiler (`interact_compiler.py`)

`compile_document(source, template_text)` transforms source + template into final Markdown.

### Compilation Pipeline

| Phase | Operation |
|-------|-----------|
| 0 | Strip template preamble (template's own frontmatter and notice) |
| 1 | Strip all `@tag` comments and inter-tag guidance prose; `@end-prompt` marks guidance boundary |
| 1.5 | Auto-inject metadata: `date` (earliest response), `performer` (all authors), `performed_date` (latest response) |
| 2 | Substitute `{{placeholders}}` with context-aware rendering |
| 3 | Expand loop iterations with subsection numbering |
| 4 | Clean up excessive blank lines |

### Context-Aware Rendering (REQ-INT-024)

| Context | Rendering |
|---------|-----------|
| **Table row** (line starts with `\|`) | Value only, no attribution |
| **Block** (any other line) | Blockquote with attribution lines below |

Amendment trails render superseded entries with strikethrough (`~~old value~~`).

### Loop Expansion (REQ-INT-025)

The template contains a single step block with `{{_n}}` placeholders. The compiler expands this into numbered subsections:

```markdown
### 4.1 Step 1

**Instructions:**
> Run the test suite

*-- claude, 2026-02-22 01:15:00*

**Expected:**
> All tests pass

*-- claude, 2026-02-22 01:15:30*

**Actual:**

```
4 tests passed, 0 failed
```

*-- claude, 2026-02-22 01:16:00 | commit: abc1234*

**Outcome:**
> Pass

*-- claude, 2026-02-22 01:16:30*
```

Each step subsection has four labeled blocks: Instructions, Expected, Actual (in a code fence), Outcome.

---

## CLI Operations

For command syntax and detailed CLI behavior, see the [CLI Reference](../../qms-cli/docs/cli-reference.md).

**Key commands:**
- `interact` (no flags) -- shows current prompt status and guidance
- `interact --respond` -- records a response to the current prompt
- `interact --goto` -- navigates to a previously-answered prompt for amendment
- `interact --reopen` -- reopens a closed loop for additional iterations
- `interact --progress` -- shows fill status of all prompts
- `interact --compile` -- previews compiled Markdown output

---

## Engine-Managed Commits (REQ-INT-020)

When a prompt has `commit: true` (only `step_actual` in the VR template), the engine:

1. Stages all changes in the project working tree (`git add -A`)
2. Commits with message: `[QMS] auto-commit | {doc_id} | {prompt_id} | Evidence capture during VR execution`
3. Records the short commit hash (7 chars) in the response entry

This pins the project state at the exact moment of observation, enabling verifiers to checkout that commit to see the code/config/output that produced the evidence.

---

## Naming Convention

```
{PARENT_DOC_ID}-VR-NNN
```

| Example | Meaning |
|---------|---------|
| `CR-091-VR-001` | First VR under CR-091 |
| `CR-091-VAR-001-VR-001` | VR under a VAR |
| `CR-091-ADD-001-VR-001` | VR under an ADD |

---

## Parent/Child Relationships

| Relationship | Details |
|--------------|---------|
| Valid parent types | [CR](CR.md), [VAR](VAR.md), [ADD](ADD.md) |
| Invalid parent types | INV, TP, ER, SOP, etc. |
| Required parent state | **IN_EXECUTION** (enforced at creation time) |
| Children | None (VRs are leaf documents) |
| Attachment flag | `True` -- enables cascade close and relaxed close rules |

---

**Key creation points:**
- VRs require a `--parent` flag and `--title`
- Parent type must be CR, VAR, or ADD
- **Parent must be IN_EXECUTION** (enforced at creation)
- **Born IN_EXECUTION**: VRs are created directly at version `1.0` in `IN_EXECUTION` status, skipping the pre-approval lifecycle
- An interactive session is automatically initialized on creation

---

## Lifecycle

VR has a **truncated lifecycle** -- it skips the entire pre-approval workflow:

```
Created as IN_EXECUTION (v1.0)
  -> IN_POST_REVIEW -> POST_REVIEWED
  -> IN_POST_APPROVAL -> POST_APPROVED
  -> CLOSED
```

The rationale: the VR template *is* the pre-approved protocol. The template was approved through the TEMPLATE document control process. Creating a VR from it is analogous to releasing a pre-approved document for execution.

### Status Transitions

| From | Action | To |
|------|--------|----|
| IN_EXECUTION | route --review | IN_POST_REVIEW |
| IN_POST_REVIEW | review (recommend) | POST_REVIEWED |
| POST_REVIEWED | route --approval | IN_POST_APPROVAL |
| IN_POST_APPROVAL | approve | POST_APPROVED |
| POST_APPROVED | close | CLOSED |

**Additional transitions:**

| From | Action | To | Notes |
|------|--------|----|-------|
| IN_POST_REVIEW | withdraw | IN_EXECUTION | |
| IN_POST_APPROVAL | withdraw | POST_REVIEWED | |
| IN_POST_APPROVAL | reject | POST_REVIEWED | |
| POST_REVIEWED | checkout | IN_EXECUTION | Continue execution |
| POST_REVIEWED | revert | IN_EXECUTION | |

**Attachment-specific behavior:**

As attachment documents, VRs can be closed from **any non-terminal status** (not just POST_APPROVED). This is essential for cascade close behavior when the parent closes -- VRs are automatically finalized regardless of their current workflow state.

---

## Checkin Behavior

VR checkin follows a special interactive path:

1. Loads the `.interact` session and seed template
2. **Compiles** source + template into final Markdown
3. Archives previous version if IN_EXECUTION
4. Writes compiled Markdown to QMS draft path
5. Saves source to `.meta/` as a permanent record (`.source.json`)
6. Cleans up workspace files

The compiled Markdown is what gets reviewed and approved -- reviewers see the rendered document, not the raw source data.

---

## Checkout Behavior

VR checkout follows an interactive path:

1. Checks for existing `.source.json` in `.meta/` (from previous checkin)
2. If found, seeds the session from it (resuming where the author left off)
3. If not found, creates a fresh source from the template
4. Saves `.interact` session file to workspace
5. Creates a placeholder `.md` in workspace with instructions to use `qms interact`

---

## Cascade Close

When a parent document closes, the CLI handles VR cascade closure:

1. Scans `.meta/VR/` for children matching `{parent_id}-VR-NNN`
2. For checked-out VRs: auto-compiles from `.interact` session or `.source.json` or empty source
3. Promotes draft to effective
4. Records CLOSE + STATUS_CHANGE in audit trail
5. Updates meta to CLOSED
6. Cleans up workspace files across all users

This ensures VRs are properly finalized even if they were still being authored when the parent closed.

---

---

## See Also

- [Interactive Authoring](../08-Interactive-Authoring.md) -- Template tags, source data model, interaction lifecycle
- [Child Documents](../07-Child-Documents.md) -- VR lifecycle, evidence standards, GMP batch record analogy
- [SDLC](../10-SDLC.md) -- VRs as an RTM verification type
- [TEMPLATE Reference](TEMPLATE.md) -- How TEMPLATE-VR is governed (dual-copy system)
- [QMS Glossary](../QMS-Glossary.md) -- Term definitions
