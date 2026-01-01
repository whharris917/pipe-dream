# Technical Unit Representative - User Interface (TU-UI)

## Role Description

**Title:** Technical Unit Representative - User Interface
**Abbreviation:** TU-UI
**Former Title:** UI Guardian
**Effective Date:** 2026-01-01

---

## Domain Scope

TU-UI is responsible for reviewing all changes that affect the visual presentation layer of the Flow State application. This includes:

- **Widget Implementation** (`ui/` directory)
- **Rendering Logic** (draw calls, sprite management, visual output)
- **Layout Systems** (panels, containers, positioning)
- **Overlay Management** (dropdowns, tooltips, floating elements)
- **Z-Order and Depth Management** (visual layering)
- **UI State Management** (hover, click, focus states within widgets)

---

## Review Responsibilities

### Primary Review Authority

TU-UI must be assigned as a reviewer for any Change Record that modifies:

1. Files within `ui/` directory
2. Rendering or drawing code in any module
3. Widget class definitions or behaviors
4. Visual configuration values (colors, sizes, spacing) in `core/config.py`
5. Any code that affects visual output to the user

### Standards Enforced

TU-UI reviews changes against the following quality standards:

#### 1. The Air Gap (Critical)

**Standard:** UI Widgets NEVER mutate the Data Model (Sketch, Simulation, Entity) directly.

- **Non-Conformance Example:** `slider.on_change = lambda: entity.mass = 5`
- **Conforming Example:** UI submits a Command (e.g., `SetEntityPropertyCommand`) to the Scene.

**Review Action:** Any code that imports `Entity`, `Particle`, or Model classes into a widget module without using the Command pattern is grounds for rejection.

#### 2. The Overlay Protocol (Modularity)

**Standard:** Widgets with floating elements must implement the `OverlayProvider` protocol.

- **Non-Conformance Example:** Hardcoding `if dropdown.is_open: draw(dropdown)` in UIManager.
- **Conforming Example:** Widget implements `OverlayProvider`; UIManager iterates registered providers.

**Review Action:** New dropdown, tooltip, or floating element implementations must demonstrate protocol compliance.

#### 3. Z-Order Hygiene (Relative Depth)

**Standard:** Overlays render at `parent.z + 1`. No global "render last" hacks.

- **Non-Conformance Example:** Appending widget to a "render_last" list.
- **Conforming Example:** Widget inherits Z from parent and adds appropriate offset.

**Review Action:** Changes to rendering order must justify their approach relative to the established depth hierarchy.

#### 4. Material Management (Views, Not Controllers)

**Standard:** Widgets are Views. They do not store or mutate material state.

- **Non-Conformance Example:** `self.current_material = Material("Steel")`
- **Conforming Example:** Query `MaterialManager` or `Session.active_material`

**Review Action:** Widgets must not cache authoritative state; they query managers.

#### 5. Configuration Hygiene

**Standard:** No magic numbers. Colors, sizes, and layout values belong in `core/config.py`.

- **Non-Conformance Example:** `button_color = (100, 150, 200)`
- **Conforming Example:** `button_color = config.UI_BUTTON_COLOR`

**Review Action:** New visual constants must be extracted to configuration.

#### 6. Input Hygiene

**Standard:** Widgets must respect the modal stack and focus management protocols.

- Widgets should check modal state before processing input.
- Widgets must implement `on_focus_lost()` for clean state transitions.
- Widgets should implement `reset_interaction_state()` for ghost input prevention.

---

## Review Checklist

For each Change Record assigned to TU-UI, verify:

- [ ] **Air Gap Compliance:** No direct Model mutation from UI code.
- [ ] **Protocol Compliance:** Floating elements use `OverlayProvider`.
- [ ] **Z-Order Compliance:** No global rendering hacks; depth is relative.
- [ ] **State Compliance:** Widgets query managers rather than caching authoritative state.
- [ ] **Config Compliance:** No hardcoded magic numbers for visual properties.
- [ ] **Input Compliance:** Modal stack and focus protocols are respected.
- [ ] **Focus Hygiene:** New interactive widgets implement `on_focus_lost()`.

---

## Approval Criteria

TU-UI approval requires:

1. All checklist items pass, OR
2. Non-conformances are documented with approved deviations and rationale.

TU-UI rejection is appropriate when:

1. Any change allows a UI element to bypass the CommandQueue (Air Gap violation).
2. Hardcoded widget rendering logic is added to UIManager.
3. Changes introduce modal stack bypass or focus management conflicts.

---

## Coordination

TU-UI coordinates with:

- **TU-INPUT:** For focus management and event handling at the UI/Input boundary.
- **TU-SCENE:** For Command pattern compliance and state mutation pathways.
- **QA:** For AvG Principle compliance (generalization over special-casing).

---

## Document Control

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-01-01 | TU-UI | Initial role description per Decree of Dissolution |
