---
title: 'Verification Record Template'
revision_summary: 'v6 — Frontmatter-driven interaction redesign per CR-107. Replaces
  @prompt/@gate/@loop annotation engine with Jinja2 conditionals and YAML frontmatter
  state. Tier 3 (sequential execution) enforcement. Preserves all evidence guarantees:
  per-response timestamps, sequential ordering, auto-commit hooks, append-only
  amendment trail.'
---

<!--
================================================================================
TEMPLATE DOCUMENT NOTICE
================================================================================
This template is a QMS-controlled document managed under the unified document
lifecycle (CR-107). The first frontmatter block above is the template's own
metadata (title and revision_summary of the TEMPLATE document itself).

The second frontmatter block below is the SCHEMA DECLARATION for VR documents
created from this template. Its keys define the user_properties schema that the
CLI stamps into every VR's metadata sidecar. At every checkout, the CLI syncs
the document's schema against this template (living schema authority).

All other metadata (version, status, responsible_user, dates) is managed
automatically by the QMS CLI in sidecar files (.meta/) per SOP-001 Section 5.
================================================================================
-->

<!--
================================================================================
TEMPLATE USAGE GUIDE
================================================================================

DOCUMENT TYPE:
VRs are EXECUTABLE, ATTACHMENT-TYPE, TIER 3 (SEQUENTIAL EXECUTION) documents
that record behavioral verification of execution items. The interactive process
is not a convenience — it is the enforcement mechanism. The entire point is to
prove that verification steps were performed in order, at specific times, with
specific system state.

LIFECYCLE (truncated):
  Born IN_EXECUTION (v1.0) -> IN_POST_REVIEW -> POST_REVIEWED
    -> IN_POST_APPROVAL -> POST_APPROVED -> CLOSED

  VRs skip the entire pre-approval workflow. The template IS the pre-approved
  protocol — it was approved through the TEMPLATE document control process.

TIER 3 ENFORCEMENT:
  This template declares tier: sequential. The checkin process enforces:

  1. SEQUENTIAL ORDERING — You can only respond to the current prompt. The
     checkin process rejects changes to fields outside the current prompt's
     scope. You cannot skip ahead or go back (except via explicit amendment).

  2. PER-RESPONSE TIMESTAMPS — Each response is recorded at the moment of
     checkin. The timestamp IS evidence. The CLI writes timestamps into the
     response history in .meta/, not into the source frontmatter.

  3. AUTO-COMMIT HOOKS — Fields marked with `commit: true` in the cursor
     map trigger an automatic git commit at checkin. The commit hash is
     recorded alongside the response, pinning the project state at the
     moment of observation.

  4. APPEND-ONLY AMENDMENT — A response, once submitted, cannot be silently
     overwritten. To amend a previous response, the user must use the
     amendment workflow (explicit goto + reason). The original value is
     preserved with strikethrough; the amendment appends with attribution.

AUTHORING WORKFLOW:
  1. Parent document (CR/VAR/ADD) must be IN_EXECUTION
  2. Create VR: qms create VR --parent {PARENT_ID} --title "..."
  3. Checkout: qms checkout {VR_ID}
  4. Workspace shows rendered prompt — the current question
  5. Respond by writing inline responses in the marked regions
  6. Checkin: qms checkin {VR_ID}
  7. Checkin extracts inline responses, enforces tier 3 rules, records
     timestamp, advances cursor
  8. New checkout shows the next prompt
  9. Repeat until all prompts are answered
  10. Route for post-execution review and approval

INPUT SURFACE:
  All responses are submitted via inline response regions in the rendered
  document body. The author never edits YAML frontmatter directly. At
  checkin, the extraction pass reads content between @response markers
  and writes it to the corresponding frontmatter field automatically.

CURSOR MAP:
  The cursor_map (below) declares the sequential prompt flow. Each entry
  specifies:
    - fields: which frontmatter fields may be set at this cursor position
    - next: which cursor position follows (unconditional)
    - next_if: conditional routing based on field values
    - commit: fields that trigger auto-commit when set
    - loop: indicates this position is inside a repeating block

  The checkin process reads sys.cursor from .meta/, looks up the allowed
  fields in cursor_map, and rejects changes to any other fields.

RESPONSE HISTORY:
  The .meta/ sidecar maintains a response history for every field. Each
  entry is: { value, author, timestamp, reason?, commit? }. The source
  frontmatter holds only the CURRENT value. The Jinja2 template can access
  the full history via sys.history.{field} for rendering amendment trails.

NAMING CONVENTION:
  {PARENT_DOC_ID}-VR-NNN (e.g., CR-091-VR-001)

Delete this comment block after reading.
================================================================================
-->

---
tier: sequential

cursor_map:
  start:
    fields: [related_eis]
    next: objective
  objective:
    fields: [objective]
    next: pre_conditions
  pre_conditions:
    fields: [pre_conditions]
    next: step_instructions
  step_instructions:
    fields: [step_instructions]
    next: step_expected
    loop: steps
  step_expected:
    fields: [step_expected]
    next: step_actual
    loop: steps
  step_actual:
    fields: [step_actual]
    next: step_outcome
    loop: steps
    commit: [step_actual]
  step_outcome:
    fields: [step_outcome]
    next: more_steps
    loop: steps
  more_steps:
    fields: [more_steps]
    loop: steps
    next_if:
      more_steps:
        'yes': step_instructions
        'no': summary_outcome
  summary_outcome:
    fields: [summary_outcome]
    next: summary_narrative
  summary_narrative:
    fields: [summary_narrative]
    next: __end__

related_eis: null
objective: null
pre_conditions: null
steps: []
summary_outcome: null
summary_narrative: null
---

{#- ======================================================================== -#}
{#- STATE EVALUATION                                                         -#}
{#- ======================================================================== -#}
{%- set ns = namespace(steps_complete = false, all_complete = false) -%}
{%- if user.steps | length > 0 and user.steps[-1].more_steps is defined
    and user.steps[-1].more_steps == 'no' -%}
  {%- set ns.steps_complete = true -%}
{%- endif -%}
{%- if ns.steps_complete and user.summary_outcome and user.summary_narrative -%}
  {%- set ns.all_complete = true -%}
{%- endif -%}


{#- ======================================================================== -#}
{#- COMPLETE DOCUMENT — rendered only when all prompts are answered           -#}
{#- ======================================================================== -#}
{% if ns.all_complete %}

# {{ sys.doc_id }}: {{ user.title }}

## 1. Verification Identification

| Parent Document | Related EI(s) | Date |
|-----------------|---------------|------|
| {{ sys.parent_doc_id }} | {{ user.related_eis }} | {{ sys.date }} |

---

## 2. Verification Objective

{{ user.objective }}

*-- {{ sys.history.objective[-1].author }}, {{ sys.history.objective[-1].timestamp }}*
{%- if sys.history.objective | length > 1 %}
{% for entry in sys.history.objective[:-1] %}
~~{{ entry.value }}~~
*-- {{ entry.author }}, {{ entry.timestamp }}{% if entry.reason %} | amended: {{ entry.reason }}{% endif %}*
{% endfor %}
{%- endif %}

---

## 3. Prerequisites

{{ user.pre_conditions }}

*-- {{ sys.history.pre_conditions[-1].author }}, {{ sys.history.pre_conditions[-1].timestamp }}*

---

## 4. Verification Steps

{% for step in user.steps %}
### 4.{{ loop.index }} Step {{ loop.index }}

**Instructions:**

{{ step.step_instructions }}

*-- {{ sys.history.steps[loop.index0].step_instructions[-1].author }}, {{ sys.history.steps[loop.index0].step_instructions[-1].timestamp }}*

**Expected:**

{{ step.step_expected }}

*-- {{ sys.history.steps[loop.index0].step_expected[-1].author }}, {{ sys.history.steps[loop.index0].step_expected[-1].timestamp }}*

**Actual:**

```
{{ step.step_actual }}
```

*-- {{ sys.history.steps[loop.index0].step_actual[-1].author }}, {{ sys.history.steps[loop.index0].step_actual[-1].timestamp }} | commit: {{ sys.history.steps[loop.index0].step_actual[-1].commit }}*

**Outcome:**

{{ step.step_outcome }}

*-- {{ sys.history.steps[loop.index0].step_outcome[-1].author }}, {{ sys.history.steps[loop.index0].step_outcome[-1].timestamp }}*

{% endfor %}

---

## 5. Summary

**Outcome:** {{ user.summary_outcome }}

*-- {{ sys.history.summary_outcome[-1].author }}, {{ sys.history.summary_outcome[-1].timestamp }}*

{{ user.summary_narrative }}

*-- {{ sys.history.summary_narrative[-1].author }}, {{ sys.history.summary_narrative[-1].timestamp }}*

---

**END OF VERIFICATION RECORD**


{#- ======================================================================== -#}
{#- PROMPTS — only the current prompt is rendered during authoring            -#}
{#- ======================================================================== -#}
{% else %}

# {{ sys.doc_id }}: {{ user.title }}

{% if not user.related_eis -%}
{#- ---- PROMPT: Related EIs ---- -#}

> **Prompt: Related EIs**
>
> Which execution item(s) in the parent document does this VR verify?
> (e.g., EI-3, or EI-3 and EI-4)

<!-- @response: related_eis -->
<<Which EI(s) does this VR verify?>>
<!-- @end-response -->

{% elif not user.objective -%}
{#- ---- PROMPT: Objective ---- -#}

> **Prompt: Verification Objective**
>
> State what CAPABILITY is being verified — not what specific mechanism
> is being tested. Frame the objective broadly enough that you naturally
> check adjacent behavior during the procedure.
>
> Good: "Verify that service health monitoring detects running and stopped
> services correctly"
>
> Avoid: "Verify the health check endpoint returns 200"

<!-- @response: objective -->
<<State the verification objective.>>
<!-- @end-response -->

{% elif not user.pre_conditions -%}
{#- ---- PROMPT: Prerequisites ---- -#}

> **Prompt: Prerequisites**
>
> Describe the state of the system BEFORE verification begins. A person
> with terminal access but no knowledge of this project must be able to
> reproduce these conditions.
>
> Include as applicable: branch and commit checked out, services running
> (which, what ports), container state, non-default configuration, data
> state, relevant environment details (OS, Python version, etc.).

<!-- @response: pre_conditions -->
<<Describe the system prerequisites.>>
<!-- @end-response -->

{%- elif not ns.steps_complete -%}
{#- ---- STEP PROMPTS ---- -#}

{%- set current = user.steps[-1] if user.steps | length > 0 else none -%}
{%- set step_num = (user.steps | length) + 1 -%}

{%- set need_new_step = (
      user.steps | length == 0
    ) or (
      current is not none
      and current.more_steps is defined
      and current.more_steps == 'yes'
    )
-%}

{% if need_new_step %}

> **Prompt: Step {{ step_num }} — Instructions**
>
> What are you about to do? Describe the action and provide the exact
> command, click target, or navigation path. Commands must be
> copy-pasteable — not retyped or abbreviated.
>
> *This is step {{ step_num }} of the verification.*

<!-- @response: step_instructions -->
<<Describe what you are about to do.>>
<!-- @end-response -->

{% elif not current.step_expected %}

> **Prompt: Step {{ user.steps | length }} — Expected Outcome**
>
> What do you expect to observe? State this BEFORE executing — not after.
> Good verification covers both sides: confirming what should be present
> and confirming what should be absent.
>
> **You said you would do:**
> {{ current.step_instructions }}

<!-- @response: step_expected -->
<<State what you expect to observe.>>
<!-- @end-response -->

{% elif not current.step_actual %}

> **Prompt: Step {{ user.steps | length }} — Actual Outcome** *(auto-commit)*
>
> What did you observe? Reference primary evidence: paste actual terminal
> output, or provide the raw output. Do not summarize or paraphrase.
> If the output is long, paste the relevant portion and note what was
> omitted.
>
> The commit hash recorded on this response pins the project state at
> the moment of observation.
>
> **You said you would do:**
> {{ current.step_instructions }}
>
> **You expected:**
> {{ current.step_expected }}

<!-- @response: step_actual -->
<<Paste the actual output or observation.>>
<!-- @end-response -->

{% elif not current.step_outcome %}

> **Prompt: Step {{ user.steps | length }} — Outcome**
>
> Did the observed output match your expectation? `Pass` or `Fail`.
> If Fail, note the discrepancy.
>
> **You expected:**
> {{ current.step_expected }}
>
> **You observed:**
> {{ current.step_actual | truncate(200) }}

<!-- @response: step_outcome -->
<<Pass or Fail. If Fail, note the discrepancy.>>
<!-- @end-response -->

{% elif current.more_steps is not defined %}

> **Prompt: More Steps?**
>
> Step {{ user.steps | length }} outcome: **{{ current.step_outcome }}**
>
> Do you have additional verification steps to record?
>
> *{{ user.steps | length }} step(s) recorded so far.*

<!-- @response: more_steps -->
<<yes or no>>
<!-- @end-response -->

{% endif %}

{%- elif not user.summary_outcome -%}
{#- ---- PROMPT: Summary Outcome ---- -#}

> **Prompt: Overall Outcome**
>
> Considering all {{ user.steps | length }} steps, what is the overall outcome?
> `Pass` if all steps passed and nothing unexpected was observed.
> `Fail` if any step failed or if unexpected behavior was discovered.
>
> **Step results:**
{% for step in user.steps %}
> - Step {{ loop.index }}: {{ step.step_outcome }}
{% endfor %}

<!-- @response: summary_outcome -->
<<Pass or Fail>>
<!-- @end-response -->

{%- elif not user.summary_narrative -%}
{#- ---- PROMPT: Summary Narrative ---- -#}

> **Prompt: Summary Narrative**
>
> Brief narrative overview of the verification: what was tested, the
> general approach, and any notable observations — even if they don't
> affect the outcome. If any step failed, reference the discrepancy
> and any VAR created.
>
> **Overall outcome:** {{ user.summary_outcome }}

<!-- @response: summary_narrative -->
<<Provide a brief summary narrative.>>
<!-- @end-response -->

{% endif %}

{% endif %}
