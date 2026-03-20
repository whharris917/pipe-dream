# External State Provider Framework

## Context

The workflow engine needs to reference arbitrary external state and present it through the same affordance mechanism that native primitives use. This requires two things:

1. **Affordance generation must become recursive and delegated.** The current `_build_affordances()` is a 7-step monolith where the renderer centrally knows about every primitive type. Each new capability means adding step N+1. This is fragile and doesn't scale.

2. **External state providers must be pluggable.** Providers conform to the engine's affordance structure — the engine defines the contract, providers adapt to it.

These are not separate changes. The AffordanceSource protocol is the foundation; providers are the first external source type that proves the design.

---

## Decisions

| Question | Decision |
|----------|----------|
| Refresh | Always fresh (query on every render). Add caching later if needed. |
| Provider-to-workflow side effects | No. Providers cannot set workflow fields. The workflow owns its state. |
| Provider declaration scope | Workflow-level (alongside `option_sets`, `column_types`). Nodes opt into `expose`/`affordances`. |
| Provider discovery | Python-only registration at startup. HTTP adapter is a natural future extension. |

---

## Part 1: AffordanceSource Protocol

### The Principle

Every element that can produce affordances implements a common protocol. A node delegates to its children. Each child answers "What is possible?" for itself. Composites delegate recursively.

### The Protocol

```python
class AffordanceContext:
    """Immutable context passed through the affordance tree."""
    data: dict            # workflow state
    defn: WorkflowDef     # workflow definition
    api_base: str         # e.g. "/agent/create-cr"

class AffordanceSource(Protocol):
    def get_affordances(self, ctx: AffordanceContext) -> list[dict]:
        """Return affordances available right now. Empty list = nothing available."""
        ...
```

Affordances returned by sources do NOT include `id` — the node assigns sequential IDs after collecting from all sources. This decouples sources from ordering.

### Source Implementations

Each existing primitive becomes an AffordanceSource:

| Source | Wraps | Current Location |
|--------|-------|-----------------|
| `FieldSource` | A single `FieldDef` | Lines 372-403 of `_build_affordances` |
| `ListSource` | A single `ListDef` | `_build_list_affordances()` |
| `NavigationSource` | A single `NavigationDef` | Lines 409-427 |
| `ProceedSource` | A `ProceedDef` | Lines 447-466 |
| `ForkSource` | A `ForkDef` + fork state | Lines 429-445, 468-488 |
| `ActionSource` | A single `ActionDef` | Lines 490-500 |
| `TableSource` | A `TableDef` + table data | `_build_table_affordances()` |
| `ExecutionSource` | Execution engine state | `_build_execution_affordances()` |
| `ProviderSource` | An external provider | NEW |

### How the Node Collects

```python
def get_node_affordances(ctx: AffordanceContext, node: NodeDef) -> list[dict]:
    """Collect affordances from all sources on this node."""
    sources = []

    # Content sources (fields, lists)
    for fdef in ctx.defn.node_fields(node.id).values():
        sources.append(FieldSource(fdef))
    for list_def in node.lists.values():
        sources.append(ListSource(list_def))

    # Navigation sources
    for nav in node.navigation:
        sources.append(NavigationSource(nav))

    # Flow control (mutually exclusive)
    if node.fork:
        sources.append(ForkSource(node.fork))
    elif node.proceed:
        sources.append(ProceedSource(node.proceed))

    # Fork branch switching (if currently in a fork)
    fork_state = ctx.data.get("fork_state")
    if fork_state:
        sources.append(BranchSwitchSource(fork_state, ctx.defn))

    # Terminal actions
    for act in node.actions:
        sources.append(ActionSource(act))

    # Table (composite — delegates to structural or execution internally)
    if node.table or node.execution:
        sources.append(TableSource(node, ctx.defn))

    # External providers
    for pid, pnode_def in (node.provider_nodes or {}).items():
        if pnode_def.affordances:
            sources.append(ProviderSource(pid, ctx.defn))

    # Collect and number
    raw = []
    for source in sources:
        raw.extend(source.get_affordances(ctx))

    # Assign sequential IDs
    for i, aff in enumerate(raw, 1):
        aff["id"] = i

    return raw
```

The node doesn't know what any source does. It just asks and collects. Adding a new primitive means adding a new `Source` class — the node's collection logic doesn't change.

### Composite Delegation

`TableSource` is itself a composite:

```python
class TableSource:
    def get_affordances(self, ctx):
        if self.node.execution and ctx.data.get("execution"):
            return ExecutionSource(ctx.data).get_affordances(ctx)
        elif self.node.table:
            return TableStructuralSource(self.node, ctx.defn).get_affordances(ctx)
        return []
```

`ExecutionSource` delegates to the PlanEngine:

```python
class ExecutionSource:
    def get_affordances(self, ctx):
        engine = _load_engine(ctx.data)
        ps = engine.get_plan_state()
        affs = []
        for act in ps.next_actions:
            affs.append(self._cell_action_affordance(act, ctx.api_base))
        if ps.status == "completed":
            affs.append({"label": "Complete Execution", ...})
        return affs
```

This is recursive delegation. Each layer answers for itself.

---

## Part 2: Provider Protocol

### Provider Interface

```python
class ExternalStateProvider(Protocol):
    provider_id: str

    def query(self, bindings: dict[str, Any]) -> dict[str, Any]:
        """Fetch current state. Returns flat key-value dict.
        Raises ProviderUnavailableError on failure."""
        ...

    def get_affordances(self, bindings: dict[str, Any], state: dict[str, Any],
                        api_base: str) -> list[dict]:
        """Return affordances in the engine's standard format (no id needed)."""
        ...

    def execute(self, bindings: dict[str, Any], action: str,
                params: dict[str, Any]) -> dict[str, Any]:
        """Execute a write action. Returns {"ok": True} or {"ok": False, "error": "..."}."""
        ...

    def evaluate(self, bindings: dict[str, Any], state: dict[str, Any],
                 condition: dict) -> tuple[bool, str]:
        """Evaluate a provider-specific condition. Returns (passed, reason)."""
        ...
```

Note: `get_affordances` (not `affordances`) — consistent with AffordanceSource. No `start_id` parameter since the node handles ID assignment.

### ProviderSource (the AffordanceSource adapter)

```python
class ProviderSource:
    """Adapts an ExternalStateProvider into an AffordanceSource."""

    def __init__(self, provider_id: str, defn: WorkflowDef):
        self.provider_id = provider_id
        self.defn = defn

    def get_affordances(self, ctx: AffordanceContext) -> list[dict]:
        provider = registry.get(self.provider_id)
        if not provider:
            return []
        pdef = self.defn.providers.get(self.provider_id)
        if not pdef:
            return []
        bindings = resolve_bindings(pdef.bindings, ctx.data)
        cached = ctx.data.get(f"_provider_cache_{self.provider_id}")
        if cached is None:
            return []  # provider unavailable
        return provider.get_affordances(bindings, cached, ctx.api_base)
```

Providers are just another source. No special casing in the node collector.

### Registry

```python
class ProviderRegistry:
    def register(self, provider: ExternalStateProvider): ...
    def get(self, provider_id: str) -> ExternalStateProvider | None: ...

registry = ProviderRegistry()  # module-level singleton
```

---

## YAML Schema

### Workflow-Level Provider Declaration

```yaml
workflow_title: Execute Change Record

providers:
  qms:
    bindings:
      doc_id: $cr_id
      user: claude

nodes:
  gather:
    title: Gather Information
    fields:
      cr_id: {label: CR ID, type: text, key: cr_id}
    proceed:
      label: Continue
      gate: {type: field_truthy, key: cr_id}

  review_gate:
    title: Review Gate
    instruction: "The CR must be under review before proceeding."
    provider_nodes:
      qms:
        expose:
          - key: status
            label: Document Status
          - key: current_owner
            label: Current Owner
        affordances: true
    proceed:
      label: Proceed
      gate:
        type: provider_state
        provider: qms
        condition: {type: status_equals, value: Under Review}
```

### Schema Additions

**WorkflowDef** gets `providers: dict[str, ProviderDef]`:
```python
@dataclass
class ProviderDef:
    provider_id: str
    bindings: dict[str, str]  # param → literal or $field_ref
```

**NodeDef** gets `provider_nodes: dict[str, ProviderNodeDef]`:
```python
@dataclass
class ProviderExposeDef:
    key: str
    label: str
    instruction: str | None = None

@dataclass
class ProviderNodeDef:
    provider_id: str
    expose: list[ProviderExposeDef]
    affordances: bool = False
```

---

## How It Flows

### Read Path

1. **Before rendering** (in `WorkflowRuntime.render_node`): query all workflow-level providers, populate `_provider_cache_{pid}` in data
2. `render_page()` checks current node's `provider_nodes` for `expose` entries → adds read-only fields to `state["fields"]`
3. Provider raw state available in `state["providers"]` for renderers

### Write Path

1. `ProviderSource.get_affordances()` returns actions with URLs: `/agent/{wf}/ext.{pid}.{action}`
2. Flask `/<resource>` captures `ext.qms.route_review` (dot-separated, no Flask changes)
3. `resolve_resource()` matches `ext.*` → `{action: "provider_action", provider: pid, provider_action: action_name}`
4. `dispatch()` routes to `_provider_action()` → calls `provider.execute()` → invalidates cache
5. No workflow state mutation — provider returns `{ok: True/False}`

### Evaluate Path

1. Gates use `{type: provider_state, provider: qms, condition: {...}}`
2. `evaluator.py` reads `_provider_cache_{pid}`, delegates to `provider.evaluate()`
3. Fail-closed: returns `False` when provider unavailable

### Error Handling

| Failure | Behavior |
|---------|----------|
| Query fails | Cache = `None`. Fields show unavailability. Affordances suppressed. Gates block. |
| Action fails | `{"error": ...}` return. |
| Provider not registered | Skipped at render. Error on action dispatch. |
| Missing binding field | Resolves to `None`. Provider decides. |

---

## Files to Change

### Phase 1: AffordanceSource Protocol

| File | Change |
|------|--------|
| **NEW** `engine/runtime/affordances.py` | `AffordanceContext`, `AffordanceSource` protocol, `get_node_affordances()` collector, all source implementations: `FieldSource`, `ListSource`, `NavigationSource`, `ProceedSource`, `ForkSource`, `BranchSwitchSource`, `ActionSource`, `TableStructuralSource`, `ExecutionSource` |
| `engine/runtime/renderer.py` | Replace `_build_affordances()` + `_build_list_affordances()` + `_build_table_affordances()` + `_build_execution_affordances()` with call to `get_node_affordances()`. Keep `_resolve_options()` and `_load_engine()` as utilities imported by the source implementations. |

### Phase 2: Provider Framework

| File | Change |
|------|--------|
| **NEW** `engine/runtime/providers.py` | `ExternalStateProvider` protocol, `ProviderRegistry`, `ProviderUnavailableError`, `resolve_bindings()` |
| `engine/runtime/affordances.py` | Add `ProviderSource` class |
| `engine/runtime/schema.py` | `ProviderDef`, `ProviderExposeDef`, `ProviderNodeDef`; extend `WorkflowDef` and `NodeDef` |
| `engine/runtime/evaluator.py` | `provider_state` expression leaf |
| `engine/runtime/renderer.py` | Provider state querying (before render), expose fields, `state["providers"]`, gate labels |
| `engine/runtime/actions.py` | `provider_action` dispatch path |
| `engine/runtime/__init__.py` | `ext.` resource resolution |
| `app/app.py` | Strip `_provider_cache_*` from save |

## Implementation Order

1. **`affordances.py`** — AffordanceContext, protocol, all 9 source implementations extracted from renderer
2. **`renderer.py`** — Replace monolithic `_build_affordances()` with `get_node_affordances()` call
3. **Verify** — Run server, confirm all existing workflows produce identical affordances
4. **`providers.py`** — Provider protocol, registry, binding resolution
5. **`schema.py`** — Provider dataclasses, WorkflowDef/NodeDef extensions
6. **`affordances.py`** — Add `ProviderSource`
7. **`evaluator.py`** — `provider_state` expression leaf
8. **`renderer.py`** — Provider query step (before render), expose, state["providers"]
9. **`actions.py`** — `provider_action` dispatch
10. **`__init__.py`** — `ext.` resource resolution
11. **`app.py`** — Persistence safety
12. **Test provider + workflow** — Verify end-to-end

## Verification

### After Phase 1 (AffordanceSource refactoring)
- Run `python run.py`
- Open each workflow type in the observer: Create CR, Create Executable Table, Create Workflow, custom workflows
- Verify affordances are identical to before the refactoring (same labels, same URLs, same parameters)
- Interact with each workflow: set fields, proceed, navigate, table operations — confirm nothing is broken

### After Phase 2 (Provider framework)
- In-memory counter test provider:
  - `query()` returns `{"counter": N}`
  - `get_affordances()` returns "Increment Counter"
  - `execute("increment")` bumps counter
  - `evaluate({"type": "counter_above", "value": 5})` checks threshold
- Test workflow YAML exercising all paths:
  - Workflow-level: declares counter provider
  - Field node: agent enters a name
  - Provider node: counter exposed as read-only via `provider_nodes`, increment affordance
  - Proceed gate: `provider_state` blocks until counter > 5
- Verify state file has no `_provider_cache_*` keys
