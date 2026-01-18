# SDLC-FLOW Design Specification (DS)

| Document ID | SDLC-FLOW-DS |
|-------------|--------------|
| Version | 1.0 |
| Status | Draft |
| Effective Date | TBD |
| Author | Claude (AI Assistant) |
| Approver | TBD |
| Related RS | SDLC-FLOW-RS v1.0 |

---

## 1. Purpose and Scope

This Design Specification (DS) describes the architectural design and implementation details for **Flow State**. It provides the technical blueprint for satisfying the requirements defined in SDLC-FLOW-RS.

### 1.1 Document Scope

This document covers:
- System architecture and component relationships
- Module designs for each Technical Unit domain
- Interface specifications
- Data structures and state management
- Design patterns and their application

### 1.2 Notation

- **Bold**: Module or class names
- `Monospace`: Code elements, methods, properties
- *Italic*: Design concepts or patterns

---

## 2. System Architecture

### 2.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                        │
│  FlowStateApp (Bootstrapper) → Creates all subsystems           │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      UI LAYER (TU-UI)                           │
│  UIManager, InputHandler, Tools, Session                        │
│  ─────────────────────────────────────────────────────────────  │
│  Receives: FlowStateApp via injection                           │
│  Accesses: Scene (read), Commands (write)                       │
└─────────────────────────────────────────────────────────────────┘
                                  │
                          ToolContext (Facade)
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER (TU-SCENE)                 │
│  Scene, CommandQueue, Commands                                  │
│  ─────────────────────────────────────────────────────────────  │
│  Owns: Sketch, Simulation, Compiler, ProcessObjects             │
│  Provides: execute(), undo(), redo()                            │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│   SKETCH DOMAIN (TU-SKETCH)   │ │     SIM DOMAIN (TU-SIM)       │
│   Sketch, Solver, Geometry    │ │   Simulation, PhysicsCore     │
│   ───────────────────────────-│ │   ─────────────────────────── │
│   Pure domain logic           │ │   Pure domain logic           │
│   No external dependencies    │ │   No external dependencies    │
└───────────────────────────────┘ └───────────────────────────────┘
                    │                           ▲
                    └──────── Compiler ─────────┘
                           (one-way bridge)
```

### 2.2 Dependency Flow

| From | To | Mechanism | Direction |
|------|----|-----------|-----------|
| UI Layer | Scene | ToolContext facade | Read + Command |
| Scene | Sketch | Direct ownership | Create/Own |
| Scene | Simulation | Direct ownership | Create/Own |
| Compiler | Sketch | Constructor injection | Read-only |
| Compiler | Simulation | Constructor injection | Write |
| Tools | Session | ToolContext | Read/Write |

### 2.3 The Air Gap

```
┌─────────────────────┐          ┌─────────────────────┐
│      UI LAYER       │          │     DATA MODEL      │
│  (Tools, Widgets)   │          │  (Sketch, Sim)      │
│                     │          │                     │
│  ┌───────────────┐  │          │  ┌───────────────┐  │
│  │ User Action   │──┼── CMD ──►│  │ State Change  │  │
│  └───────────────┘  │          │  └───────────────┘  │
│                     │          │                     │
│  ┌───────────────┐  │          │  ┌───────────────┐  │
│  │ Display       │◄─┼── READ ──│  │ Current State │  │
│  └───────────────┘  │          │  └───────────────┘  │
└─────────────────────┘          └─────────────────────┘
         │                                  ▲
         │         ╔═══════════════╗        │
         └────────►║  COMMAND BUS  ║────────┘
                   ╚═══════════════╝
                   (scene.execute())
```

---

## 3. Module Designs

### 3.1 Sketch Domain (TU-SKETCH)

#### 3.1.1 Module: `model/sketch.py`

**Purpose**: Container for geometric entities and constraints.

**Class: Sketch**
```python
class Sketch:
    entities: Dict[int, Entity]      # All geometric entities by ID
    constraints: List[Constraint]    # Active constraints
    next_id: int                     # Entity ID generator

    def add_entity(entity: Entity) -> int
    def remove_entity(entity_id: int) -> None
    def get_entity(entity_id: int) -> Optional[Entity]
    def add_constraint(constraint: Constraint) -> None
    def remove_constraint(constraint: Constraint) -> None
```

**Design Rationale**: Sketch is a passive data container. It stores but does not process. All modifications flow through Commands.

#### 3.1.2 Module: `model/geometry.py`

**Purpose**: Geometric entity definitions.

**Class Hierarchy**:
```
Entity (Abstract)
├── Point
│   └── position: Tuple[float, float]
├── Line
│   ├── start: Tuple[float, float]
│   ├── end: Tuple[float, float]
│   └── rotation: float
└── Circle
    ├── center: Tuple[float, float]
    └── radius: float
```

**Key Properties**:
- `id`: Unique identifier within Sketch
- `material`: Reference to material properties
- `is_static`: Whether entity participates in physics

#### 3.1.3 Module: `model/solver.py`

**Purpose**: Position-Based Dynamics constraint solver.

**Class: Solver**
```python
class Solver:
    backend: str                     # "python" or "numba"
    iterations: int                  # Solver iterations per frame

    def solve(sketch: Sketch, interaction_data: Optional[InteractionData]) -> None
    def set_backend(backend: str) -> None
```

**Algorithm**:
1. Collect constraint projections
2. For each iteration:
   - Project each constraint
   - Apply position corrections
3. If interaction_data present:
   - Treat mouse as infinite-mass target
   - Apply interaction constraint

#### 3.1.4 Module: `model/solver_kernels.py`

**Purpose**: Numba-optimized constraint projection functions.

**Key Functions**:
```python
@njit
def project_distance(p1: ndarray, p2: ndarray, target: float) -> Tuple[ndarray, ndarray]

@njit
def project_anchor(p: ndarray, anchor: ndarray) -> ndarray

@njit
def project_parallel(line1: ndarray, line2: ndarray) -> Tuple[ndarray, ndarray]
```

**Design Rationale**: Hot-path math is isolated in pure functions compatible with Numba JIT. No Python objects, only NumPy arrays.

#### 3.1.5 Module: `model/constraints.py`

**Purpose**: Constraint type definitions.

**Class Hierarchy**:
```
Constraint (Abstract)
├── AnchorConstraint
│   └── entity_id, point_index, anchor_position
├── LengthConstraint
│   └── entity_id, target_length
├── ParallelConstraint
│   └── entity1_id, entity2_id
├── PerpendicularConstraint
│   └── entity1_id, entity2_id
└── EqualLengthConstraint
    └── master_id, follower_id
```

---

### 3.2 Simulation Domain (TU-SIM)

#### 3.2.1 Module: `engine/simulation.py`

**Purpose**: Particle simulation container and integrator.

**Class: Simulation**
```python
class Simulation:
    # Structure of Arrays (SoA)
    positions: ndarray      # Shape: (max_particles, 2)
    velocities: ndarray     # Shape: (max_particles, 2)
    masses: ndarray         # Shape: (max_particles,)
    materials: ndarray      # Shape: (max_particles,)
    is_static: ndarray      # Shape: (max_particles,)
    is_active: ndarray      # Shape: (max_particles,)

    particle_count: int
    max_particles: int

    def step(dt: float) -> None
    def add_particle(pos, vel, mass, material) -> int
    def remove_particle(index: int) -> None
    def get_particles_in_region(rect: Tuple) -> ndarray
```

**Design Rationale**: SoA layout enables cache-efficient iteration and Numba vectorization. No particle objects—only arrays.

#### 3.2.2 Module: `engine/physics_core.py`

**Purpose**: Physics integration kernels.

**Key Functions**:
```python
@njit
def integrate_verlet(positions: ndarray, velocities: ndarray,
                     forces: ndarray, dt: float) -> None

@njit
def apply_gravity(velocities: ndarray, gravity: float, dt: float) -> None

@njit
def resolve_collisions(positions: ndarray, velocities: ndarray,
                       grid: SpatialHash) -> None
```

#### 3.2.3 Module: `engine/compiler.py`

**Purpose**: Bridge from Sketch geometry to Simulation particles.

**Class: Compiler**
```python
class Compiler:
    sketch: Sketch          # Injected read-only reference
    simulation: Simulation  # Injected write reference
    atom_spacing: float     # Discretization resolution

    def rebuild() -> None
    def discretize_line(line: Line) -> ndarray
    def discretize_circle(circle: Circle) -> ndarray
```

**Algorithm**:
1. Clear all static particles from Simulation
2. For each entity in Sketch:
   - Discretize into point samples
   - Add as static particles to Simulation
3. Update spatial hash

**Design Rationale**: One-way data flow. Compiler reads Sketch, writes Simulation. Simulation never references Sketch.

#### 3.2.4 Module: `engine/particle_brush.py`

**Purpose**: User-controlled particle spawning.

**Class: ParticleBrush**
```python
class ParticleBrush:
    simulation: Simulation
    radius: float
    rate: int               # Particles per frame

    def paint(position: Tuple[float, float], material: int) -> None
```

---

### 3.3 Orchestration (TU-SCENE)

#### 3.3.1 Module: `core/scene.py`

**Purpose**: Document root and subsystem orchestrator.

**Class: Scene**
```python
class Scene:
    sketch: Sketch
    simulation: Simulation
    compiler: Compiler
    process_objects: ProcessObjectManager
    command_queue: CommandQueue

    def update(dt: float, interaction_data: Optional[InteractionData]) -> None
    def execute(command: Command) -> None
    def undo() -> None
    def redo() -> None
    def save(path: str) -> None
    def load(path: str) -> None
```

**Update Loop** (REQ-SCENE-004):
```python
def update(self, dt, interaction_data):
    # 1. Update Drivers
    self.process_objects.update(dt)

    # 2. Snapshot for change detection
    pre_snapshot = self.sketch.snapshot()

    # 3. Solver Step
    self.sketch.solver.solve(self.sketch, interaction_data)

    # 4. Rebuild if geometry changed
    if self.sketch.snapshot() != pre_snapshot:
        self.compiler.rebuild()

    # 5. Physics Step
    self.simulation.step(dt)
```

#### 3.3.2 Module: `core/commands.py`

**Purpose**: Command definitions for all mutations.

**Base Class**:
```python
class Command(ABC):
    historize: bool = True

    @abstractmethod
    def execute(self) -> None

    @abstractmethod
    def undo(self) -> None
```

**Key Commands**:

| Command | Purpose | Undo Strategy |
|---------|---------|---------------|
| `AddEntityCommand` | Create entity | Remove entity |
| `RemoveEntityCommand` | Delete entity | Restore entity snapshot |
| `SetEntityGeometryCommand` | Move/resize | Store before/after positions |
| `AddConstraintCommand` | Add constraint | Remove constraint |
| `RemoveConstraintCommand` | Remove constraint | Restore constraint |

**Geometry Command Design** (REQ-SCENE-002):
```python
class SetEntityGeometryCommand(Command):
    def __init__(self, entity_id, new_geometry):
        self.entity_id = entity_id
        self.new_geometry = new_geometry
        self.old_geometry = None  # Captured on first execute

    def execute(self):
        entity = self.sketch.get_entity(self.entity_id)
        if self.old_geometry is None:
            self.old_geometry = entity.snapshot()
        entity.apply_geometry(self.new_geometry)

    def undo(self):
        entity = self.sketch.get_entity(self.entity_id)
        entity.apply_geometry(self.old_geometry)
```

#### 3.3.3 Module: `core/command_base.py`

**Purpose**: Command infrastructure.

**Class: CommandQueue**
```python
class CommandQueue:
    history: List[Command]
    redo_stack: List[Command]
    max_history: int

    def execute(command: Command) -> None
    def undo() -> Optional[Command]
    def redo() -> Optional[Command]
    def clear() -> None
```

---

### 3.4 User Interface (TU-UI)

#### 3.4.1 Module: `core/tool_context.py`

**Purpose**: Facade providing controlled access to application state.

**Class: ToolContext**
```python
class ToolContext:
    _app: FlowStateApp      # Private reference

    @property
    def session(self) -> Session

    @property
    def scene(self) -> Scene

    @property
    def sketch(self) -> Sketch

    @property
    def simulation(self) -> Simulation

    def execute(self, command: Command) -> None
    def screen_to_world(self, pos: Tuple) -> Tuple
    def world_to_screen(self, pos: Tuple) -> Tuple
```

**Design Rationale** (REQ-UI-002): Tools receive ToolContext, not FlowStateApp. This narrows the interface and enforces the Air Gap—tools cannot accidentally access internal app state.

#### 3.4.2 Module: `core/session.py`

**Purpose**: Transient application state.

**Class: Session**
```python
class Session:
    camera: CameraController
    selection: SelectionManager
    constraint_builder: ConstraintBuilder
    status_bar: StatusBar
    active_tool: Tool
    active_material: int
    focused_element: Optional[Widget]
```

**Design Rationale**: Session holds UI state that is NOT saved to disk. Camera position, current selection, and active tool are transient concerns.

#### 3.4.3 Module: `ui/tools.py`

**Purpose**: User interaction tools.

**Base Class**:
```python
class Tool(ABC):
    ctx: ToolContext
    name: str

    def __init__(self, ctx: ToolContext, name: str):
        self._app = ctx._app
        self.ctx = ctx
        self.name = name

    @abstractmethod
    def on_mouse_down(self, pos: Tuple, button: int) -> bool

    @abstractmethod
    def on_mouse_up(self, pos: Tuple, button: int) -> bool

    @abstractmethod
    def on_mouse_move(self, pos: Tuple) -> bool

    @abstractmethod
    def draw(self, surface: Surface) -> None
```

**Tool Implementations**:

| Tool | Purpose | Commands Used |
|------|---------|---------------|
| `SelectTool` | Select, drag entities | `SetEntityGeometryCommand` |
| `LineTool` | Create lines | `AddEntityCommand` |
| `CircleTool` | Create circles | `AddEntityCommand` |
| `BrushTool` | Paint particles | Direct simulation access (transient) |

#### 3.4.4 Module: `ui/input_handler.py`

**Purpose**: Event routing through 4-layer protocol.

**Class: InputHandler**
```python
class InputHandler:
    app: FlowStateApp

    def handle_event(self, event: Event) -> bool:
        # Layer 1: System
        if self._handle_system(event):
            return True

        # Layer 2: Global Hotkeys
        if self._handle_global(event):
            return True

        # Layer 3: Modal
        if self.app.controller.modal_stack:
            return self._handle_modal(event)

        # Layer 4: HUD/Tools
        return self._handle_hud(event)
```

#### 3.4.5 Module: `ui/ui_manager.py`

**Purpose**: Widget tree management and rendering.

**Class: UIManager**
```python
class UIManager:
    root: Container
    overlay_providers: List[OverlayProvider]

    def update(self) -> None
    def draw(self, surface: Surface) -> None:
        # Draw main tree
        self.root.draw(surface)

        # Draw overlays (correct Z-order)
        for provider in self.overlay_providers:
            provider.draw_overlay(surface)

    def reset_interaction_state(self) -> None:
        self.root.reset_interaction_state_recursive()
```

---

## 4. Design Patterns

### 4.1 Command Pattern

**Intent**: Encapsulate mutations as objects for undo/redo and history.

**Participants**:
- `Command`: Abstract base with execute/undo
- `ConcreteCommand`: Specific mutation (e.g., `AddEntityCommand`)
- `CommandQueue`: Invoker managing history
- `Scene`: Receiver executing commands

**Sequence**:
```
Tool → Command → Scene.execute() → CommandQueue.push() → Command.execute()
```

### 4.2 Facade Pattern

**Intent**: Provide simplified interface to complex subsystem.

**Application**: `ToolContext` facades `FlowStateApp`:
- Hides internal app structure
- Exposes only what tools need
- Enforces read-only access patterns

### 4.3 Observer Pattern

**Intent**: Notify dependents of state changes.

**Application**: Constraint change detection:
- Solver snapshots constraint state before iteration
- Compares after iteration
- Triggers rebuild if changed

### 4.4 Protocol Pattern

**Intent**: Define interfaces without inheritance coupling.

**Applications**:
- `OverlayProvider`: Widgets that spawn floating elements
- `Drawable`: Entities that can render themselves
- `Constrainable`: Entities that participate in solving

---

## 5. Data Structures

### 5.1 Entity Geometry

```python
@dataclass
class LineGeometry:
    start: Tuple[float, float]
    end: Tuple[float, float]
    rotation: float

@dataclass
class CircleGeometry:
    center: Tuple[float, float]
    radius: float
```

### 5.2 Interaction Data

```python
@dataclass
class InteractionData:
    target_position: Tuple[float, float]
    entity_id: int
    handle_parameter: float  # 0.0 = start, 1.0 = end, 0.5 = midpoint
```

### 5.3 Particle Arrays (SoA)

| Array | Shape | Type | Description |
|-------|-------|------|-------------|
| `positions` | (N, 2) | float64 | World coordinates |
| `velocities` | (N, 2) | float64 | Velocity vectors |
| `masses` | (N,) | float64 | Particle mass |
| `materials` | (N,) | int32 | Material index |
| `is_static` | (N,) | bool | Static flag |
| `is_active` | (N,) | bool | Alive flag |

---

## 6. Interface Specifications

### 6.1 Tool Interface

All tools must implement:

```python
class Tool(Protocol):
    ctx: ToolContext
    name: str

    def on_mouse_down(self, pos: Tuple[int, int], button: int) -> bool: ...
    def on_mouse_up(self, pos: Tuple[int, int], button: int) -> bool: ...
    def on_mouse_move(self, pos: Tuple[int, int]) -> bool: ...
    def on_key_down(self, key: int, mods: int) -> bool: ...
    def draw(self, surface: Surface) -> None: ...
    def reset(self) -> None: ...
```

### 6.2 Widget Interface

All widgets must implement:

```python
class Widget(Protocol):
    rect: Rect
    is_visible: bool

    def update(self) -> None: ...
    def draw(self, surface: Surface) -> None: ...
    def handle_event(self, event: Event) -> bool: ...
    def wants_focus(self) -> bool: ...
    def on_focus_lost(self) -> None: ...
    def reset_interaction_state(self) -> None: ...
```

### 6.3 Overlay Provider Interface

```python
class OverlayProvider(Protocol):
    def has_overlay(self) -> bool: ...
    def draw_overlay(self, surface: Surface) -> None: ...
```

---

## 7. Traceability Matrix

| Requirement | Design Section | Implementation |
|-------------|----------------|----------------|
| REQ-SKETCH-001 | 3.1.2 | `model/geometry.py` |
| REQ-SKETCH-002 | 3.1.5 | `model/constraints.py` |
| REQ-SKETCH-003 | 3.1.3, 3.1.4 | `model/solver.py`, `solver_kernels.py` |
| REQ-SKETCH-004 | 2.1 | Architecture enforces separation |
| REQ-SKETCH-005 | 3.1.3 | Solver interaction_data handling |
| REQ-SIM-001 | 3.2.1 | `engine/simulation.py` SoA design |
| REQ-SIM-002 | 3.2.2 | `engine/physics_core.py` |
| REQ-SIM-003 | 3.2.1, 3.2.2 | NumPy arrays, Numba kernels |
| REQ-SIM-004 | 3.2.3 | `engine/compiler.py` |
| REQ-SIM-005 | 3.3.1 | `ProcessObjectManager` |
| REQ-SCENE-001 | 3.3.1 | `core/scene.py` |
| REQ-SCENE-002 | 3.3.2 | `core/commands.py` |
| REQ-SCENE-003 | 2.3 | Air Gap architecture |
| REQ-SCENE-004 | 3.3.1 | Scene.update() order |
| REQ-SCENE-005 | 3.3.1 | Scene.save()/load() |
| REQ-UI-001 | 3.4.3 | `ui/tools.py` |
| REQ-UI-002 | 3.4.1 | `core/tool_context.py` |
| REQ-UI-003 | 3.4.4 | `ui/input_handler.py` |
| REQ-UI-004 | 3.4.2 | Session.focused_element |
| REQ-UI-005 | 3.4.5 | `ui/ui_manager.py` |
| REQ-UI-006 | 3.4.3 | Tool batch operation logic |

---

## 8. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | Claude | Initial draft |

---

*End of Document*
