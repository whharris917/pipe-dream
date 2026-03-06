# Meta-Lifecycle Experiment Report

## 1. Did the meta-workflow successfully guide through all three phases?

Yes. The meta-workflow completed all three phases without errors:

- **Phase 1 (Author):** 83 meta-workflow steps to define a 9-node template. The define-step / define-field / define-edges / more-X loop pattern correctly accumulated all step definitions, evidence fields, and edge connections.
- **Phase 2 (Instantiate):** 20 meta-workflow steps (85-104) to specialize all 9 steps. The inst-specialize / inst-more loop pattern worked cleanly.
- **Phase 3 (Execute):** 2 meta-workflow steps (104-105) plus 9 steps on the generated instance workflow. The execute node correctly handed off to a separate ticket on the generated instance, then collected confirmation back.

The meta-workflow reached terminal state at step 106. The generated template validated (9 nodes, all reachable), the generated instance validated (9 nodes), and the instance execution completed (9/9, 100%).

## 2. Step count comparison

| Approach | Steps to produce template | Steps to produce instance | Steps to execute | Total |
|----------|--------------------------|--------------------------|------------------|-------|
| **Direct YAML authoring (previous)** | 0 (wrote 12 YAML files by hand) | 0 (wrote 12 YAML files by hand) | 9 | 9 traversal steps |
| **Meta-workflow** | 83 | 20 | 9 + 2 (execute + summary) | 106 meta-workflow steps + 9 execution steps |

The meta-workflow required **106 steps** to accomplish what direct YAML authoring did in **0 workflow steps** (just file creation). The 9 execution steps are equivalent in both approaches.

The 83-step authoring phase breaks down as:
- 1 template metadata (m.start)
- 9 step definitions (m.define-step)
- 22 field definitions (m.define-field) for 22 total fields across 9 steps
- 22 field continuation prompts (m.more-fields)
- 11 edge definitions (m.define-edges) for 10 real edges + 1 empty terminal edge
- 11 edge continuation prompts (m.more-edges)
- 8 step continuation prompts (m.more-steps, with the 9th being "no" leading to generate)
- 1 generation confirmation (m.generate-template)

The overhead comes almost entirely from the yes/no continuation nodes. Every field requires two meta-steps (define + confirm-more). Every edge requires two meta-steps. Every step requires one meta-step to confirm whether to add another. For a 9-step template with 22 fields and 10 edges, that is 22 + 10 + 8 = 40 continuation prompts that carry no information beyond "keep going" or "stop."

## 3. What was gained by going through the meta-workflow?

**Structured decomposition.** The meta-workflow forced each design decision into its own step with its own evidence record. When defining a field, I had to explicitly declare: name, type, required, values, hint. When defining an edge, I had to specify: target and condition. This leaves a complete audit trail of every authoring decision.

**Separation of concerns between structure and content.** The instantiation phase cleanly separated what changes (prompts, context, hints) from what stays the same (field names, types, edge topology). This validated that the template/instance pattern works: you define structure once, then override content per scenario.

**Validation gates.** The generate-template and generate-instance nodes include confirmation checkpoints. If the generated YAML looks wrong, the workflow loops back to the authoring phase. This provides a natural review cycle.

**Reproducibility.** The ticket file (lifecycle-001.json) contains every response from every step. The generator script is deterministic. Given the same ticket, the same template and instance will be produced. This is better provenance than "someone wrote YAML files."

## 4. What was lost or made harder?

**Extreme verbosity.** 83 steps to define 9 nodes is a 9:1 overhead ratio. The yes/no continuation nodes (more-fields, more-edges, more-steps) are pure friction. They exist because the graph engine handles loops by revisiting the same node, but the "do you want to continue?" pattern adds no information when the author already knows how many fields and edges they declared in the step definition.

**Loss of holistic view.** When writing YAML by hand, I could see the entire template at once, reason about edge connectivity across nodes, and refactor freely. In the meta-workflow, I defined each step in isolation. I had to plan the entire template upfront (including exact field counts and edge targets) because the sequential accumulation pattern does not support going back to modify a previous step without restarting. The meta-workflow is strictly forward-only within a phase.

**Hint assignment fragility.** The instance specialization uses semicolon-separated hints applied positionally to evidence schema fields. But YAML serialization (via PyYAML's `yaml.dump`) reorders dictionary keys alphabetically. So the hint "Describe the 504 timeout on /api/v2/orders" intended for `incident_summary` ended up on `active_harm` (which comes first alphabetically). This is a bug in the generator's interaction with YAML serialization.

**No iteration within a step.** Once a step definition is submitted, it cannot be revised without completing the entire authoring loop and using the "template_looks_correct: no" escape hatch, which loops all the way back to define-step. There is no way to say "actually, I want to change the hint on the second field of step 3."

## 5. Did the generated template/instance match hand-written YAML?

**Template topology: close match.** The generated template has the same 9 happy-path nodes with the same linear progression and the one branch at start (contain vs timeline). The hand-written template had 12 nodes because it included 3 error-recovery loops (contain-failed, reproduce-failed, fix-failed). The meta-workflow version is simpler by design, as instructed.

**Field schemas: functionally equivalent.** The generated fields use the same names, types, and enum values as the hand-written version, though with fewer fields per node (2-3 vs 3-5 in the hand-written version). This was a deliberate simplification.

**Key difference: YAML formatting.** The hand-written YAML used human-friendly formatting: multi-line context strings with `>` block scalars, logical field ordering, and consistent indentation. The generated YAML uses PyYAML's default dump format: alphabetically sorted keys, quoted strings for values containing special characters, and less readable whitespace. Functionally identical; aesthetically worse.

**Instance specialization: mostly correct.** Prompts and contexts were correctly overridden. The hint positional assignment bug caused some hints to land on the wrong fields, but the evidence schemas themselves (field names, types, required flags) were preserved correctly from the template.

## 6. Suggestions for improving the meta-workflow

**1. Eliminate continuation nodes for pre-declared counts.** The define-step response already includes `num_fields` and `num_edges`. The meta-workflow should use these to loop the correct number of times without asking "add another?" after each one. This would cut the 83-step authoring phase roughly in half.

**2. Support field-level hint specialization.** Instead of semicolon-separated positional hints, the inst-specialize node should present each field by name and let the author provide a per-field hint. This avoids the YAML key-ordering problem entirely.

**3. Add an "edit step" capability.** After defining all steps, before generation, allow the author to revisit and modify a specific step. The current architecture only supports forward iteration or full restart.

**4. Batch response support for homogeneous loops.** Allow submitting all field definitions for a step in a single response (as an array), rather than one per meta-workflow visit. This would collapse the field definition loop from 2N steps (N defines + N confirmations) to 1 step.

**5. Use ordered dict or insertion-order preservation in the generator.** Replace `yaml.dump` with a serializer that preserves insertion order (e.g., `ruamel.yaml`), or explicitly sort evidence_schema fields in definition order rather than alphabetical order. This fixes the hint-misassignment bug.

**6. Add a "dry run" mode to the generator** that shows the would-be output structure without writing files, so the author can validate before committing to the generate-template step.
