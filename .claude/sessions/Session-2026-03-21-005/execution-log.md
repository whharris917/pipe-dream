# Agent API Evaluation — Execution Log

## Objective
Evaluate agent-friendliness of the Create Workflow workflow API by building a complex workflow using only curl. Document challenges, confusion, and observations.

---

## Execution

### Step 1: Discovery — What workflows exist?
**Action:** GET the agent portal to see available workflows.

**Observation 1 — Content negotiation:** First attempt returned HTML. Need `Accept: application/json` header to get the machine-readable payload. This is important for agents — if I hadn't known to ask for JSON, I'd be parsing HTML.

**Observation 2 — Portal structure is excellent.** The response has three clear sections:
- `state`: What exists (workflow types and their instances)
- `instructions`: Natural language guidance
- `affordances`: Exactly what I can do, with method/url/body

**Observation 3 — Affordance design is HATEOAS-compliant.** Each affordance gives me the exact URL and body. I don't need to construct URLs or guess parameters. The labels are human-readable. The `id` field provides a stable reference.

**Observation 4 — Instance model is clear.** Each workflow type can have multiple instances. Each instance shows its current node (state). Existing instances: create-workflow has 2 (one at metadata, one published).

**Decision:** Create a new Create Workflow instance via affordance #11 (POST /agent/create-workflow/new).

---

### Step 2: Create new Create Workflow instance
**Action:** POST /agent/create-workflow/new with empty body.
**Response:** `{"instance_id": "57f1ba09", "workflow_id": "create-workflow"}`

**Observation 5 — Minimal creation response.** Just returns the IDs. Good — no bloated response. But it doesn't redirect or include the URL of the new instance. An agent needs to construct the GET URL from the IDs. Minor friction — the portal affordances already showed the URL pattern, so I could infer `/agent/create-workflow/57f1ba09`.

---

### Step 3: GET initial state of new instance
**Action:** GET /agent/create-workflow/57f1ba09

**Observation 6 — Rich initial state.** The response has:
- `state.node`: "metadata" — current position in the builder workflow
- `state.fields`: Three fields with null values and instructions
- `state.banner_definition`: The builder's own workflow topology (4 nodes: metadata → node_builder → preview → published)
- `state.definition`: The workflow I'm building (empty)
- `instructions`: Clear natural language guidance
- `affordances`: Three SET operations, one per field

**Observation 7 — Instructions are excellent.** They explain what each field is for (slug for URLs, human-readable name, one-line summary). Format guidance (lowercase, hyphens only) is inline.

**Observation 8 — Field instructions are redundant with node instructions.** Both `state.fields[].instruction` and the top-level `instructions` describe the same things. This is slightly noisy but not harmful — belt and suspenders.

---

### Steps 4-6: Set metadata fields
**Actions:** Three POSTs to set_workflow_id, set_workflow_title, set_workflow_description.

**Observation 9 — Feedback diffs are clean.** Each POST returns `{attempted_action, outcome, effects}`. Effects show exactly what changed: `modified_fields`, `modified_affordances`, `new_affordances`, `new_fields`. The affordance labels update to show current values. Very agent-friendly — I can confirm my action took effect without re-fetching.

**Observation 10 — Proceed gate is title-only.** After setting the title, "Proceed to Lifecycle" appeared. The ID and description are optional for advancing. This makes sense — you might want to iterate on those later.

**Observation 11 — Affordance URLs use action names, not field keys.** The URL is `/set_workflow_id` but the field is `Workflow ID`. The mapping is implicit — an agent must infer that underscored URL segments correspond to title-cased field labels. This works but could cause confusion if the naming convention isn't perfectly consistent.

**Workflow plan:** I'll build a "Document Review and Approval" workflow with:
1. **intake** — Document metadata + severity classification
2. **severity_router** — Router: auto-routes based on severity (Critical→escalation, Major→parallel_review, Minor→quick_review)
3. **escalation** — Executive review fields for critical items
4. **parallel_review** — Fork: splits into technical_review and compliance_review
5. **technical_review** — Technical assessment fields
6. **compliance_review** — Compliance assessment fields
7. **review_merge** — Merge point for parallel tracks
8. **quick_review** — Streamlined single-reviewer path for minor items
9. **approval** — Final approval decision with show_all_fields
10. **complete** — Terminal node

---

### Step 7: Proceed to Node Builder
**Action:** POST /agent/create-workflow/57f1ba09/proceed with empty body.

**Observation 12 — Proceed transitions cleanly.** The feedback shows the new affordances available on the node_builder page: Add node, Add option set, Add column type, Go back. No state confusion.

**Observation 13 — Option sets and column types are global.** They're defined at the workflow level, not per-node. This is a good design — reusable across nodes.

---

### Step 8: Add first node (intake)
**Action:** POST /agent/create-workflow/57f1ba09/add_node with id, title, instruction.

**Observation 14 — Auto-focus is powerful but chatty.** Adding the first node triggered a *massive* response — the node auto-focused, exposing all node-editing affordances (add field, add list, set table, set proceed, add navigation, add action, set show_all_fields, set pause, set execution, set node mode). This is correct behavior (focus → show editing tools) but the response payload is very large.

**Observation 15 — Field parameters are self-documenting.** The `add_field` affordance includes descriptions for every parameter: `visible_when`, `side_effects`, `dynamic_options`, `compute`, `options_from`, `annotate_from`. The expression language syntax is fully documented inline in the affordance description. An agent can construct complex expressions without external documentation. This is *excellent* agent-friendliness.

**Observation 16 — Expression language is consistent.** The same expression dict format (`{type, key, value}` for leaves, `{op, conditions}` for composites) appears everywhere: `visible_when`, `gate`, `side_effects`, `compute`, `when` (routes/navigation). One syntax for all conditional logic.

---

### Steps 9-13: Add remaining intake fields
**Actions:** Five more add_field POSTs (document_type, author, description, severity, escalation_justification).

**Observation 17 — Conditional visibility works.** For `escalation_justification`, I used `visible_when: {type: field_equals, key: severity, value: Critical}`. Accepted without error. I won't know if it actually works until runtime, but the builder accepted the expression.

**Observation 18 — Subsequent add_field responses are lean.** After the first field (which triggered edit/remove affordances and the Proceed button), subsequent fields produce minimal responses with empty `new_affordances`. The system is smart about not repeating structural affordances that already exist.

---

### Step 14: Set proceed gate for intake
**Action:** POST /agent/create-workflow/57f1ba09/set_proceed with `requires` array.

**Observation 19 — `requires` shorthand is ergonomic.** Instead of constructing `{op: AND, conditions: [{type: field_truthy, key: k1}, ...]}`, I just passed `["document_title", "document_type", "author", "severity"]`. The system expanded it into the full expression. The affordance label now shows the expanded gate for verification.

**Observation 20 — The `requires` parameter shows available keys.** After setting the gate, the modified affordance shows `"Available: ['document_title', 'document_type', 'author', 'description', 'severity', 'escalation_justification']"`. This tells me which field keys exist for future gate construction. Very helpful.

---

### Steps 15-22: Add remaining nodes
**Actions:** Added 9 more nodes: severity_router, escalation, parallel_review, technical_review, compliance_review, review_merge, quick_review, approval, complete.

**Observation 21 — Each add_node auto-focuses the new node.** This means I can immediately start configuring the just-added node. But if I'm batch-adding nodes (like I was), I need to re-select each node later. The auto-focus is good for interactive use but adds overhead for batch operations.

**Observation 22 — Node ordering.** Nodes are listed in creation order. The `select_node` affordance shows all nodes with index-based selection. A "Move node up" affordance appeared after the second node was added.

---

### Step 23: Configure severity_router as router
**Action:** Set node mode to "router", then add 3 routes.

**Observation 23 — Router mode transformation.** Switching to router mode added "Add route" affordance. But initially the only target option was "intake" (the only other existing node at that time). I had to add all target nodes first, then come back. This is a natural ordering dependency, not a design flaw — but it means you can't fully configure a router until all its targets exist.

**Observation 24 — Route target options are dynamic.** After adding all nodes, the `add_route` affordance showed all 9 other nodes as valid targets. The options update dynamically based on the current node list.

**Observation 25 — Route conditions use the same expression language.** `{type: field_equals, key: severity, value: Critical}` for each route condition. Consistent with gates, visible_when, etc.

---

### Step 24: Configure escalation node (in progress)
**Action:** Selected escalation (index 2), adding fields.
- Added: executive_sponsor (text), risk_assessment (select with 3 options)
- Still need: mitigation_plan (text, conditional), executive_approval (boolean), proceed gate, proceed target → approval

---

### Steps 25-40: Configure all remaining nodes
**Escalation:** Added executive_sponsor, risk_assessment, mitigation_plan (visible_when risk = "Acceptable with mitigations"), executive_approval (boolean). Proceed gate with requires + target → approval. Go_back navigation.

**Parallel_review:** Set to fork mode, set merge target to review_merge, added two branches (technical → technical_review, compliance → compliance_review).

**Technical_review:** 4 fields (tech_reviewer, tech_assessment, tech_comments, impact_analysis). Proceed gate requiring reviewer + assessment.

**Compliance_review:** 4 fields (compliance_reviewer, regulatory_alignment, compliance_findings, policy_references). Proceed gate.

**Review_merge:** show_all_fields=true. Added computed field `reviews_acceptable` with complex AND/OR expression checking both tech_assessment and regulatory_alignment for acceptable values. instruction_when_true/false for guidance. Added consolidation_notes field. Proceed → approval.

**Quick_review:** 3 fields (reviewer, assessment, comments). Proceed gate → approval.

**Approval:** show_all_fields=true. 4 fields (approver, approval_decision, approval_conditions [visible when "Approved with conditions"], rejection_reason [visible when rejected via OR composite]). Proceed gate → complete. Conditional navigation "Return for Revision" → intake when rejected.

**Complete:** show_all_fields=true. 2 fields (effective_date, document_version). Restart action.

---

### Step 41: Verification — Full State Audit

**CRITICAL FINDING: Fork configuration silently lost.**

After configuring all 10 nodes, I did a full GET and inspected the definition. The severity_router's routes are correctly stored (under a `router` key, not `routes` — a naming difference from what I expected). But the **parallel_review fork configuration is empty**:

```json
"fork": {
    "branches": {},
    "label": "Continue",
    "merge": ""
}
```

Despite receiving `{outcome: {}}` success responses for `set_fork_merge` and two `add_branch` calls, the fork data didn't persist. This is a **silent failure** — the API accepted my requests and returned what looked like success, but the state wasn't modified.

**Hypotheses:**
1. The fork target must be set before adding branches (ordering dependency)
2. The `set_fork_merge` and `add_branch` actions may require the node to be in fork mode at the time they're called — but I did set the mode to fork first
3. The select_node to parallel_review and subsequent set_node_mode to fork may not have actually focused correctly — the responses said OK but I wasn't verifying the focused node in subsequent responses

**Observation 26 — Empty `{outcome: {}}` is ambiguous.** A response with empty outcome and empty effects could mean "success, nothing new to report" OR "silently ignored." There's no explicit success/failure indicator in the response. An agent has no way to distinguish between "accepted and applied" vs "ignored." This is a significant agent-friendliness gap.

**Observation 27 — Also note intake proceed target.** The intake proceed gate shows `target: severity_router`, but I never set an explicit target. It was auto-populated based on sequential node order. This is helpful default behavior — sequential nodes auto-link.

**Action:** Re-attempt fork configuration with careful verification.

---

### Step 42: Fork Configuration — Root Cause Found

**Root cause: I was using wrong parameter names.** The affordances clearly specify the body structure, and I wasn't following it:

| What I sent | What the affordance said | Correct body |
|---|---|---|
| `{"target": "review_merge"}` | `{"merge": "<merge>"}` | `{"merge": "review_merge"}` |
| `{"name": "technical", "target": "technical_review"}` | `{"branch_id": "<branch_id>", "label": "<label>", "nodes": "<nodes>"}` | `{"branch_id": "technical", "label": "Technical Review", "nodes": ["technical_review"]}` |

**Observation 28 — The affordance body template IS the schema.** The `body` field in each affordance is not just a hint — it's the exact JSON structure the endpoint expects. `<merge>` is a placeholder for the merge parameter. I was constructing bodies from my understanding of the domain model instead of reading the affordance's body template. This is 100% an agent error.

**Observation 29 — But the error messages are unhelpful.** When I sent `{"target": "review_merge"}`, the error was `"Merge target '' does not exist."` — it validated the empty default, not my unrecognized parameter. A better error would be: `"Unknown parameter 'target'. Expected: merge."` The first two `add_branch` calls returned `{outcome: {}}` with NO error — complete silent failure. That's the bigger problem.

**Observation 30 — The `parameters` object is the REAL documentation.** The `body` template shows the shape, but `parameters` shows the types, options, and descriptions. For `add_branch`, `parameters.nodes` says `"Array of node IDs"` and lists available options. For `set_fork_merge`, `parameters.merge` lists all valid node IDs as options. An agent should parse `parameters` for constructing the body, not infer parameter names from domain knowledge.

**Observation 31 — Error asymmetry.** `set_fork_merge` with wrong params → error in outcome. `add_branch` with wrong params → silent success (empty outcome, empty effects). Same category of mistake, different behavior. The handler probably has different validation paths.

**Resolution:** Fork now correctly configured. Merge → review_merge. Branches: technical (→ technical_review), compliance (→ compliance_review).

---

### Step 43: Proceed to Preview & Publish
**Action:** POST proceed → preview node. Then POST publish.

**Observation 32 — No explicit validation output.** The preview instructions say "Validation checks run automatically" but the state doesn't include a `validation` section with results. Validation is implicit — if the "Publish Workflow" affordance appears, it passed. An agent has no way to see *what* was validated or *what* passed. If validation failed, presumably the Publish affordance wouldn't appear, but there'd be no error message explaining what's wrong.

**Observation 33 — Publish response is clean.** Returns the restart affordance as the only available action on the "published" terminal node.

**Observation 34 — YAML output is excellent.** 398 lines of clean YAML. All features are faithfully serialized: router conditions, fork branches with merge target, computed fields with nested AND/OR expressions, visible_when conditions, proceed gates, navigation with conditional guards, show_all_fields, actions. The YAML is human-readable and could be hand-edited.

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total API calls | ~50 (GET + POST) |
| Nodes created | 10 |
| Fields created | 29 |
| Routes configured | 3 |
| Fork branches | 2 |
| Computed fields | 1 |
| Conditional visibility | 4 fields |
| Proceed gates | 7 |
| Navigation links | 2 |
| Terminal actions | 1 |
| Errors encountered | 3 (2 silent, 1 with message) |
| YAML output | 398 lines |

---

## Overall Agent-Friendliness Assessment

### What Works Well

1. **HATEOAS affordance model is excellent.** Every action an agent can take is explicitly listed with method, URL, body template, and parameter descriptions. No URL construction, no guessing. The agent just picks from a menu of available actions.

2. **Feedback diffs are precise.** POST responses show exactly what changed (modified fields, modified affordances, new affordances, new fields). An agent can confirm success without re-fetching.

3. **Expression language is consistent and self-documenting.** The same expression syntax appears everywhere (gates, visibility, compute, route conditions, navigation guards). Parameter descriptions include the full syntax inline. An agent can construct complex expressions without external docs.

4. **Progressive disclosure.** Affordances appear as they become relevant (Proceed only when gate requirements are met, route affordances only in router mode, fork affordances only in fork mode). The agent is never overwhelmed with irrelevant options.

5. **Field parameter richness.** The `add_field` affordance exposes the full feature set: type, options, visible_when, side_effects, dynamic_options, compute, annotate_from, instruction_when_true/false. An agent can author complex fields in a single call.

6. **The `requires` shorthand.** Converting an array of field keys into an AND gate expression is a major convenience. The full expression language is available for complex cases, but simple gates are trivial.

### What Needs Improvement

1. **Silent failures are the #1 problem.** When I sent `add_branch` with wrong parameter names (`name`/`target` instead of `branch_id`/`label`/`nodes`), the response was `{outcome: {}}` — identical to success. The same mistake with `set_fork_merge` at least returned an error. Unrecognized parameters should *always* produce an error, or at minimum, the response should include a positive success indicator (e.g., `"outcome": {"status": "ok", "applied": true}`).

2. **Content negotiation requirement.** The default GET response is HTML, requiring `Accept: application/json` for the machine-readable payload. For an agent API, JSON should be the default or the agent endpoint should always return JSON. Having to know about content negotiation is a barrier.

3. **Parameter naming divergence.** The affordance body templates use parameter names that sometimes differ from what a domain-knowledgeable agent would guess:
   - `merge` (not `target`) for fork merge
   - `branch_id` + `nodes` (not `name` + `target`) for branches
   - `field_index` (not `field_key` or `field_name`) for field references

   The affordance *does* document these, but the names aren't always intuitive. An agent that constructs bodies from domain knowledge rather than reading the affordance template will fail silently.

4. **No explicit validation feedback on preview.** Validation passes/fails invisibly. The agent can only infer pass/fail from the presence/absence of the Publish affordance. Failed validation should produce structured errors.

5. **Response payload size.** Adding the first node to a fresh workflow produces a response with ~15 affordances, each with full parameter documentation including the expression language syntax repeated in every `description` field. This is correct (progressive disclosure) but verbose. The expression language description alone is ~100 characters repeated in 5+ places per response.

6. **Error messages don't identify the real problem.** "Merge target '' does not exist" when the issue is "you sent 'target' but the parameter is 'merge'." The error validates the default value instead of flagging the unrecognized parameter.

### Verdict

The API is **highly agent-friendly** with one critical gap: **silent failures on malformed requests**. The HATEOAS model, affordance-driven interaction, feedback diffs, and expression language documentation make it genuinely possible for an agent to author complex workflows without external documentation. The parameter naming issue is a learning curve, not a design flaw — if the agent reads the affordance body template (as it should), the correct names are right there.

The single most impactful improvement would be: **reject unrecognized parameters in POST bodies and return an error listing the expected parameters.** This alone would have prevented the 30-minute fork debugging detour.
