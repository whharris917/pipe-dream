# Interactive Engine Redesign — Design Discussion

**Source:** Ghost Session (Session-2026-02-22-004 was active for a different task; this discussion occurred in a parallel session)

---

## Context

This document captures a design discussion about decoupling the `qms interact` system's workflow/prompt engine from its document compilation engine. The goal is to enable more complex interactive document types (CRs, VARs, ADDs) beyond the current VR-only support, and to lay the groundwork for a unified QMS authoring engine.

---

## Problem Statement

The current interactive system (CR-091) uses a single template file (TEMPLATE-VR.md) that serves three purposes simultaneously:

1. **State machine definition** — HTML comment tags define the prompt sequence
2. **Author guidance** — prose between tags shown during interaction
3. **Output template** — markdown structure with `{{placeholder}}` slots

This works for VR because the prompt sequence closely matches the document section order. It breaks for more complex documents (CRs, VARs) where:

- The authoring order differs from the document section order (e.g., justification asked early, rendered in Section 6)
- Conditional sections exist (code CR sections 7.4/7.5 vs document-only CRs)
- The EI table is composed from multiple earlier answers plus SOP-mandated steps
- Loop expansion is hardcoded to VR-specific prompt IDs in the compiler

---

## Proposed Architecture: Three-Artifact Separation

### 1. Workflow Spec (data harvesting)

Defines what to ask, in what order, with what branching logic. Knows nothing about the output document.

**Near-term format:** YAML with Jinja2 expressions for conditions/validation
**Long-term format:** Python declarative (Django-model pattern) for arbitrary logic

Example (YAML):

```yaml
# workflows/vr.yaml
workflow: VR
version: 6
start: related_eis

prompts:
  related_eis:
    next: objective
    guidance: |
      Which execution item(s) in the parent document does this VR
      verify? (e.g., EI-3, or EI-3 and EI-4)

  objective:
    next: pre_conditions
    guidance: |
      State what CAPABILITY is being verified -- not what specific
      mechanism is being tested.

  pre_conditions:
    next: steps
    guidance: |
      Describe the state of the system BEFORE verification begins.

  summary_outcome:
    next: summary_narrative
    guidance: |
      Overall outcome? Pass or Fail.

  summary_narrative:
    next: __end__
    guidance: |
      Brief narrative overview...

loops:
  steps:
    exit_to: summary_outcome
    prompts:
      step_instructions:
        next: step_expected
        guidance: "What are you about to do?..."
      step_expected:
        next: step_actual
        guidance: "What do you expect to observe?..."
      step_actual:
        next: step_outcome
        commit: true
        guidance: "What did you observe?..."
      step_outcome:
        next: __gate__
        guidance: "Pass or Fail."
    gate:
      type: yesno
      guidance: "Do you have additional verification steps?"
```

### 2. Rendering Template (Jinja2)

Defines how collected data becomes a document. Consumes the source data as its context.

```jinja2
{# templates/vr.j2 #}
{% extends "base/executable.j2" %}

{% block body %}
## 1. Verification Identification

| Parent Document | Related EI(s) | Date |
|-----------------|---------------|------|
| {{ meta.parent_doc_id }} | {{ related_eis | val }} | {{ meta.date }} |

---

## 2. Verification Objective

{{ objective | bq_attr }}

---

## 3. Prerequisites

{{ pre_conditions | bq_attr }}

---

## 4. Verification Steps

{% for step in steps %}
### 4.{{ step.n }} Step {{ step.n }}

**Instructions:**

{{ step.instructions | bq_attr }}

**Expected:**

{{ step.expected | bq_attr }}

**Actual:**

{{ step.actual | code_attr }}

**Outcome:**

{{ step.outcome | bq_attr }}

{% endfor %}
---

## 5. Summary

{{ summary_outcome | bq_attr }}

{{ summary_narrative | bq_attr }}
{% endblock %}
```

### 3. Template Inheritance Hierarchy

```
base/
  document.j2              -- frontmatter, title, END OF DOCUMENT
  executable.j2            -- extends document; adds signature block
  executable_planned.j2    -- extends executable; adds pre-approved + execution split

templates/
  vr.j2                    -- extends executable
  cr.j2                    -- extends executable_planned
  var.j2                   -- extends executable_planned
  add.j2                   -- extends executable_planned
  inv.j2                   -- extends executable_planned
  sop.j2                   -- extends document (non-executable)

workflows/
  vr.yaml                  -- VR prompt sequence
  cr.yaml                  -- CR prompt sequence (future)
  var.yaml                 -- VAR prompt sequence (future)
```

### Custom Jinja2 Filters

| Filter | Behavior |
|--------|----------|
| `val` | Active value only (for tables, inline) |
| `bq_attr` | Blockquote with attribution line below, amendment trail with ~~strikethrough~~ |
| `code_attr` | Code fence with attribution below |
| `attr_only` | Just the attribution lines |

### Bridge: Source Data to Template Context

The `.source.json` format is unchanged. A context-builder transforms it into Jinja2-friendly objects:

- Non-loop prompts become `Response` objects with `.value`, `.entries`, `.has_amendments`
- Loops become lists of dicts, each containing `Response` objects keyed by prompt ID
- Metadata is passed through as `meta.*`

---

## Two-Layer Architecture

The system has two independent concerns that compose into a single agent interface:

### Authoring Layer (inner)

- Walks workflow state machine
- Presents prompts, records responses
- Manages loops, gates, amendments
- Compiles source to document via Jinja2
- Knows nothing about SOPs or QMS routing

### Process Layer (outer)

- Knows SOPs and document state
- Enriches prompts with contextual SOP guidance
- Enforces stage gates at transitions
- Suggests next actions post-completion
- Works with or without an active interactive session

Interface between layers:

- **Prompt enrichment:** Process layer appends SOP guidance before prompt display
- **Gate checks:** Process layer evaluates conditions at cursor transitions
- **Lifecycle events:** Authoring layer emits events; process layer observes and suggests

Either layer works independently: process layer advises on freehand CRs; authoring layer works for non-QMS documents.

---

## Workflow Language Progression

### Level 1: YAML
Sufficient for VR-class workflows. Falls apart at conditional branching, validation, computed values.

### Level 2: YAML + Jinja2 Expressions
Conditions, validation, computed defaults via Jinja2 expressions embedded in YAML. Sufficient for most interactive document types.

### Level 3: Python Declarative
Django-model pattern. Workflows as Python classes with lambdas for validation and conditions. Arbitrary power, testable, composable via inheritance.

### Level 4: Python Declarative + Orchestration Hooks
Process layer hooks observe state changes and suggest/enforce QMS actions. This is the "front door" level.

**Recommendation:** Build for Level 3, start at Level 2. Design engine interfaces against an abstract workflow API so the backend can evolve without changing the engine, source model, or rendering pipeline.

---

## Example: CR Prompt Path (qms-cli code change)

### Phase 1: Framing

| Prompt | Response |
|--------|----------|
| `cr.title` | Add `diff` command to compare document versions |
| `cr.purpose` | No way to compare versions; adds `qms diff` command |
| `cr.context` | Independent improvement, no parent document |

### Phase 2: Change Classification

| Prompt | Response | Engine Effect |
|--------|----------|---------------|
| `cr.change_type` | Code change to governed system | Enables code CR sections (7.4, 7.5, phases 1-7) |
| `cr.target_system` | qms-cli | Loads system profile (CLI-14.0, d73f154, RS v18.0, RTM v23.0) |
| `cr.adds_requirements` | Yes | Include RS/RTM update phases in EI table |
| `cr.modifies_templates` | No | Skip template alignment EIs |

### Phase 3: Before/After

| Prompt | Response |
|--------|----------|
| `cr.current_state` | CLI has `read --version` and `history` but no comparison |
| `cr.proposed_state` | CLI provides `diff` command with unified diff output |

### Phase 4: Technical Detail

| Prompt | Response |
|--------|----------|
| `cr.change_description` | Command interface, implementation plan, edge cases (freeform) |

### Phase 5: Files and Impact

| Prompt | Response |
|--------|----------|
| `cr.files_affected` | commands/diff.py (create), qms.py (modify), test_diff.py (create), RS, RTM |
| `cr.documents_affected` | SDLC-QMS-RS, SDLC-QMS-RTM |
| `cr.other_impacts` | None |

### Phase 6: Development Controls (auto-populated)

Engine auto-generates Section 7.4 and 7.5 from system profile. Author confirms.

### Phase 7: Verification Planning

| Prompt | Response | Engine Effect |
|--------|----------|---------------|
| `cr.automated_testing` | 6 new tests + full suite regression | — |
| `cr.integration_testing` | Exercise diff against real QMS docs | — |
| `cr.needs_vr` | Integration verification EI | VR=Yes flagged on that EI |

### Phase 8: EI Table Selection (variant-based)

The engine does NOT interactively construct the EI table. It is entirely programmatic: the classification flags from Phase 2 select a pre-defined EI table variant. Mandatory/structural EIs are fixed and non-removable. The author provides task descriptions only for the content-specific slots.

**Variant selection logic:**

| Flag | Effect on EI table |
|------|-------------------|
| `change_type = code` | Include: test env setup, qualification, merge gate |
| `adds_requirements = true` | Include: RS update, RTM update |
| `modifies_templates = true` | Include: template alignment verification |
| `has_vr = true` | Set VR=Yes on integration verification EI |

**Selected variant: `code-cr + adds-requirements + has-vr`**

| EI | Task Description | VR | Type |
|----|------------------|----|------|
| EI-1 | Pre-execution baseline: commit and push | | Fixed (SOP-004 §5) |
| EI-2 | Set up test environment, create branch | | Fixed (SOP-005 §7.1) |
| EI-3 | Update RS to EFFECTIVE | | Fixed (adds_requirements) |
| EI-4 | *[author-prompted: implementation work]* | | Prompted |
| EI-5 | Run full suite, push, CI, qualified commit | | Fixed (SOP-005 §7.1.2) |
| EI-6 | *[author-prompted: integration verification]* | Yes | Prompted (has_vr) |
| EI-7 | Update RTM to EFFECTIVE | | Fixed (adds_requirements) |
| EI-8 | Merge gate: PR, merge (--no-ff), submodule update | | Fixed (SOP-005 §7.1.3) |
| EI-9 | Post-execution baseline: commit and push | | Fixed (SOP-004 §5) |

The engine prompts the author only for the content-specific slots (EI-4, EI-6). The author cannot reorder, remove, or rename the fixed EIs — those are determined by the variant.

### Key Engine Contributions

1. **Section 7.4** auto-populated from system profile
2. **Section 7.5** auto-populated with current commit, RS/RTM versions, release number
3. **EI table variant** selected programmatically from classification flags
4. **Mandatory EIs** non-removable, with SOP citations
5. **Conditional EIs** included/excluded by flags, not by author choice
6. **VR flagging** placed on integration verification EI when `has_vr = true`
7. **SOP guidance** surfaced at moment of relevance per prompt

---

## Key Design Insight

The prompt sequence follows the **author's thinking** (what -> why -> how -> verify -> plan), while the compiled document follows the **reader's structure** (Sections 1-12 in template order). The decoupling between workflow and rendering is what makes this possible. The `.source.json` is the clean interface between them.

---

**END OF DOCUMENT**
