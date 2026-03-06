# Prototype-2 Critical Analysis: Can This Be QMS DNA?

*Date: 2026-03-05, Session-2026-03-04-001*

This document captures a deep structural analysis of `qms-graph-prototype-2` against the real Pipe Dream QMS. The prototype was examined alongside the production interaction engine (`interact_engine.py`, `interact_source.py`, `interact_parser.py`, `interact_compiler.py`), all QMS templates (TEMPLATE-CR, TEMPLATE-VR, TEMPLATE-VAR), the governing SOPs (SOP-001, SOP-002, SOP-004), and real completed CRs.

---

## 1. What the Prototype Gets Right

### 1.1 Python Inheritance for Templates

This is the best idea in the prototype. The existing interaction engine uses HTML comment tags in markdown (`@prompt: id | next: id`, `@gate: id | type: yesno`). That works for flat, single-template documents like VRs but cannot express what the prototype expresses trivially: `ProcedureBase -> Diagnostic -> Incident -> SafetyIncident`, a 4-level inheritance chain where each level adds nodes and extension points while preserving the parent's structure. The existing system would require duplicating the entire template for each variant.

This solves the template-specialization problem that's been lurking in the design discussions around CR-106/CR-107.

### 1.2 Extension Points via `fill()`

ProcedureBase says "there's a procedure body here" and lets subclasses define it. Diagnostic fills it with observe/hypothesize/test and opens its own extension point (`post_diagnosis`). Incident fills post_diagnosis with contain/remediate. SafetyIncident calls `super().define_post_diagnosis()` and adds regulatory_report/lessons_learned. This is real composability -- not configuration, not parameterization, but structural composition through code.

### 1.3 Evidence Schemas

The real interaction engine captures plain text responses. The prototype validates typed fields at input time -- enum values are checked, required fields are enforced, unexpected fields are warned about. This catches errors *before* they're recorded, which is exactly what design principle P6 ("Errors are Structurally Impossible") calls for.

### 1.4 Deep Diff for Compliance

No existing mechanism compares a document against its template. The prototype's `diff()` detects prompt tampering, edge rewiring, schema changes, and structural additions/deletions. Directly useful for post-execution review: "did the document stay faithful to the approved template?"

### 1.5 The Acyclic Invariant

The real system's loop management (`interact_source.py` lines 100-148) is ~50 lines of loop state tracking: init, increment, close, reopen, iteration counters. The prototype replaces all of this with forward node spawning -- each iteration creates new unique nodes. The result: every step in the audit trail has a unique ID, the graph is always a DAG, and there's no complex loop state to manage.

---

## 2. What the Prototype Gets Wrong or Misses

### 2.1 No Amendment Mechanism (Critical)

The real interaction engine has `goto(prompt_id, reason)` -- navigate back to any previously-answered prompt, provide a new response (appended, not replaced), with a mandatory reason. The prototype has no way to amend a previous response. Once the cursor moves forward, the answer is final.

In a GMP-compliant system, amendments are essential. Auditors need to see "the original answer was X, it was amended to Y because Z."

**Resolution path:** Add an `amend(node_id, new_response, reason)` operation to the Ticket that doesn't change the cursor but appends to the response history for that node.

### 2.2 Responses Are Single-Value, Not Append-Only (Critical)

`ticket.responses[node_id] = response` overwrites. The real system stores `[{value, author, timestamp, reason, commit}, ...]` -- a list of entries per prompt. With the acyclic model, each node is visited only once, so overwrite doesn't lose traversal data. But once amendments are added (2.1), list storage becomes necessary.

The prototype's `history` list captures the sequence of all steps, which is good, but `responses` should also be append-only per node.

**Resolution path:** Change `ticket.responses[node_id]` from single dict to list of `{response, author, timestamp, reason?}` entries. `get_active_response()` returns the last entry's value.

### 2.3 No Compilation to Human-Readable Output (High)

The real system compiles `source + template -> markdown`. The prototype serializes to JSON. QMS documents need to be readable by humans -- reviewers, approvers, auditors. JSON with node IDs like `diagnostic.hypothesize-2` is machine-readable but not a controlled document.

**Resolution path:** Add a compilation layer. Template classes could define a `render()` method or companion Jinja2 template (connecting to the CR-107 work) that produces structured markdown from collected evidence.

### 2.4 No Child Document Mechanism (High)

The real QMS heavily uses child documents:
- CRs spawn VRs for evidence capture during execution
- Failed EIs spawn VARs for exception handling
- VARs can spawn their own VRs and even nested VARs

These child documents *block* the parent -- a CR can't close until its Type 1 VARs are closed. In the real QMS, roughly 30% of workflow complexity comes from child documents.

The prototype has no concept of inter-document dependencies or blocking relationships.

**Resolution path:** Node-level child document declarations (e.g., `children={"vr": {"template": "vr", "blocking": True}}`). Engine checks child document status as a gate condition before advancing past the parent node.

### 2.5 Hooks Declared But Never Executed (Medium)

Nodes have a `hooks: dict` field. The real system uses hooks for auto-commits (`commit: true` on evidence prompts pins project state at observation time, per ALCOA+ contemporaneousness). The prototype carries the field through serialization but never acts on it.

**Resolution path:** Define hook categories (per the earlier design work on hook boundaries) and execute them at the appropriate engine lifecycle points.

### 2.6 No Multi-Actor Enforcement (Medium)

Nodes have `performer: str` but the engine doesn't enforce it. The real QMS involves initiator, reviewer(s), approver(s), and executor. The existing system enforces this through the CLI (`--user` parameter) and metadata routing.

**Resolution path:** `do_respond()` accepts a `performer` argument and validates it against `node.performer`. This integrates with the CLI's `--user` parameter.

---

## 3. Things That Seem Wrong But Are Probably Right

### 3.1 Lifecycle Phases Managed Outside the Graph

The prototype has no concept of DRAFT -> PRE_APPROVED -> IN_EXECUTION -> CLOSED. This initially seems like a huge gap. But the graph engine handles *structured evidence capture within a phase*. The lifecycle transitions are managed by the CLI/metadata layer -- `qms route`, `qms checkout`, `qms checkin`. The graph is the *content* engine; the CLI is the *lifecycle* engine. This is probably the correct separation of concerns.

### 3.2 Graph Mutates During Execution

`spawn_retry` adds nodes and rewires edges at runtime. The serialized document differs from the template it was created from. This initially feels wrong -- shouldn't the document be a stable snapshot? But spawned nodes ARE the execution record. When the agent tested a hypothesis and it failed, that failure AND the retry are part of the document's evidence trail. The graph growing forward is the right behavior.

### 3.3 `eval()` for Conditions

Both gates and retry conditions use `eval()` with a restricted namespace. This works for a prototype where conditions are authored by the Lead in committed Python code. For production, a proper expression evaluator or actual Python functions (lambda or method references, not string expressions) would be safer. But this is a refinement, not a structural flaw.

---

## 4. Edge Cases and Minor Issues

### 4.1 No Retry Limit

Retry spawning can grow unboundedly. `max_steps` in `auto_run` prevents infinite test loops, but production should have a configurable per-retry limit.

### 4.2 Node Local IDs Must Not Contain Dots

`spawn_retry` uses `node.id.rsplit(".", 1)` to extract prefix and local name. A local ID containing a dot (e.g., `g.node("step.1", ...)`) would produce `prefix.step` / `1` instead of `prefix` / `step.1`. Current templates use hyphens (`test-repair`) so this doesn't trigger, but it's not validated.

### 4.3 `render_map` References "Loop Back"

Line 400 of `engine.py` prints `"^ loop back to {nid}"` when the walk function revisits a node. With the acyclic invariant, this would only trigger for diamond patterns (two paths converging on the same node), not loops. The message should say "^ (see above)" or similar.

### 4.4 SafetyIncident Start Node Missing Gate

SafetyIncident overrides the start node from Incident but doesn't carry forward the `gate="response.get('ready') == 'yes'"` condition. Its parent Incident and grandparent ProcedureBase both have this gate. The override silently drops it.

### 4.5 Diff After Spawn Shows Added Nodes

After retry spawning, `diff()` against the template reports spawned nodes (e.g., `hypothesize-2`, `test-2`) as "added." This is technically correct but could be confusing. The diff might benefit from distinguishing "author-added nodes" from "engine-spawned retry nodes."

---

## 5. Structural Mapping: Prototype vs Real QMS

| Real QMS Concept | Prototype Equivalent | Status |
|---|---|---|
| Template (TEMPLATE-CR, TEMPLATE-VR) | Python Template class with `define()` | Strong |
| Template specialization | Python class inheritance + `fill()` | Strong |
| Sequential prompts | Nodes with auto-linear edges | Strong |
| Evidence capture | `evidence_schema` with typed Field validation | Strong |
| Gate decisions (yes/no routing) | `gate` condition on nodes | Strong |
| Loops (VR verification steps) | `retry` with forward node spawning | Strong |
| Template compliance checking | `Graph.diff()` | Strong |
| Template locking (pre-approved content) | `locked: bool` on nodes, `instantiate()` / `freeze()` | Strong |
| Append-only responses | `ticket.responses[id] = value` (single-value) | Gap |
| Amendments with reason | Not implemented | Gap |
| Child documents (VR, VAR) | Not implemented | Gap |
| Auto-commit hooks | `hooks` field exists, no execution | Gap |
| Compilation to markdown | Not implemented | Gap |
| Performer enforcement | `performer` field exists, no enforcement | Gap |
| Lifecycle state machine | Not in scope (managed by CLI/metadata) | By design |
| Metadata tiers (content/state/audit) | Single JSON file | Prototype simplification |

---

## 6. Verdict

The prototype has the right **structural DNA**. The Template/Graph/Node/fill-point layer maps cleanly onto the real QMS hierarchy. Python inheritance for templates is genuinely superior to what exists. The acyclic invariant with forward spawning is cleaner than loop state tracking. Evidence schemas, deep diff, and gate conditions are direct improvements.

The **operational DNA** is incomplete. The prototype can traverse a graph and collect evidence. It cannot amend previously captured evidence, compile evidence into human-readable documents, spawn and track child documents, execute hooks on evidence capture, or enforce performer identity. These are structural requirements of a GMP-compliant QMS, not optional features.

The existing interaction engine (`interact_engine.py`, `interact_source.py`) already handles most of the operational requirements. The question is whether the prototype's structural improvements can be married to the operational capabilities that already exist.

### Recommended Integration Path

1. Replace `interact_parser.py`'s HTML comment tag parser with the Python template system
2. Adapt `interact_source.py`'s append-only response model into the Ticket
3. Bring `interact_engine.py`'s amendment/goto mechanism forward
4. Add `interact_compiler.py`'s markdown compilation as a rendering layer
5. Build child document spawning/blocking as an extension to the graph engine

The prototype is a valid foundation. The structural choices -- inheritance, fill points, acyclic DAG, evidence schemas, deep diff -- are sound and would be significantly harder to retrofit onto the existing system than to build on top of.
