# Usability Report: Cold Start -- Incident Response Procedure

**Tester:** Claude (AI agent, no prior exposure to this system)
**Date:** 2026-03-05
**Document:** INC-TEST-001
**Template:** templates.incident.Incident
**Outcome:** Successfully completed in 9 steps, zero errors

---

## Executive Summary

I completed the full incident response procedure from cold start to completion with
no prior knowledge of the QMS graph engine. The system was intuitive enough that I
never got stuck, and every step was completed on the first attempt. The total process
took 9 response submissions across approximately 3 minutes of wall-clock time.

---

## Step-by-Step Experience

### Discovery Phase (before starting the document)

| Action | Clarity | Notes |
|--------|---------|-------|
| `--help` | Excellent | Clean subcommand list, obvious what each does |
| `list-templates` | Good | Shows inheritance hierarchy which helps understanding |
| `start` command | Good | The template path syntax (`templates.incident`) worked on first try |

**Minor friction:** The `start` help says the argument is `<template.module.Class>` but
it also accepts just the module path (e.g., `templates.incident`) and auto-discovers
the class. This is a nice convenience, but the help text could mention it explicitly.

### Step 1: Triage (incident.start)

- **Prompt:** "Triage the incident."
- **Context:** "Assess the severity and immediate impact of this incident."
- **Was it clear?** Yes. The evidence schema made it obvious what was needed: a
  description, severity level, whether there's active impact, and a readiness check.
- **Hints useful?** Yes, especially "Brief description of the incident" for the
  `objective` field.
- **Suggestion:** The `ready` field has no hint. Adding "Confirm you are ready to
  proceed with incident response" would be more helpful.

### Step 2: Observe (incident.observe)

- **Prompt:** "Observe and document the symptoms."
- **Context:** "Gather all observable facts about the problem. Do not jump to conclusions."
- **Was it clear?** Very clear. The context instruction to "not jump to conclusions"
  is a good guardrail for structured thinking.
- **Hints useful?** Yes. All three fields had descriptive hints.

### Step 3: Hypothesize (incident.hypothesize)

- **Prompt:** "Form a hypothesis about the root cause."
- **Was it clear?** Yes. The enum for confidence level (low/medium/high) is well chosen.
- **Note:** The `alternative_hypotheses` field being optional is correct -- it
  encourages thorough thinking without blocking progress.

### Step 4: Test (incident.test)

- **Prompt:** "Test your hypothesis."
- **Context:** "Design and execute a test that would confirm or refute your hypothesis."
- **Was it clear?** Yes. The three-way enum for `hypothesis_confirmed` (yes/no/inconclusive)
  is particularly good -- it acknowledges ambiguity.
- **Observation:** There is no loop-back mechanism if the hypothesis is refuted. The
  graph goes straight from test -> contain regardless of whether the hypothesis was
  confirmed. In a real incident, you might want to loop back to hypothesize if the
  test result is "no" or "inconclusive."

### Step 5: Contain (incident.contain)

- **Prompt:** "Contain the incident."
- **Context:** "Take immediate action to stop ongoing damage or impact."
- **Was it clear?** Yes. Simple and focused.
- **Observation:** The `impact_stopped` field accepts "partial" which is a realistic
  option. Good design choice.

### Step 6: Remediate (incident.remediate)

- **Prompt:** "Remediate the root cause."
- **Was it clear?** Yes. The optional `rollback_plan` field is a smart inclusion --
  it prompts the responder to think about failure scenarios without requiring it.

### Step 7: Conclude (incident.conclude)

- **Prompt:** "State your conclusion."
- **Was it clear?** Yes, though there is some redundancy with the earlier test step.
  The `root_cause` field here overlaps with the hypothesis that was already confirmed
  in step 4. However, this serves as a useful synthesis point where all evidence is
  summarized together.

### Step 8: Verify (incident.verify)

- **Prompt:** "Verify the resolution."
- **Context:** "Confirm the incident is fully resolved and services are restored."
- **Was it clear?** Yes. The `services_restored` field is specific to incident
  response (vs. the generic ProcedureBase verify step) which shows good template
  specialization.
- **Observation:** Like the test step, there is no loop-back if verification fails.
  If `all_steps_passed` or `services_restored` is "no", the graph still proceeds
  to close.

### Step 9: Close (incident.close)

- **Prompt:** "Close the incident."
- **Was it clear?** Yes. The three-way `outcome` enum (resolved/mitigated/unresolved)
  is well designed -- it captures the realistic range of incident outcomes.
- **Observation:** The `follow_up_needed` field captures future work, but there is
  no mechanism to create a follow-up document from within the graph.

---

## Quantitative Summary

| Metric | Value |
|--------|-------|
| Total steps | 9 |
| Steps with confusion | 0 |
| Validation errors encountered | 0 |
| Times I needed to re-read the schema | 0 |
| Commands used to complete | 11 (1 start + 1 map + 9 respond) |
| Time from start to finish | ~3 minutes |

---

## What Worked Well

1. **The `status` output after each `respond` is excellent.** It immediately shows the
   next node's prompt, context, and evidence schema, so you always know what to do next
   without running a separate status command.

2. **Evidence schemas are self-documenting.** The combination of field type, required
   flag, values list (for enums), and hint text gives enough information to construct
   a valid response without guessing.

3. **The `map` command is genuinely useful.** The `>>>` cursor, `+` for completed nodes,
   and `.` for pending nodes makes it easy to see progress at a glance.

4. **The template inheritance model makes sense.** Reading that Incident extends
   Diagnostic which extends ProcedureBase gave me a clear mental model of the
   procedure structure before I even started.

5. **The response file approach (--response-file) is agent-friendly.** Writing JSON
   to a file and referencing it is cleaner than trying to inline JSON on the command
   line.

6. **Error messages from validation are clear.** I did not encounter any validation
   errors, but the code shows that errors like "Missing required field 'X'" and
   "Field 'X': 'Y' not in [values]" are straightforward.

---

## What Could Be Improved

### High Priority

1. **No loop-back edges for failed tests or verification.** The graph is strictly
   linear. If `hypothesis_confirmed` is "no" or "inconclusive", you should be able
   to loop back to `hypothesize`. If `services_restored` is "no" in verify, you
   should loop back to `remediate`. Without these edges, the procedure cannot enforce
   its own quality gates.

2. **No gate conditions on node transitions.** Even without loop-back edges, the
   graph could use gate conditions to prevent advancing when critical fields indicate
   failure. For example, `ready: "no"` in the start step should block progression.

### Medium Priority

3. **The `ready` field in the start step has no hint.** Every other field has
   contextual guidance; this one is bare.

4. **No inline response option.** For simple responses, having to write a JSON file
   feels heavyweight. An `--inline '{"key": "value"}'` option would speed up
   interactive use.

5. **History output truncates field values at 60 characters.** For an audit trail,
   this loses important detail. Consider a `--full` flag or making truncation optional.

### Low Priority

6. **No progress percentage.** The status output shows `steps_completed` but not
   total steps remaining. A "Step 5 of 9" or "56% complete" indicator would be nice.

7. **No way to go back and amend a previous response.** Once a node is completed,
   its evidence is locked. For incident response, you often learn new details that
   should be appended to earlier observations.

8. **The `context` field on the close step is empty.** A brief "Record the final
   outcome, provide a summary, and indicate if follow-up actions are needed" would
   maintain consistency.

9. **Template auto-discovery is undocumented.** The `start` command accepts both
   `templates.incident.Incident` (explicit class) and `templates.incident` (auto-find).
   The help text only shows the explicit form.

---

## Suggestions for the Template Design

1. **Add conditional edges to make the diagnostic loop iterative:**
   ```
   test --[hypothesis_confirmed == "no"]--> hypothesize
   test --[hypothesis_confirmed == "inconclusive"]--> observe
   test --[hypothesis_confirmed == "yes"]--> contain
   ```

2. **Add a gate on the start node** to prevent proceeding when `ready` is "no".

3. **Add a gate on verify** to loop back to remediate when `services_restored` is "no".

4. **Consider adding a "timeline" or "impact_duration" field to the close step** --
   this is standard for incident response reports and would enrich the audit trail.

5. **Consider an optional "lessons_learned" field in the close step** -- this is a
   common requirement in incident management frameworks (ITIL, etc.).

---

## Conclusion

The QMS graph engine is highly usable for a cold-start agent. The CLI is well-designed,
the template structure is intuitive, and the evidence schema system is self-documenting
enough that no external documentation was needed to complete the procedure. The main
gap is the lack of conditional branching and quality gates -- the graph is currently
a straight line, which means it cannot enforce the "re-do until correct" pattern that
real incident response requires. Adding conditional edges would transform this from a
simple checklist into a genuine procedure enforcer.

**Overall cold-start usability rating: 8/10**

Deductions:
- -1 for no conditional branching (procedure cannot enforce its own quality gates)
- -1 for no inline response option and minor polish items
