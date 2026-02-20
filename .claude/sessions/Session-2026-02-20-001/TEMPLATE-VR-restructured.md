<!--
@template: VR | version: 2 | start: parent_doc_id

Schema Tag Reference
====================

Flow Tags:
  @prompt: id | next: id           Content prompt. Response stored in {{id}}.
  @gate: id | type: yesno | ...    Flow-control prompt. Routes only, no compiled content.
  @loop: name                      Repeating block start. {{_n}} = iteration counter.
  @end-loop: name                  Repeating block end.
  @end                             Terminal state.

Attributes:
  next: id                         Unconditional transition.
  type: yesno                      Prompt/gate accepts yes or no.
  yes: id / no: id                 Conditional transitions for yesno types.
  default: value                   Auto-fill value (author can override).

Response Model
==============

Every response is a timestamped list, not a scalar. The initial response
creates a single-entry list. Amendments append to the list — they never
replace or delete prior entries.

Entry structure:
  - value:      The response content
  - author:     Who recorded this entry
  - timestamp:  When this entry was recorded (ISO 8601)
  - reason:     Why the entry was amended (omitted for initial entry)

Amendment rules:
  - Original entries are never modified or deleted
  - Each amendment appends a new entry with a reason
  - Only the most recent entry is "active"
  - Superseded entries compile with strikethrough
  - Amendments are allowed on @prompt responses only, not @gate decisions

Compiled rendering:

  Single entry (normal):
    **Action:** Run health check against running MCP service
    *— claude, 2026-02-20 10:30*

  Multiple entries (amended):
    **Action:**
    1. ~~Run health check against MCP endpoint~~
       *— claude, 2026-02-20 10:30*
    2. Run health check against running MCP service
       *— claude, 2026-02-20 10:35 | Amended: Clarified which service state*

Navigation
==========

The execution cursor tracks the author's current position in the state
machine. Normal flow advances the cursor forward via next/respond.

  goto <prompt_id>     Move cursor to a previously-completed @prompt.
                       Displays current response. Author provides a new
                       response (appended as amendment). Cursor returns
                       to its prior position afterward.

  reopen <loop_name>   Re-enter a closed @loop to add iterations.
                       Records a reopening event (timestamp, author,
                       reason). Iteration counter continues from last
                       completed iteration. Normal loop flow resumes
                       until the @gate closes the loop again, then the
                       cursor returns to its prior position.

Rules:
  - goto and reopen target only completed prompts / closed loops
  - The cursor cannot skip ahead past unfilled prompts
  - Amendments do NOT invalidate downstream responses — corrections
    are self-contained. If a correction is material enough to affect
    later sections, the author amends those separately.
  - All cursor movements are recorded in the audit trail

Compilation
===========
  - Strip all <!-- @... --> tags
  - Strip all prose between tags (guidance text)
  - Keep markdown structure (headings, tables, code blocks)
  - Substitute {{placeholders}} with active response values
  - Render amendment trails beneath amended fields
  - Timestamps shown on all responses (amended or not)
-->

---
title: '{{title}}'
revision_summary: 'Initial draft'
---

# {{vr_id}}: {{title}}

## 1. Verification Identification

<!-- @prompt: parent_doc_id | next: related_eis -->

What is the parent document for this verification record?

<!-- @prompt: related_eis | next: date -->

Which execution item(s) in the parent document does this VR verify? (e.g., EI-3, or EI-3 and EI-4)

<!-- @prompt: date | next: objective | default: today -->

| Parent Document | Related EI(s) | Date |
|-----------------|---------------|------|
| {{parent_doc_id}} | {{related_eis}} | {{date}} |

---

## 2. Verification Objective

<!-- @prompt: objective | next: pre_conditions -->

State what CAPABILITY is being verified — not what specific mechanism is being tested. Frame the objective broadly enough that you naturally check adjacent behavior during the procedure.

Good: "Verify that service health monitoring detects running and stopped services correctly"
Avoid: "Verify the health check endpoint returns 200"

**Objective:** {{objective}}

---

## 3. Pre-Conditions

<!-- @prompt: pre_conditions | next: step_action -->

Describe the state of the system BEFORE verification begins. A person with terminal access but no knowledge of this project must be able to reproduce these conditions.

Include as applicable: branch and commit checked out, services running (which, what ports), container state, non-default configuration, data state, relevant environment details (OS, Python version, etc.).

{{pre_conditions}}

---

## 4. Verification Steps

<!-- @loop: steps -->

### Step {{_n}}

<!-- @prompt: step_action | next: step_expected -->

What action are you about to perform? (e.g., "Run health check against running service", "Stop the MCP server and re-check")

**Action:** {{step_action}}

<!-- @prompt: step_expected | next: step_detail -->

What do you expect to observe when you perform this action? State this BEFORE executing — not after.

**Expected:** {{step_expected}}

<!-- @prompt: step_detail | next: step_observed -->

Provide the exact command, click target, or navigation path. Commands must be copy-pasted from the terminal, not retyped or abbreviated.

```
{{step_detail}}
```

<!-- @prompt: step_observed | next: step_outcome -->

What did you observe? Paste actual terminal output or log excerpts. Do not summarize or paraphrase. If the output is long, paste the relevant portion and note what was omitted.

**Observed:**

```
{{step_observed}}
```

<!-- @prompt: step_outcome | next: more_steps -->

Did the observed output match your expected outcome? State Pass or Fail. If Fail, briefly note the discrepancy.

**Outcome:** {{step_outcome}}

<!-- @gate: more_steps | type: yesno | yes: step_action | no: summary_outcome -->

Do you have additional verification steps to record?

<!-- @end-loop: steps -->

---

## 5. Summary

<!-- @prompt: summary_outcome | next: summary_narrative -->

Considering all steps above, what is the overall outcome? Pass if all steps passed and no side effects were observed. Fail if any step failed or unexpected side effects occurred.

**Overall Outcome:** {{summary_outcome}}

<!-- @prompt: summary_narrative | next: performer -->

Provide a brief narrative overview of the verification. Include:
- What was tested and the general approach
- Any negative verification (side effects, regressions, unintended state changes — or their confirmed absence)
- Notable observations, even if they don't affect the outcome
- If any step failed, reference the discrepancy and any VAR created

{{summary_narrative}}

---

## 6. Signature

<!-- @prompt: performer | next: performed_date | default: current_user -->

Who performed this verification?

<!-- @prompt: performed_date | next: end | default: today -->

| Role | Identity | Date |
|------|----------|------|
| Performed By | {{performer}} | {{performed_date}} |

<!-- @end -->

---

## 7. References

- **{{parent_doc_id}}:** Parent document
- **SOP-004:** Document Execution

---

**END OF VERIFICATION RECORD**
