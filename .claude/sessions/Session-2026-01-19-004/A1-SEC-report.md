# A1-SEC: Security Domain Review

## Summary

- **Total REQs reviewed:** 6
- **Accurate:** 3 (REQ-SEC-001, REQ-SEC-005, REQ-SEC-006)
- **Accurate with issues:** 2 (REQ-SEC-003, REQ-SEC-004)
- **Inaccurate:** 1 (REQ-SEC-002)

---

## Requirement Analysis

### REQ-SEC-001

**Requirement:** The CLI shall classify all users into exactly one of three groups: Initiators, QA, or Reviewers.

**Assessment:** ACCURATE

**Completeness:** COMPLETE

**Rebuildability:** SUFFICIENT

**Evidence:**

`qms_config.py` (lines 107-111):
```python
USER_GROUPS = {
    "initiators": {"lead", "claude"},       # Can create documents, initiate workflows
    "qa": {"qa"},                            # Can modify workflows, review, approve
    "reviewers": {"tu_ui", "tu_scene", "tu_sketch", "tu_sim", "bu"},  # Review/approve only
}
```

`qms_auth.py` (lines 30-35):
```python
def get_user_group(user: str) -> str:
    """Get the group a user belongs to."""
    for group_name, members in USER_GROUPS.items():
        if user in members:
            return group_name
    return "unknown"
```

**Issues:** None. Each user belongs to exactly one group, and the code correctly iterates through groups to find membership.

**Recommendation:** PASS

---

### REQ-SEC-002

**Requirement:** The CLI shall authorize actions based on user group membership: create, checkout, checkin, route, release, revert, close (Initiators); assign (QA); fix (QA, lead).

**Assessment:** INACCURATE

**Completeness:** INCOMPLETE

**Rebuildability:** INSUFFICIENT

**Evidence:**

`qms_config.py` (lines 115-131):
```python
PERMISSIONS = {
    "create":    {"groups": ["initiators"]},
    "checkout":  {"groups": ["initiators"]},
    "checkin":   {"groups": ["initiators"], "owner_only": True},
    "route":     {"groups": ["initiators", "qa"], "owner_only": True},  # CR-032
    "assign":    {"groups": ["qa"]},
    "review":    {"groups": ["initiators", "qa", "reviewers"], "assigned_only": True},
    "approve":   {"groups": ["qa", "reviewers"], "assigned_only": True},
    "reject":    {"groups": ["qa", "reviewers"], "assigned_only": True},
    "release":   {"groups": ["initiators"], "owner_only": True},
    "revert":    {"groups": ["initiators"], "owner_only": True},
    "close":     {"groups": ["initiators"], "owner_only": True},
    ...
}
```

`commands/fix.py` (lines 33-35):
```python
if current_user not in {"qa", "lead"}:
    print("Error: Only QA or lead can run administrative fixes.", file=sys.stderr)
    return 1
```

**Issues:**

1. **"route" is not Initiator-only:** The code shows `route` is authorized for both `["initiators", "qa"]`. The requirement states only Initiators can route. This is a code vs. requirement mismatch (CR-032 changed this).

2. **"fix" authorization is user-based, not group-based:** The requirement states "fix (QA, lead)" but "lead" is a *user* within the Initiators group, not a *group*. The actual code bypasses the permission system entirely and uses hardcoded user checking: `if current_user not in {"qa", "lead"}`. This is an architectural inconsistency.

3. **"fix" command not in PERMISSIONS dict:** The `fix` command does not appear in the PERMISSIONS dictionary, meaning it does not follow the standard authorization model.

4. **Missing commands from PERMISSIONS:** The requirement lists only a subset of actions. The code also includes `review`, `approve`, `reject` which have their own authorization rules but are not mentioned in REQ-SEC-002.

**Recommendation:** REVISE

Suggested revision:
> **REQ-SEC-002.** Group-Based Action Authorization. The CLI shall authorize actions based on user group membership:
> - Initiators: create, checkout, checkin, release, revert, close
> - Initiators and QA: route
> - QA: assign
> - QA and lead (user): fix (administrative command with user-level override)

Note: Consider whether to restructure "fix" to use the standard permission model or document the user-level exception explicitly.

---

### REQ-SEC-003

**Requirement:** The CLI shall restrict checkin, route, release, revert, and close actions to the document's responsible_user (owner).

**Assessment:** ACCURATE (with issue)

**Completeness:** INCOMPLETE

**Rebuildability:** INSUFFICIENT

**Evidence:**

`qms_config.py` (lines 118-126):
```python
"checkin":   {"groups": ["initiators"], "owner_only": True},
"route":     {"groups": ["initiators", "qa"], "owner_only": True},
"release":   {"groups": ["initiators"], "owner_only": True},
"revert":    {"groups": ["initiators"], "owner_only": True},
"close":     {"groups": ["initiators"], "owner_only": True},
```

`qms_auth.py` (lines 84-98):
```python
# Check owner requirement
if perm.get("owner_only") and doc_owner and doc_owner != user:
    # For initiators, any initiator can act on behalf of documents
    if user_group == "initiators" and doc_owner in USER_GROUPS.get("initiators", set()):
        pass  # Allow initiators to act on each other's documents
    else:
        error = f"""
Permission Denied: '{command}' command

You ({user}) are not the responsible user for this document.
Responsible user: {doc_owner}

Only the document owner or another Initiator can perform this action.
"""
        return False, error
```

**Issues:**

1. **Initiator Cross-Action:** The code allows ANY Initiator to act on documents owned by ANY OTHER Initiator. This is an intentional design but NOT documented in the requirement. Lines 87-88 show that if the current user is an initiator and the document owner is also an initiator, the ownership check is bypassed.

2. **This is a significant security policy** that the requirement does not capture. A developer reading only REQ-SEC-003 would implement strict owner-only enforcement.

**Recommendation:** REVISE

Suggested revision:
> **REQ-SEC-003.** Owner-Only Restrictions. The CLI shall restrict checkin, route, release, revert, and close actions to the document's responsible_user (owner). **Exception:** Any Initiator may perform these actions on documents owned by another Initiator.

---

### REQ-SEC-004

**Requirement:** The CLI shall permit review and approve actions only for users listed in the document's pending_assignees.

**Assessment:** ACCURATE (with issue)

**Completeness:** INCOMPLETE

**Rebuildability:** INSUFFICIENT

**Evidence:**

`qms_config.py` (lines 121-122):
```python
"review":    {"groups": ["initiators", "qa", "reviewers"], "assigned_only": True},
"approve":   {"groups": ["qa", "reviewers"], "assigned_only": True},
```

`qms_auth.py` (lines 100-112):
```python
# Check assignment requirement
if perm.get("assigned_only") and assigned_users is not None:
    if user not in assigned_users:
        error = f"""
Permission Denied: '{command}' command

You ({user}) are not assigned to this workflow.
Assigned users: {', '.join(assigned_users) if assigned_users else 'None'}

You can only {command} documents you are assigned to.
Check your inbox for assigned tasks: qms --user {user} inbox
"""
        return False, error
```

**Issues:**

1. **"review" is also gated by GROUP membership.** The requirement says "only for users listed in pending_assignees" but the code ALSO requires group membership. Initiators CAN review (if assigned), but CANNOT approve. This dual-gate behavior is not fully captured.

2. **Approve has different group permissions than review.** The requirement lumps them together, but:
   - Review: Initiators, QA, Reviewers (if assigned)
   - Approve: QA, Reviewers ONLY (if assigned)

   This means Initiators cannot approve even if somehow assigned.

**Recommendation:** REVISE

Suggested revision:
> **REQ-SEC-004.** Assignment-Based Review Access. The CLI shall permit review actions only for users who are: (1) listed in the document's pending_assignees, AND (2) members of Initiators, QA, or Reviewers groups. The CLI shall permit approve actions only for users who are: (1) listed in pending_assignees, AND (2) members of QA or Reviewers groups.

---

### REQ-SEC-005

**Requirement:** The CLI shall permit reject actions using the same authorization rules as approve (pending_assignees).

**Assessment:** ACCURATE

**Completeness:** COMPLETE

**Rebuildability:** SUFFICIENT

**Evidence:**

`qms_config.py` (lines 122-123):
```python
"approve":   {"groups": ["qa", "reviewers"], "assigned_only": True},
"reject":    {"groups": ["qa", "reviewers"], "assigned_only": True},
```

**Issues:** None. The `reject` and `approve` permissions are defined identically.

**Recommendation:** PASS

---

### REQ-SEC-006

**Requirement:** The CLI shall reject any command invoked with a user identifier not present in the user registry, returning an error without modifying any state.

**Assessment:** ACCURATE

**Completeness:** COMPLETE

**Rebuildability:** SUFFICIENT

**Evidence:**

`qms_auth.py` (lines 38-52):
```python
def verify_user_identity(user: str) -> bool:
    """Verify that the user is a valid QMS user."""
    if user not in VALID_USERS:
        print(f"""
Error: '{user}' is not a valid QMS user.

Valid users by group:
  Initiators: {', '.join(sorted(USER_GROUPS['initiators']))}
  QA:         {', '.join(sorted(USER_GROUPS['qa']))}
  Reviewers:  {', '.join(sorted(USER_GROUPS['reviewers']))}

Specify your identity with: qms --user <username> <command>
""")
        return False
    return True
```

`qms_config.py` (line 104):
```python
VALID_USERS = {"lead", "claude", "qa", "bu", "tu_ui", "tu_scene", "tu_sketch", "tu_sim"}
```

**Issues:** None. The verification happens before any state modification.

**Recommendation:** PASS

---

## Undocumented Functionality

### 1. Folder Access Control (`verify_folder_access`)

**Location:** `qms_auth.py` (lines 121-135)

```python
def verify_folder_access(user: str, target_user: str, operation: str) -> bool:
    """Verify that user has access to target_user's folder."""
    if user != target_user:
        print(f"""
Error: Access denied.

User '{user}' cannot {operation} for user '{target_user}'.
You can only access your own inbox and workspace.
...
""")
        return False
    return True
```

**Issue:** This function restricts users from accessing other users' workspace/inbox directories. This is a security boundary not captured by any REQ-SEC requirement.

**Recommendation:** ADD_REQ

Suggested new requirement:
> **REQ-SEC-007.** Workspace/Inbox Isolation. The CLI shall restrict workspace and inbox operations (query, task access) to the requesting user's own directories. Users shall not access other users' workspaces or inboxes.

### 2. Unknown Command Permissiveness

**Location:** `qms_auth.py` (lines 64-65)

```python
if command not in PERMISSIONS:
    return True, ""  # Unknown command, let it through
```

**Issue:** Commands not defined in the PERMISSIONS dictionary are automatically allowed. This is a permissive-by-default security model that could allow new commands to bypass authorization.

**Recommendation:** ADD_REQ or document as known behavior. Consider whether the RS should specify that undefined commands should PASS or FAIL authorization.

---

## Recommended Actions

1. **HIGH PRIORITY:** Revise REQ-SEC-002 to accurately reflect:
   - Route is allowed for both Initiators AND QA
   - Fix uses user-level authorization (qa, lead) not group-level
   - Fix bypasses the standard permission model

2. **HIGH PRIORITY:** Revise REQ-SEC-003 to document the Initiator cross-action exception (any Initiator can act on any other Initiator's documents).

3. **MEDIUM PRIORITY:** Revise REQ-SEC-004 to clarify the dual-gate (group membership + assignment) for both review and approve, and note that Initiators cannot approve.

4. **MEDIUM PRIORITY:** Add REQ-SEC-007 for workspace/inbox isolation (`verify_folder_access`).

5. **LOW PRIORITY:** Consider documenting or addressing the permissive-by-default behavior for undefined commands.

---

**Review completed:** 2026-01-19

**Reviewer:** A1-SEC (Security Domain)
