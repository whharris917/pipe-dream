# Agent API Evaluation — Findings & Recommendations

**Date:** 2026-03-21, Session 005
**Method:** Built a 10-node "Document Review and Approval" workflow via the Create Workflow builder using only curl, then executed an instance of the published workflow through the Major severity (fork/merge) path.

---

## 1. Create Workflow Builder — Improvement Suggestions

### 1.1 Silent Failures on Malformed POST Bodies

**The single most impactful issue.** When a POST body contains unrecognized parameter names, the builder's behavior is inconsistent:

| Endpoint | Wrong params sent | Behavior |
|----------|-------------------|----------|
| `set_fork_merge` | `{"target": "review_merge"}` (should be `{"merge": ...}`) | Error in `outcome.error`: "Merge target '' does not exist" |
| `add_branch` | `{"name": "technical", "target": "technical_review"}` (should be `{"branch_id": ..., "nodes": ...}`) | Empty outcome `{}`, empty effects — indistinguishable from success |

The `add_branch` silent failure caused a 30-minute debugging detour. I only discovered the problem when I did a full GET and found the fork branches were empty.

**Recommendation:** All POST handlers should reject unrecognized parameters. A response like `{"outcome": {"error": "Unknown parameter 'target'. Expected one of: merge"}}` would have immediately surfaced my mistake. Alternatively, add a positive success indicator (e.g., `"outcome": {"status": "applied"}`) so that empty-outcome responses are unambiguous failures.

### 1.2 Affordance Noise on Focused Nodes

When a node is focused in the builder, the affordance list includes every possible editing operation: add field, edit field, remove field, add list, set table, set proceed, add navigation, add action, set show_all_fields, set pause, set execution, set node mode — plus structural affordances like select/edit/remove node, add option set, add column type, move node, go back, and proceed. That's 15-20 affordances even for a simple node.

Each field-related affordance also includes the full expression language documentation in its parameter descriptions — the same ~100-character syntax description repeated in `visible_when`, `side_effects`, `compute`, `gate`, and `when` parameters across multiple affordances.

**The problem isn't that the information is wrong — it's that the signal-to-noise ratio degrades.** An agent adding a simple text field must parse through table, list, execution, and column type affordances to find what it needs.

**Recommendations:**

- **Tiered affordance disclosure.** Group affordances by category (fields, structure, navigation, meta) and consider a `?detail=full` query parameter that expands parameter documentation. The default response would include affordance IDs, labels, methods, and URLs — enough for an agent that already knows the schema. The detailed response would include the full parameter specs. This cuts the per-response payload substantially without losing information.

- **Suppress irrelevant affordances.** If a node already has a proceed gate, the "set table" and "add list" affordances are rarely needed simultaneously. Consider context-aware suppression — or at minimum, order affordances by likely relevance (fields first, then proceed/navigation, then structural operations, then meta).

- **Factor out the expression language.** Instead of repeating the expression syntax in every parameter description, include it once at the top level of the response (e.g., `"expression_syntax": {...}`) and reference it from parameters. This alone would cut significant payload size.

### 1.3 Content Negotiation Default

The `/agent` portal and `/agent/{wf}/{id}` endpoints default to HTML. An agent must send `Accept: application/json` to get the machine-readable payload. For endpoints under `/agent/`, JSON should arguably be the default — the URL prefix implies programmatic access. An agent that doesn't know about content negotiation will get HTML and have to parse it or fail.

**Recommendation:** Either default to JSON on `/agent/` routes, or return a `406 Not Acceptable` with a hint when no Accept header is present, rather than silently serving HTML.

### 1.4 Parameter Naming Intuitiveness

The affordance body templates are the authoritative schema, and they're always correct. But the parameter names sometimes diverge from what a domain-knowledgeable agent would guess:

| Intuitive guess | Actual parameter | Affordance |
|-----------------|------------------|------------|
| `target` | `merge` | `set_fork_merge` |
| `name` | `branch_id` | `add_branch` |
| `target` (single node) | `nodes` (array) | `add_branch` |

These are defensible naming choices. But when combined with silent failures (1.1), the divergence becomes costly. An agent that guesses instead of reading the body template gets no feedback that it guessed wrong.

**Recommendation:** This is low priority if silent failures are fixed. With proper error messages, the agent would immediately learn the correct parameter names. As a secondary measure, consider accepting common aliases (e.g., `target` as an alias for `merge` in `set_fork_merge`).

### 1.5 Fork Activation Speed Bump

The fork node (`parallel_review`) presented a single "Continue" affordance with no fields. The agent's only action was to click proceed to activate the fork. Since there's no gate, no fields, and no decision to make, this step adds a round-trip without adding value.

**Recommendation:** If a fork node has no gate and no fields, auto-activate it (like routers auto-advance). If a gate exists, pause for evaluation. This would make forks consistent with the router pattern: automation nodes that don't require agent interaction should be transparent.

### 1.6 No Explicit Validation Output on Preview

The preview node's instructions say "Validation checks run automatically" and list what's checked (field keys in gates, node IDs in targets, duplicate keys, etc.). But the state doesn't include a validation results section. The agent can only infer pass/fail from the presence or absence of the Publish affordance.

**Recommendation:** Include a `"validation": {"status": "pass", "checks": [...]}` section in the preview state, or `{"status": "fail", "errors": [...]}` when validation fails. This lets the agent understand what was validated and gives it actionable error messages if something is wrong.

---

## 2. Runtime Execution Bugs

### 2.1 Computed Field Evaluates Incorrectly

**Severity: High** — Computed fields are a core feature for workflow logic.

**Expected:** The computed field "All Reviews Acceptable" should evaluate to `true` when:
- `tech_assessment` is "Acceptable" OR "Acceptable with comments" — **actual value: "Acceptable with comments" (should match)**
- AND `regulatory_alignment` is "Fully aligned" OR "Minor gaps identified" OR "Not applicable" — **actual value: "Minor gaps identified" (should match)**

**Actual:** The field evaluates to `false`, and `instruction_when_false` is displayed ("One or more reviews flagged issues").

**Expression as authored:**
```yaml
compute:
  op: AND
  conditions:
    - op: OR
      conditions:
        - type: field_equals
          key: tech_assessment
          value: Acceptable
        - type: field_equals
          key: tech_assessment
          value: Acceptable with comments
    - op: OR
      conditions:
        - type: field_equals
          key: regulatory_alignment
          value: Fully aligned
        - type: field_equals
          key: regulatory_alignment
          value: Minor gaps identified
        - type: field_equals
          key: regulatory_alignment
          value: Not applicable
```

**Hypothesis:** The evaluator may have a bug in how it resolves field keys when the compute expression is on a different node than where the field was defined. Both `tech_assessment` and `regulatory_alignment` are defined on `technical_review` and `compliance_review` respectively, but the computed field is on `review_merge`. If the evaluator only looks at the current node's field state rather than the global state, all `field_equals` checks would return false.

### 2.2 Conditional Field Visibility Not Working

**Severity: High** — Conditional visibility is a core feature for dynamic forms.

**Expected:** After setting `approval_decision` to "Approved with conditions", the field `approval_conditions` (with `visible_when: {type: field_equals, key: approval_decision, value: "Approved with conditions"}`) should appear as an affordance.

**Actual:** The field never appears. Neither does `rejection_reason` (which has an OR condition on the two rejection options). Neither conditional field is present in affordances or in `state.fields`.

**Context:** This was on the `approval` node with `show_all_fields: true`. The conditional fields are defined on the same node where `approval_decision` lives.

**Hypothesis:** Either `visible_when` evaluation isn't running at all during affordance generation, or `show_all_fields` mode has a separate code path that doesn't invoke visibility checks. The fields may be omitted entirely rather than evaluated and hidden.

### 2.3 Field Value Lost During Branch Transition

**Severity: Medium** — Data loss during normal workflow operation.

**Observed twice:**

1. **`impact_analysis`** — Set on the `technical_review` branch, then switched to `compliance` branch, filled compliance, submitted compliance (which auto-switched back to technical). Value was null. Had to re-enter.

2. **`compliance_findings`** — Set on the `compliance_review` branch, then submitted the compliance review (proceed). Value was null at the `review_merge` node. Other compliance fields (`compliance_reviewer`, `regulatory_alignment`, `policy_references`) persisted.

**Pattern:** Both lost fields were optional (not in the proceed gate's `requires` list). Fields that *were* in the gate persisted. This suggests the proceed handler may only carry forward gate-required field values, discarding others. However, `tech_comments` (also optional) persisted, so the pattern isn't perfectly consistent — it may be timing-dependent or related to the branch switch mechanism specifically.
