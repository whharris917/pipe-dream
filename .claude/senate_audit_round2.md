# Senate of Guardians: Consolidated Round 2 Cross-Review

**Subject:** Comprehensive Codebase Audit of Flow State
**Date:** 2025-12-31
**Session Type:** Special Session - Full Codebase Audit
**Round:** 2 of 3

---

## Executive Summary

Round 2 cross-review is complete. All six Guardians have reviewed findings outside their domains and provided positions on the 5 key questions. This document consolidates the emerging consensus and identifies remaining points of contention for Round 3 resolution.

---

## PART I: EMERGING CONSENSUS

### Unanimous Agreement

The following items have **unanimous Guardian agreement**:

| Issue | Consensus Position | Vote |
|-------|-------------------|------|
| Air Gap Integrity | STRICT ENFORCEMENT - No exceptions | 6-0 |
| SelectTool.cancel() | MUST USE Scene.discard() pattern | 6-0 |
| MaterialPropertyWidget | MUST USE SetEntityMaterialCommand | 6-0 |
| pop_modal() Reset | MUST ADD reset_interaction_state() | 6-0 |
| GeometricEntity Protocol | USE typing.Protocol (not ABC) | 6-0 |
| Magic Numbers | EXTRACT ALL to config.py | 6-0 |
| Import Operations | SHOULD BE UNDOABLE | 6-0 |
| Numba Parity | WARN USERS (don't delay availability) | 6-0 |

### Strong Majority Agreement (5-1)

| Issue | Majority Position | Dissent |
|-------|-------------------|---------|
| Physics in Geometry | ACCEPTABLE for two-way coupling | Sketch Guardian (extraction preferred) |
| BrushTool Inheritance | SHOULD inherit from Tool base | Sketch Guardian (abstain - outside domain) |

---

## PART II: ANSWERS TO THE 5 QUESTIONS (Round 2 Tally)

### Q1: SelectTool.cancel() Pattern

**CONSENSUS: Formalize discard_pending() / Scene.discard() mechanism**

| Guardian | Vote | Rationale |
|----------|------|-----------|
| UI Guardian | discard_pending() | "If it touches the Model, it goes through the Scene" |
| Input Guardian | Scene.discard() | "Current pattern violates Air Gap" |
| Scene Guardian | discard_pending() | "Infrastructure already exists (LineTool uses it)" |
| Sketch Guardian | discard_pending() | "Solver coherence requires formal pattern" |
| Sim Guardian | discard_pending() | "Pattern should trigger rebuild() and sync" |
| Generalizer | Scene.discard() | "LineTool already does this correctly" |

**Resolution:** Use `Scene.discard()` for canceling non-historized commands. SelectTool should follow the same pattern as LineTool.

---

### Q2: GeometricEntity Protocol

**CONSENSUS: typing.Protocol (NOT ABC)**

**Required Methods (Consolidated from all Guardians):**

```python
from typing import Protocol, Optional, List, Tuple
import numpy as np

class GeometricEntity(Protocol):
    # Core Identity
    material_id: str
    entity_type: int  # 0=LINE, 1=CIRCLE, 2=POINT

    # Point Access (Unanimous)
    def get_point(self, index: int) -> np.ndarray: ...
    def set_point(self, index: int, pos: np.ndarray) -> None: ...
    def get_point_count(self) -> int: ...
    def get_inv_mass(self, index: int) -> float: ...

    # Geometry Manipulation (Unanimous)
    def move(self, dx: float, dy: float, indices: Optional[List[int]] = None) -> None: ...
    def get_center_of_mass(self) -> Tuple[float, float]: ...
    def get_bounds(self) -> Tuple[float, float, float, float]: ...

    # Serialization (Unanimous)
    def to_dict(self) -> dict: ...

    # Physics Flags (Sim Guardian, Sketch Guardian)
    physical: bool
    dynamic: bool
```

**Additional Protocols Proposed:**
- `Serializable` - for `to_dict()` / `from_dict()`
- `Constrainable` - for constraint participation
- `RigidBody` - for dynamic physics entities

**Location:** Create `model/protocols.py`

---

### Q3: Numba Parity

**CONSENSUS: WARN USERS, DO NOT DELAY AVAILABILITY**

| Guardian | Vote | Additional Notes |
|----------|------|------------------|
| UI Guardian | Warn | "Display warning icon next to unsupported constraints" |
| Input Guardian | Warn | "Status bar message on F9 toggle" |
| Scene Guardian | Warn | "Commands store absolute snapshots anyway" |
| Sketch Guardian | Warn | "Partial Numba is better than no Numba" |
| Sim Guardian | Warn | "Physics Numba is feature-complete" |
| Generalizer | Warn | "Silent degradation is a bug" |

**Implementation Plan:**
1. When F9 toggles Numba ON, check constraint types in scene
2. If unsupported constraints exist, display: "Numba mode: PERPENDICULAR, ANGLE, RADIUS, MIDPOINT constraints will use legacy solver"
3. Consider hybrid mode: Numba for supported, fallback for unsupported

---

### Q4: Physics in Geometry

**MAJORITY: ACCEPTABLE for Two-Way Coupling (5-1)**

| Guardian | Vote | Rationale |
|----------|------|-----------|
| UI Guardian | Acceptable | "Condition: Physics methods only called from engine/" |
| Input Guardian | Extract | "Tools should not encounter physics fields" |
| Scene Guardian | Acceptable | "Required for orchestration loop Step 4" |
| Sketch Guardian | Extract | "Violates domain sovereignty" |
| Sim Guardian | Acceptable | "This IS the Skin & Bone pattern" |
| Generalizer | Acceptable (Deferred) | "Technical debt, not violation. Priority 3" |

**Resolution:** Accept current implementation as intentional design for two-way coupling. Document as architectural decision. Consider future extraction to PhysicsProxy pattern as Priority 3 (Backlog).

---

### Q5: Import Operations

**CONSENSUS: IMPORTS SHOULD BE UNDOABLE**

| Guardian | Vote | Implementation Suggestion |
|----------|------|---------------------------|
| UI Guardian | Yes | "Wrap in CompositeCommand" |
| Input Guardian | Yes | "Full undo of import removes all imported entities" |
| Scene Guardian | Yes | "Create ImportModelCommand" |
| Sketch Guardian | Yes | "Command stores before/after state" |
| Sim Guardian | Yes | "Import should be single atomic command" |
| Generalizer | Yes | "CompositeCommand wrapping all additions" |

**Implementation:** Create `ImportModelCommand` that captures before-state and can fully revert the import operation.

---

## PART III: GUARDIAN DISAGREEMENTS

### Disagreement 1: Physics in Geometry Extraction Priority

**Sketch Guardian Position:** Physics concepts in `geometry.py` are a Domain Sovereignty Violation. Should be extracted to `RigidBodyState` or `PhysicsProxy`.

**Majority Position:** This is intentional two-way coupling, documented in CLAUDE.md Section 5.4 ("Skin & Bone"). The entity MUST have physics state for dynamic simulation.

**Resolution for Round 3:** Vote on whether to classify as:
- (A) Accepted Architectural Decision (no action)
- (B) Technical Debt (document, defer to backlog)
- (C) Priority Refactor (address this sprint)

---

### Disagreement 2: Priority of pop_modal() Reset

**Input Guardian Position:** Should be Priority 0 (Critical) - ghost inputs are data corruption risk.

**Round 1 Report:** Listed as Priority 1 (This Sprint).

**Resolution for Round 3:** Vote on priority level.

---

### Disagreement 3: Scene Guardian Self-Correction

The Scene Guardian in Round 2 noted that Round 1's "commit methods bypass dirty flags" finding was incorrect - the Scene wrapper handles dirty flags properly. This finding should be removed.

**Resolution:** Remove from findings list.

---

## PART IV: PRIORITIZED ACTION ITEMS (Updated)

### Priority 0: Critical (Block Release)

| # | Issue | Owner | Consensus |
|---|-------|-------|-----------|
| 1 | SelectTool.cancel() - Use Scene.discard() | Scene Guardian | UNANIMOUS |
| 2 | MaterialPropertyWidget - Use SetEntityMaterialCommand | UI Guardian | UNANIMOUS |
| 3 | pop_modal() - Add reset_interaction_state() | Input Guardian | UNANIMOUS |
| 4 | Convert physics Python loops to Numba | Sim Guardian | 5-0 (1 abstain) |

### Priority 1: High (This Sprint)

| # | Issue | Owner | Consensus |
|---|-------|-------|-----------|
| 5 | Create GeometricEntity Protocol | Generalizer | UNANIMOUS |
| 6 | Implement missing Numba constraints (5 types) | Sketch Guardian | 5-0 |
| 7 | Add Numba warning on F9 toggle | Input Guardian | UNANIMOUS |
| 8 | Extract magic numbers to config.py | All | UNANIMOUS |
| 9 | Create ImportModelCommand for undoable imports | Scene Guardian | UNANIMOUS |

### Priority 2: Medium (Next Sprint)

| # | Issue | Owner | Consensus |
|---|-------|-------|-----------|
| 10 | MenuBar implement OverlayProvider | UI Guardian | 5-0 |
| 11 | Dialog classes inherit from UIElement | UI Guardian | 5-0 |
| 12 | Deprecate MoveEntityCommand (use absolute snapshots) | Scene Guardian | 5-0 |
| 13 | Standardize epsilon constants | Sketch Guardian | UNANIMOUS |
| 14 | BrushTool inherit from Tool base | Input Guardian | 4-1 |
| 15 | Remove debug print from _resize_arrays() | Sim Guardian | UNANIMOUS |

### Priority 3: Low (Backlog)

| # | Issue | Owner | Consensus |
|---|-------|-------|-----------|
| 16 | Create TooltipProvider protocol | UI Guardian | 4-0 |
| 17 | Parallel tether force kernel | Sim Guardian | 3-0 |
| 18 | Add Serializable protocol | Generalizer | 4-0 |
| 19 | Consider physics extraction to PhysicsProxy | Sketch Guardian | 2-4 (deferred) |
| 20 | Focus acquisition hardcoded to MaterialPropertyWidget | Input Guardian | 3-0 |

---

## PART V: CROSS-DOMAIN INSIGHTS

### Insight 1: The discard() Pattern Already Exists

The Generalizer and Scene Guardian both noted that `Scene.discard()` and `CommandQueue.discard()` already exist and are used correctly by `LineTool`. The issue is not missing infrastructure but **inconsistent adoption**. SelectTool should simply follow the established pattern.

### Insight 2: Two-Way Coupling is Intentional

Multiple Guardians (Scene, Sim, Generalizer) confirmed that physics properties in `geometry.py` are part of the documented "Skin & Bone" architecture for dynamic entities. This is not a violation but an architectural decision that enables rigid body simulation.

### Insight 3: Protocol Replaces 82 isinstance() Checks

The Generalizer identified 82 `isinstance()` occurrences. The GeometricEntity Protocol would eliminate the majority of these, significantly improving extensibility and maintainability.

### Insight 4: Numba Has Two Separate Concerns

- **Solver Numba** (CAD): Missing 5 constraint types - user-facing warning needed
- **Physics Numba** (Engine): Feature-complete - no issues

These are independent concerns. Physics performance should not be gated by solver completeness.

---

## PART VI: ROUND 3 VOTING AGENDA

The following items require final votes in Round 3:

### Vote 1: Physics in Geometry Classification
- (A) Accepted Architectural Decision
- (B) Technical Debt (document, backlog)
- (C) Priority Refactor (this sprint)

### Vote 2: pop_modal() Reset Priority
- (A) Priority 0 (Critical)
- (B) Priority 1 (This Sprint)

### Vote 3: Final Report Approval
- All Guardians must vote APPROVE or REJECT with conditions

---

## Round 3 Instructions

This is the final round. All Guardians are requested to:

1. **Cast final votes** on the two outstanding items
2. **Review the Priority 0 items** and confirm agreement
3. **Approve or Reject** the final consensus report
4. **Add any final comments** for the record

The Secretary will compile all Round 3 votes into the final "Consensus Report on the State of the Flow State Codebase."

---

*Document compiled by: The Secretary of the Senate*
*Round 2 Complete - Awaiting Round 3 Final Votes*
