# SDLC-FLOW Requirements Specification (RS)

| Document ID | SDLC-FLOW-RS |
|-------------|--------------|
| Version | 1.0 |
| Status | Draft |
| Effective Date | TBD |
| Author | Claude (AI Assistant) |
| Approver | TBD |

---

## 1. Purpose and Scope

This Requirements Specification (RS) defines the functional and non-functional requirements for **Flow State** (codenamed *Pipe Dream*), a hybrid interactive application combining a Geometric Constraint Solver (CAD) with a Particle-Based Physics Engine.

### 1.1 Document Scope

This document covers:
- Functional requirements organized by Technical Unit (TU) domain
- Non-functional requirements (performance, maintainability, testability)
- Architectural constraints
- Traceability to design specifications

### 1.2 Audience

- Technical Unit Representatives (TU-SKETCH, TU-SIM, TU-SCENE, TU-UI)
- Quality Assurance
- Development team

---

## 2. System Overview

Flow State consists of two primary domains operating under strict separation of concerns:

1. **Sketch Domain (CAD)**: High-level vector geometry, constraints, and materials
2. **Simulation Domain (Physics)**: Low-level particle arrays with no knowledge of high-level geometry

The Compiler serves as a one-way bridge from Sketch to Simulation.

---

## 3. Functional Requirements

### 3.1 Sketch Domain (TU-SKETCH)

#### REQ-SKETCH-001: Geometric Entities
The system shall support the following geometric entity types:
- Lines (defined by two endpoints)
- Circles (defined by center and radius)
- Points (discrete positions)

#### REQ-SKETCH-002: Geometric Constraints
The system shall support the following constraint types:
- **Positional**: Anchor (fix point in space)
- **Dimensional**: Length, Radius
- **Relational**: Parallel, Perpendicular, Tangent, Coincident
- **Equality**: Equal Length, Equal Radius

#### REQ-SKETCH-003: Constraint Solver
The system shall use Position-Based Dynamics (PBD) to satisfy geometric constraints:
- Iterative projection method
- Support for both Python (legacy) and Numba (optimized) backends
- Runtime backend switching (F9 hotkey)

#### REQ-SKETCH-004: Domain Isolation
The Sketch domain shall have no knowledge of or dependency on the Simulation domain. Information flows one-way: Sketch -> Compiler -> Simulation.

#### REQ-SKETCH-005: Interaction Constraints
The system shall treat mouse cursor position as a temporary constraint target during drag operations, enabling physical behaviors like torque and rotation while maintaining cursor responsiveness.

---

### 3.2 Simulation Domain (TU-SIM)

#### REQ-SIM-001: Particle Representation
The simulation shall represent all physical entities as particles stored in flat NumPy arrays:
- Position arrays (x, y)
- Velocity arrays (vx, vy)
- Property arrays (mass, material, is_static)

#### REQ-SIM-002: Physics Integration
The system shall use Verlet integration for particle dynamics with:
- Configurable timestep
- Gravity and external forces
- Spatial hashing for collision detection

#### REQ-SIM-003: Data-Oriented Design
All physics kernels shall follow Data-Oriented Design principles:
- Structure of Arrays (SoA) memory layout
- Numba JIT compilation for performance
- No Python object overhead in hot paths

#### REQ-SIM-004: Static Geometry
Static geometry (walls, obstacles) shall be represented as particles with `is_static=True`, populated by the Compiler from Sketch geometry.

#### REQ-SIM-005: Particle Sources and Sinks
The system shall support dynamic Process Objects:
- **Sources (Emitters)**: Spawn particles at configurable rates
- **Sinks (Drains)**: Remove particles that enter their region

---

### 3.3 Orchestration (TU-SCENE)

#### REQ-SCENE-001: Scene as Single Source of Truth
The Scene class shall serve as the root container for all document state:
- Sketch (geometry and constraints)
- Simulation (particle arrays)
- Compiler (geometry-to-physics bridge)
- ProcessObjects (sources, sinks)
- CommandQueue (mutation history)

#### REQ-SCENE-002: Command Pattern
All mutations to persistent state shall flow through the Command system:
- Commands implement `execute()` and `undo()`
- Commands are recorded in history for undo/redo
- The `historize` flag controls whether a command enters the stack

#### REQ-SCENE-003: Air Gap Enforcement
The UI layer shall never directly mutate the Data Model:
- All modifications via `scene.execute(command)`
- Transient state (camera, selection) may be modified directly
- Violations constitute critical defects

#### REQ-SCENE-004: Orchestration Loop Order
The Scene update loop shall execute in this order:
1. Update Drivers (animation, motors)
2. Snapshot (detect constraint changes)
3. Solver Step (geometric constraints + interaction)
4. Rebuild (recompile if geometry changed)
5. Physics Step (particle integration)

#### REQ-SCENE-005: File I/O
The system shall support saving and loading scenes:
- Serialize Sketch geometry and constraints
- Serialize Process Object configurations
- Simulation state is transient (not persisted)

---

### 3.4 User Interface (TU-UI)

#### REQ-UI-001: Tool System
The system shall provide tools for user interaction:
- **SelectTool**: Select and manipulate entities
- **LineTool**: Create line geometry
- **CircleTool**: Create circle geometry
- **BrushTool**: Paint particles into simulation

#### REQ-UI-002: ToolContext Facade
All tools shall access application state through ToolContext:
- `ctx.session` - Camera, selection, transient state
- `ctx.scene` - Document state (read-only queries)
- `ctx.execute(cmd)` - Submit commands for execution
- Tools shall not access FlowStateApp directly

#### REQ-UI-003: Input Handling Protocol
Input events shall flow through a 4-layer protocol:
1. **System Layer**: Window events (quit, resize)
2. **Global Layer**: Hotkeys (Ctrl+Z, tool switches)
3. **Modal Layer**: Blocking dialogs (modal stack)
4. **HUD Layer**: UI widgets with generic focus

#### REQ-UI-004: Focus Management
The system shall track a single focused element:
- Widgets declare `wants_focus()` based on hover/click
- Focus transitions trigger `on_focus_lost()` on previous widget
- Modal stack changes reset all interaction state

#### REQ-UI-005: Widget Tree
The UI shall be organized as a hierarchical tree:
- Root -> Panels -> Widgets -> Elements
- Overlays render after main tree (correct Z-ordering)
- OverlayProvider protocol for dropdowns, tooltips

#### REQ-UI-006: Batch Operations
Constraint tools shall support batch operations:
- **Unary constraints** (H, V, Fix): Apply to all selected entities
- **Binary constraints** (Equal, Parallel): First selection is master, subsequent are followers

---

## 4. Non-Functional Requirements

### 4.1 Performance

#### REQ-PERF-001: Solver Performance
The Numba solver backend shall achieve:
- 60 FPS with up to 50 constraints
- Sub-frame latency for interaction response

#### REQ-PERF-002: Simulation Performance
The physics engine shall achieve:
- 60 FPS with up to 10,000 active particles
- Numba-compiled kernels for all hot paths

#### REQ-PERF-003: UI Responsiveness
The UI shall remain responsive during:
- Solver iterations
- Physics simulation
- File I/O operations

---

### 4.2 Maintainability

#### REQ-MAINT-001: Domain Separation
Code shall maintain strict separation between:
- Sketch and Simulation domains
- UI and Data Model (Air Gap)
- Transient and Persistent state

#### REQ-MAINT-002: Protocol-Based Design
Cross-cutting concerns shall use protocols:
- `OverlayProvider` for floating UI elements
- `Drawable` for renderable entities
- `Constrainable` for solver-managed entities

#### REQ-MAINT-003: Configuration Externalization
Magic numbers and strings shall be extracted to `core/config.py`.

---

### 4.3 Testability

#### REQ-TEST-001: Command Reversibility
All Commands shall have verifiable undo behavior:
- `execute()` followed by `undo()` restores prior state
- State comparison via snapshot or property check

#### REQ-TEST-002: Solver Determinism
Given identical input, the solver shall produce identical output:
- No random number usage without seeding
- Consistent iteration order

---

## 5. Architectural Constraints

### 5.1 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Graphics | Pygame |
| Numerics | NumPy |
| Optimization | Numba JIT |
| Serialization | JSON |

### 5.2 Design Patterns

| Pattern | Application |
|---------|-------------|
| Command | All persistent mutations |
| Facade | ToolContext for tool-app interface |
| Observer | Constraint change detection |
| Protocol | Cross-cutting behaviors |

---

## 6. Traceability

| Requirement | Design Section | TU Owner |
|-------------|----------------|----------|
| REQ-SKETCH-* | DS Section 3.1 | TU-SKETCH |
| REQ-SIM-* | DS Section 3.2 | TU-SIM |
| REQ-SCENE-* | DS Section 3.3 | TU-SCENE |
| REQ-UI-* | DS Section 3.4 | TU-UI |
| REQ-PERF-* | DS Section 4.1 | All TUs |
| REQ-MAINT-* | DS Section 4.2 | All TUs |
| REQ-TEST-* | DS Section 4.3 | QA |

---

## 7. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | Claude | Initial draft |

---

*End of Document*
