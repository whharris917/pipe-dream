# Formalization Analysis: Simplification Opportunities

## Summary

The formal model reveals that the QMS CLI is fundamentally simple—it's the repeated application of three primitives:

1. **Authorization check** (group ∧ owner ∧ assignment)
2. **Transition validation** (is edge in graph?)
3. **State transformation + audit log**

However, comparing the formal model to the actual code and RS reveals some structural observations.

---

## Code Observations

### 1. Dual Transition Tables (Redundancy)

The code has **two** representations of valid transitions:

**qms_config.py:47** - Simple adjacency list:
```python
TRANSITIONS = {
    Status.DRAFT: [Status.IN_REVIEW, Status.IN_PRE_REVIEW, Status.IN_POST_REVIEW],
    Status.IN_REVIEW: [Status.REVIEWED],
    ...
}
```

**workflow.py:95** - Rich transition definitions:
```python
WORKFLOW_TRANSITIONS: List[StatusTransition] = [
    StatusTransition(
        from_status=Status.DRAFT,
        to_status=Status.IN_REVIEW,
        action=Action.ROUTE_REVIEW,
        workflow_type=WorkflowType.REVIEW,
        ...
    ),
    ...
]
```

These encode the **same edges** in two places. If they diverge, bugs result.

**Simplification opportunity:** Derive `TRANSITIONS` from `WORKFLOW_TRANSITIONS`:
```python
TRANSITIONS = {
    t.from_status: [t.to_status for t in WORKFLOW_TRANSITIONS if t.from_status == s]
    for s in Status
}
```

### 2. Hardcoded Status Mappings

Functions like `get_workflow_type_for_status` have explicit if/elif chains:
```python
if status == Status.IN_REVIEW:
    return WorkflowType.REVIEW
elif status == Status.IN_APPROVAL:
    return WorkflowType.APPROVAL
...
```

This could be derived from the transition table, eliminating another source of potential divergence.

---

## RS Observations

### 1. Requirements as Transition Instances

The formal model shows that REQ-WF-002 through REQ-WF-013 are all instances of:
```
δ(from_status, trigger) = to_status
```

Currently, each transition has its own requirement:
- REQ-WF-002: Non-executable lifecycle
- REQ-WF-003: Executable lifecycle
- REQ-WF-008: Release transition
- REQ-WF-009: Revert transition
- etc.

### 2. Requirements as Authorization Instances

Similarly, REQ-SEC-002 through REQ-SEC-005 are all instances of:
```
authorized(user, action, doc) = inGroup ∧ isOwner ∧ isAssigned
```

---

## Simplification Assessment

### Should we consolidate RS requirements?

**Arguments for consolidation:**
- Reduces redundancy
- Aligns RS with the formal model's simplicity
- Changes to transition rules require updating one place

**Arguments against consolidation:**
- Current structure enables explicit test traceability (RTM maps requirements to test lines)
- Human readers can understand individual requirements without parsing a table
- Regulatory/compliance contexts often expect enumerated requirements

**Recommendation:** Keep the current RS structure. The explicit enumeration serves traceability and readability purposes, even though it's formally redundant.

### Should we consolidate code?

**Arguments for consolidation:**
- Eliminates dual maintenance of TRANSITIONS and WORKFLOW_TRANSITIONS
- Reduces risk of divergence bugs
- Aligns code with the formal model

**Arguments against consolidation:**
- TRANSITIONS is a quick O(1) lookup; deriving it adds overhead
- Code already works and is tested
- Change introduces risk for limited benefit

**Recommendation:** This is a minor simplification opportunity, but not urgent. If a future CR touches the workflow engine, consider consolidating then.

---

## Invariants Not in RS

The formal model identified these invariants that are **implicit** in the code but not stated in the RS:

| Invariant | Description | Currently in RS? |
|-----------|-------------|------------------|
| INV-1 | checked_out ⟹ responsible_user ≠ null | No (implicit in REQ-DOC-007) |
| INV-2 | status = EFFECTIVE ⟹ responsible_user = null | No (implicit in REQ-WF-006) |
| INV-3 | Audit trail is append-only | Yes (REQ-AUDIT-001) |
| INV-4 | Version format N.X | Yes (REQ-DOC-006) |
| INV-5 | Transitions follow δ | Yes (REQ-WF-001) |
| INV-6 | Task ⟺ pending_assignees sync | No (implicit in REQ-TASK-001, REQ-TASK-004) |

**Recommendation:** Consider adding explicit invariant requirements (REQ-INV-*) to the RS. This would make the constraints explicit and testable.

---

## Conclusion

The formalization confirms that the QMS CLI is well-structured. The apparent complexity (64 requirements, 20+ commands) reduces to a small set of primitives applied repeatedly.

**Simplifications worth considering:**
1. *(Optional, Low Priority)* Derive `TRANSITIONS` from `WORKFLOW_TRANSITIONS` in code
2. *(Optional)* Add explicit invariant requirements to RS

**Simplifications NOT recommended:**
1. Collapsing RS requirements into table references (loses traceability)
2. Major code refactoring (working system, tested, low benefit)

The current structure is acceptable. The formal model serves as documentation and mental model, not as a mandate for code restructuring.
