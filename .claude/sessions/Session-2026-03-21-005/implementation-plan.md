# Plan: Resolve All Agent API Evaluation Findings

## Context

Session-2026-03-21-005 performed an end-to-end agent-friendliness evaluation of the workflow engine. A 10-node "Document Review and Approval" workflow was built via the Create Workflow builder using only curl, then executed through the Major severity fork/merge path. The evaluation identified 3 runtime bugs and 6 improvement suggestions. This plan resolves all of them.

All changes are in the `qms-workflow-engine/` submodule.

---

## Phase 1: Evaluator Unification (Bugs 2.1 + 2.2)

Both bugs share the same root cause: two code paths bypass the canonical `evaluate()` function with incomplete reimplementations.

### 1a. Fix `check_visibility()` — `evaluator.py:130-144`

`check_visibility()` only handles legacy `{key: value}` format. When it receives a modern expression tree like `{type: field_equals, key: approval_decision, value: "Approved with conditions"}`, it iterates the dict keys `type`, `key`, `value` as field name lookups — all fail, returning False.

**Change:** After the `if not visible_when: return True` guard, add expression tree detection:
```python
if "type" in visible_when or "op" in visible_when:
    passed, _ = evaluate(visible_when, data)
    return passed
```
The existing legacy loop remains as fallback. Three lines added, zero existing behavior changed.

### 1b. Fix `_evaluate_computed()` — `renderer.py:343-356`

`_evaluate_computed()` only handles `set_membership` leaves and returns `False` for all other expression types (AND/OR composites, field_equals, etc.).

**Change:** Replace the function body to delegate to `evaluate()`:
```python
def _evaluate_computed(defn: WorkflowDef, fdef: FieldDef, data: dict) -> bool:
    compute = fdef.compute
    if not compute:
        return False
    # Inject option sets for set_membership support
    for name, values in defn.option_sets.items():
        data[f"__option_set_{name}"] = set(values)
    passed, _ = evaluate(compute, data)
    return passed
```
Add `evaluate` to the import from `.evaluator`. The option set injection uses the same `__option_set_*` convention that `evaluate()`'s `set_membership` handler expects.

---

## Phase 2: Field Value Persistence Investigation (Bug 2.3)

Code analysis shows field values live in a single global `data` dict, persisted via straightforward JSON serialization in `_wf_save_state()`. No filtering or clearing occurs during branch switches (`_switch_branch()` only updates `active_branch` and `node`). The `_wf_save_state` strips only `_provider_*` transient keys.

**Likely explanation:** The observed "data loss" may have been a rendering artifact — fields are only shown when the current node defines them or `show_all_fields` is true. Or it may have been a curl-side observation error (similar to the "silent failure" misattribution).

**Action:** After implementing Phase 1 fixes, re-execute the fork/merge path and verify whether field values actually persist. If the issue reproduces, add logging in `_wf_save_state`/`_wf_load_state` to trace the exact point of loss. If it doesn't reproduce, document the finding and close.

---

## Phase 3: Content Negotiation Default — `app.py`

Currently `/agent/` GET routes return HTML unless `Accept: application/json` is explicitly set. Agents that don't know about content negotiation get HTML.

**Change:** Add a helper:
```python
def _wants_json() -> bool:
    best = request.accept_mimetypes.best
    return best in ("application/json", None, "*/*", "")
```
Replace `request.accept_mimetypes.best == "application/json"` with `_wants_json()` in:
- `agent_portal()` (~line 709)
- `agent_workflow_get()` (~line 852)

POST routes already return JSON unconditionally — no change needed. Browsers send `text/html` explicitly and will continue to get HTML.

---

## Phase 4: Unrecognized Parameter Detection — `builder.py`, `actions.py`

Error messages exist but describe default-value validation failures rather than identifying the real problem (wrong parameter names).

### 4a. Shared validation helper — `engine/runtime/actions.py`

```python
def _validate_params(body: dict, expected: set[str]) -> dict | None:
    extra = set(body.keys()) - expected - {"action"}
    if extra:
        action = body.get("action", "?")
        return {"error": f"Unknown parameter(s) for '{action}': {', '.join(sorted(extra))}. "
                         f"Expected: {', '.join(sorted(expected))}"}
    return None
```

### 4b. Builder parameter whitelist — `builder.py`

Add a module-level dict mapping each of the 44 actions to its expected parameter set:
```python
_BUILDER_EXPECTED_PARAMS = {
    "set_workflow_id": {"value"},
    "set_workflow_title": {"value"},
    "set_workflow_description": {"value"},
    "add_node": {"id", "title", "instruction"},
    "select_node": {"index"},
    "edit_node": {"index", "title", "instruction"},
    "remove_node": {"index"},
    "reorder_node": {"index", "direction"},
    "add_field": {"key", "label", "type", "instruction", "options", "options_from",
                  "default", "visible_when", "side_effects", "dynamic_options",
                  "compute", "instruction_when_true", "instruction_when_false",
                  "annotate_from"},
    "add_branch": {"branch_id", "label", "nodes"},
    "set_fork_merge": {"merge"},
    "set_fork_label": {"label"},
    "set_fork_gate": {"gate", "requires"},
    "add_route": {"target", "when"},
    "remove_route": {"route_index"},
    "set_proceed": {"label", "requires", "gate", "target"},
    # ... remaining actions
}
```

At the top of `process_action()`, after extracting `action`:
```python
expected = _BUILDER_EXPECTED_PARAMS.get(action)
if expected is not None:
    err = _validate_params(body, expected)
    if err:
        return err
```

### 4c. Runtime parameter whitelist — `actions.py`

Same pattern for runtime actions. The runtime has fewer actions (~10 vs 44), so the dict is smaller. For `set_field`, the expected params are `{"field", "value"}`. For `switch_branch`, `{"branch"}`. Etc.

---

## Phase 5: Fork Auto-Activation — `actions.py:182-220`

The fork node has no fields and no decision to make — the "Continue" button is a speed bump. Routers auto-advance; forks should too (when gateless and pauseless).

**Change in `_enter_node()`:** After the router check (line 198) and before the pause check (line 201), add:

```python
# Fork auto-activation: if pause=False (or not set to True explicitly)
# and no gate (or gate passes), auto-activate
if dest_node.fork and not dest_node.pause:
    fork_gate = dest_node.fork.gate
    if fork_gate:
        passed, _ = evaluate(fork_gate, data)
        if not passed:
            return render_page(defn, data, workflow_id)
    return _activate_fork(defn, data, workflow_id, dest_node)
```

**Builder change:** When `set_node_mode` switches a node to "fork", set `pause: false` as the default (currently defaults to true). This makes forks auto-activate by default, matching router behavior. Workflow authors can set `pause: true` if they want the speed bump.

---

## Phase 6: Explicit Validation Output — `builder.py`

The preview node stores `state["validation_errors"]` but this is a flat list without structure.

**Change in `render_node()` preview branch (~line 407):**
```python
elif node == "preview":
    errors = _validate(data)
    state["validation"] = {
        "status": "fail" if errors else "pass",
        "errors": errors,
        "checks": [
            "All field keys in proceed gates exist",
            "All node IDs in navigation/route targets exist",
            "No duplicate field keys across workflow",
            "At least one proceed gate or terminal action exists",
            "Router/fork structural integrity",
        ],
    }
```

Remove the old `state["validation_errors"]` key. The Human renderer should be updated to read `state.validation.errors` instead.

---

## Phase 7: Expression Syntax Factoring — `builder.py`

The `_EXPR_HINT` constant (~100 chars) is repeated in 8+ parameter descriptions per response.

**Change:** In `render_node()`, add to the returned dict:
```python
return {
    "state": state,
    "instructions": ...,
    "affordances": affordances,
    "expression_syntax": _EXPR_HINT,
}
```

In `_build_affordances()`, replace every instance of `+ _EXPR_HINT` in parameter descriptions with a short reference: `"(see expression_syntax)"`. This cuts ~800 bytes per response.

---

## Files Modified

| File | Phases | Changes |
|------|--------|---------|
| `engine/runtime/evaluator.py` | 1a | 3-line addition to `check_visibility()` |
| `engine/runtime/renderer.py` | 1b | Replace `_evaluate_computed()` body (~8 lines), add import |
| `app/app.py` | 3 | Add `_wants_json()` helper, replace 2 checks |
| `engine/runtime/actions.py` | 4a, 5 | Add `_validate_params()`, fork auto-activation in `_enter_node()` |
| `engine/builder.py` | 4b, 5, 6, 7 | Param whitelist dict, fork default pause, validation output, expr factoring |

---

## Verification

After implementation, re-run the exact curl sequence from the evaluation:

1. **Builder test:** Create a workflow with a fork. Send `add_branch` with wrong params (`{"name": "x"}`) — should get explicit error naming the unrecognized parameter.

2. **Computed field test:** Create a workflow with a computed field using AND/OR/field_equals. Execute it, set the referenced fields to matching values, advance to the computed field's node. Verify it evaluates to `true`.

3. **Visible_when test:** Create a workflow with a conditional field (`visible_when: {type: field_equals, ...}`). Execute it, set the trigger field, verify the conditional field appears in affordances.

4. **Content negotiation test:** `curl http://127.0.0.1:5000/agent` (no Accept header) should return JSON.

5. **Fork auto-activation test:** Create a workflow with a gateless fork node. Execute it, proceed through the preceding node, verify the fork auto-activates without requiring a manual "Continue".

6. **Field persistence test:** In a fork workflow, set optional fields on both branches, proceed through merge, verify all values are present at the merge node.

---

*Plan file: also saved to `.claude/sessions/Session-2026-03-21-005/implementation-plan.md`*
