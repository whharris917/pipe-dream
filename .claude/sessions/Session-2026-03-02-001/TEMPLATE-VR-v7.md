---
title: Verification Record Template
revision_summary: '<<description of changes in this revision>>'

# === VR DOCUMENT SCHEMA ===
#
# This frontmatter is the schema authority for Verification Record documents.
# It serves two purposes:
#
#   1. Initialization — the CLI stamps this schema into QMS/.meta/<doc_id>.json
#      at creation, with all interactive fields initialized as empty lists.
#
#   2. Interaction graph — the interactive engine traverses this graph to drive
#      the verifier through prompts, enforcing ordering and recording timestamps
#      and commit hashes.
#
# Response model: every interactive field is a timestamped list. The initial
# response creates a single-entry list. Amendments append -- they never replace.
# Each entry: {value, author, timestamp, reason (omitted on first), commit (if applicable)}
#
# Graph conventions:
#   node id        = field name written to the metadata JSON
#   implicit next  = next node in dict (omit for sequential flow)
#   stamp: true    = pass-through node; auto-records {timestamp, commit}, no user wait
#   commit: true   = commit project state and record hash when response is submitted
#   values: [...]  = constrains response to listed options
#   yes: / no:     = conditional transitions for binary-choice nodes
#   on: {v: id}   = conditional transitions for enum nodes
#   Loops emerge from backward edges; no special syntax needed.

document_type: VR
schema_version: "1.0"

# Populated by the CLI at creation. Not prompted.
system_fields: [doc_id, parent_doc_id, title, created_at]

graph:
  nodes:
    related_eis:
      prompt: >
        Which execution item(s) in the parent document does this VR verify?
        (e.g., EI-3, or EI-3 and EI-4)

    date:
      prompt: "Enter the verification date (YYYY-MM-DD)."

    objective:
      prompt: |
        State what CAPABILITY is being verified -- not what specific mechanism
        is being tested. Frame the objective broadly enough that you naturally
        check adjacent behavior during the procedure.

        Good: "Verify that service health monitoring detects running and stopped
        services correctly"
        Avoid: "Verify the health check endpoint returns 200"

    pre_conditions:
      prompt: |
        Describe the state of the system BEFORE verification begins. A person
        with terminal access but no knowledge of this project must be able to
        reproduce these conditions.

        Include as applicable: branch and commit checked out, services running
        (which, what ports), container state, non-default configuration, data
        state, environment details (OS, Python version, etc.).

    step_instructions:
      prompt: |
        What are you about to do? Describe the action and provide the exact
        command, click target, or navigation path. Commands must be
        copy-pasteable -- not retyped or abbreviated.

    step_expected:
      prompt: |
        What do you expect to observe? State this BEFORE executing -- not
        after. Good verification covers both sides: confirming what should
        be present and confirming what should be absent. A step might check
        that a service responds correctly, or that an error no longer
        appears, or that an unrelated subsystem remains unaffected. All of
        these are evidence.

    step_actual:
      commit: true
      prompt: |
        What did you observe? Reference primary evidence: paste actual
        terminal output, or attach raw output via --respond --file. Do not
        summarize or paraphrase. If the output is long, paste the relevant
        portion and note what was omitted.

        The commit hash recorded on this response pins the project state at
        the moment of observation. A verifier can checkout this commit to
        see the exact code, configuration, and any output files referenced
        below.

    step_completed_at:
      stamp: true

    step_outcome:
      values: [Pass, Fail]
      prompt: >
        Did the observed output match your expectation? Pass or Fail.
        If Fail, note the discrepancy.

    more_steps:
      values: [yes, no]
      prompt: "Do you have additional verification steps to record?"
      yes: step_instructions
      no: summary_outcome

    summary_outcome:
      values: [Pass, Fail]
      prompt: >
        Considering all steps above, what is the overall outcome? Pass if all
        steps passed and nothing unexpected was observed. Fail if any step
        failed or if unexpected behavior was discovered.

    summary_narrative:
      prompt: |
        Brief narrative overview of the verification: what was tested, the
        general approach, and any notable observations -- even if they don't
        affect the outcome. If any step failed, reference the discrepancy and
        any VAR created.
---

{%- macro show_amendments(entries) %}
{%- if entries | length > 1 %}
{%- for entry in entries[:-1] %}
> **Amendment ({{ entry.timestamp }}, {{ entry.author }}):** {{ entry.reason }}
> Previous value: "{{ entry.value }}"
{% endfor %}
{%- endif %}
{%- endmacro -%}

---
title: '{{ title }}'
revision_summary: 'Initial draft'
---

# {{ doc_id }}: {{ title }}

## 1. Verification Identification

| Parent Document | Related EI(s) | Date |
|-----------------|---------------|------|
| {{ parent_doc_id }} | {{ related_eis[-1].value }} | {{ date[-1].value }} |

---

## 2. Verification Objective

{{ objective[-1].value }}
{{ show_amendments(objective) }}

---

## 3. Prerequisites

{{ pre_conditions[-1].value }}
{{ show_amendments(pre_conditions) }}

---

## 4. Verification Steps

{% for step in steps %}
### 4.{{ loop.index }} Step {{ loop.index }}

**{{ step.step_instructions[-1].value }}**
{{ show_amendments(step.step_instructions) }}

{{ step.step_expected[-1].value }}
{{ show_amendments(step.step_expected) }}

```
{{ step.step_actual[-1].value }}
```

*Commit: {{ step.step_completed_at.commit }} — {{ step.step_completed_at.timestamp }}*
{{ show_amendments(step.step_actual) }}

{{ step.step_outcome[-1].value }}
{{ show_amendments(step.step_outcome) }}

---
{% endfor %}

## 5. Summary

{{ summary_outcome[-1].value }}

{{ summary_narrative[-1].value }}
{{ show_amendments(summary_narrative) }}

---

**END OF VERIFICATION RECORD**
