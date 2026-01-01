# Official Action Item Tracker

**Maintained by:** Secretary of the Senate of Guardians
**Created:** 2025-12-31
**Source Document:** SENATE_CONSENSUS_REPORT.md
**Last Updated:** 2025-12-31

---

## Summary Statistics

| Priority Level | Count | Status |
|----------------|-------|--------|
| Priority 0 (Critical) | 4 | 1 Closed, 3 Open |
| Priority 1 (High) | 9 | All Open |
| Priority 2 (Medium) | 5 | All Open |
| Priority 3 (Backlog) | 5 | All Open |
| **Total** | **23** | **1 Closed, 22 Open** |

### By Owner

| Guardian | Items Assigned |
|----------|----------------|
| Scene Guardian | 4 |
| UI Guardian | 4 |
| Input Guardian | 4 |
| Sketch Guardian | 3 |
| Sim Guardian | 4 |
| Generalizer | 2 |
| All (Shared) | 1 |

---

## Priority 0 - Critical (Block Release)

These items have **unanimous Senate consensus** and must be resolved before any release.

---

### AIT-001: SelectTool.cancel() Air Gap Violation

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P0 (Critical) |
| **Owner** | Scene Guardian |
| **Status** | **Closed** |
| **Effort** | Medium |
| **Closed Date** | 2025-12-31 |
| **Resolution** | PROP-2025-001 implemented |

**Description:**

The `SelectTool.cancel()` method in `ui/tools.py` (lines 764-796) directly mutates entity state, bypassing the Command Queue. This is a critical Air Gap violation that breaks undo/redo functionality and corrupts the command history chain of custody.

**Violations identified:**
- Line 772: `entity.set_point(self.target_pt, np.array(self.original_position))`
- Line 776: `entity.radius = self.original_radius`
- Lines 783, 786: `self.sketch.entities[idx].move(-self.total_dx, -self.total_dy)`

**Resolution:** ✓ IMPLEMENTED via PROP-2025-001. SelectTool now uses the supersede pattern:
- All drag start methods create initial commands with `historize=True, supersede=False`
- All drag handlers use `historize=True, supersede=True`
- `cancel()` now calls `scene.discard()` instead of direct entity mutation
- Senate approved unanimously (6-0) on 2025-12-31

---

### AIT-002: MaterialPropertyWidget Air Gap Violation

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P0 (Critical) |
| **Owner** | UI Guardian |
| **Status** | Open |
| **Effort** | Small |

**Description:**

The `MaterialPropertyWidget` in `ui/ui_widgets.py` directly mutates entity material assignments, bypassing the Command Queue. This breaks undo functionality for material changes.

**Violations identified:**
- Line 1957: `entity.material_id = clean_name`
- Line 2230: `entity.material_id = new_name`

**Resolution:** Replace direct assignment with `SetEntityMaterialCommand` submitted via `scene.execute()`. This ensures material changes are recorded in command history and properly undoable.

---

### AIT-003: pop_modal() Missing Interaction Reset

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P0 (Critical) |
| **Owner** | Input Guardian |
| **Status** | Open |
| **Effort** | Small |

**Description:**

The `pop_modal()` method in `app/app_controller.py` (lines 63-67) does not call `reset_interaction_state()` when closing a modal, creating an asymmetric implementation. While `push_modal()` correctly resets interaction state, `pop_modal()` does not. This creates a ghost input risk where stale click/hover states from before the modal can trigger unintended actions after the modal closes.

**Current problematic code:**
```python
def pop_modal(self):
    if self._modal_stack:
        return self._modal_stack.pop()['modal']
    return None
    # MISSING: reset_interaction_state() call
```

**Resolution:** Add `self.app.ui.root.reset_interaction_state()` call before the return statement in `pop_modal()`. This enforces the Modal Stack Symmetry decision adopted by the Senate.

---

### AIT-004: Python Loops in Physics Hot Path

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P0 (Critical) |
| **Owner** | Sim Guardian |
| **Status** | Open |
| **Effort** | Medium |

**Description:**

Three performance-critical functions in `engine/simulation.py` use pure Python loops that cause significant frame drops when particle counts exceed 5000. These represent O(N) operations that run every frame or on rebuild.

**Bottlenecks identified:**
- Lines 472-508: `sync_static_atoms_to_geometry()` - O(N) Python loop every frame
- Lines 525-566: `snap_tethered_atoms_to_anchors()` - O(N) Python loop on rebuild
- Lines 654-660: `_check_overlap()` - O(N) Python loop per overlap check

**Resolution:** Convert these loops to Numba JIT-compiled kernels and add them to `engine/physics_core.py`. The existing Numba infrastructure should make this conversion straightforward while providing 10-100x speedup for these operations.

---

## Priority 1 - High Priority (This Sprint)

These items have strong Senate consensus and should be completed in the current sprint.

---

### AIT-005: Create GeometricEntity Protocol

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P1 (High) |
| **Owner** | Generalizer |
| **Status** | Open |
| **Effort** | Medium |
| **Consensus** | 6-0 (Unanimous) |

**Description:**

Create a formal `typing.Protocol` for geometric entities to eliminate the 82 `isinstance()` checks scattered throughout the codebase. This is the highest-impact single change identified by the audit, as it enables systematic cleanup of type-checking anti-patterns.

**Required Protocol Definition:**
```python
class GeometricEntity(Protocol):
    material_id: str
    entity_type: int
    physical: bool
    dynamic: bool

    def get_point(self, index: int) -> np.ndarray: ...
    def set_point(self, index: int, pos: np.ndarray) -> None: ...
    def get_point_count(self) -> int: ...
    def get_inv_mass(self, index: int) -> float: ...
    def move(self, dx: float, dy: float, indices: Optional[List[int]] = None) -> None: ...
    def get_center_of_mass(self) -> Tuple[float, float]: ...
    def get_bounds(self) -> Tuple[float, float, float, float]: ...
    def to_dict(self) -> dict: ...
```

**Resolution:** Create new file `model/protocols.py` with the GeometricEntity Protocol. Then systematically update type hints across the codebase to use the protocol instead of Union types or isinstance() checks.

---

### AIT-006: Implement Missing Numba Constraints (5 types)

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P1 (High) |
| **Owner** | Sketch Guardian |
| **Status** | Open |
| **Effort** | Large |
| **Consensus** | 5-0 |

**Description:**

The Numba solver backend is missing implementations for 5 constraint types, causing silent fallback to the legacy Python solver when these constraints are present. Users are not warned about this degraded performance mode.

**Missing Numba kernels:**
1. PERPENDICULAR constraint
2. ANGLE constraint
3. RADIUS constraint
4. MIDPOINT constraint
5. (Fifth type TBD - verify against constraint type enum)

**Resolution:** Implement Numba JIT kernels for all 5 constraint types in `model/solver_kernels.py`. Each kernel should follow the existing pattern of the implemented constraints. This will provide full Numba parity and enable users to benefit from JIT compilation regardless of constraint types used.

---

### AIT-007: Add Numba Warning on F9 Toggle

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P1 (High) |
| **Owner** | Input Guardian |
| **Status** | Open |
| **Effort** | Small |
| **Consensus** | 6-0 (Unanimous) |

**Description:**

When users toggle to Numba mode (F9), they are not warned if unsupported constraint types exist in their scene. This leads to confusion when performance does not improve as expected (due to silent fallback).

**Required behavior:** When F9 is pressed and Numba mode is enabled, scan the current scene for unsupported constraints and display a status bar warning.

**Message format:** "Numba mode: PERPENDICULAR, ANGLE, RADIUS, MIDPOINT constraints will use legacy solver"

**Resolution:** Modify the F9 handler in InputHandler to:
1. Forward the toggle event to UIManager for status display
2. Check scene constraints against supported Numba types
3. Display warning in status bar if unsupported types are present

---

### AIT-008: Extract Magic Numbers to config.py

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P1 (High) |
| **Owner** | All (Shared) |
| **Status** | Open |
| **Effort** | Small |
| **Consensus** | 6-0 (Unanimous) |

**Description:**

The audit identified 15+ magic numbers scattered throughout the codebase that should be centralized in `core/config.py`. This violates the "No Magic Numbers" rule established in the AvG case studies and makes tuning physics/UI parameters unnecessarily difficult.

**Resolution:** Each Guardian should audit their domain for magic numbers and extract them to `core/config.py` with descriptive constant names. Examples include physics constants (friction, restitution), UI dimensions (padding, margins), and solver parameters (iterations, epsilon).

---

### AIT-009: Create ImportModelCommand (Undoable Imports)

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P1 (High) |
| **Owner** | Scene Guardian |
| **Status** | Open |
| **Effort** | Medium |
| **Consensus** | 6-0 (Unanimous) |

**Description:**

Currently, model imports are not undoable because they do not go through the Command Queue. When a user imports a model and wants to undo, the operation fails or produces inconsistent state.

**Resolution:** Create `ImportModelCommand` in `core/commands.py` that:
1. Stores the imported entities in `execute()`
2. Properly removes them in `undo()`
3. Handles re-importing in `redo()`

This ensures imports follow the Air Gap principle and maintains command history integrity.

---

### AIT-010: MenuBar Implement OverlayProvider

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P1 (High) |
| **Owner** | UI Guardian |
| **Status** | Open |
| **Effort** | Medium |
| **Consensus** | 5-0 |

**Description:**

The MenuBar does not implement the OverlayProvider protocol, which means its dropdown menus may have incorrect Z-ordering or clipping issues. This is inconsistent with the established Overlay Protocol pattern.

**Resolution:** Update MenuBar to implement the OverlayProvider protocol:
1. Add `get_overlay_elements()` method
2. Register MenuBar with UIManager's overlay providers
3. Ensure menu dropdowns render with proper Z-order (parent.z + 1)

This follows the AvG principle of using established protocols rather than special-case handling.

---

### AIT-011: Dialog Classes Inherit from UIElement

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P1 (High) |
| **Owner** | UI Guardian |
| **Status** | Open |
| **Effort** | Medium |
| **Consensus** | 5-0 |

**Description:**

Dialog classes do not properly inherit from UIElement, which means they may lack standard widget behaviors like focus management, interaction state reset, and consistent event handling.

**Resolution:** Refactor dialog classes to:
1. Properly inherit from UIElement (or appropriate base class)
2. Implement required methods: `wants_focus()`, `on_focus_lost()`, `reset_interaction_state()`
3. Ensure dialogs integrate properly with the UI tree

---

### AIT-012: Deprecate MoveEntityCommand (Use Snapshots)

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P1 (High) |
| **Owner** | Scene Guardian |
| **Status** | Open |
| **Effort** | Medium |
| **Consensus** | 5-0 |

**Description:**

The `MoveEntityCommand` uses delta-based undo which does not properly capture solver-induced changes (rotation, constraint satisfaction). The architectural decision for geometric undo is to use Absolute State Snapshots as documented in CLAUDE.md Section 3.3.

**Resolution:**
1. Deprecate `MoveEntityCommand`
2. Replace all usages with `SetEntityGeometryCommand` which stores absolute start/end positions
3. Remove `MoveEntityCommand` from `core/commands.py` after migration

---

### AIT-013: Standardize Epsilon Constants in Config

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P1 (High) |
| **Owner** | Sketch Guardian |
| **Status** | Open |
| **Effort** | Small |
| **Consensus** | 6-0 (Unanimous) |

**Description:**

Epsilon values for floating-point comparisons are defined inconsistently across the codebase. Some use `1e-6`, others `1e-9`, and some have hardcoded values inline. This creates subtle bugs when tolerance assumptions don't match.

**Resolution:**
1. Define standard epsilon constants in `core/config.py`:
   - `EPSILON_GEOMETRY` for CAD comparisons
   - `EPSILON_PHYSICS` for simulation comparisons
   - `EPSILON_RENDER` for display comparisons
2. Replace all hardcoded epsilon values with appropriate constants
3. Document the expected use case for each epsilon level

---

## Priority 2 - Medium Priority (Next Sprint)

---

### AIT-014: BrushTool Inherit from Tool Base

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P2 (Medium) |
| **Owner** | Input Guardian |
| **Status** | Open |
| **Effort** | Small |

**Description:**

BrushTool does not properly inherit from the Tool base class, causing inconsistent behavior compared to other tools. It may be missing standard tool lifecycle methods or event handling patterns.

**Resolution:** Refactor BrushTool to properly extend the Tool base class, implementing all required abstract methods and following established tool patterns.

---

### AIT-015: Remove Debug Print from _resize_arrays()

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P2 (Medium) |
| **Owner** | Sim Guardian |
| **Status** | Open |
| **Effort** | Trivial |

**Description:**

The `_resize_arrays()` function in `engine/simulation.py` contains debug print statements that should be removed for production. These prints can cause console spam and minor performance degradation.

**Resolution:** Remove or convert debug prints to proper logging with appropriate log levels.

---

### AIT-016: Create TooltipProvider Protocol

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P2 (Medium) |
| **Owner** | UI Guardian |
| **Status** | Open |
| **Effort** | Medium |

**Description:**

Following the AvG principle and the success of OverlayProvider, create a TooltipProvider protocol for widgets that need to display tooltips. This generalizes tooltip handling rather than implementing it per-widget.

**Resolution:** Create TooltipProvider protocol with:
1. `get_tooltip_text()` method
2. `get_tooltip_position()` method
3. UIManager registration and rendering of tooltip providers

---

### AIT-017: Implement on_focus_lost() for Dropdown

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P2 (Medium) |
| **Owner** | Input Guardian |
| **Status** | Open |
| **Effort** | Small |

**Description:**

Dropdown widgets do not implement `on_focus_lost()`, which means they may not properly close or clean up state when focus moves to another widget. This is part of the incomplete focus management adoption identified in the audit.

**Resolution:** Implement `on_focus_lost()` for all Dropdown widgets to:
1. Close the dropdown menu if open
2. Reset any transient selection state
3. Clear hover states

---

### AIT-018: Generalize Focus Acquisition (Not Hardcoded)

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P2 (Medium) |
| **Owner** | Input Guardian |
| **Status** | Open |
| **Effort** | Medium |

**Description:**

Focus acquisition logic contains hardcoded widget type checks rather than using a generalized protocol. This violates the AvG principle and makes adding new focusable widgets more difficult.

**Resolution:**
1. Ensure all focusable widgets implement `wants_focus()` consistently
2. Remove any isinstance() checks in focus management code
3. Use the centralized `focused_element` tracking in Session as documented

---

## Priority 3 - Backlog

These items are deferred and will be addressed as time permits.

---

### AIT-019: Consider Physics Extraction to PhysicsProxy

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P3 (Backlog) |
| **Owner** | Sketch Guardian |
| **Status** | Open |
| **Effort** | Large |

**Description:**

The presence of physics properties (velocity, force_accum, dynamic, mass) in `model/geometry.py` could potentially be extracted to a separate PhysicsProxy pattern. However, the Senate voted 4-2 that the current "Skin & Bone" coupling pattern is an Accepted Architectural Decision.

**Resolution:** Deferred. Current design is acceptable. Revisit if physics requirements significantly change or if the coupling creates maintenance burden.

---

### AIT-020: Parallel Tether Force Kernel

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P3 (Backlog) |
| **Owner** | Sim Guardian |
| **Status** | Open |
| **Effort** | Medium |

**Description:**

The tether force calculation could be parallelized for better performance with large numbers of tethered atoms. This is a performance optimization that becomes relevant at high particle counts.

**Resolution:** Implement parallel Numba kernel for tether force calculations when performance profiling indicates this is a bottleneck.

---

### AIT-021: Add Serializable Protocol

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P3 (Backlog) |
| **Owner** | Generalizer |
| **Status** | Open |
| **Effort** | Medium |

**Description:**

Create a Serializable protocol to standardize how objects are converted to/from persistent format. This would provide consistency and type safety for save/load operations.

**Resolution:** Create Serializable protocol with `to_dict()` and `from_dict()` methods. Apply to entities, constraints, and other serialized objects.

---

### AIT-022: Add Constrainable Protocol

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P3 (Backlog) |
| **Owner** | Sketch Guardian |
| **Status** | Open |
| **Effort** | Medium |

**Description:**

Create a Constrainable protocol for objects that can participate in the constraint solver. This formalizes the interface expected by the solver and enables better type checking.

**Resolution:** Define Constrainable protocol with methods for constraint participation. Apply to geometric entities.

---

### AIT-023: Graph-Coloring for Parallel Force Loop

| Field | Value |
|-------|-------|
| **Creation Date** | 2025-12-31 |
| **Priority** | P3 (Backlog) |
| **Owner** | Sim Guardian |
| **Status** | Open |
| **Effort** | Large |

**Description:**

Implement graph-coloring algorithm to identify independent constraint groups that can be solved in parallel. This is an advanced optimization for scaling to very large simulations.

**Resolution:** Research and implement graph-coloring approach for parallel constraint solving. This is a significant architectural change that should only be pursued when scaling requirements demand it.

---

## Appendix: Status Definitions

| Status | Meaning |
|--------|---------|
| Open | Work has not started |
| In Progress | Work is actively being done |
| Blocked | Work cannot proceed due to dependency |
| In Review | Implementation complete, pending review |
| Closed | Work is complete and verified |

## Appendix: Priority Definitions

| Priority | SLA | Definition |
|----------|-----|------------|
| P0 (Critical) | Block Release | Must be fixed before any release can proceed |
| P1 (High) | This Sprint | Should be completed in current sprint |
| P2 (Medium) | Next Sprint | Target for next sprint planning |
| P3 (Backlog) | As Time Permits | Deferred, address when capacity allows |

## Appendix: Effort Definitions

| Effort | Definition |
|--------|------------|
| Trivial | < 30 minutes, single file change |
| Small | 1-2 hours, few files affected |
| Medium | Half day to full day, moderate scope |
| Large | Multiple days, significant scope or complexity |

---

*This document is maintained by the Secretary of the Senate of Guardians.*
*All changes must be tracked with date and reason.*
