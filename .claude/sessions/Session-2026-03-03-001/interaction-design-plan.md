# Interaction Design Plan: Unified Interactive Document System

**Session:** 2026-03-03-001
**Purpose:** Final design for interactive documents within CR-107's unified document lifecycle.
**Status:** DRAFT — under review with Lead

---

## 1. Core Concept

Every QMS document follows one lifecycle:

```
TEMPLATE-{TYPE}.md  →  copied to QMS/.source/  →  rendered to QMS/{TYPE}/ (draft)
                                                    ↑
                                              QMS/.meta/ (data context)
```

For **non-interactive documents**, the author edits the source file directly. At checkin, frontmatter values are extracted into `.meta/`, and the source's Jinja2 body is rendered with the full metadata context to produce the draft. No interaction engine is involved.

For **interactive documents**, an additional layer sits between checkout and final rendering:

```
Source frontmatter (workflow graph)  +  .meta/ (current state)
        ↓
   Interaction Engine
        ↓
   TEMPLATE-INTERACT  →  workspace document (current prompt)
        ↓
   Agent edits workspace (inline response)
        ↓
   Checkin extracts response → writes to .meta/ → re-renders workspace
        ↓
   ... repeat until all prompts answered ...
        ↓
   Source Jinja2 body + complete .meta/  →  final rendered document
```

The presence of a `graph:` section in the source file's frontmatter is what activates the interaction layer. No graph → no interaction → direct editing.

### Authoring vs. Execution

Interactive documents participate in two distinct lifecycle phases, each with its own workflow:

1. **Authoring** (DRAFT state) — the document is being *built*. The interaction engine drives the author through prompts that construct the document's content. Example: building a VR step-by-step, or constructing a CR's EI table interactively.

2. **Execution** (IN_EXECUTION state) — the document has been approved and released. The interaction engine drives the executor through prompts that *act on* the content built during authoring. Example: completing each EI in a CR (recording status, evidence, completion timestamps), or executing each verification step in a VR.

These are different workflows operating on the same zones at different lifecycle phases. The authoring phase *creates* data; the execution phase *acts on* it. A zone's graph declares sub-workflows for each phase it participates in:

```yaml
graph:
  zones:
    ei_table:
      authoring:    # active during DRAFT
        collection: true
        nodes: ...  # prompts to build EIs
      execution:    # active during IN_EXECUTION
        each: ei_table    # iterates over items built during authoring
        nodes: ...  # prompts to complete each EI
```

The engine selects the active phase based on the document's lifecycle state. Metadata from authoring becomes input data for execution — the EI definitions built during authoring are the items the executor completes.

Not all zones need both phases. A VR's step-building zone might only have an authoring workflow (the steps are both built and executed in a single pass during IN_EXECUTION). A zone could also have only an execution phase if its content is authored freeform.

### Fully vs. Partially Interactive Documents

Some document types are **fully interactive** — the entire document is authored through the interaction engine (e.g., Verification Records). The source body's Jinja2 template is used only for final rendering; during interaction, the workspace is entirely engine-controlled.

Other document types are **partially interactive** — most of the document is authored via freeform editing, but specific sections are interactive zones managed by the engine (e.g., a Change Record where the EI table is built interactively but the purpose statement is freeform). Interactive zones are delimited in the source body with markers:

```markdown
## Execution Items

<!-- @interactive: ei_table -->
<!-- @end-interactive -->

## References

(freeform — author edits directly)
```

The markers serve two purposes:
1. **For authors:** "Don't edit inside here — the engine manages this section."
2. **For the engine:** Where to inject the interactive UI for that zone during interaction.

When an interactive zone is active, the workspace renders the zone's interaction UI (current prompt, response region) inside the markers, with freeform sections visible and editable around it. When a zone's interaction is complete, the markers contain the rendered output for that zone.

---

## 2. Two Templates, Two Concerns

### TEMPLATE-{TYPE}.md (type-specific)

One per document type. Lives in `QMS/TEMPLATE/`. Controlled document.

**Frontmatter** declares:
- **Metadata schema** — the user property fields for this document type (same as CR-107's existing design)
- **Workflow graph** — the prompt sequence, gates, stamps, and transitions that define interactive authoring for this type. For partially interactive documents, the graph is organized into named **zones** corresponding to `@interactive` markers in the body.

**Body** contains:
- **Jinja2 template** for the final rendered document — sections, formatting, loops over collected data
- **Interactive zone markers** (`<!-- @interactive: zone_name -->` / `<!-- @end-interactive -->`) in partially interactive documents, identifying sections managed by the engine
- Never contains interaction logic (no "if we're on prompt 3, show this")
- For fully interactive documents (no zone markers), the entire body is used only for final rendering
- For partially interactive documents, freeform sections are always visible and editable; zone markers delimit engine-managed sections

Example structure (VR — fully interactive, execution-phase only):
```yaml
---
title: '<<Document title>>'
revision_summary: '<<Description of changes>>'

# Metadata schema (user properties)
schema:
  related_eis: { type: text }
  objective: { type: text }
  pre_conditions: { type: text }
  summary_outcome: { type: enum, values: [Pass, Fail] }
  summary_narrative: { type: text }

# Workflow graph — single phase, no zones (fully interactive)
# VRs are authored entirely during execution: the verifier builds
# and executes steps in one pass during IN_EXECUTION.
graph:
  phase: execution
  nodes:
    related_eis:
      prompt: "Which execution item(s) does this VR verify?"
    objective:
      prompt: "State what CAPABILITY is being verified..."
    pre_conditions:
      prompt: "Describe system state BEFORE verification begins..."
    step_instructions:
      prompt: "What are you about to do?..."
    step_expected:
      prompt: "What do you expect to observe?..."
    step_actual:
      prompt: "What did you observe?..."
      commit: true
    step_outcome:
      values: [Pass, Fail]
      prompt: "Did the observed output match your expectation?"
    more_steps:
      values: [yes, no]
      prompt: "Do you have additional verification steps?"
      yes: step_instructions
      no: summary_outcome
    summary_outcome:
      values: [Pass, Fail]
      prompt: "Overall outcome?"
    summary_narrative:
      prompt: "Brief narrative overview..."
---

{# === FINAL RENDITION TEMPLATE (fully interactive — no zone markers) === #}

# {{ doc_id }}: {{ title }}

## 1. Verification Identification

| Parent Document | Related EI(s) | Date |
|-----------------|---------------|------|
| {{ parent_doc_id }} | {{ related_eis }} | {{ date }} |

## 2. Verification Objective

{{ objective }}

## 3. Prerequisites

{{ pre_conditions }}

## 4. Verification Steps

{% for step in steps %}
### 4.{{ loop.index }} Step {{ loop.index }}

**Instructions:** {{ step.step_instructions }}

**Expected:** {{ step.step_expected }}

**Actual:**

```
{{ step.step_actual }}
```

*Commit: {{ step.step_actual_commit }} — {{ step.step_completed_at }}*

**Outcome:** {{ step.step_outcome }}

{% endfor %}

## 5. Summary

**Outcome:** {{ summary_outcome }}

{{ summary_narrative }}

**END OF VERIFICATION RECORD**
```

#### Partially Interactive Example (CR template with interactive EI table)

```yaml
---
title: '<<Change Record title>>'
revision_summary: '<<Description of changes>>'

schema:
  purpose: { type: text }
  impact_analysis: { type: text }
  # ... other freeform fields ...

# Graph organized into zones — each zone maps to an @interactive marker in the body.
# This zone participates in two lifecycle phases.
graph:
  zones:
    ei_table:

      # ── Authoring phase (DRAFT) ──
      # Build the EI table interactively.
      authoring:
        collection: true
        nodes:
          ei_type:
            values: [Implementation, Verification, Documentation]
            prompt: "What type of execution item is this?"
          ei_description:
            prompt: "Describe what this execution item accomplishes."
          ei_acceptance:
            prompt: "What are the acceptance criteria for this item?"
          add_another:
            values: [yes, no]
            prompt: "Add another execution item?"
            yes: ei_type
            no: ~

      # ── Execution phase (IN_EXECUTION) ──
      # Complete each EI built during authoring.
      execution:
        each: ei_table   # iterate over the collection from authoring
        nodes:
          ei_status:
            values: [Complete, Blocked, Deferred]
            prompt: "What is the status of EI-{{ item.index }}: {{ item.ei_description }}?"
          ei_evidence:
            prompt: "Provide evidence of completion for this item."
            commit: true
          ei_completed_at:
            stamp: true
---

{# === FINAL RENDITION TEMPLATE (partially interactive — zone markers below) === #}

# {{ doc_id }}: {{ title }}

## 1. Purpose

{{ purpose }}

## 2. Impact Analysis

{{ impact_analysis }}

## 3. Execution Items

<!-- @interactive: ei_table -->
| # | Type | Description | Acceptance | Status | Evidence |
|---|------|-------------|------------|--------|----------|
{% for ei in ei_table %}
| EI-{{ loop.index }} | {{ ei.ei_type }} | {{ ei.ei_description }} | {{ ei.ei_acceptance }} | {{ ei.ei_status | default("—") }} | {{ ei.ei_evidence | default("—") }} |
{% endfor %}
<!-- @end-interactive -->

## 4. References

(freeform)
```

In this example:
- **During authoring (DRAFT):** The author edits Purpose, Impact Analysis, and References as freeform text. The EI table zone shows interactive prompts to build EIs one at a time.
- **During execution (IN_EXECUTION):** The freeform sections are locked (document is approved). The EI table zone shows interactive prompts to complete each EI — iterating over the items built during authoring with `each: ei_table`.
- **Final rendering:** The table includes both authoring columns (Type, Description, Acceptance) and execution columns (Status, Evidence). The Jinja2 uses `default("—")` for execution fields that may not yet be filled.

### TEMPLATE-INTERACT.j2 (generic)

One for the entire QMS. Lives in `QMS/TEMPLATE/`. Controlled document.

Renders the workspace during interactive authoring. The workspace IS the user interface — there is no `qms interact` command. Everything the agent needs to do (respond, amend, review history, navigate) happens by editing this document and checking in.

The template renders different **views** depending on the engine state:

#### Prompt View (default)

The agent sees: the current prompt, a response region, and a navigation section. Nothing else.

```jinja2
# {{ doc_id }}{% if title %}: {{ title }}{% endif %}

{% if complete %}

> **Interaction complete.** Check in this document to render the final version.

{% else %}

{% if section %}**{{ section }}** | {% endif %}Prompt {{ progress.current }} of {{ progress.total }}

{{ current.prompt }}
{% if current.values %}

**Valid responses:** {{ current.values | join(' | ') }}
{% endif %}

<!-- @response: {{ current.node_id }} -->
<<Respond here>>
<!-- @end-response -->

{% endif %}

---

## Navigation

<!-- @nav -->

<!-- @end-nav -->

Available: HISTORY | PROGRESS | AMEND <field> [reason] | REOPEN <section> [reason] | PREVIEW
```

#### Amendment View

Rendered when the engine is in amendment mode (agent previously submitted `AMEND <field> [reason]`). Shows the current value, the prompt, and a response region for the new value.

```jinja2
# {{ doc_id }}: Amending "{{ amend.field }}"

**Current value:**

> {{ amend.current_value }}
>
> *{{ amend.author }}, {{ amend.timestamp }}*

**Reason for amendment:** {{ amend.reason }}

{{ amend.prompt }}
{% if amend.values %}

**Valid responses:** {{ amend.values | join(' | ') }}
{% endif %}

<!-- @response: {{ amend.field }} -->
<<Enter amended response>>
<!-- @end-response -->

---

## Navigation

<!-- @nav -->

<!-- @end-nav -->

Available: CANCEL (return without amending)
```

#### History View

Rendered when the agent submits `HISTORY`. Shows all collected responses grouped by section.

```jinja2
# {{ doc_id }}: Response History

{% for group in history %}
{% if group.section %}
### {{ group.section }}

{% endif %}
{% for entry in group.entries %}
**{{ entry.field }}:**

> {{ entry.value }}
>
> *{{ entry.author }}, {{ entry.timestamp }}{% if entry.commit %} | commit: {{ entry.commit }}{% endif %}*
{% if entry.amendments %}
{% for a in entry.amendments %}

> ~~{{ a.value }}~~ *({{ a.author }}, {{ a.timestamp }} | {{ a.reason }})*
{% endfor %}
{% endif %}

{% endfor %}
{% endfor %}

---

## Navigation

<!-- @nav -->

<!-- @end-nav -->

Available: RETURN (back to current prompt) | AMEND <field> [reason]
```

#### Progress View

Rendered when the agent submits `PROGRESS`. Shows all prompts with fill status.

```jinja2
# {{ doc_id }}: Progress

| # | Field | Status | Section |
|---|-------|--------|---------|
{% for item in progress_items %}
| {{ loop.index }} | {{ item.field }} | {{ "filled" if item.filled else "---" }} | {{ item.section or "" }} |
{% endfor %}

---

## Navigation

<!-- @nav -->

<!-- @end-nav -->

Available: RETURN | AMEND <field> [reason]
```

The views are deliberately simple. The Jinja2 is straightforward conditionals and loops — the complexity lives in the engine's context-building, not in the template.

#### Zone Rendering (partially interactive documents)

For partially interactive documents, TEMPLATE-INTERACT is NOT used to render the full workspace. Instead, the workspace is the source body itself, with zone markers replaced by engine-managed content. TEMPLATE-INTERACT renders only the UI fragment injected into the active zone:

```jinja2
{# Zone fragment — injected between @interactive markers #}

{% if zone_complete %}
{# Render final output for this zone using the source body's Jinja2 within the markers #}
{{ zone_rendered_content }}
{% elif zone_active %}
{% if zone_context %}
{{ zone_context }}

---

{% endif %}
{% if section %}**{{ section }}** | {% endif %}Prompt {{ progress.current }} of {{ progress.total }}

{{ current.prompt }}
{% if current.values %}

**Valid responses:** {{ current.values | join(' | ') }}
{% endif %}

<!-- @response: {{ current.node_id }} -->
<<Respond here>>
<!-- @end-response -->

---

### Navigation

<!-- @nav -->

<!-- @end-nav -->

Available: HISTORY | PROGRESS | AMEND <field> [reason]
{% else %}
*(Interactive — not yet started)*
{% endif %}
```

The `zone_context` variable lets the engine inject context from previously collected items — e.g., rendering the EI table built so far above the "Add another EI?" prompt. Whether to include this context is controlled by the zone's graph definition.

---

## 3. The Interaction Engine

### 3.1 Responsibilities

The engine is a stateless function that mediates between the source file, the metadata, and the workspace. It has two operations:

1. **Render** — Read source frontmatter (graph) + metadata (state) → determine active phase → determine current view → render TEMPLATE-INTERACT → write workspace
2. **Process** — Read workspace → extract response OR navigation command → validate → update metadata → re-render

The engine has no persistent state of its own. The current position in the graph is derived by walking the graph against the metadata: the first node whose field is not populated in metadata is the current node. The active phase is derived from the document's lifecycle state (DRAFT → authoring, IN_EXECUTION → execution). Navigation state (amendment mode, history view, etc.) is persisted in metadata under a `_navigation` key for crash resilience.

### 3.2 Graph Walking

The graph is a directed structure of nodes. Each node has an implicit `next` (the next node in declaration order) unless it specifies explicit transitions.

#### Phase Selection

The engine determines the active phase from the document's lifecycle state:

| Document State | Active Phase | Behavior |
|---|---|---|
| DRAFT | `authoring` | Engine walks authoring sub-graphs |
| IN_REVIEW, PRE_APPROVED | *(no interaction)* | Document is in workflow — no interactive editing |
| IN_EXECUTION | `execution` | Engine walks execution sub-graphs |
| POST_REVIEWED, POST_APPROVED | *(no interaction)* | Document is in post-workflow |
| EFFECTIVE, CLOSED, RETIRED | *(no interaction)* | Terminal states |

For graphs that declare a single `phase:` (e.g., VR with `phase: execution`), the engine only activates during that phase. For zones with both `authoring:` and `execution:` sub-graphs, the engine selects the sub-graph matching the current phase.

#### The `each:` Directive

Execution-phase sub-graphs can declare `each: <zone_name>` to iterate over items collected during authoring. Instead of a gate-driven loop, the engine walks the execution nodes once per item in the authoring-phase collection:

```yaml
execution:
  each: ei_table        # iterate over items from authoring
  nodes:
    ei_status: ...      # prompted once per EI
    ei_evidence: ...
    ei_completed_at: ...
```

The iteration variable `item` is available in prompt text (e.g., `{{ item.ei_description }}`), giving the executor context about what they're completing. The engine tracks progress per item in metadata under `interaction.ei_table[N]` — authoring fields and execution fields coexist in each item's dict.

#### Graph Walking

**Fully interactive documents** have a flat `graph.nodes` structure — the graph walks linearly from start to end:

```python
def find_current_node(graph, metadata):
    """Walk graph from start. Return first node not yet satisfied in metadata."""
    node = graph.start
    while node is not None:
        if node.type == "stamp":
            # Stamps are auto-satisfied — check if recorded
            if node.id not in metadata:
                return node  # needs auto-recording
            node = node.next
        elif node.type == "gate":
            if node.id not in metadata:
                return node  # needs response
            # Follow the chosen branch
            choice = metadata[node.id]
            node = node.routes[choice]
        elif node.type == "prompt":
            if node.id not in metadata:
                return node  # needs response
            node = node.next
    return None  # all nodes satisfied — interaction complete
```

**Partially interactive documents** have a `graph.zones` structure — each zone is an independent subgraph. The engine walks zones in declaration order, finding the first zone with unsatisfied nodes:

```python
def find_current_zone_and_node(graph, metadata):
    """Walk zones in order. Return (zone_name, node) for first unsatisfied zone."""
    for zone_name, zone in graph.zones.items():
        zone_meta = metadata.get("interaction", {}).get(zone_name, {})
        node = find_current_node(zone, zone_meta)
        if node is not None:
            return (zone_name, node)
    return (None, None)  # all zones complete
```

For nodes inside a loop (the step sequence in VR, or the EI collection in CR), the walk checks the section list in metadata. When a gate routes backward (`yes: step_instructions`), the engine appends a new section entry and re-enters the subgraph.

### 3.2.1 Zone-Aware Workspace Rendering

For **fully interactive documents** (no zone markers in source body), the workspace is entirely rendered by TEMPLATE-INTERACT — the source body is not visible during interaction.

For **partially interactive documents** (zone markers in source body), the workspace is the source body itself, with each `<!-- @interactive: zone_name -->` region replaced by the engine:

- **Active zone** (current zone has unsatisfied nodes): Engine injects the interactive UI (prompt, response region, navigation) inside the markers. The zone may also include context — e.g., the EI table built so far, rendered above the current ADD EI prompt.
- **Completed zone**: Engine renders the zone's final output inside the markers (e.g., the completed EI table).
- **Future zone** (not yet reached): Markers contain a placeholder like `(Interactive — not yet started)`.
- **Freeform sections** (outside all markers): Passed through unchanged — the author can edit them freely.

This means the workspace for a partially interactive document is a hybrid: freeform sections are directly editable, while interactive zones are engine-managed. The agent can write the Purpose section freeform while the EI table section shows an interactive prompt.

### 3.3 Node Types

Three node types, matching the graph conventions from Session 2026-03-02-001:

**Prompt** — Collects a response from the author.
- `id`: Field name written to metadata
- `prompt`: Text displayed to the author
- `values`: Optional constraint list (enum). If present, response must be one of these values.
- `commit`: If true, trigger a git commit when response is recorded. Commit hash stored alongside response.
- `next`: Implicit (next in declaration order) or explicit

**Stamp** — Auto-records a timestamp and optional commit hash. No user interaction.
- `id`: Field name written to metadata
- `stamp: true`: Marker
- Auto-processed when the engine encounters it during graph walking

**Gate** — Routes based on response value.
- `id`: Field name written to metadata
- `values`: Valid options
- `prompt`: Question text
- `yes`/`no` or `on: {value: node_id}`: Transition rules
- Backward edges (e.g., `yes: step_instructions`) create loops naturally

### 3.4 Section Model (Loops)

Loops emerge from backward edges in the graph. When a gate's transition points backward (e.g., `more_steps.yes → step_instructions`), the engine:

1. Appends a new empty dict to `metadata["steps"]` (the section list)
2. Re-enters the subgraph at the target node
3. All prompts in the subgraph write to `metadata["steps"][-1]` (current section)

Prompts outside a loop write to the root metadata dict. Prompts inside a loop write to the current section sub-dict. This distinction is declared in the graph structure — nodes between a loop-entry point and a backward-edge gate belong to the loop.

The current section is always `metadata["steps"][-1]`. The section count is `len(metadata["steps"])`.

### 3.5 Metadata Structure

All interactive response data lives in the document's `.meta/` JSON file alongside existing workflow metadata:

```json
{
  "doc_id": "CR-096-VR-001",
  "status": "IN_EXECUTION",
  "version": "1.0",
  "user_properties": {
    "title": "Hook Integration Test",
    "revision_summary": "Initial verification"
  },
  "interaction": {
    "related_eis": {
      "value": "EI-8",
      "author": "claude",
      "timestamp": "2026-03-03T10:00:00Z"
    },
    "objective": {
      "value": "Verify that service health monitoring...",
      "author": "claude",
      "timestamp": "2026-03-03T10:01:00Z"
    },
    "pre_conditions": {
      "value": "System running on branch cr-096...",
      "author": "claude",
      "timestamp": "2026-03-03T10:02:00Z"
    },
    "steps": [
      {
        "step_instructions": {
          "value": "Run health check endpoint...",
          "author": "claude",
          "timestamp": "2026-03-03T10:05:00Z"
        },
        "step_expected": {
          "value": "Service returns 200...",
          "author": "claude",
          "timestamp": "2026-03-03T10:06:00Z"
        },
        "step_actual": {
          "value": "Service returned 200...",
          "author": "claude",
          "timestamp": "2026-03-03T10:07:00Z",
          "commit": "fa515d7"
        },
        "step_completed_at": {
          "timestamp": "2026-03-03T10:07:00Z",
          "commit": "fa515d7"
        },
        "step_outcome": {
          "value": "Pass",
          "author": "claude",
          "timestamp": "2026-03-03T10:08:00Z"
        },
        "more_steps": {
          "value": "yes",
          "author": "claude",
          "timestamp": "2026-03-03T10:08:30Z"
        }
      },
      {
        "step_instructions": {
          "value": "Run integration test...",
          "author": "claude",
          "timestamp": "2026-03-03T10:10:00Z"
        }
      }
    ],
    "summary_outcome": null,
    "summary_narrative": null
  }
}
```

Key properties:
- **Flat fields** (related_eis, objective, etc.) live at `interaction.*`
- **Section fields** (step_instructions, step_outcome, etc.) live at `interaction.steps[N].*`
- **Zone fields** (for partially interactive docs) live at `interaction.<zone_name>.*` — e.g., `interaction.ei_table[N].ei_type`
- **Every response** carries `value`, `author`, `timestamp`, and optionally `commit`
- **Null fields** indicate prompts not yet answered
- **Amendment history** — if a response is amended, the field becomes a list of entries (append-only, most recent is active)

For partially interactive documents, each zone gets its own namespace under `interaction`. Authoring-phase and execution-phase fields coexist in the same item dicts:

```json
{
  "interaction": {
    "ei_table": [
      {
        "_comment": "EI-1 — authoring complete, execution complete",
        "ei_type": { "value": "Implementation", "author": "claude", "timestamp": "..." },
        "ei_description": { "value": "Implement feature X", "author": "claude", "timestamp": "..." },
        "ei_acceptance": { "value": "All tests pass", "author": "claude", "timestamp": "..." },
        "add_another": { "value": "yes", "author": "claude", "timestamp": "..." },
        "ei_status": { "value": "Complete", "author": "claude", "timestamp": "..." },
        "ei_evidence": { "value": "All tests pass, see CI run #42", "author": "claude", "timestamp": "...", "commit": "fa515d7" },
        "ei_completed_at": { "timestamp": "...", "commit": "fa515d7" }
      },
      {
        "_comment": "EI-2 — authoring complete, execution in progress",
        "ei_type": { "value": "Verification", "author": "claude", "timestamp": "..." },
        "ei_description": { "value": "Verify feature X", "author": "claude", "timestamp": "..." },
        "ei_acceptance": { "value": "VR passes", "author": "claude", "timestamp": "..." },
        "add_another": { "value": "no", "author": "claude", "timestamp": "..." },
        "ei_status": null,
        "ei_evidence": null,
        "ei_completed_at": null
      }
    ]
  }
}
```

The engine knows which fields belong to which phase from the graph declaration. During authoring, it stamps null placeholders for authoring nodes. When the document transitions to execution, it stamps null placeholders for execution nodes alongside the existing authoring data.

### 3.6 Checkin Flow for Interactive Documents

When the agent checks in an interactive document, the engine processes the workspace in two passes:

**Pass 1: Navigation** — Extract `<!-- @nav -->` content. If non-empty, process the navigation command:

| Command | Engine Action |
|---------|---------------|
| `HISTORY` | Set `_navigation.view: "history"`, re-render workspace with history view |
| `PROGRESS` | Set `_navigation.view: "progress"`, re-render workspace with progress view |
| `PREVIEW` | Render source Jinja2 body with current metadata, show as workspace |
| `AMEND <field> [reason]` | Set `_navigation: {mode: "amend", target: field, reason: reason, return_to: current_node}`, re-render with amendment view |
| `REOPEN <section> [reason]` | Append new empty section to `interaction.<section>`, record reopening, clear `_navigation`, re-render with prompt view at first node of section subgraph |
| `RETURN` | Clear `_navigation`, re-render with prompt view at current graph position |
| `CANCEL` | Clear `_navigation` (discard amendment), re-render with prompt view at `_navigation.return_to` |

If a navigation command is present, the response region is ignored. The workspace is re-rendered and the document stays checked out. No graph advancement occurs.

**Pass 2: Response** — If no navigation command, extract `<!-- @response: FIELD -->` content:

1. **Extract** — Scan workspace for response markers. Extract content, trim whitespace. If content is still `<<Respond here>>` or empty, reject with error.
2. **Validate** — Check that the extracted field matches the expected node ID (current prompt, or amendment target if in amendment mode). If the node has `values` constraint, check the response is in the allowed set.
3. **Record** — Write `{value, author, timestamp}` to metadata. If in amendment mode: append to existing field's entry list (preserving original), clear `_navigation`, return to `_navigation.return_to` position. If `commit: true` on the node: perform atomic git commit first, include hash.
4. **Advance** — Walk graph from the recorded node. Auto-process any stamp nodes (record timestamp/commit, continue). Stop at the next prompt or gate, or at graph completion.
5. **Re-render** — If the active phase's interaction is not complete: render TEMPLATE-INTERACT with next prompt view → workspace stays checked out. If phase interaction IS complete: render source Jinja2 body with full metadata → normal checkin completes (document returns to `QMS/`, lock released). Note: "complete" means the active phase's graph is fully satisfied — authoring completion and execution completion are independent events.

**Key behavior:** During active interaction, checkin always re-renders and keeps the document checked out. The document only truly checks in (returns to `QMS/`, lock released) when interaction is complete and the final rendition is generated. This is distinct from non-interactive checkin, which always completes fully.

**Informational output:** Every interactive checkin must produce a clear message telling the agent what happened. For a response: `Interactive checkin: response recorded for "<field>". Document re-rendered with next prompt — remains checked out.` For a navigation command: `Navigation: showing <view>. Document remains checked out.` For the final checkin: `Interaction complete. Final document rendered. Checked in <doc_id> (v<version>).` This prevents agents from assuming checkin means "done" and abandoning the interaction mid-flow.

### 3.7 Navigation State

Navigation state is persisted in metadata under `_navigation` for crash resilience:

```json
{
  "interaction": {
    "...responses...",
    "_navigation": {
      "mode": "amend",
      "target": "objective",
      "reason": "Correcting scope description",
      "return_to": "step_expected"
    }
  }
}
```

When the engine renders the workspace, it checks `_navigation` first:
- If `_navigation` is absent or empty → render prompt view (default)
- If `_navigation.view` is set → render that view (history, progress)
- If `_navigation.mode == "amend"` → render amendment view for the target field

On any response submission or RETURN/CANCEL, `_navigation` is cleared. The navigation state is transient in intent but durable on disk — if the system crashes mid-amendment, recovery picks up exactly where the agent left off.

### 3.8 Checkout Flow for Interactive Documents

When an interactive document is checked out:

1. **Schema sync** — Standard CR-107 schema sync from template (unchanged)
2. **Determine phase** — Map document state to active phase (DRAFT → authoring, IN_EXECUTION → execution). If no graph sub-workflow exists for this phase, proceed with non-interactive checkout.
3. **Initialize interaction** — If `interaction` key does not exist in metadata, stamp the active phase's field structure into metadata with null values (including `steps: []` for collection zones). If transitioning to execution phase and authoring data already exists, stamp execution-phase null fields alongside existing authoring data (e.g., add `ei_status: null`, `ei_evidence: null` to each item in a collection).
4. **Determine state** — Walk active phase's graph against metadata to find current node
5. **Render workspace** — If interaction not yet complete for this phase: render TEMPLATE-INTERACT with current prompt. If phase interaction is complete: render source Jinja2 body with full metadata (normal checkout).

---

## 4. Lifecycle Operations

### 4.1 Create (interactive document)

1. Read `TEMPLATE-{TYPE}.md`
2. Copy template to source file in `QMS/.source/` (frontmatter graph + Jinja2 body — the full template)
3. Parse schema from template frontmatter → stamp `user_properties` into `.meta/`
4. Parse graph from template frontmatter → stamp empty `interaction` structure into `.meta/`
5. Write stub draft
6. Auto-checkout: determine first prompt → render TEMPLATE-INTERACT → write workspace

### 4.2 The Interaction Cycle

The only commands the agent needs are `qms checkout` and `qms checkin`. The workspace document is the complete interface.

```
checkout → workspace shows current prompt + navigation section
                ↓
         agent writes response between @response markers
         (or enters a navigation command between @nav markers)
                ↓
         checkin → engine processes response or navigation command
                ↓
         navigation command? → re-render appropriate view, stay checked out
                ↓
         response? → validate, record, advance graph
                ↓
         more prompts? → render next prompt, stay checked out
                ↓
         complete? → render final document via source Jinja2 body, true checkin
```

Each checkin during interaction re-renders the workspace and keeps the document checked out. The document only truly checks in when interaction is complete.

### 4.3 Navigation: The Document as UI

All operations that the old `qms interact` command handled are now navigation commands entered in the workspace document's Navigation section:

| Old CLI Command | Navigation Command | Effect |
|---|---|---|
| `qms interact DOC_ID` (bare) | *(default — just check in with response)* | Advance to next prompt |
| `qms interact --progress` | `PROGRESS` | Re-render with progress view |
| `qms interact --history` | `HISTORY` | Re-render with history view |
| `qms interact --compile` | `PREVIEW` | Re-render with final document preview |
| `qms interact --amend FIELD --reason "..."` | `AMEND field reason` | Navigate to amendment view |
| `qms interact --reopen SECTION --reason "..."` | `REOPEN section reason` | Reopen closed loop section |
| `qms interact --goto` | *(eliminated — AMEND replaces it)* | — |
| `qms interact --cancel-goto` | `CANCEL` | Return from amendment without changes |

The `qms interact` command is eliminated entirely. No CLI interface for interaction remains. The workspace document IS the interface.

### 4.4 Amendment Workflow (via Navigation)

1. Agent writes `AMEND objective Correcting scope description` in the `@nav` region
2. Checkin processes the command: sets `_navigation` state, re-renders workspace as amendment view
3. Amendment view shows: current value with attribution, the prompt, a response region
4. Agent writes the amended response in the `@response` region
5. Checkin records the amendment: appends new entry to the field's response list (original preserved), clears `_navigation`, re-renders prompt view at the position where the agent was before amending

The reason is captured from the navigation command. The original response is preserved in the entry list and rendered with strikethrough in the final document.

### 4.5 Reopen (via Navigation)

1. Agent writes `REOPEN steps Additional verification needed` in the `@nav` region
2. Checkin processes: appends new empty section to `interaction.steps`, records reopening event, re-renders prompt view at first node of the loop subgraph
3. Agent continues with new iteration as normal

---

## 5. What This Replaces

| Current System (CR-091) | New System (CR-107) |
|---|---|
| `@prompt` / `@gate` / `@loop` annotation parser | YAML graph in template frontmatter |
| `compile_document()` custom compiler | Jinja2 render engine (same as all documents) |
| `qms interact --respond VALUE` CLI per prompt | Inline response via file editing + checkin |
| `.interact` session file (workspace) | Workspace document rendered by TEMPLATE-INTERACT |
| `.source.json` in `.meta/` | `interaction` dict in `.meta/` metadata JSON |
| `interact_engine.py` state machine | Stateless graph walker (current node derived from metadata) |
| `interact_parser.py` annotation parser | Standard YAML frontmatter parsing |
| `interact_compiler.py` output generator | Jinja2 render of source body (same as all documents) |
| `interact_source.py` data model | Standard metadata JSON operations |

### Files Eliminated
- `interact_parser.py` — replaced by YAML parsing of template frontmatter
- `interact_engine.py` — replaced by stateless graph walker
- `interact_compiler.py` — replaced by Jinja2 render engine
- `interact_source.py` — replaced by metadata JSON operations
- `commands/interact.py` — eliminated entirely; all interaction via checkout/checkin

### Files Created
- `qms_interact.py` (or similar) — the new stateless interaction engine: graph walking, context building, response/navigation extraction, TEMPLATE-INTERACT rendering
- `QMS/TEMPLATE/TEMPLATE-INTERACT.j2` — generic interaction workspace template

### Files Modified
- `commands/checkin.py` — gains response extraction, navigation processing, and graph advancement for interactive documents; interactive checkin re-renders and stays checked out until complete
- `commands/checkout.py` — gains interaction initialization and TEMPLATE-INTERACT rendering
- `qms.py` — remove `interact` subcommand registration

---

## 6. Design Principles

1. **Stateless engine.** Current position derived from metadata by walking the graph. No cursor variable, no session file, no persistent engine state. If the system crashes, the metadata tells you exactly where you are. Navigation state (`_navigation`) is the one transient datum — persisted in metadata for crash resilience, cleared on every response or RETURN/CANCEL.

2. **The document is the UI.** The workspace document is a complete, self-contained interface. It shows the current prompt, accepts the response, and offers navigation — all through file editing. No CLI commands beyond `checkout` and `checkin`. The `qms interact` command is eliminated.

3. **Concise workspace.** The agent sees only the current prompt and response region by default. History, progress, and previews are available via navigation commands — rendered into the workspace on request, not cluttering the default view.

4. **One durable artifact.** The metadata JSON in `.meta/` is the only state that matters. Everything else (workspace rendering, progress display, final document) is derived from metadata + source.

5. **Two templates, two jobs.** TEMPLATE-{TYPE} defines what the document IS (schema, workflow, final rendering). TEMPLATE-INTERACT defines how to present the interaction (generic, works for any document type). Neither does the other's job.

6. **Same pipeline.** Interactive and non-interactive documents use the same render engine (Jinja2), the same data store (`.meta/`), the same source location (`QMS/.source/`). The interaction layer is additive — it's an extra phase before the same final rendering.

7. **Checkout/checkin is the only interface.** The agent's entire interaction with the system is: check out, edit the workspace, check in. For non-interactive documents, this is one cycle. For interactive documents, it repeats (staying checked out) until interaction is complete. The primitive is the same.

8. **Zones are composable interaction points.** Interactive zones can be placed anywhere in a document's source body. A document can have zero zones (non-interactive), one zone (single interactive section), or many zones (multiple interactive sections). The engine treats each zone as an independent sub-workflow. This enables a spectrum from fully freeform to fully interactive — the same engine handles both extremes and everything in between.

9. **Phases follow the document lifecycle.** The same zone can be interactive in multiple lifecycle phases — authoring builds data, execution acts on it. The engine selects the active phase from the document's state, not from a separate configuration. Metadata from earlier phases is input data for later phases, and all phase data coexists in the same metadata structure.

---

## 7. Open Questions

1. **TEMPLATE-INTERACT format.** Should it be `.md` or `.j2`? The content is Jinja2 either way. The extension is a convention question. For partially interactive documents, TEMPLATE-INTERACT renders only the zone UI (injected into the source body), not the entire workspace — does this change the answer?

2. **Graph declaration syntax.** The exact YAML format for the graph in template frontmatter needs to be finalized. Two variants now exist: `graph.nodes` for fully interactive documents, `graph.zones` for partially interactive documents. Should fully interactive documents also use `graph.zones` with a single implicit zone for uniformity?

3. **Loop boundary markers.** How does the graph declare which nodes belong to a loop subgraph? Options: explicit `section: steps` attribute on nodes, or inferred from the backward-edge structure. The `collection: true` attribute on zones (Section 2 example) partially addresses this for zone-level loops — does it also handle nested loops within zones?

4. **Schema and graph merge.** The template frontmatter currently shows both a `schema:` section and a `graph:` section. For interactive documents, the graph nodes implicitly define most of the schema — a prompt node with `values: [Pass, Fail]` is both a workflow node and a schema declaration. Should the separate `schema:` section be eliminated for interactive documents, with the graph serving as the schema authority? For partially interactive documents, `schema:` would still be needed for freeform fields that have no graph node.

5. **Navigation command parsing.** The `AMEND field reason` format packs the field name and reason into one line. Should the reason be quoted? Should there be a delimiter? Example: `AMEND objective | Correcting scope description` vs `AMEND objective Correcting scope description`. The latter is ambiguous if the field name has spaces (it shouldn't, but worth specifying). For zone fields, the format may need to include zone context: `AMEND ei_table.2.ei_description reason`.

6. **Interactive checkin semantics.** During interaction, checkin re-renders and keeps the document checked out. This means `checkin.py` needs to distinguish "interactive document in progress" from "normal checkin." The cleanest approach may be: if the metadata has an `interaction` key with unfilled nodes, the checkin is an interactive cycle (process + re-render + stay locked). Otherwise, it's a normal checkin. For partially interactive documents, freeform edits are also extracted during interactive checkin — they update `user_properties` in metadata as usual.

7. **Zone completion independence.** Can zones complete independently, or must they complete in declaration order? If independent: the author could finish the EI table while leaving the purpose blank. If ordered: the engine presents zones sequentially. The sequential approach is simpler and matches the document's natural reading order, but the independent approach is more flexible.

8. **Non-document interactions.** The Lead mentioned a help desk application where an agent navigates the Quality Manual interactively. This has no final rendition — no source body template. Should such interactions be modeled as a fully interactive document where the "final rendition" is just an acknowledgement, or does the system need a concept of interaction-only workflows with no rendering phase?

9. **Zone context rendering.** When an interactive zone is active, should it show context from previously collected items? For example, when adding EI-3, should the prompt show the EI table with EI-1 and EI-2 already filled in? The design plan proposes reusing the zone's Jinja2 body (between `@interactive` markers) as the context template — the engine evaluates it with items collected so far. This avoids duplication but requires the body Jinja2 to render gracefully with partial data.

10. **YAML vs. Python for graph definition.** The graph declaration is growing complex: phases, zones, collection semantics, `each:` iteration directives, backward edges, conditional transitions. YAML is straining under this weight — it's becoming a configuration DSL where a programming language would be more natural. Session 2026-03-02-001 designed a Python graph model (Prompt/Stamp/Gate dataclasses, factory functions, bottom-up composition) that handles this complexity natively. Should the graph move to Python modules (`WORKFLOW-CR.py`, `WORKFLOW-VR.py`) referenced from the template frontmatter? The template would retain the schema and rendering body; the workflow logic would live in code. This splits the "living schema authority" but arguably along a natural seam — rendering vs. workflow are different concerns.

11. **Phase transition mechanics.** When a document transitions from DRAFT to IN_EXECUTION (via approval + release), when are execution-phase null fields stamped into metadata? Options: (a) at release time (`qms release` stamps execution fields), (b) at first checkout after release (lazy initialization), (c) at approval time. Option (b) is most consistent with the current lazy-init pattern in checkout.

12. **Execution-phase rendering.** During execution, the final-rendition body Jinja2 must render both authoring data and in-progress execution data (e.g., showing completed EIs alongside pending ones). The `default("—")` filter handles missing execution fields, but the body template needs to be designed for this dual-phase rendering from the start — it's not just a "final" template anymore, it's also the execution-phase context template.

---

## 8. Relationship to CR-107

This design extends CR-107 by replacing its Section 5.7 ("VR Source Consolidation") and the surrounding references to an unchanged `qms interact` system. The changes to CR-107:

1. **Section 4.3** — "Two Input Channels, One Data Store" becomes "One Input Channel, One Data Store." There is no separate `qms interact` response channel. Inline response extraction at checkin is the input mechanism for interactive responses, feeding into the same `.meta/` data store as frontmatter properties.

2. **Section 5.7** — Replaced entirely. VR source consolidation is subsumed by the unified source model. Interactive response data lives in the `interaction` key of the metadata JSON, not in a separate `.source.json`.

3. **New section** — Describes the two-template model, the interaction engine, TEMPLATE-INTERACT views, graph format, navigation commands, and the interaction lifecycle.

4. **EI table** — Gains EIs for: TEMPLATE-INTERACT creation, interaction engine implementation, `qms interact` command removal, interactive document lifecycle testing.

5. **Files affected** — Adds TEMPLATE-INTERACT, interaction engine module. Removes five files (four `interact_*.py` modules + `commands/interact.py`).

6. **Placeholder syntax** — `{{placeholder}}` → `<<placeholder>>` throughout.

7. **Scope increase** — CR-107 is no longer just a rendering unification. It is a full document lifecycle unification that subsumes the interactive document system. The title and purpose statement should reflect this broader scope.
