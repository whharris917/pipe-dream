# Security Audit Report: Air Gap Between UI and Data Model

**Date:** 2025-12-28
**Audited Files:** `ui/tools.py`, `ui/input_handler.py`, `app/app_controller.py`, `core/session.py`

---

## Executive Summary

This audit examines the enforcement of the "Air Gap" between the UI layer and the Data Model, focusing on the Command Pattern implementation that ensures replayability of all model mutations.

**Core Philosophy:**
- Replayability is paramount: The source of truth is the Command History
- Physics is time-dependent: Physics undo uses state snapshots, not command reversal

**Findings:** 11 items identified
- 6 CRITICAL (breaks replayability)
- 1 Potential Issue
- 4 Safe/Transient

---

## CRITICAL Violations (Breaks Replayability)

### 1. SelectTool Commit Methods Bypass `scene.execute()`

**File:** `ui/tools.py:1006-1007, 1036-1038, 1052-1054, 1062-1064`

```python
# _commit_edit (line 1006-1007)
self.scene.commands.undo_stack.append(cmd)
self.scene.commands.redo_stack.clear()

# Same pattern in _commit_resize and _commit_move
```

**Issue:** Commands are appended directly to the undo stack instead of going through `scene.execute()`. This bypasses any rebuild/solve logic that `scene.execute()` may perform and breaks the contract that all changes flow through the orchestrator.

**Impact:** Command history exists but orchestrator hooks are skipped.

---

### 2. `toggle_extend` - Direct Entity Mutation Without Command

**File:** `app/app_controller.py:137-141`

```python
entity.infinite = not entity.infinite
self.scene.rebuild()
```

**Issue:** The `infinite` property is toggled directly on the entity. No command is recorded.

**Impact:** Cannot be undone. Not replayable.

---

### 3. `atomize_selected` - Direct Entity Mutation Without Command

**File:** `app/app_controller.py:171`

```python
self.sketch.update_entity(idx, physical=True)
```

**Issue:** Entity's `physical` property is modified directly. No command is recorded.

**Impact:** Cannot be undone. Not replayable.

---

### 4. `apply_material_from_dialog` - Direct Sketch Mutation Without Command

**File:** `app/app_controller.py:216, 226`

```python
self.sketch.add_material(mat)
# ...
self.sketch.update_entity(idx, material_id=mat.name)
```

**Issue:** Material is added and entities are updated directly. No command is recorded.

**Impact:** Cannot be undone. Not replayable.

---

### 5. `apply_animation_from_dialog` - Direct Driver Mutation Without Command

**File:** `app/app_controller.py:240`

```python
self.sketch.set_driver(self.ctx_vars['const'], dialog.get_values())
```

**Issue:** Constraint driver is set directly. No command is recorded.

**Impact:** Cannot be undone. Not replayable.

---

### 6. `handle_context_menu_action` (Anchor) - Direct Anchor Toggle Without Command

**File:** `app/app_controller.py:311`

```python
self.sketch.toggle_anchor(self.ctx_vars['wall'], self.ctx_vars['pt'])
```

**Issue:** Anchor state is toggled directly. No command is recorded.

**Impact:** Cannot be undone. Not replayable.

---

## Potential Issue

### 7. `action_clear_particles` - No Snapshot Before Clear

**File:** `app/app_controller.py:104-107`

```python
def action_clear_particles(self):
    self.sim.clear()
    self.scene.rebuild()
```

**Issue:** Particles are cleared without calling `sim.snapshot()` first. The clear operation cannot be undone. This may be intentional (destructive action), but breaks consistency with BrushTool which snapshots before every paint operation.

**Impact:** Cannot be undone. May be intentional design choice.

---

## Transient (Acceptable Visual Feedback)

### 8. SelectTool Drag Preview Commands (`historize=False`)

**File:** `ui/tools.py:919-925, 957-961, 970-980`

```python
cmd = SetPointCommand(..., historize=False)
cmd = SetCircleRadiusCommand(..., historize=False)
cmd = MoveEntityCommand(..., historize=False)
```

**Classification:** SAFE

These are transient preview commands during drag operations. The final commit uses `historize=True`. This is the documented "historize pattern" for drag feedback.

---

### 9. SelectTool Cancel - Direct State Restoration

**File:** `ui/tools.py:685-704`

```python
entity.set_point(self.target_pt, np.array(self.original_position))
entity.radius = self.original_radius
self.sketch.entities[idx].move(-self.total_dx, -self.total_dy)
```

**Classification:** SAFE

Cancel operations restore state to what it was BEFORE the uncommitted drag began. No command should be recorded for a cancelled operation.

---

## Safe (Correct Implementation)

### 10. BrushTool Physics Operations

**File:** `ui/tools.py:190-192, 217`

```python
self.app.sim.snapshot()  # Called before painting
self.brush.paint(wx, wy, self.brush_radius)
self.brush.erase(wx, wy, self.brush_radius)
```

**Classification:** SAFE

Physics operations correctly use the snapshot pattern for undo. The snapshot captures full particle state before modification, and `sim.undo()` restores that state. This aligns with the philosophy that physics cannot be mathematically reversed.

---

### 11. Geometry Tools (LineTool, RectTool, CircleTool, PointTool)

**File:** `ui/tools.py:316-612`

**Classification:** SAFE

All geometry creation tools use the supersede pattern correctly:
- Initial creation: `scene.execute(cmd)` with default `historize=True`
- Drag updates: `scene.execute(cmd)` with `supersede=True`
- Final release: `scene.execute(cmd)` with `supersede=True`
- Cancel: `scene.discard()` removes preview

---

## Summary Table

| # | Location | Operation | Classification |
|---|----------|-----------|----------------|
| 1 | `tools.py:1006` | Direct undo_stack manipulation | CRITICAL |
| 2 | `app_controller.py:139` | toggle_extend | CRITICAL |
| 3 | `app_controller.py:171` | atomize_selected | CRITICAL |
| 4 | `app_controller.py:216,226` | apply_material | CRITICAL |
| 5 | `app_controller.py:240` | apply_animation | CRITICAL |
| 6 | `app_controller.py:311` | toggle_anchor | CRITICAL |
| 7 | `app_controller.py:105` | clear_particles (no snapshot) | Potential Issue |
| 8 | `tools.py:919-980` | Drag preview (historize=False) | Transient/Safe |
| 9 | `tools.py:685-704` | Cancel state restoration | Safe |
| 10 | `tools.py:190,217` | BrushTool snapshot pattern | Safe |
| 11 | `tools.py:316-612` | Geometry tools supersede pattern | Safe |

---

## Recommendations

### High Priority

1. **Create Commands for Missing Operations:**
   - `ToggleExtendCommand` - for line infinite property
   - `AtomizeCommand` - for entity physical property
   - `SetMaterialCommand` - for material assignment
   - `SetDriverCommand` - for constraint animation drivers
   - `ToggleAnchorCommand` - for point anchor state

2. **Fix SelectTool Commit Methods:**
   Replace direct `undo_stack.append()` with proper `scene.execute()` calls, or create a dedicated "commit already-applied change" mechanism in the command queue that properly triggers orchestrator hooks.

### Medium Priority

3. **Consider `action_clear_particles`:**
   Either add a snapshot before clear to enable undo, or explicitly document that this is an intentional non-undoable destructive action (similar to "New Scene").

### Low Priority

4. **Audit Additional Files:**
   Consider extending this audit to other files that may interact with the sketch or simulation directly, such as file I/O handlers and any import/export functionality.

---

## Conclusion

The geometry creation tools and physics brush tool correctly implement the command/snapshot patterns. However, several editor actions in `AppController` bypass the command system entirely, breaking the replayability guarantee. The `SelectTool` commit methods also bypass `scene.execute()` which may skip important orchestration logic.

Addressing the 6 CRITICAL violations will restore full command history integrity and enable reliable undo/redo across all operations.
