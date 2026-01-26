# Impact Assessment: Removal of SUPERSEDED Status

**Date:** 2026-01-25
**Decision:** Remove SUPERSEDED as it's an unimplemented vestigial concept

---

## Summary

SUPERSEDED is mentioned as a terminal state but has no mechanism to reach it. Removing it simplifies the system and eliminates one test failure. This requires changes to RS requirements, CLI code, and test files.

---

## Impact Categories

### 1. Requirements Specification (RS) - CHANGES REQUIRED

| File | Line(s) | Current Text | Change Required |
|------|---------|--------------|-----------------|
| SDLC-QMS-RS-draft.md | 339 | "QMS/.archive/ for superseded versions" | Change to "QMS/.archive/ for archived versions" |
| SDLC-QMS-RS-draft.md | 359 | "SUPERSEDED and RETIRED are terminal states" | Change to "RETIRED is a terminal state" |
| SDLC-QMS-RS-draft.md | 368 | "terminal states (SUPERSEDED, CLOSED, RETIRED)" | Change to "terminal states (CLOSED, RETIRED)" |

**Note:** SDLC-QMS-RS.md is EFFECTIVE v1.0 and should not be edited. The -draft.md is v1.1 in progress.

### 2. RTM - CHANGES REQUIRED

| File | Section | Change Required |
|------|---------|-----------------|
| SDLC-QMS-RTM-draft.md | REQ-WF-011 row | Remove "(xfail)" note about superseded test |
| SDLC-QMS-RTM-draft.md | Section 6.11 | Update terminal state test description |

### 3. qms-cli Code - CHANGES REQUIRED

| File | Line(s) | Change Required |
|------|---------|-----------------|
| `qms_schema.py` | 23 | Remove "SUPERSEDED" from status list |
| `qms_config.py` | 38 | Remove `SUPERSEDED = "SUPERSEDED"` from Status enum |
| `qms_config.py` | 56 | Remove `Status.EFFECTIVE: [Status.SUPERSEDED],` transition |
| `qms_config.py` | 69 | Remove `Status.SUPERSEDED: [],` empty transitions |
| `qms_meta.py` | 109 | Remove `"supersedes": None,` from initial meta |
| `commands/migrate.py` | 99 | Remove `meta["supersedes"] = frontmatter.get("supersedes")` |

### 4. Test Files - CHANGES REQUIRED

| File | Change Required |
|------|-----------------|
| `.test-env/.../test_sop_lifecycle.py` | DELETE `test_terminal_state_superseded()` function (lines 714-756) |
| `qms-cli/tests/.../test_sop_lifecycle.py` | DELETE `test_terminal_state_superseded()` function (lines 714-756) |

### 5. Session Notes - NO CHANGES NEEDED

These are historical records and do not need updating:
- `Session-2026-01-25-001/test-failure-analysis.md` - Documents the decision
- `Session-2026-01-25-001/qualification-readiness-report.md` - Historical analysis
- Various other session notes - Informational references

### 6. Archive Files - NO CHANGES NEEDED

Archived SOPs mention "supersedes" in their template structure. These are historical and should not be modified.

### 7. Workspace Files - CLEANUP

| File | Change Required |
|------|-----------------|
| `.claude/users/claude/workspace/CR-001.md` | Has `supersedes: null` in frontmatter - will be cleaned up naturally |

---

## Execution Plan

Since RS and RTM are already in DRAFT and part of CR-036's scope, this can be handled as part of CR-036 execution:

1. **Update RS-draft.md** (3 line changes)
2. **Update RTM-draft.md** (remove xfail reference)
3. **Update qms-cli code** (6 files, minor changes)
4. **Delete test function** (both copies)
5. **Re-run qualification tests** - should now have 5 xfails instead of 6

---

## Requirements Affected

| REQ ID | Current Text | New Text |
|--------|--------------|----------|
| REQ-DOC-003 | ".archive/ for superseded versions" | ".archive/ for archived versions" |
| REQ-WF-002 | "SUPERSEDED and RETIRED are terminal states" | "RETIRED is a terminal state" |
| REQ-WF-011 | "SUPERSEDED, CLOSED, RETIRED" | "CLOSED, RETIRED" |

---

## Risk Assessment

**Risk:** LOW
- SUPERSEDED was never reachable, so removing it changes no actual behavior
- No existing documents have SUPERSEDED status
- Simplifies the codebase and requirements

**Benefit:**
- One fewer failing test
- Cleaner state machine
- No dead code paths
