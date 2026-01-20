# A3-WF: Workflow State Machine Domain Review

## Summary
- Total REQs reviewed: 13
- Accurate: 9
- Accurate with issues: 2
- Inaccurate: 2

## Requirement Analysis

### REQ-WF-001
**Status Transition Validation.** The CLI shall reject any status transition not defined in the workflow state machine. Invalid transitions shall produce an error without modifying document state.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `qms_config.py` lines 47-71: TRANSITIONS dict defines all valid transitions
- `workflow.py` lines 308-334: `WorkflowEngine.get_transition()` returns error when no matching transition found
- `workflow.py` lines 444-451: `validate_transition()` checks against TRANSITIONS dict
- `route.py` lines 108-117: Uses workflow engine and returns error on invalid transition

**Issues**: None
**Recommendation**: PASS

---

### REQ-WF-002
**Non-Executable Document Lifecycle.** Non-executable documents shall follow this status progression: DRAFT -> IN_REVIEW -> REVIEWED -> IN_APPROVAL -> APPROVED -> EFFECTIVE. SUPERSEDED and RETIRED are terminal states.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `qms_config.py` lines 51-56: TRANSITIONS dict defines exactly this progression:
  ```python
  Status.DRAFT: [Status.IN_REVIEW, Status.IN_PRE_REVIEW, Status.IN_POST_REVIEW],
  Status.IN_REVIEW: [Status.REVIEWED],
  Status.REVIEWED: [Status.IN_REVIEW, Status.IN_APPROVAL],
  Status.IN_APPROVAL: [Status.APPROVED, Status.REVIEWED],
  Status.APPROVED: [Status.EFFECTIVE],
  Status.EFFECTIVE: [Status.SUPERSEDED],
  ```
- `workflow.py` lines 98-104, 134-140, 162-169, 191-200: StatusTransition definitions for non-executable docs match this lifecycle

**Issues**: None
**Recommendation**: PASS

---

### REQ-WF-003
**Executable Document Lifecycle.** Executable documents (CR, INV, TP, ER, VAR) shall follow this status progression: DRAFT -> IN_PRE_REVIEW -> PRE_REVIEWED -> IN_PRE_APPROVAL -> PRE_APPROVED -> IN_EXECUTION -> IN_POST_REVIEW -> POST_REVIEWED -> IN_POST_APPROVAL -> POST_APPROVED -> CLOSED. RETIRED is a terminal state.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `qms_config.py` lines 59-70: TRANSITIONS dict defines this progression:
  ```python
  Status.IN_PRE_REVIEW: [Status.PRE_REVIEWED],
  Status.PRE_REVIEWED: [Status.IN_PRE_REVIEW, Status.IN_PRE_APPROVAL],
  Status.IN_PRE_APPROVAL: [Status.PRE_APPROVED, Status.PRE_REVIEWED],
  Status.PRE_APPROVED: [Status.IN_EXECUTION],
  Status.IN_EXECUTION: [Status.IN_POST_REVIEW],
  Status.IN_POST_REVIEW: [Status.POST_REVIEWED],
  Status.POST_REVIEWED: [Status.IN_POST_REVIEW, Status.IN_POST_APPROVAL, Status.IN_EXECUTION],
  Status.IN_POST_APPROVAL: [Status.POST_APPROVED, Status.POST_REVIEWED],
  Status.POST_APPROVED: [Status.CLOSED],
  ```
- `workflow.py` lines 106-130, 142-158, 171-187, 201-222, 253-279: StatusTransition definitions for executable docs

**Issues**: REQ does not mention CAPA as an executable type, though it is defined in qms_config.py line 82
**Recommendation**: REVISE - Add CAPA to the list of executable document types

---

### REQ-WF-004
**Review Completion Gate.** The CLI shall automatically transition a document from IN_REVIEW to REVIEWED (or equivalent pre/post states) only when all users in pending_assignees have submitted reviews.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `review.py` lines 133-144:
  ```python
  remaining_assignees = [u for u in pending_assignees if u != user]
  all_complete = len(remaining_assignees) == 0

  new_status = None
  if all_complete:
      # Transition to REVIEWED state using WorkflowEngine
      new_status = engine.get_reviewed_status(current_status)
  ```
- `workflow.py` lines 417-424: `get_reviewed_status()` maps IN_REVIEW -> REVIEWED, IN_PRE_REVIEW -> PRE_REVIEWED, IN_POST_REVIEW -> POST_REVIEWED

**Issues**: None
**Recommendation**: PASS

---

### REQ-WF-005
**Approval Gate.** The CLI shall block routing for approval if any reviewer submitted a review with `request-updates` outcome. All reviews must have `recommend` outcome before approval routing is permitted.

**Assessment**: INACCURATE
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `review.py` lines 63-66: Review outcomes are recorded as "RECOMMEND" or "UPDATES_REQUIRED"
- `review.py` line 131: Outcome is logged via `log_review()` to audit trail
- **MISSING**: `route.py` does NOT check review outcomes before allowing approval routing
- The test in `test_sop_lifecycle.py` lines 328-350 includes a note: "This test depends on whether the CLI implements this gate. If not implemented, this test will reveal the gap."
- `README.md` line 144 documents: "Approval Gate: Documents cannot be routed for approval unless all reviewers submitted --recommend"

**Issues**:
1. The approval gate check is **NOT IMPLEMENTED** in route.py
2. Review outcomes are logged to audit trail but not stored in .meta for runtime checking
3. The REQ matches the documented behavior but not the actual implementation

**Recommendation**: ADD_REQ or REVISE
- Either: Revise REQ to state this is NOT currently enforced (gap to close)
- Or: Add implementation requirement to track review outcomes in .meta and check in route command

---

### REQ-WF-006
**Approval Version Bump.** Upon successful approval (all approvers complete), the CLI shall: (1) increment the major version (N.X -> N+1.0), (2) archive the previous version, (3) transition to EFFECTIVE (non-executable) or PRE_APPROVED/POST_APPROVED (executable), and (4) clear the responsible_user.

**Assessment**: ACCURATE
**Completeness**: INCOMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `approve.py` lines 101-119:
  ```python
  if all_approved:
      new_status = engine.get_approved_status(current_status)
      if new_status:
          # Bump to major version
          major = int(str(current_version).split(".")[0])
          new_version = f"{major + 1}.0"

          # Archive current draft
          archive_path = get_archive_path(doc_id, current_version)
          archive_path.parent.mkdir(parents=True, exist_ok=True)
          shutil.copy(draft_path, archive_path)
  ```
- `approve.py` lines 152-166: For non-executable, transitions to EFFECTIVE and clears owner
- `approve.py` lines 167-170: For executable, stays at PRE_APPROVED/POST_APPROVED, owner NOT cleared

**Issues**:
1. REQ says "clear the responsible_user" but code only clears owner for EFFECTIVE/RETIRED, not for PRE_APPROVED/POST_APPROVED (line 169: `clear_owner=False`)
2. This is intentional behavior - executable docs keep owner during execution phase

**Recommendation**: REVISE - Clarify that responsible_user is cleared only for non-executable documents transitioning to EFFECTIVE, not for executable documents which retain ownership through execution

---

### REQ-WF-007
**Rejection Handling.** When any approver rejects a document, the CLI shall transition the document back to the most recent REVIEWED state (REVIEWED, PRE_REVIEWED, or POST_REVIEWED) without incrementing the version.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `reject.py` lines 98-104:
  ```python
  # Transition back to REVIEWED state using WorkflowEngine
  new_status = engine.get_rejection_target(current_status)
  if new_status:
      print(f"Document rejected. Status: {current_status.value} -> {new_status.value}")
  ```
- `workflow.py` lines 435-442:
  ```python
  def get_rejection_target(self, current_status: Status) -> Optional[Status]:
      status_map = {
          Status.IN_APPROVAL: Status.REVIEWED,
          Status.IN_PRE_APPROVAL: Status.PRE_REVIEWED,
          Status.IN_POST_APPROVAL: Status.POST_REVIEWED,
      }
  ```
- Version is not modified in rejection handling

**Issues**: None
**Recommendation**: PASS

---

### REQ-WF-008
**Release Transition.** The CLI shall transition executable documents from PRE_APPROVED to IN_EXECUTION upon release command. Only the document owner may release.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `release.py` lines 74-83: Status check for PRE_APPROVED
- `release.py` lines 68-72: Owner check via `check_permission(user, "release", doc_owner=doc_owner)`
- `release.py` lines 92-95: Transition to IN_EXECUTION and set execution_phase to "post_release"
- `qms_config.py` line 124: `"release": {"groups": ["initiators"], "owner_only": True}`

**Issues**: None
**Recommendation**: PASS

---

### REQ-WF-009
**Revert Transition.** The CLI shall transition executable documents from POST_REVIEWED to IN_EXECUTION upon revert command, requiring a reason. Only the document owner may revert.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `revert.py` lines 45-56: Reason required via `--reason` flag
- `revert.py` lines 74-78: Owner check via `check_permission(user, "revert", doc_owner=doc_owner)`
- `revert.py` lines 80-89: Status must be POST_REVIEWED
- `revert.py` lines 94-96: Transition to IN_EXECUTION
- `qms_config.py` line 125: `"revert": {"groups": ["initiators"], "owner_only": True}`

**Issues**: None
**Recommendation**: PASS

---

### REQ-WF-010
**Close Transition.** The CLI shall transition executable documents from POST_APPROVED to CLOSED upon close command. Only the document owner may close.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `close.py` lines 69-72: Owner check via `check_permission(user, "close", doc_owner=doc_owner)`
- `close.py` lines 75-84: Status must be POST_APPROVED
- `close.py` lines 99-100: Transition to CLOSED and clear owner
- `qms_config.py` line 126: `"close": {"groups": ["initiators"], "owner_only": True}`

**Issues**: None
**Recommendation**: PASS

---

### REQ-WF-011
**Terminal State Enforcement.** The CLI shall reject all transitions from terminal states (SUPERSEDED, CLOSED, RETIRED).

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `qms_config.py` lines 68-70:
  ```python
  Status.CLOSED: [],
  Status.SUPERSEDED: [],
  Status.RETIRED: [],
  ```
- Empty transition lists mean `WorkflowEngine.get_transition()` will return error for any action from these states
- `test_cr_lifecycle.py` lines 241-275: Test verifies routing from CLOSED fails

**Issues**: None
**Recommendation**: PASS

---

### REQ-WF-012
**Retirement Routing.** The CLI shall support routing for retirement approval, which signals that approval leads to RETIRED status rather than EFFECTIVE or PRE_APPROVED. Retirement routing shall only be permitted for documents with version >= 1.0 (once-effective).

**Assessment**: PARTIAL
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `route.py` lines 33, 122-129: `--retire` flag sets `meta["retiring"] = True`
- `approve.py` lines 122-149: Handles retirement workflow when `retiring` flag is set
- **MISSING**: `route.py` does NOT check if version >= 1.0 before allowing retirement routing
- `test_sop_lifecycle.py` lines 430-445: Test exists with note "Test depends on CLI implementation of this check"

**Issues**:
1. The version >= 1.0 check for retirement is **NOT IMPLEMENTED**
2. A never-effective document (version 0.X) can currently be routed for retirement

**Recommendation**: REVISE - Either:
- Update REQ to note this check is not yet implemented
- Or implement the version check in route.py

---

### REQ-WF-013
**Retirement Transition.** Upon approval of a retirement-routed document, the CLI shall: (1) archive the document to `.archive/`, (2) remove the working copy from the QMS directory, (3) transition status to RETIRED, and (4) log a RETIRE event to the audit trail.

**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `approve.py` lines 124-149:
  ```python
  if is_retiring:
      # Archive
      archive_path = get_archive_path(doc_id, new_version)
      write_document_minimal(archive_path, frontmatter, body)

      # Remove working copy
      draft_path.unlink()
      if effective_path.exists():
          effective_path.unlink()

      # Update meta to RETIRED
      meta = update_meta_approval(meta, new_status=Status.RETIRED.value, ...)

      # Log RETIRE event
      log_retire(doc_id, doc_type, user, current_version, new_version)
  ```
- `qms_audit.py` lines 290-293: `log_retire()` function exists

**Issues**: None
**Recommendation**: PASS

---

## Undocumented Functionality

1. **Execution Phase Tracking**: `qms_meta.py` lines 93-104 implements `execution_phase` field ("pre_release" / "post_release") that determines which workflow path executable documents follow. This is critical for correct routing but not explicitly covered by a REQ.

2. **Checkout from Terminal States**: `test_cr_lifecycle.py` line 274-275 notes "Checkout from CLOSED is allowed (creates new revision for amendment)". This exception to terminal state enforcement is not documented in REQs.

3. **Auto-assign QA**: `route.py` line 132 automatically assigns QA if no `--assign` provided. This default behavior is not documented.

4. **Status Change Logging (CAPA-3)**: Multiple commands log `STATUS_CHANGE` events in addition to their primary events. This comprehensive status tracking isn't captured in the workflow REQs.

5. **Checked-in Requirement for Routing**: `route.py` lines 65-80 blocks routing if document is still checked out. This pre-condition is not documented in workflow REQs.

---

## Recommended Actions

### Priority 1 - Implementation Gaps
1. **REQ-WF-005**: Implement approval gate check in `route.py` - review outcomes should block approval routing if any reviewer submitted `request-updates`
2. **REQ-WF-012**: Implement version >= 1.0 check for retirement routing in `route.py`

### Priority 2 - REQ Revisions
3. **REQ-WF-003**: Add CAPA to list of executable document types
4. **REQ-WF-006**: Clarify that responsible_user is only cleared for non-executable documents, not executable documents during execution phase

### Priority 3 - New REQs to Consider
5. Add REQ for execution_phase tracking mechanism
6. Add REQ for checked-in requirement before routing
7. Add REQ documenting checkout exception from terminal states (for amendments)
