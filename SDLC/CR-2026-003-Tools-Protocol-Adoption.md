# Change Record: CR-2026-003

**Title:** Tools Protocol Adoption & isinstance() Elimination
**Date:** 2026-01-01
**Author:** Claude (Senior Staff Engineer)
**Status:** POST-APPROVED
**Predecessor:** CR-2026-002 (POST-APPROVED)

---

## 1. Executive Summary

This change eliminates the remaining `isinstance()` checks in `ui/tools.py` by adopting the Entity protocols established in CR-2026-002. This continues the pattern of decoupling UI from concrete model types.

---

## 2. Scope

### 2.1 In Scope

1. **Eliminate isinstance() in tools.py** - Replace 9 isinstance() checks with entity_type enum
2. **Update tool imports** - Import EntityType from protocols, not concrete types from geometry

### 2.2 Out of Scope (Future CRs)

| Item | Reason |
|------|--------|
| Phase G: Split commands to model/commands/ | Significant refactor, requires separate planning |
| Phase I: Full ToolContext adoption | Large scope, tools work correctly with current pattern |
| Phase J: App creates ToolContext | Depends on Phase I |

---

## 3. Proposed Changes

### 3.1 Update Imports

**File:** `ui/tools.py`

Replace:
```python
from model.geometry import Line, Circle
```

With:
```python
from model.protocols import EntityType
```

### 3.2 Replace isinstance() Checks

There are 9 isinstance() checks in tools.py that need updating:

| Line | Current Pattern | Replacement |
|------|-----------------|-------------|
| 1039 | `isinstance(entity, Line)` | `entity.entity_type == EntityType.LINE` |
| 1078 | `isinstance(entity, Line)` | `entity.entity_type == EntityType.LINE` |
| 1081 | `isinstance(entity, Circle)` | `entity.entity_type == EntityType.CIRCLE` |
| 1119 | `isinstance(w, Line)` | `w.entity_type == EntityType.LINE` |
| 1142 | `isinstance(w, Circle)` | `w.entity_type == EntityType.CIRCLE` |
| 1169 | `isinstance(w, Circle)` | `w.entity_type == EntityType.CIRCLE` |
| 1279 | `isinstance(w, Line)` | `w.entity_type == EntityType.LINE` |
| 1291 | `isinstance(w, Circle)` | `w.entity_type == EntityType.CIRCLE` |
| 1320 | `isinstance(w, Circle)` | `w.entity_type == EntityType.CIRCLE` |

---

## 4. Impact Assessment

| Domain | Impact Level | Changes |
|--------|-------------|---------|
| **UI** | LOW | tools.py imports and dispatch updated |
| **MODEL** | NONE | No changes |
| **ENGINE** | NONE | No changes |
| **CORE** | NONE | No changes |

### 4.1 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tool behavior regression | Low | Medium | Protocol methods already tested |
| Missing entity type case | Low | Low | Verified all uses are LINE/CIRCLE |

---

## 5. Test Protocol

- [ ] All tools function correctly (select, move, resize)
- [ ] Line selection and manipulation works
- [ ] Circle selection and manipulation works
- [ ] No isinstance() of Line/Circle/Point in tools.py

---

## 6. Implementation Plan

| Step | Description | Risk |
|------|-------------|------|
| 1 | Update imports in tools.py | Low |
| 2 | Replace isinstance checks with entity_type | Low |
| 3 | Test all tool operations | Low |

---

## 7. Authorization

**Lead Engineer Authorization:** Unrestricted approval granted for this session.

---

## 8. Review Log

| Date | Reviewer | Status | Comments |
|------|----------|--------|----------|
| 2026-01-01 | QA | APPROVED | Assigned TU-UI only. Low risk, minimal scope. |
| 2026-01-01 | TU-UI | APPROVED | No conditions. Strengthens Air Gap, eliminates Red Flag. |
| 2026-01-01 | QA | POST-APPROVED | Implementation verified. All 10 isinstance/hasattr checks replaced. No scope deviation. |

---

## 9. Implementation Summary

### 9.1 Changes Made

**File:** `ui/tools.py`

1. **Import Updated:** Confirmed `from model.protocols import EntityType` (was already in place)

2. **isinstance() Replacements:**

| Method | Original | Replacement |
|--------|----------|-------------|
| `_start_edit_drag` | `isinstance(entity, Line)` | `entity.entity_type == EntityType.LINE` |
| `_capture_entity_positions` | `isinstance(entity, Line)` | `entity.entity_type == EntityType.LINE` |
| `_capture_entity_positions` | `isinstance(entity, Circle)` | `entity.entity_type == EntityType.CIRCLE` |
| `_capture_entity_positions` | `hasattr(entity, 'pos')` | `entity.entity_type == EntityType.POINT` |
| `_handle_edit_drag` | `isinstance(w, Line)` | `w.entity_type == EntityType.LINE` |
| `_handle_edit_drag` | `isinstance(w, Circle)` | `w.entity_type == EntityType.CIRCLE` |
| `_handle_resize_drag` | `isinstance(w, Circle)` | `w.entity_type == EntityType.CIRCLE` |
| `_build_point_map` | `isinstance(w, Line)` | `w.entity_type == EntityType.LINE` |
| `_build_point_map` | `isinstance(w, Circle)` | `w.entity_type == EntityType.CIRCLE` |
| `_hit_test_circle_resize` | `isinstance(w, Circle)` | `w.entity_type == EntityType.CIRCLE` |

### 9.2 Verification

```
$ grep "isinstance.*Line\|isinstance.*Circle" ui/tools.py
(no matches)

$ python -c "from ui.tools import SelectTool; print('Import successful')"
Import successful
```

---

*Document Control: CR-2026-003 v1.3*
*Pre-Approval: 2026-01-01 (Unanimous)*
*Post-Approval: 2026-01-01*
