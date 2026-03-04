# Frontmatter-Driven Interaction: Eliminating the Workflow Engine

## Context

This document captures a design insight from Session-2026-02-27-001 that fundamentally simplifies the interactive document architecture proposed in CR-107. Rather than maintaining a separate workflow engine (`qms interact`, `.interact` session files, `interact_engine.py`, `interact_compiler.py`), the existing checkout/checkin lifecycle can drive interactive authoring natively through Jinja2 conditional rendering and incremental frontmatter population.

---

## Why Documents

The document-based approach is not an implementation choice — it is an architectural thesis about how to orchestrate AI agents.

### The Convergence

A document in this system is simultaneously five things that are normally separate tools:

| Role | What it means | Traditional tool |
|------|--------------|-----------------|
| **Instruction** | The rendered prompt tells the agent what to do next | Task tracker |
| **Workspace** | The agent does the work by editing the same document | Code editor |
| **State** | The frontmatter IS the current state, on disk, always | Database |
| **Evidence** | The checkin history proves what was done and when | Logging system |
| **Communication** | Agents coordinate by passing documents through checkout/review/approval | Messaging platform |

This convergence is the source of the system's power. There is no separate orchestration layer — the document IS the orchestration.

### Crash Resilience

AI agents are inherently stateless between invocations. They don't remember previous sessions. Every system that relies on an agent maintaining in-memory state — a running process, a session object, a websocket connection — is building on sand.

A document on disk doesn't care. It's the same file whether the agent that reads it next is the same instance, a fresh spawn, or a completely different model. If the system crashes, the documents remain exactly where they fell. A new set of agents reads them and picks up where the previous ones left off. There is no session to recover, no state to reconstruct, no handoff protocol.

This is why `qms interact` as a command-line session was always wrong for this project. A CLI session is ephemeral state. The `.interact` session files were a mitigation — saving state to disk so it could be recovered. The frontmatter-driven design eliminates the problem rather than mitigating it. There is no session. There is only the document.

### Guidance Injection

The rendered document is a prompt. Not metaphorically — literally. When an AI agent checks out a document, the Jinja2 template has produced text that tells the agent what to do, what options are valid, what context matters, and where to put its response. The template author is programming agent behavior through document design.

Every conditional branch in the template is a different instruction set, activated by the data state. Changes to how agents are instructed go through the same CR/review/approval process as everything else. Agent behavior is governed by the same change control that governs the code the agents produce.

### The Paperwork Principle

This approach mirrors how complex organizations worked before the invention of computers: documents as the universal state medium, routed between workers who each perform their role and pass the document along.

| Pre-computer | QMS |
|-------------|-----|
| The form | The template (Jinja2 source) |
| Filling in the form | Editing frontmatter / inline responses |
| The routing slip | Document status + workflow transitions |
| The filing cabinet | `QMS/.source/` + `QMS/.meta/` |
| The carbon copy | `.audit/` JSONL trail |
| The signature | Review recommend / approval |
| The clerk's desk | `.claude/users/{user}/workspace/` |
| The outbox | `qms route` |
| The inbox | `qms inbox` |

These systems worked for centuries because they had a property that in-memory computing abandoned: **the state survives the worker.** The clerk doesn't need to remember what they were doing — the form on their desk tells them. The next clerk doesn't need a handoff meeting — they read the form.

That property is exactly what AI agents need. Most agent orchestration frameworks build elaborate state machines, session managers, and recovery protocols to compensate for the fundamental fragility of in-process state. The document-based approach doesn't need any of that because the state was never in-process to begin with.

### Robustness by Default

Most orchestration systems are fragile by default and add robustness through engineering (retry logic, checkpointing, distributed consensus). This system is robust because the medium itself — files on disk — is durable. The engineering effort goes into the document design, not into keeping the system alive.

---

## The Insight

A Jinja2 template is a pure function: given a set of frontmatter values, produce an output. If few values are populated, the output is a prompt asking for the next value. If all values are populated, the output is the complete document. The transition from "authoring mode" to "finished document" is not a mode switch — it's just the final conditional branch.

The checkout/checkin cycle IS the workflow engine:

1. **Render** shows the current prompt (determined by which fields are populated)
2. **User responds** — either by editing frontmatter fields or by writing inline responses in marked regions
3. **Checkin** extracts inline responses, merges with frontmatter values, populates source, re-renders
4. **New render** shows the next prompt (because the data state changed)
5. **Repeat** until all fields are collected
6. **Final render** is the complete document

No cursor variable is needed. The "cursor" is implicit in the set of non-null fields. The Jinja2 conditionals examine what exists and render accordingly.

---

## Three Tiers of Authoring

Not all documents need the same level of interactivity. The design supports three tiers, distinguished by what the checkin process enforces:

### Tier 1: Drafting

**Documents:** RTM, RS, SOP, and other non-executable types.

The author writes the document in one or more checkout/checkin cycles. Jinja2 variables in frontmatter are a convenience — they prevent manual maintenance of values like commit hashes. There is no sequence, no enforcement, no temporal dimension. The author can fill in all frontmatter fields at once and check in.

This is not interactive. It is templated drafting.

### Tier 2: Guided Authoring

**Documents:** CR (EI table construction), potentially others.

The prompt-and-response mechanism helps the author construct the document correctly. "What type of change?" leads to "Which systems?" leads to the EI table, with required EIs (pre-execution baseline, post-execution baseline) auto-injected based on the answers. This improves document quality and completeness.

But if the author filled in all the fields at once and checked in, nothing bad happens. The temporal order doesn't matter; the final content does.

### Tier 3: Sequential Execution

**Documents:** VR.

The interactivity is not a convenience — it is the enforcement mechanism. The entire point is to prove that verification steps were performed in order, at specific times, with specific system state. This requires:

- **Per-response timestamps** — each response is recorded at the moment of checkin, not reconstructed later. The timestamp IS evidence.
- **Sequential enforcement** — you cannot answer step 3 before step 2. The checkin process must refuse out-of-order responses.
- **Auto-commit hooks** — certain responses trigger a git commit to anchor the codebase state at the moment of verification. The commit hash becomes part of the evidence.
- **Immutable amendment trail** — a response, once submitted, cannot be silently overwritten. Amendments preserve the original with strikethrough and record when and why the change was made.

These requirements are about temporal integrity. A VR isn't documenting what the author thinks — it's documenting what the author *observed at a specific moment*. The sequential, timestamped, committed nature of the process is what makes it credible evidence rather than post-hoc narrative.

### Tier Comparison

| | Tier 1 (Drafting) | Tier 2 (Guided) | Tier 3 (Execution) |
|---|---|---|---|
| Fill multiple fields per checkin? | Yes | Yes | Only the current prompt's fields |
| Overwrite a previous value? | Yes | Yes | No — amendment only |
| Per-field timestamps? | No | No | Yes — recorded at checkin |
| Auto-commit on certain fields? | No | No | Yes — template declares triggers |
| Checkin order matters? | No | No | Yes — sequential enforcement |

The template declares which tier it operates in. For tiers 1 and 2, checkin is permissive. For tier 3, checkin enforces temporal constraints. The core mechanism is the same across all tiers — edit workspace, check in, render, repeat. The difference is what the checkin process enforces.

---

## Conventions

### Placeholder Syntax

Two placeholder conventions serve distinct roles:

| Syntax | Meaning | Consumed by |
|--------|---------|-------------|
| `{{ expression }}` | Jinja2 expression — resolved by the render engine | Jinja2 |
| `<<placeholder>>` | Human-replaceable scaffolding — replaced by the author | Human |

`<<placeholder>>` is used for one-time scaffolding in template frontmatter (e.g., `system_name: <<Human-readable system name>>`) and for inline response regions (e.g., `<<Place response here.>>`). It has no meaning to Jinja2, YAML, markdown, or HTML — it passes through all layers untouched and is recognized only by humans and the checkin extraction logic.

### Inline Response Regions

Freetext responses are collected via inline response regions in the rendered workspace. The region is delimited by HTML comment markers that identify the target frontmatter field:

```
<!-- @response: description -->
<<Place response here.>>
<!-- @end-response -->
```

The user replaces the placeholder with plain text:

```
<!-- @response: description -->
Fix particle collision detection in engine/simulation.py
to handle edge cases where particles overlap at spawn.
<!-- @end-response -->
```

At checkin, the CLI extracts everything between the markers, trims whitespace, and writes it to the named frontmatter field (`user_properties.description`). The markers are invisible in most markdown renderers, so the response region looks like plain document content to the author.

---

## Architecture

### Single File, Two Sections

Every template is one QMS-controlled file with two sections:

1. **YAML frontmatter** — declares the schema (all user property keys with null defaults or `<<placeholder>>` scaffolding). Includes both simple metadata fields and response fields that the interactive workflow collects.

2. **Jinja2 body** — contains conditional logic that renders different output depending on which frontmatter fields are populated. Early branches render prompts; the final branch renders the complete document.

### Document Lifecycle

```
Template (static)                  Source (growing)               Workspace (rendered)
─────────────────                  ───────────────                ──────────────────────
YAML schema:                       YAML values:                   Rendered view:
  change_type: null                  change_type: null              "Prompt: What type
  subsystem: null                    subsystem: null                 of change? Set
  description: null                  description: null               change_type to..."
Jinja2 body:
  {% if not change_type %}
    show prompt 1
  {% elif ... %}                     ── user sets ──►
    show prompt 2                    change_type: code
  {% else %}
    render final doc                 ── checkin ──►
  {% endif %}                        re-render
                                                                   "Prompt: Which
                                     change_type: code              subsystem? Set
                                     subsystem: null                subsystem to..."
                                     description: null
                                                                    ── user sets ──►
                                     change_type: code              subsystem: engine
                                     subsystem: engine
                                     description: null              ── checkin ──►
                                                                    re-render

                                                                   "Prompt: Describe
                                                                    the engine changes."
                                                                    <!-- @response -->
                                                                    <<Place response>>
                                                                    <!-- @end-response -->

                                                                    ── user writes ──►
                                     change_type: code              inline response
                                     subsystem: engine
                                     description: null              ── checkin extracts,
                                                                    populates, re-renders

                                     change_type: code
                                     subsystem: engine
                                     description: "Fix..."         "# CR-108: Fix...
                                                                    ## 1. Change Type
                                                                    code
                                                                    ## 2. Subsystem
                                                                    engine
                                                                    ## 3. Description
                                                                    Fix..."
```

The template never changes. The source frontmatter grows. Each render reflects the current state.

### Two Input Surfaces

Authors respond to prompts through two mechanisms, matched to the nature of the data:

| Data Type | Input Surface | Examples |
|-----------|--------------|----------|
| Constrained choices | Frontmatter field | `change_type: code`, `result: Pass` |
| Short structured values | Frontmatter field | `qualified_commit: abc123`, `rs_version: '22.0'` |
| Freetext prose | Inline response region | Descriptions, analyses, justifications |

The template author decides which mechanism each prompt uses. A prompt for "which subsystem?" instructs the user to set a frontmatter field. A prompt for "describe the changes" renders an inline response region. Both end up in the same place — `user_properties` in `.meta/`.

A single prompt can use both surfaces: "Set `result` to `Pass` or `Fail` in the frontmatter, and describe your observations below:"

### State Machine via Conditionals

The prompt tree is encoded as Jinja2 conditionals that check which fields are populated:

```jinja2
{% if not user.change_type %}
{# Prompt 1: ask for change_type #}

{% elif user.change_type == "code" and not user.subsystem %}
{# Prompt 2a: ask for subsystem (code path) #}

{% elif user.change_type == "docs" and not user.document_set %}
{# Prompt 2b: ask for document_set (docs path) #}

{% elif not user.description %}
{# Prompt 3: ask for description (both paths converge) #}

<!-- @response: description -->
<<Describe the changes you intend to make.>>
<!-- @end-response -->

{% else %}
{# All collected — render final document #}
{% endif %}
```

Branching is natural: the response to one field determines which subsequent field the template asks for. Property-based transitions work the same way — the template can condition on any frontmatter value, whether user-provided or system-populated.

### List-Based Responses

For workflows with repeating prompts (e.g., VR verification steps), frontmatter uses a YAML list instead of individual named fields:

```yaml
user_responses:
  - step: 1
    expected: "Login form appears"
    actual: "Login form appeared correctly"
    result: Pass
```

The template checks `user_responses | length` to determine progress and prompt for the next entry.

---

## The Checkin Enhancement

The checkin process gains a response extraction pass before the existing frontmatter processing:

```
Current checkin:
  1. Parse workspace frontmatter -> extract values
  2. Write to user_properties
  3. Save to source, render

Enhanced checkin:
  1. Scan workspace body for <!-- @response: FIELD --> markers
  2. Extract text between markers, trim whitespace
  3. Inject extracted values into workspace frontmatter (in memory)
  4. Parse workspace frontmatter -> extract values (now includes inline responses)
  5. Write to user_properties
  6. Save to source (frontmatter updated, Jinja2 body unchanged), render
```

Steps 1-3 are new. The rest is unchanged. From the frontmatter/source/render system's perspective, the inline response arrived via frontmatter — it doesn't know or care that the user typed it inline. The inline extraction is a preprocessing step that feeds into the existing pipeline.

For tier 3 (sequential execution) templates, the checkin process adds enforcement after extraction:

```
Tier 3 checkin (additional steps after extraction):
  3a. Compare extracted/edited fields against the current prompt's expected fields
  3b. Reject if fields outside the current prompt's scope were modified
  3c. Reject if previously-set fields were modified (amendment requires explicit flag)
  3d. Timestamp the accepted response fields individually in .meta/
  3e. If template declares an auto-commit trigger for this field, execute commit
```

The core mechanism is the same. The enforcement layer is additive and activated only when the template declares `tier: sequential` (or equivalent).

---

## What This Eliminates

| Current Component | Status Under This Design |
|-------------------|-------------------------|
| `qms interact` command | Eliminated — authors use checkout/checkin |
| `.interact` session files | Eliminated — state lives in source frontmatter |
| `interact_engine.py` | Eliminated — Jinja2 conditionals are the state machine |
| `interact_source.py` | Eliminated — source data is YAML frontmatter |
| `interact_compiler.py` | Eliminated — Jinja2 is the compiler |
| `compile_document()` | Eliminated — `jinja2.render()` replaces it |
| `@prompt` / `@gate` / `@loop` annotation parser | Eliminated — no annotations needed |
| Workflow spec files (proposed in interactive engine redesign) | Never needed — template is self-contained |

What remains: checkout, edit frontmatter / write inline responses, checkin, render. The existing lifecycle.

---

## What This Preserves

The design preserves every capability of the current interactive system:

- **Sequential prompting** — template conditionals enforce ordering
- **Branching** — `{% if user.field == "value" %}` conditions on prior responses
- **Property-based transitions** — conditions on document properties or system metadata
- **Loops / repeating sections** — YAML list fields with `{% for %}` rendering
- **Progressive disclosure** — user sees one prompt at a time plus running summary
- **Deterministic rendering** — same template + same frontmatter = same output, always
- **Temporal evidence** (tier 3) — per-field timestamps, sequential enforcement, auto-commits
- **Amendment trails** (tier 3) — immutable history with strikethrough rendering

---

## Prompt Rendering Convention

Each prompt rendered by the template should include:

1. **The question** — what information is being requested
2. **Valid options** — if the response is constrained (e.g., `code` or `docs`)
3. **Response mechanism** — either an instruction naming the frontmatter field to set, or an inline response region, or both
4. **Responses collected so far** — running summary of completed fields (provides context and confirms prior entries)

Example with frontmatter response:

```markdown
## Current Prompt

Which subsystem does this affect?

Set `subsystem` to one of: `engine`, `ui`, `solver`

Then check in this document.

### Responses Collected

| Field | Value |
|-------|-------|
| change_type | code |
```

Example with inline response:

```markdown
## Current Prompt

Describe the engine changes you intend to make:

<!-- @response: description -->
<<Place response here.>>
<!-- @end-response -->

Then check in this document.

### Responses Collected

| Field | Value |
|-------|-------|
| change_type | code |
| subsystem | engine |
```

---

## Single-File Rationale

The template is a QMS-controlled document. Having one file under change control means:

- One CR to authorize changes
- One review cycle to verify correctness
- One version to track
- No drift between a workflow spec and a rendering template
- A reviewer reads the template top-to-bottom and sees the entire interactive flow and output structure in one pass

This was a deliberate design constraint from the Lead: scattering the workflow across multiple controlled files adds change control overhead with no compensating benefit.

---

## Open Design Questions

### 1. Checkin Validation

When the user sets `subsystem: engine`, should checkin validate that "engine" is a legal value? The template knows the valid options (it rendered them), but the checkin process doesn't parse the template.

Options:
- **(a) No validation at checkin.** Let the next render produce unexpected output if the value is wrong. The user sees the problem immediately and can fix it on the next cycle. Simplest to implement.
- **(b) Encode valid options in the frontmatter schema.** The template frontmatter includes validation metadata that the checkin process reads. Adds complexity to the schema format.
- **(c) Validate by rendering.** After checkin writes the new values, render the template. If the output doesn't contain a recognized prompt or final document structure, reject the checkin. Fragile.

### 2. Amendment Trail (Tier 3)

The current VR system tracks response history — if a user changes a previously-set response, the old value gets strikethrough and the new value appears with attribution. Under this design, editing a frontmatter field simply overwrites the previous value.

Options:
- **(a) No amendment tracking in v1.** Overwrite is fine for tiers 1 and 2. Add amendment history for tier 3 later if needed.
- **(b) Checkin detects changes to previously-set fields** and maintains a history list in metadata (not in frontmatter — the user shouldn't see or manage this). The Jinja2 template can render amendment trails via a filter on the history data.
- **(c) Use YAML lists for all response fields** so appending is the natural operation. The template renders the last entry as current and prior entries as superseded.

### 3. Branching and Dead Fields

If the user sets `change_type: code` (which prompts for `subsystem`), then later changes `change_type: docs`, the `subsystem` field becomes irrelevant. The populated value is now orphaned.

Options:
- **(a) Template ignores it.** The Jinja2 conditionals simply don't reference `subsystem` on the `docs` path. The value persists in frontmatter but is never rendered. Simplest.
- **(b) Checkin clears downstream fields** when an upstream field changes. This requires the checkin process to understand the dependency graph, which means parsing the template. Complex.
- **(c) Template renders a warning.** If `change_type == "docs"` and `subsystem` is populated, the template includes a note: "subsystem is set but not applicable to docs changes." Informative without requiring engine logic.

### 4. Cursor as System Property vs. Implicit State

The design as described uses implicit state (set of populated fields = cursor position). An explicit `cursor` system property is also possible:

- **Implicit:** The template's conditional logic determines the current prompt by examining field values. No additional state to manage. But the template's conditional tree must be carefully structured — every possible data state must map to exactly one prompt or the final document.
- **Explicit:** A system property `interaction_cursor` tracks the current position. The checkin process advances it (potentially by evaluating a transition rule from the frontmatter schema). The template conditionals check `cursor` rather than inferring state from field values. More robust for complex trees but introduces state that must be kept in sync with the data.

For tier 3, an explicit cursor is likely necessary — the sequential enforcement needs an authoritative "you are here" marker to determine which fields are currently valid to set.

### 5. Tier 3 Enforcement Scope

How much of the tier 3 enforcement should be in the checkin process vs. in the template? The checkin process needs to know the current prompt to enforce sequential access, which means it needs to understand the template's state machine — or at least have a cursor to reference.

Options:
- **(a) Cursor + field whitelist per prompt.** The template frontmatter declares, for each cursor position, which fields may be set. The checkin process reads the cursor, looks up the whitelist, and rejects changes to other fields. The template body handles rendering; the frontmatter handles enforcement.
- **(b) Render-based enforcement.** The checkin process renders the template to determine the current prompt, then validates that only the prompted fields were changed. Requires the checkin process to parse rendered output, which is fragile.
- **(c) Explicit cursor with template-declared transitions.** The template frontmatter includes a state machine (cursor -> next cursor, given field values). The checkin process evaluates transitions mechanically. The template body only handles rendering.

---

## Relationship to CR-107

This design is compatible with CR-107's unified lifecycle but simplifies it significantly:

- **Universal source files** — unchanged. Source in `QMS/.source/`, draft always derived.
- **Jinja2 render engine** — unchanged. `jinja2.render(source, context)` for all documents.
- **`.meta/` as data store** — unchanged. User properties populated from frontmatter at checkin.
- **Template as living schema authority** — unchanged. Schema synced at checkout.
- **Frontmatter as sole input channel** — **strengthened**. Frontmatter is not just the input channel for metadata — it's the input channel for interactive responses too. The interactive engine's second input channel (`qms interact`) is eliminated. Inline response regions are a UX convenience that feed into frontmatter at checkin — they are a second input *surface*, not a second input *channel*.

The key delta: CR-107 Section 4.3 describes "Two Input Channels, One Data Store" (frontmatter editing + interactive engine). This design reduces it to **One Input Channel, One Data Store** (frontmatter editing only). Inline response regions provide a more natural authoring surface for freetext content, but the data path is the same — checkin extracts inline content and writes it to frontmatter before the existing pipeline processes it.

---

## Relationship to Interactive Engine Redesign

The interactive engine redesign (Session-2026-02-22-004) proposed three independent artifacts: workflow specs, rendering templates, and source data. This design collapses all three into one:

- **Workflow spec** -> Jinja2 conditionals in the template body
- **Rendering template** -> the same Jinja2 template body (final `{% else %}` branch)
- **Source data** -> YAML frontmatter in the source file

The separation of concerns still exists conceptually (the template has workflow logic AND rendering logic), but it's unified in a single file rather than scattered across artifacts. The QMS change control process governs one document, not three.
