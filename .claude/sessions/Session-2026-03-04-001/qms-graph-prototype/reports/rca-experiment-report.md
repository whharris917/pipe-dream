# RCA Experiment Report

## 1. Node Counts: Template vs Instance

Both `rca-template/` and `rca-504/` contain **12 nodes** each. The node counts are identical because the instance was designed as a direct specialization of the template — same graph structure, same branching logic, same error-handling paths. The only differences are in the *content* of each node (prompts, context, hints), not the *topology*.

This is the expected outcome for a well-designed template. The template defines the procedural skeleton (what questions to ask, in what order, with what branching logic), and the instance fills in the domain-specific details. If the instance needed a different number of nodes, it would indicate either that the template was too rigid or that the specific incident didn't fit the general procedure.

**Template nodes:** start, contain, contain-failed, timeline, reproduce, reproduce-failed, isolate, root-cause, fix, fix-failed, deploy, postmortem

**Instance nodes:** Identical set of 12, with the same IDs and edge structure.

## 2. Did the Instance Workflow Guide the Investigation?

Yes. The workflow traversed 9 of the 12 nodes on the "happy path with containment":

```
start -> contain -> timeline -> reproduce -> isolate -> root-cause -> fix -> deploy -> postmortem
```

Three nodes were not visited: `contain-failed`, `reproduce-failed`, and `fix-failed`. These are error-recovery loops that exist in the graph but were not triggered because:
- Containment was "partial" (not "no"), so it advanced to timeline rather than escalating.
- Reproduction succeeded on the first attempt.
- The fix validated successfully in staging.

The branching logic worked correctly at every decision point:
- `active_harm == yes` at triage correctly routed to containment before timeline.
- `containment_effective == partial` correctly fell through to timeline (only `no` triggers the failure path).
- `reproduced == yes` correctly routed to isolation (skipping the reproduce-failed loop).
- `fix_validated == yes` correctly routed to deploy (skipping the fix-failed loop).
- `fix_confirmed == yes` at deploy correctly routed to postmortem (terminal).

The specific context at each node was genuinely useful — it reminded me what to check, what the expected values were, and what the next logical question should be. The hints in the evidence schema acted as a checklist within each step.

## 3. Translating Prose Procedure to Graph Workflow

The translation process revealed several structural insights:

**What mapped cleanly:** The 8 steps of the prose procedure mapped almost 1:1 to 8 primary nodes. The linear progression (triage -> contain -> timeline -> reproduce -> isolate -> root cause -> fix -> deploy -> postmortem) was straightforward to encode as a chain of edges.

**What required additional structure:** The prose procedure described error handling in natural language ("if reproduction fails, gather more information or proceed observationally"). In the graph, these became explicit nodes with branching edges. This produced 4 additional "failure path" nodes (contain-failed, reproduce-failed, fix-failed, and the triage-to-contain branch). The prose procedure has 8 steps; the graph has 12 nodes because every failure mode needs an explicit recovery path.

**What was harder than expected:** Deciding the evidence schema for each node required more precision than prose. In prose, "establish the timeline" is a paragraph of guidance. In the graph, I had to decide: how many fields? What types? Which are required? What are the exact enum values for branching decisions? This forced me to think about what *structured evidence* each step actually produces, which is more rigorous than prose.

**What was easier than expected:** The conditional edge syntax (`response.get('active_harm') == 'yes'`) made branching logic very explicit and testable. In prose, branching is expressed as "if X, do Y" scattered through paragraphs. In the graph, every branch is a first-class edge with a machine-evaluable condition.

## 4. What the Graph Structure Added and Lost

**Added:**

- **Enforced completeness.** Every step requires structured evidence. You cannot skip a field or hand-wave through "I checked the logs." The evidence schema demands specific answers to specific questions.
- **Explicit error recovery.** The prose procedure mentions "if the fix doesn't work, reassess" in a sentence. The graph has a dedicated node with a three-way branch (revise fix, re-examine root cause, re-isolate) that ensures the investigator has a clear path forward. The loop-back edges make it impossible to get stuck.
- **Machine-verifiable progress.** The engine tracked that 9/12 nodes were completed, showed which path was taken, and could report the state at any point. This is audit trail for free.
- **Deterministic routing.** The branching conditions are unambiguous. The prose says "if active harm is occurring, contain first." The graph evaluates `response.get('active_harm') == 'yes'` — there is no room for interpretation.

**Lost:**

- **Narrative flow.** The prose procedure reads as a coherent story with reasoning and rationale woven through. The YAML nodes are isolated fragments. Reading the YAML files sequentially does not convey *why* the steps are in this order or how they build on each other.
- **Flexibility in depth.** The prose procedure's "5 Whys" section is a rich, recursive analytical technique. In the graph, it becomes a single text field. The graph enforces that you *provide* the five whys, but it cannot enforce that you actually performed deep analysis — it only captures the output.
- **Contextual judgment.** The prose procedure says things like "apply the least-invasive containment measure." The graph can hint at this but cannot evaluate whether the chosen measure was actually minimally invasive. The evidence schema captures *what* was done, not whether it was the *right* thing.
- **Proportional attention.** In prose, I naturally spent more words on the harder/more important steps (root cause analysis, postmortem). In the graph, every node has roughly equal structural weight regardless of intellectual difficulty.

## 5. Engine Issues

**No blocking issues encountered.** The engine performed correctly throughout execution:

- `validate` caught the entry-point naming issue immediately (the engine expects the start node to have an ID ending in `.start` or be in a file named `start.yaml`). This was a minor naming convention that was easy to fix but not documented in the graph files themselves — I had to read the engine source to understand the requirement.
- `respond` correctly evaluated all branching conditions and advanced the cursor to the expected nodes.
- `map` provided a clear visualization of the graph topology with accurate cursor position tracking (`+` for completed, `>>>` for current, `.` for upcoming).
- The `--response-file` flag was essential for providing complex JSON responses without shell escaping issues.
- The `history` command provided a readable audit trail of all evidence collected.

**One minor observation:** The `map` command reported "Progress: 9/12 (75%)" for a completed workflow. This is technically accurate (9 of 12 nodes were visited), but could be misleading — the workflow is 100% complete (it reached a terminal node), it just didn't need to visit the error-recovery nodes. A "completion" metric distinct from "coverage" might be useful for distinguishing "finished successfully" from "visited every node."
