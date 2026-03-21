# Sub-Workflow Embedding — Implementation Plan

## Context

Workflows should be composable: a node in one workflow can embed an entire other workflow as a sub-step. For example, "Create Change Record" could embed "Create Executable Table" at a specific node. When the agent reaches that node, it enters the sub-workflow, completes it, and returns to the parent — with explicit data flow in (bindings) and out (outputs).

**Design decisions (from Lead):**
1. **Isolated state** — sub-workflows get their own data dict
2. **Arbitrary nesting** — sub-workflows can contain sub-workflows (stack-based)
3. **URL schema change** — URLs clearly indicate sub-workflow context
4. **Banner replacement** — while inside a sub-workflow, banner + state dict show only the sub-workflow

## YAML Syntax

```yaml
nodes:
  build_table:
    title: Build Execution Table
    instruction: Configure the execution table for this CR.
    subworkflow:
      workflow: create-executable-table
      bindings:                          # parent field → sub-workflow field
        table_title: "$cr_title"         # $ref resolves from parent data
        sequential: "false"              # literal value
      outputs:                           # parent field ← sub-workflow field
        table: "table"
        execution: "execution"
      label: Configure Table             # affordance button text
      gate:                              # optional gate (evaluated against parent data)
        type: field_truthy
        key: cr_title
```

## State Model

Sub-workflow context is a **stack** in the parent's data dict:

```python
data["_subworkflow_stack"] = [
    {
        "workflow_id": "create-executable-table",
        "parent_node": "build_table",
        "data": { ... isolated sub-workflow state ... },
        "outputs": {"table": "table", "execution": "execution"},
    },
    # ... deeper nesting pushes more entries
]
```

When the stack is non-empty, **all rendering and dispatch operates on the top entry's data and defn**. The parent is invisible until the sub-workflow completes.

## Implementation Phases

### Phase 1: Schema (`engine/runtime/schema.py`)

Add `SubworkflowDef` dataclass after `ForkDef`:

```python
@dataclass
class SubworkflowDef:
    workflow: str
    bindings: dict[str, str]   # sub_field_key → "$parent_field" or literal
    outputs: dict[str, str]    # parent_field_key → sub_field_key
    label: str = "Continue"
    gate: dict | None = None
```

Add to `NodeDef`:
- Field: `subworkflow: SubworkflowDef | None = None` (mutually exclusive with proceed/router/fork)
- Parse in `NodeDef.from_dict()` after the fork block

### Phase 2: Workflow Resolver (`engine/runtime/__init__.py`)

Add `_resolver` attribute to `WorkflowRuntime`:

```python
def __init__(self, raw_definition, workflow_resolver=None):
    ...
    self._resolver = workflow_resolver
```

Thread resolver through `render_node()` and `process_action()` to their underlying calls:

```python
def render_node(self, data, workflow_id):
    return render_page(self.defn, data, workflow_id, resolver=self._resolver)

def process_action(self, data, workflow_id, body):
    return dispatch(self.defn, data, workflow_id, body, resolver=self._resolver)
```

Also add `"enter_subworkflow"` and `"exit_subworkflow"` to `VALID_RESOURCES`.

### Phase 3: Actions (`engine/runtime/actions.py`)

**Signature change:** Add optional `resolver=None` parameter to `dispatch()`.

**Sub-workflow delegation at top of `dispatch()`:**

```python
stack = data.get("_subworkflow_stack")
if stack:
    entry = stack[-1]
    sub_defn = resolver(entry["workflow_id"]) if resolver else None
    if not sub_defn:
        return {"error": f"Cannot resolve sub-workflow: {entry['workflow_id']}"}

    # "submit" inside sub-workflow → complete and return to parent
    if action == "submit":
        return _complete_subworkflow(defn, data, workflow_id, resolver)

    # "restart" inside sub-workflow → restart sub only
    if action == "restart":
        return _restart_subworkflow(data, sub_defn, workflow_id, resolver)

    # All other actions → recurse into sub-workflow's data
    result = dispatch(sub_defn, entry["data"], workflow_id, body, resolver)
    # After dispatch, re-render from root so the stack delegation picks up changes
    if "error" not in result:
        return render_page(defn, data, workflow_id, resolver)
    return result
```

**In `_proceed()`** — add subworkflow check between fork and standard proceed:

```python
if node and node.subworkflow:
    return _activate_subworkflow(defn, data, workflow_id, node, resolver)
```

**New functions:**

`_activate_subworkflow(defn, data, workflow_id, node, resolver)`:
1. Validate: resolver exists, sub-workflow ID resolves, no circular reference (walk stack for duplicate workflow_ids)
2. Load sub-workflow defn via `resolver(node.subworkflow.workflow)`
3. Build initial sub-data via `_build_default_data(sub_defn)`
4. Apply bindings: for each `sub_key → value`, if value starts with `$`, resolve from `data[value[1:]]`, else use literal
5. Mark parent node as completed
6. Push stack entry with sub-data, outputs mapping, workflow_id, parent_node
7. Return `render_page(defn, data, workflow_id, resolver)` (delegation renders the sub-workflow)

`_complete_subworkflow(defn, data, workflow_id, resolver)`:
1. Pop top stack entry
2. Apply outputs: for each `parent_key → sub_key`, copy `entry["data"][sub_key]` into data (or stack[-1]["data"] if still nested)
3. If stack is now empty → proceed past `entry["parent_node"]` in parent workflow
4. If stack still has entries → return to the parent sub-workflow (re-render)
5. Return `render_page(defn, data, workflow_id, resolver)`

`_restart_subworkflow(data, sub_defn, workflow_id, resolver)`:
1. Rebuild sub-data from `_build_default_data(sub_defn)`
2. Replace `stack[-1]["data"]` with fresh sub-data
3. Re-apply bindings from parent data
4. Return render

**`_go_back()` modification:**
- If stack is non-empty and at first node of sub-workflow → error "Already at first node of sub-workflow"
- Otherwise delegate to sub-workflow's go_back

### Phase 4: Renderer (`engine/runtime/renderer.py`)

**Signature change:** Add optional `resolver=None` parameter to `render_page()`.

**At top of `render_page()`:** If `_subworkflow_stack` is non-empty, delegate:

```python
stack = data.get("_subworkflow_stack")
if stack:
    entry = stack[-1]
    sub_defn = resolver(entry["workflow_id"]) if resolver else None
    if sub_defn:
        page = render_page(sub_defn, entry["data"], workflow_id, resolver)
        page["subworkflow_context"] = {
            "parent_workflow": workflow_id,
            "parent_node": entry["parent_node"],
            "depth": len(stack),
            "workflow_id": entry["workflow_id"],
        }
        return page
```

This means:
- `_build_lifecycle()` uses sub-workflow's defn → banner shows sub-workflow only
- Fields, affordances, definition all come from sub-workflow
- State dict presented to agent is the sub-workflow's isolated data

### Phase 5: Affordances (`engine/runtime/affordances.py`)

Add `SubworkflowSource` (analogous to `ForkSource`):

```python
class SubworkflowSource(AffordanceSource):
    def __init__(self, node, api_base):
        self._node = node
        self._api_base = api_base

    def get_affordances(self, ctx):
        sw = self._node.subworkflow
        return [{
            "label": sw.label,
            "method": "POST",
            "url": f"{ctx.api_base}/proceed",
            "body": {},
        }]
```

In `get_node_affordances()`: if node has `subworkflow` and gate passes, add `SubworkflowSource`. This reuses the "proceed" action (which `_proceed()` will intercept for subworkflow nodes).

**API base:** When rendering inside a sub-workflow, `api_base` changes:
- Normal: `/agent/{workflow_id}`
- Inside sub: `/agent/{workflow_id}/sub/{sub_wf_id}`
- Nested: `/agent/{workflow_id}/sub/{sub1}/sub/{sub2}`

Build the api_base from the stack in `render_page()` before passing to affordance context.

### Phase 6: URL Routing (`app/app.py`)

**New route:**

```python
@app.route("/agent/<workflow_id>/sub/<path:sub_path>", methods=["POST"])
def agent_subworkflow_post(workflow_id, sub_path):
    # Parse: sub_path = "create-executable-table/proceed"
    # or nested: "create-executable-table/sub/nested-wf/field_key"
    # Extract the resource (last segment after all sub/ prefixes)
    parts = sub_path.split("/")
    resource = parts[-1]  # Always the last segment

    # Validate: workflow must exist, state must have matching stack
    handler = _get_handler(workflow_id)
    # Use the ROOT handler's resolve_resource for field validation
    # But sub-workflow field keys aren't in the root handler's VALID_RESOURCES
    # → Need to resolve from the active sub-workflow's handler
    ...
```

**Key insight for resolve_resource:** When inside a sub-workflow, `resolve_resource()` must use the sub-workflow's field keys, not the parent's. The simplest approach:

In `WorkflowRuntime.resolve_resource()`, if the state has a sub-workflow stack, resolve against the active sub-workflow's defn instead. This requires passing state context to `resolve_resource()`.

**Alternative (simpler):** The sub-workflow route handler loads state, checks the stack, gets the sub-workflow's handler from the registry, and calls its `resolve_resource()`.

```python
@app.route("/agent/<workflow_id>/sub/<path:sub_path>", methods=["POST"])
def agent_subworkflow_post(workflow_id, sub_path):
    parts = sub_path.split("/")
    resource = parts[-1]
    body = request.get_json(silent=True) or {}

    # Load parent state, walk the stack to find active sub-workflow
    data = _wf_load_state(workflow_id)
    stack = data.get("_subworkflow_stack", [])
    if not stack:
        return jsonify({"error": "Not in a sub-workflow"}), 400

    # Get the active sub-workflow's handler for resource resolution
    active_wf_id = stack[-1]["workflow_id"]
    sub_handler = _get_handler(active_wf_id)
    if not sub_handler:
        return jsonify({"error": f"Unknown sub-workflow: {active_wf_id}"}), 404

    resolved = sub_handler.resolve_resource(resource, body)
    if resolved is None:
        return jsonify({"error": f"Unknown resource: {resource}"}), 404

    internal_body, acted_label = resolved
    # Execute through the parent handler — stack delegation handles the rest
    feedback, status = _execute_and_feedback(workflow_id, internal_body, acted_label=acted_label)
    return jsonify(feedback), status
```

### Phase 7: State Persistence (`app/app.py`)

Update `_wf_save_state()` to recursively strip `_provider_*` keys from sub-workflow data:

```python
def _strip_transient(d):
    clean = {k: v for k, v in d.items() if not k.startswith("_provider_")}
    if "_subworkflow_stack" in clean:
        for entry in clean["_subworkflow_stack"]:
            entry["data"] = _strip_transient(entry["data"])
    return clean
```

### Phase 8: Test Workflow

Create a test YAML (`data/custom_workflows/subworkflow-test.yaml`) that embeds `create-executable-table` as a sub-workflow to verify end-to-end.

## Files Modified

| File | Change |
|------|--------|
| `engine/runtime/schema.py` | Add `SubworkflowDef`, add field to `NodeDef` |
| `engine/runtime/__init__.py` | Add resolver to `WorkflowRuntime`, thread through methods |
| `engine/runtime/actions.py` | Stack delegation in `dispatch()`, `_activate_subworkflow()`, `_complete_subworkflow()`, modify `_proceed()`/`_go_back()`/`_restart()` |
| `engine/runtime/renderer.py` | Stack delegation in `render_page()`, api_base construction |
| `engine/runtime/affordances.py` | Add `SubworkflowSource`, handle subworkflow gate |
| `app/app.py` | Resolver injection, new `/sub/` route, recursive transient stripping |
| `data/custom_workflows/subworkflow-test.yaml` | Test workflow |

## Verification

1. Start the Flask server (`python -m app.app`)
2. Navigate to Agent Portal, select the sub-workflow test
3. Advance through parent nodes until reaching the sub-workflow node
4. Verify: affordance appears to enter sub-workflow (gated if configured)
5. Enter sub-workflow → verify banner shows only sub-workflow topology
6. Verify: all sub-workflow affordances use `/sub/` URL scheme
7. Complete sub-workflow → verify return to parent, outputs mapped correctly
8. Verify: parent banner resumes, parent state has sub-workflow outputs
9. Test restart inside sub-workflow (should restart sub only)
10. Test go_back at sub-workflow start (should error)
11. Test persistence: reload page mid-sub-workflow, verify state preserved
