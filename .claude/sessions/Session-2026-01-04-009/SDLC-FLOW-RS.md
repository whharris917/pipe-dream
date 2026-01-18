# RS-001: Flow State Requirements Specification

| Document ID | RS-001 |
|-------------|--------|
| Version | 2.0 |
| Status | Draft |
| Effective Date | TBD |

---

## 1. Purpose and Scope

This Requirements Specification defines the functional and non-functional requirements for **Flow State** (codenamed *Pipe Dream*), a hybrid interactive application combining a Geometric Constraint Solver (CAD) with a Particle-Based Physics Engine.

### 1.1 Document Scope

This document covers:
- Functional requirements organized by domain
- Non-functional requirements (performance, architecture, testability)
- Verification type for each requirement (Unit Test or Qualitative Proof)

### 1.2 Verification Types

Each requirement specifies how it will be verified:

| Type | Description |
|------|-------------|
| **Unit Test** | Automated, reproducible test script |
| **Qualitative Proof** | Intelligent analysis (AI, human, or both) documented in RTM |

### 1.3 Requirement Categories

| Category | Domain |
|----------|--------|
| REQ-SKETCH | Geometric entities, constraints, solver |
| REQ-SIM | Particle physics, integration, data structures |
| REQ-SCENE | Orchestration, command pattern, state management |
| REQ-UI | Tools, widgets, input handling, focus |
| REQ-ARCH | Architectural constraints, separation of concerns |
| REQ-PERF | Performance requirements |
| REQ-TEST | Testability requirements |

---

## 2. System Overview

Flow State consists of two primary domains operating under strict separation of concerns:

1. **Sketch Domain (CAD)**: High-level vector geometry, constraints, and materials
2. **Simulation Domain (Physics)**: Low-level particle arrays with no knowledge of high-level geometry

The Compiler serves as a one-way bridge from Sketch to Simulation.

---

## 3. Sketch Domain Requirements (REQ-SKETCH)

### REQ-SKETCH-001: Geometric Entities

The system shall support the following geometric entity types:
- Lines (defined by two endpoints)
- Circles (defined by center and radius)
- Points (discrete positions)

| Attribute | Value |
|-----------|-------|
| Category | REQ-SKETCH |
| Verification Type | Unit Test |

---

### REQ-SKETCH-002: Geometric Constraints

The system shall support the following constraint types:
- **Positional**: Anchor (fix point in space)
- **Dimensional**: Length, Radius
- **Relational**: Parallel, Perpendicular, Tangent, Coincident
- **Equality**: Equal Length, Equal Radius

| Attribute | Value |
|-----------|-------|
| Category | REQ-SKETCH |
| Verification Type | Unit Test |

---

### REQ-SKETCH-003: Constraint Solver

The system shall use Position-Based Dynamics (PBD) to satisfy geometric constraints:
- Iterative projection method
- Support for both Python (legacy) and Numba (optimized) backends
- Runtime backend switching (F9 hotkey)

| Attribute | Value |
|-----------|-------|
| Category | REQ-SKETCH |
| Verification Type | Unit Test |

---

### REQ-SKETCH-004: Interaction Constraints

The system shall treat mouse cursor position as a temporary constraint target during drag operations, enabling physical behaviors like torque and rotation while maintaining cursor responsiveness.

| Attribute | Value |
|-----------|-------|
| Category | REQ-SKETCH |
| Verification Type | Unit Test |

---

## 4. Simulation Domain Requirements (REQ-SIM)

### REQ-SIM-001: Particle Representation

The simulation shall represent all physical entities as particles stored in flat NumPy arrays:
- Position arrays (x, y)
- Velocity arrays (vx, vy)
- Property arrays (mass, material, is_static)

| Attribute | Value |
|-----------|-------|
| Category | REQ-SIM |
| Verification Type | Unit Test |

---

### REQ-SIM-002: Physics Integration

The system shall use Verlet integration for particle dynamics with:
- Configurable timestep
- Gravity and external forces
- Spatial hashing for collision detection

| Attribute | Value |
|-----------|-------|
| Category | REQ-SIM |
| Verification Type | Unit Test |

---

### REQ-SIM-003: Data-Oriented Design

All physics kernels shall follow Data-Oriented Design principles:
- Structure of Arrays (SoA) memory layout
- Numba JIT compilation for performance
- No Python object overhead in hot paths

| Attribute | Value |
|-----------|-------|
| Category | REQ-SIM |
| Verification Type | Qualitative Proof |

---

### REQ-SIM-004: Static Geometry

Static geometry (walls, obstacles) shall be represented as particles with `is_static=True`, populated by the Compiler from Sketch geometry.

| Attribute | Value |
|-----------|-------|
| Category | REQ-SIM |
| Verification Type | Unit Test |

---

### REQ-SIM-005: Particle Sources and Sinks

The system shall support dynamic Process Objects:
- **Sources (Emitters)**: Spawn particles at configurable rates
- **Sinks (Drains)**: Remove particles that enter their region

| Attribute | Value |
|-----------|-------|
| Category | REQ-SIM |
| Verification Type | Unit Test |

---

## 5. Orchestration Requirements (REQ-SCENE)

### REQ-SCENE-001: Scene as Single Source of Truth

The Scene class shall serve as the root container for all document state:
- Sketch (geometry and constraints)
- Simulation (particle arrays)
- Compiler (geometry-to-physics bridge)
- ProcessObjects (sources, sinks)
- CommandQueue (mutation history)

| Attribute | Value |
|-----------|-------|
| Category | REQ-SCENE |
| Verification Type | Qualitative Proof |

---

### REQ-SCENE-002: Command Pattern

All mutations to persistent state shall flow through the Command system:
- Commands implement `execute()` and `undo()`
- Commands are recorded in history for undo/redo
- The `historize` flag controls whether a command enters the stack

| Attribute | Value |
|-----------|-------|
| Category | REQ-SCENE |
| Verification Type | Unit Test |

---

### REQ-SCENE-003: Orchestration Loop Order

The Scene update loop shall execute in this order:
1. Update Drivers (animation, motors)
2. Snapshot (detect constraint changes)
3. Solver Step (geometric constraints + interaction)
4. Rebuild (recompile if geometry changed)
5. Physics Step (particle integration)

| Attribute | Value |
|-----------|-------|
| Category | REQ-SCENE |
| Verification Type | Qualitative Proof |

---

### REQ-SCENE-004: File I/O

The system shall support saving and loading scenes:
- Serialize Sketch geometry and constraints
- Serialize Process Object configurations
- Simulation state is transient (not persisted)

| Attribute | Value |
|-----------|-------|
| Category | REQ-SCENE |
| Verification Type | Unit Test |

---

## 6. User Interface Requirements (REQ-UI)

### REQ-UI-001: Tool System

The system shall provide tools for user interaction:
- **SelectTool**: Select and manipulate entities
- **LineTool**: Create line geometry
- **CircleTool**: Create circle geometry
- **BrushTool**: Paint particles into simulation

| Attribute | Value |
|-----------|-------|
| Category | REQ-UI |
| Verification Type | Unit Test |

---

### REQ-UI-002: ToolContext Facade

All tools shall access application state through ToolContext:
- `ctx.session` - Camera, selection, transient state
- `ctx.scene` - Document state (read-only queries)
- `ctx.execute(cmd)` - Submit commands for execution
- Tools shall not access FlowStateApp directly

| Attribute | Value |
|-----------|-------|
| Category | REQ-UI |
| Verification Type | Qualitative Proof |

---

### REQ-UI-003: Input Handling Protocol

Input events shall flow through a 4-layer protocol:
1. **System Layer**: Window events (quit, resize)
2. **Global Layer**: Hotkeys (Ctrl+Z, tool switches)
3. **Modal Layer**: Blocking dialogs (modal stack)
4. **HUD Layer**: UI widgets with generic focus

| Attribute | Value |
|-----------|-------|
| Category | REQ-UI |
| Verification Type | Qualitative Proof |

---

### REQ-UI-004: Focus Management

The system shall track a single focused element:
- Widgets declare `wants_focus()` based on hover/click
- Focus transitions trigger `on_focus_lost()` on previous widget
- Modal stack changes reset all interaction state

| Attribute | Value |
|-----------|-------|
| Category | REQ-UI |
| Verification Type | Unit Test |

---

### REQ-UI-005: Widget Tree

The UI shall be organized as a hierarchical tree:
- Root -> Panels -> Widgets -> Elements
- Overlays render after main tree (correct Z-ordering)
- OverlayProvider protocol for dropdowns, tooltips

| Attribute | Value |
|-----------|-------|
| Category | REQ-UI |
| Verification Type | Qualitative Proof |

---

### REQ-UI-006: Batch Operations

Constraint tools shall support batch operations:
- **Unary constraints** (H, V, Fix): Apply to all selected entities
- **Binary constraints** (Equal, Parallel): First selection is master, subsequent are followers

| Attribute | Value |
|-----------|-------|
| Category | REQ-UI |
| Verification Type | Unit Test |

---

## 7. Architecture Requirements (REQ-ARCH)

### REQ-ARCH-001: Domain Isolation

The Sketch domain shall have no knowledge of or dependency on the Simulation domain. Information flows one-way: Sketch → Compiler → Simulation.

| Attribute | Value |
|-----------|-------|
| Category | REQ-ARCH |
| Verification Type | Qualitative Proof |

---

### REQ-ARCH-002: Air Gap Enforcement

The UI layer shall never directly mutate the Data Model:
- All modifications via `scene.execute(command)`
- Transient state (camera, selection) may be modified directly
- Violations constitute critical defects

| Attribute | Value |
|-----------|-------|
| Category | REQ-ARCH |
| Verification Type | Qualitative Proof |

---

### REQ-ARCH-003: Domain Separation

Code shall maintain strict separation between:
- Sketch and Simulation domains
- UI and Data Model (Air Gap)
- Transient and Persistent state

| Attribute | Value |
|-----------|-------|
| Category | REQ-ARCH |
| Verification Type | Qualitative Proof |

---

### REQ-ARCH-004: Protocol-Based Design

Cross-cutting concerns shall use protocols:
- `OverlayProvider` for floating UI elements
- `Drawable` for renderable entities
- `Constrainable` for solver-managed entities

| Attribute | Value |
|-----------|-------|
| Category | REQ-ARCH |
| Verification Type | Qualitative Proof |

---

### REQ-ARCH-005: Configuration Externalization

Magic numbers and strings shall be extracted to `core/config.py`.

| Attribute | Value |
|-----------|-------|
| Category | REQ-ARCH |
| Verification Type | Qualitative Proof |

---

### REQ-ARCH-006: Technology Stack

The system shall use the following technology stack:

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Graphics | Pygame |
| Numerics | NumPy |
| Optimization | Numba JIT |
| Serialization | JSON |

| Attribute | Value |
|-----------|-------|
| Category | REQ-ARCH |
| Verification Type | Qualitative Proof |

---

## 8. Performance Requirements (REQ-PERF)

### REQ-PERF-001: Solver Performance

The Numba solver backend shall achieve:
- 60 FPS with up to 50 constraints
- Sub-frame latency for interaction response

| Attribute | Value |
|-----------|-------|
| Category | REQ-PERF |
| Verification Type | Unit Test |

---

### REQ-PERF-002: Simulation Performance

The physics engine shall achieve:
- 60 FPS with up to 10,000 active particles
- Numba-compiled kernels for all hot paths

| Attribute | Value |
|-----------|-------|
| Category | REQ-PERF |
| Verification Type | Unit Test |

---

### REQ-PERF-003: UI Responsiveness

The UI shall remain responsive during:
- Solver iterations
- Physics simulation
- File I/O operations

| Attribute | Value |
|-----------|-------|
| Category | REQ-PERF |
| Verification Type | Unit Test |

---

## 9. Testability Requirements (REQ-TEST)

### REQ-TEST-001: Command Reversibility

All Commands shall have verifiable undo behavior:
- `execute()` followed by `undo()` restores prior state
- State comparison via snapshot or property check

| Attribute | Value |
|-----------|-------|
| Category | REQ-TEST |
| Verification Type | Unit Test |

---

### REQ-TEST-002: Solver Determinism

Given identical input, the solver shall produce identical output:
- No random number usage without seeding
- Consistent iteration order

| Attribute | Value |
|-----------|-------|
| Category | REQ-TEST |
| Verification Type | Unit Test |

---

## 10. Requirements Summary

| Category | Count | Unit Test | Qualitative Proof |
|----------|-------|-----------|-------------------|
| REQ-SKETCH | 4 | 4 | 0 |
| REQ-SIM | 5 | 4 | 1 |
| REQ-SCENE | 4 | 2 | 2 |
| REQ-UI | 6 | 3 | 3 |
| REQ-ARCH | 6 | 0 | 6 |
| REQ-PERF | 3 | 3 | 0 |
| REQ-TEST | 2 | 2 | 0 |
| **Total** | **30** | **18** | **12** |

---

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | Claude | Initial draft |
| 2.0 | 2026-01-04 | Claude | Restructured per RS model; added verification types; separated architecture requirements; removed TU ownership |

---

*End of Document*
