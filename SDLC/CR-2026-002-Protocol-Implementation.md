# Change Record: CR-2026-002

**Title:** Entity Protocol Implementation
**Date:** 2026-01-01
**Author:** Claude (Senior Staff Engineer)
**Status:** POST-APPROVED ✅
**Predecessor:** CR-2026-001 (POST-APPROVED)

---

## 1. Executive Summary

This change implements the Entity Protocols defined in CR-2026-001 Phase B by updating the geometry entities (Line, Circle, Point) to implement the Renderable and Draggable protocols, then updating the renderer to use these protocols instead of isinstance() checks.

This is a continuation of the domain reorganization, focusing on eliminating UI-Model type coupling.

---

## 2. Scope

### 2.1 Phases from CR-2026-001

| Phase | Description | Status |
|-------|-------------|--------|
| C | Update entities to implement protocols | **THIS CR** |
| H | Update renderer to use protocols | **THIS CR** |

### 2.2 Out of Scope (Future CRs)

| Phase | Description | Reason |
|-------|-------------|--------|
| G | Split commands to model/commands/ | Separate refactor |
| I | Update tools to use ToolContext | Requires careful per-tool testing |
| J | Update app to create ToolContext | Depends on Phase I |

---

## 3. Proposed Changes

### 3.1 Phase C: Update Entities to Implement Protocols

**File:** `model/geometry.py`

Add to Entity base class:
- `entity_type` property (abstract)
- `is_reference` property
- `get_render_data()` method (abstract)
- `point_count()` method (abstract)
- `get_anchored()` method

Add to Line class:
- `entity_type` returns `EntityType.LINE`
- `get_render_data()` returns dict with start, end, infinite, anchored, physical, dynamic

Add to Circle class:
- `entity_type` returns `EntityType.CIRCLE`
- `get_render_data()` returns dict with center, radius, anchored, physical, dynamic

Add to Point class:
- `entity_type` returns `EntityType.POINT`
- `get_render_data()` returns dict with pos, is_anchor, is_handle, anchored

### 3.2 Phase H: Update Renderer to Use Protocols

**File:** `ui/renderer.py`

Replace:
```python
from model.geometry import Line, Circle, Point
...
if isinstance(w, Line):
elif isinstance(w, Circle):
elif isinstance(w, Point):
```

With:
```python
from model.protocols import EntityType
...
if w.entity_type == EntityType.LINE:
elif w.entity_type == EntityType.CIRCLE:
elif w.entity_type == EntityType.POINT:
```

And use `entity.get_render_data()` to access rendering properties.

---

## 4. Impact Assessment

### 4.1 Affected Domains

| Domain | Impact Level | Changes |
|--------|-------------|---------|
| **MODEL** | MEDIUM | geometry.py updated to implement protocols |
| **UI** | MEDIUM | renderer.py updated to use protocols |
| **ENGINE** | NONE | No changes |
| **CORE** | NONE | No changes |
| **APP** | NONE | No changes |

### 4.2 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Rendering regression | Low | High | Visual inspection of all entity types |
| Protocol interface mismatch | Low | Medium | Type hints and testing |
| Performance impact | Very Low | Low | Enum comparison vs isinstance() is equivalent |

---

## 5. Test Protocol

### 5.1 Pre-Implementation
- [ ] All imports work correctly
- [ ] Application launches

### 5.2 Post-Implementation
- [ ] Lines render correctly (endpoints, segments, infinite refs)
- [ ] Circles render correctly (outline, center)
- [ ] Points render correctly (anchor points, handles)
- [ ] Selection highlighting works
- [ ] Constraint visualization works
- [ ] No isinstance(Line/Circle/Point) in ui/renderer.py

---

## 6. Implementation Plan

| Step | Description | Risk |
|------|-------------|------|
| 1 | Add EntityType import to geometry.py | Low |
| 2 | Add entity_type property to Entity base class | Low |
| 3 | Implement entity_type in Line, Circle, Point | Low |
| 4 | Add get_render_data() to Entity base class | Low |
| 5 | Implement get_render_data() in Line, Circle, Point | Medium |
| 6 | Update renderer imports | Low |
| 7 | Replace isinstance checks with entity_type | Medium |
| 8 | Update render methods to use get_render_data() | Medium |
| 9 | Visual testing | Low |

---

## 7. Rollback Plan

If critical issues are discovered:
1. Revert all changes via git
2. Document failure mode
3. Revise approach

---

## 8. Authorization

**Lead Engineer Authorization:** Unrestricted approval granted for this session.

---

## 9. Review Log

| Date | Reviewer | Status | Comments |
|------|----------|--------|----------|
| 2026-01-01 | QA | APPROVED | Assigned TU-SKETCH, TU-UI. BU not required. |
| 2026-01-01 | TU-SKETCH | APPROVED | With 2 required conditions, 1 recommended. |
| 2026-01-01 | TU-UI | APPROVED | With 2 required conditions, 1 optional. |
| 2026-01-01 | QA (Post) | APPROVED | All conditions met. isinstance() eliminated. Proceed to archival. |

---

## 10. Implementation Conditions

### From TU-SKETCH:

**S1 (REQUIRED):** Implement `is_reference` property on Entity base class and all subclasses:
- Line: `return self.ref`
- Circle: `return False`
- Point: `return False`

**S2 (REQUIRED):** Ensure `get_render_data()` returns tuples (not numpy array references) for position data to prevent inadvertent mutation.

**S3 (RECOMMENDED):** Log TD-001 for future remediation of physics concepts in Entity base class.

### From TU-UI:

**U1 (REQUIRED):** Replace BOTH `isinstance()` blocks in renderer.py:
- Lines 271-276 in `_draw_geometry()`
- Lines 646-651 in `_draw_editor_overlays()`

Use `entity.get_anchored(pt_idx)` from Draggable protocol for anchor queries.

**U2 (REQUIRED):** Clarify `line.ref` handling - use `entity.is_reference` property from Renderable protocol.

**U3 (OPTIONAL):** Consider migrating `_get_entity_center_screen()` hasattr() pattern in follow-up CR.

---

## 11. Implementation Summary

### 11.1 Phase C: Entity Protocol Implementation

**File:** `model/geometry.py`

Added to Entity base class:
- `entity_type` property (abstract)
- `is_reference` property (default: False)
- `point_count()` method (abstract)
- `get_anchored(index)` method (abstract)
- `distance_to(x, y)` method (abstract)
- `parameter_at(x, y)` method (abstract)
- `get_render_data()` method (abstract)

Implemented in Line:
- `entity_type` returns `EntityType.LINE`
- `is_reference` returns `self.ref`
- `point_count()` returns 2
- `get_render_data()` returns start, end, infinite, anchored, physical, dynamic as tuples

Implemented in Circle:
- `entity_type` returns `EntityType.CIRCLE`
- `point_count()` returns 1
- `get_render_data()` returns center, radius, anchored, physical, dynamic as tuples

Implemented in Point:
- `entity_type` returns `EntityType.POINT`
- `point_count()` returns 1
- `get_render_data()` returns pos, is_anchor, is_handle, anchored as tuples

### 11.2 Phase H: Renderer Protocol Usage

**File:** `ui/renderer.py`

- Replaced `from model.geometry import Line, Circle, Point` with `from model.protocols import EntityType`
- Updated `_draw_geometry()` to use `entity_type` enum instead of `isinstance()`
- Updated `_draw_line_entity()` to use `get_render_data()` and `is_reference`
- Updated `_draw_circle_entity()` to use `get_render_data()`
- Updated `_draw_point_entity()` to use `get_render_data()`
- Updated `_draw_editor_overlays()` to use `get_anchored()` instead of isinstance()
- Updated `_get_entity_center_screen()` to use `entity_type` and `get_render_data()` (U3 optional)

### 11.3 Condition Compliance

| Condition | Status | Evidence |
|-----------|--------|----------|
| S1 | ✅ MET | `is_reference` property added to Entity base class and Line override |
| S2 | ✅ MET | All `get_render_data()` return tuples for positions, not numpy arrays |
| S3 | NOTED | TD-001 technical debt acknowledged (out of scope) |
| U1 | ✅ MET | Both isinstance() blocks replaced (lines 271-276 and 644-645) |
| U2 | ✅ MET | `is_reference` property used in _draw_line_entity() |
| U3 | ✅ DONE | hasattr() pattern also migrated in _get_entity_center_screen() |

### 11.4 Verification

```
Line entity_type: EntityType.LINE
Line is_reference: False
Line get_render_data: {'start': (0.0, 0.0), 'end': (1.0, 1.0), ...}
Circle entity_type: EntityType.CIRCLE
Point entity_type: EntityType.POINT
Renderer import successful
```

---

*Document Control: CR-2026-002 v1.3*
*Pre-Approval: 2026-01-01 (Unanimous)*
*Implementation: 2026-01-01*
*Post-Approval: 2026-01-01 (QA APPROVED)*
