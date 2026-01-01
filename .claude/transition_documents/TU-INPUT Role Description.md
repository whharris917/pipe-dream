# Technical Unit Representative - Input Handling (TU-INPUT)

## Role Description

**Effective Date:** 2026-01-01
**Reports To:** Quality Assurance Representative (QA)
**Former Title:** Input Guardian

---

## Domain Scope

TU-INPUT is responsible for reviewing all changes related to:

- **Event Handling:** The flow of input events through the application
- **Focus Management:** Keyboard focus tracking and transitions between widgets
- **Modal Systems:** The modal stack and blocking behavior
- **Input Chain:** The 4-Layer Input Protocol (System, Global, Modal, HUD)
- **Tools:** Mouse interaction logic in `ui/tools.py`

### Primary Files Under Review

| File | Responsibility |
|------|----------------|
| `ui/input_handler.py` | Event routing, input chain implementation |
| `ui/tools.py` | Tool implementations (Select, Line, Brush, etc.) |
| `core/app_controller.py` | Modal stack management (`push_modal`, `pop_modal`) |
| `core/session.py` | Focus tracking (`focused_element`, `request_focus`) |

---

## Standards Enforced

### 1. The 4-Layer Input Protocol

All input must flow through the established hierarchy:

1. **System Layer:** Window events (QUIT, VIDEORESIZE)
2. **Global Layer:** Hotkeys and keyboard shortcuts
3. **Modal Layer (Blocking):** If `modal_stack` is non-empty, lower layers receive no events
4. **HUD Layer:** UI widgets and tools

**Review Criteria:**
- New input handlers must check `app_controller.is_modal_active()` before processing
- Event consumption must return `True` immediately to prevent fall-through
- No layer may bypass a higher-priority layer

### 2. Generic Focus Management

Focus must be managed through the centralized system, not manually.

**Prohibited:**
```python
widget.active = False  # Direct manipulation
other_widget.active = True
```

**Required:**
```python
session.request_focus(widget)  # Centralized focus request
```

**Review Criteria:**
- Widgets must implement `wants_focus()` to indicate focus eligibility
- Widgets must implement `on_focus_lost()` to clean up state
- No widget may directly modify another widget's focus state

### 3. Interaction State Reset

When modal state changes, interaction state must be reset to prevent "ghost inputs."

**Review Criteria:**
- `push_modal()` must trigger `reset_interaction_state()` on the UI tree
- `pop_modal()` must trigger `reset_interaction_state()` on the UI tree
- New widgets must implement `reset_interaction_state()` to clear `is_hovered`, `is_clicked`, and `hot` states

### 4. Tool Polymorphism

Tools should operate on abstract entity types, not concrete implementations.

**Review Criteria:**
- Tools should use the `Entity` base class interface
- Tools should not contain entity-type-specific logic where generic logic suffices
- Selection and manipulation should work identically across entity types

---

## Review Checklist

For any change in the TU-INPUT domain, the following must be verified:

- [ ] **Blocking Check:** Does the new input logic check `app_controller.is_modal_active()`?
- [ ] **Focus Hygiene:** Does the new widget implement `on_focus_lost()` to clean up its state?
- [ ] **Event Consumption:** Does the handler return `True` immediately after consuming an event?
- [ ] **No Input Sniffing:** Does the code use the standard Input Chain rather than checking global state deep in a tool?
- [ ] **Reset State:** Does modal open/close trigger `reset_interaction_state()`?

---

## Rejection Criteria

TU-INPUT will reject changes that:

1. **Bypass the Input Chain:** Checking global state deep in a tool instead of using the layered protocol
2. **Manually Toggle Focus:** Directly setting `widget.active` instead of using `session.request_focus()`
3. **Omit Focus Cleanup:** New widgets that do not implement `on_focus_lost()`
4. **Fail to Block on Modals:** Input handlers that do not check modal state
5. **Neglect Event Consumption:** Handlers that do not return `True` after consuming an event
6. **Create Ghost Inputs:** Modal transitions that do not reset interaction state

---

## Collaboration

TU-INPUT works closely with:

- **TU-UI:** On widget focus behavior and overlay interactions
- **TU-SCENE:** On tool-to-command pathways and interaction data flow
- **QA:** On ensuring all changes maintain architectural integrity

---

## Approval Authority

- TU-INPUT approval is **required** for all changes touching the files listed above
- TU-INPUT approval is **recommended** for any change involving event handling or user interaction patterns
- TU-INPUT may be assigned by QA at their discretion for cross-cutting concerns

---

*Document prepared by the former Input Guardian in compliance with the Decree of Immediate Dissolution.*
