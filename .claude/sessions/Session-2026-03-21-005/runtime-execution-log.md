# Runtime Execution Log — Document Review and Approval

## Objective
Execute the workflow built in the builder evaluation, testing all paths and verifying runtime behavior matches design intent. Evaluate agent-friendliness of the *runtime* experience.

**Instance:** 443892f3
**Plan:** Execute the Major path (fork/merge) first, then start a second instance for the Critical path, and a third for Minor.

---

## Path 1: Major Severity (Fork/Merge)

### Intake Node

**Initial GET observations:**
- 5 affordances for 5 visible fields. `escalation_justification` correctly hidden (severity is null).
- Instructions are clear and match what I authored.
- `state.fields` mirrors affordances — each field shows label, instruction, options (if select), and current value.
- `state.definition` shows the full workflow topology including router conditions, fork branches, etc. This is useful for an agent to understand the full workflow structure upfront.
- No Proceed affordance yet — gate requires document_title, document_type, author, severity.

**Observation R1 — Field instructions appear in two places.** Both `state.fields["Severity"].instruction` and the top-level `instructions` text mention severity routing behavior. Good redundancy — an agent reading just the affordances OR just the instructions gets the same guidance.

**Observation R2 — Affordance URLs use field keys.** URL is `/443892f3/document_title` (the field key), not `/443892f3/set_document_title` or a numbered endpoint. Clean and predictable.

**Observation R3 — Select field options in affordance parameters.** Document Type and Severity affordances include `parameters.value.options` arrays. An agent knows the valid choices without reading the field definitions separately.

---

### Filling Intake Fields & Proceeding
- Set all 5 visible fields. Each POST returns the updated field in `outcome`.
- Proceed gate opened after all 4 required fields were set (Submit for Review appeared).
- `escalation_justification` never appeared (correct — severity ≠ Critical).

**Observation R4 — Runtime outcome contains field value.** Unlike the builder (which returns empty outcome on success), the runtime returns the updated field in `outcome`. Inconsistent across builder vs runtime, but helpful here.

---

### Router Auto-Advance
After proceeding from intake, the router (`severity_router`) auto-evaluated severity = "Major" and advanced to `parallel_review`. Both intake and severity_router appeared in `completed_nodes`. No agent interaction required. This is the correct behavior for routers.

**Observation R5 — Router is invisible to the agent.** Perfect. The agent never sees the router node. It proceeds from intake, and the next thing it sees is the fork node. Routers are pure automation.

---

### Fork Node
The fork node (`parallel_review`) presented a single "Continue" affordance. No fields, just a proceed-to-activate.

**Observation R6 — Fork activation feels like a speed bump.** The fork node has no fields, so the only action is "Continue." An agent landing here might wonder why it can't just auto-advance like the router. The fork *could* auto-activate if it has no gate and no fields. The manual "Continue" adds a step without adding value.

---

### Parallel Branch Execution
After activating the fork, I landed in the `technical` branch with 4 field affordances plus a "Switch to Compliance Review" button.

**Observation R7 — Branch switching is excellent.** The `switch_branch` affordance toggles between parallel branches. Affordances update to show the other branch's fields. An agent can work on both branches before submitting either. Very intuitive.

**Observation R8 — Branch submit auto-switches.** After submitting the compliance review, the engine auto-switched to the still-incomplete technical branch and showed its fields (with preserved values). Smart flow management.

---

### Review Merge (show_all_fields) — FINDINGS

#### BUG: Computed field evaluates incorrectly
**"All Reviews Acceptable" = false** when it should be true.
- Tech Assessment: "Acceptable with comments" → should match `field_equals("Acceptable with comments")` in the OR set
- Regulatory Alignment: "Minor gaps identified" → should match `field_equals("Minor gaps identified")` in the OR set
- The AND of two true ORs should be true. Getting false.
- The `instruction_when_false` text is showing ("One or more reviews flagged issues"), confirming the engine thinks the expression is false.
- **Root cause hypothesis:** The evaluator may be checking the wrong field keys, or the `field_equals` comparison has a case/whitespace issue. Need to inspect the evaluator code.

#### BUG: Compliance Findings field value lost
- Set to a paragraph about ISO 9001 records retention
- Shows null at review_merge
- Other compliance fields persisted (reviewer, regulatory_alignment, policy_references)
- This is the second data loss incident (first was impact_analysis during branch switch)
- **Pattern:** Both lost values were in non-gate fields (not required by the proceed gate). Gate-required fields persisted. Possible that only gate-required fields are carried through?

Actually — impact_analysis persisted after I re-set it on the second pass. So the data loss may be related to the branch switch timing, not the field's gate status. compliance_findings was set, then I proceeded (which submitted compliance and auto-switched to technical), and the value was lost during that transition.

#### Issue: show_all_fields noise
- Fields from **unvisited** paths (escalation: executive_sponsor, risk_assessment; quick_review: reviewer, assessment, comments) are visible with null values
- 24 affordances on one page — overwhelming for an agent
- An agent might try to fill escalation fields thinking they're required
- **Design question:** Should show_all_fields only show fields from *visited* nodes? Or is the "complete picture" intent valuable enough to accept the noise?

#### Observation R9 — No proceed gate on review_merge
I deliberately left the review_merge proceed gate empty (no `requires`). This means the Proceed button should appear unconditionally. Let me verify it's available.
