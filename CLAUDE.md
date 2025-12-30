# Flow State: Technical Architecture & Onboarding Guide

## 1. Project Overview

**Flow State** (codenamed *Pipe Dream*) is a hybrid interactive application that combines a **Geometric Constraint Solver (CAD)** with a **Particle-Based Physics Engine**.

The primary goal of the system is to allow users to design rigorous geometric structures (pipes, containers, funnels) using CAD tools, and then immediately "compile" that geometry into a physical simulation where fluid particles interact with the structures in real-time.

### Key Domains

The application is strictly divided into two distinct domains to maintain a Separation of Concerns (SoC):

1. **The Sketch (CAD Domain):** High-level vector geometry (lines, circles), logical constraints (parallel, perpendicular), and material properties.
2. **The Simulation (Physics Domain):** Low-level arrays of particle data (positions, velocities). It has **no knowledge** of high-level geometry.

---

## 2. High-Level Architecture

The application follows a custom architectural pattern centered around the **Scene Orchestrator**.

### 2.1 Entry Points (`main.py`)

The application is launched via `main.py`, which utilizes `argparse` to determine the execution mode. There are three distinct modes:

* **Dashboard:** The main menu/launcher GUI.
* **Simulation (`--mode sim`):** The primary gameplay mode where physics runs.
* **Builder (`--mode builder`):** A dedicated CAD editor mode for constructing geometry without active physics.

### 2.2 The Scene Pattern (`core/scene.py`)

The `Scene` class is the root container for the document state. It serves as the **Single Source of Truth** for the user's project. The Scene owns and orchestrates the interaction between the subsystems:

* **Sketch:** Stores entities (Lines, Circles) and constraints.
* **Simulation:** Stores particle arrays and physics logic.
* **Compiler:** A one-way bridge that translates Sketch geometry into Simulation atoms.
* **ProcessObjects:** Dynamic entities like Emitters (Sources) or Drains (Sinks).
* **CommandQueue:** The exclusive gatekeeper for modifying the Sketch or Simulation.

### 2.3 The Session (`core/session.py`)

While the `Scene` holds the persistent data (what is saved to disk), the `Session` holds the **transient application state**. This includes:

* Current Camera view (Pan/Zoom).
* Active Tool (Brush, Line, Select).
* Selection state (highlighted entities).
* **Interaction Data:** Live data for the constraint solver regarding mouse drag targets.

---

## 3. The Command Architecture & The "Air Gap"

To ensure stability, replayability, and reliable undo/redo, the application enforces a strict **Air Gap** between the UI and the Data Model.

### 3.1 The "Air Gap" Principle

The UI (Tools, Widgets, Inputs) is **strictly forbidden** from modifying the Data Model (`Sketch` or `Simulation`) directly.
* **Illegal:** `select_tool.py` directly setting `line.end_point = (10, 10)`.
* **Legal:** `select_tool.py` constructing a `SetEntityGeometryCommand` (or `SetPointCommand`) and submitting it to `scene.execute()`.

This separation ensures that no "sneaky" state changes occur without being recorded in the history stack.

### 3.2 The Command Pattern (`core/commands.py`)

The `Command` class is the atomic unit of change in the application. It serves as the primary history chronicle for the project.
* **Source of Truth:** The Command History is the ultimate authority.
* **Replayability:** Any tool that modifies the model without recording a Command breaks the chain of custody and is considered a critical bug.
* **Structure:** Every command implements:
    * `execute()`: Apply the mutation.
    * `undo()`: Revert the mutation exactly.
    * `historize`: A flag indicating if this command should be pushed to the stack (true) or is transient (false).

### 3.3 Physics vs. Geometry Undo

1.  **Geometric Undo (State Snapshots):**
    * Because the Solver introduces complex behavior (rotation, constraint satisfaction) that cannot be captured by simple deltas, geometric manipulation commands now store **Absolute State Snapshots** (start pos vs. end pos).
    * *Command:* `SetEntityGeometryCommand` restores the exact coordinates and rotation of entities, ensuring the solver's work is preserved/reverted perfectly.

2.  **Physics Undo (Time Travel):**
    * Fluid dynamics are irreversible.
    * *Strategy:* Commands that alter physics state rely on full **State Snapshots**. Undo reverts the scene to a specific point in time.

---

## 4. State Classification

To adhere to the Air Gap, developers must classify all data into one of two categories.

### 4.1 Persistent State ("The Vault") -> **Must Use Commands**
Data that constitutes the "Document."
* **Examples:** Entity coordinates, Constraints, Simulation Atoms.
* **Rule:** **Zero Trust.** No direct mutation allowed. Must flow through `scene.execute()`.

### 4.2 Transient State ("The Lobby") -> **Direct Access Allowed**
Data that describes *how the user is looking at* the document.
* **Examples:** Camera Zoom, Selection, Interaction Targets (Mouse Pos).
* **Rule:** Direct modification via Managers is acceptable.

---

## 5. Core Systems Detail

### 5.1 The Sketch & Solver (`model/sketch.py`, `model/solver.py`)

The CAD engine uses a **Position-Based Dynamics (PBD)** solver to enforce geometric rules.

* **Hybrid Architecture:** The solver has two backends:
    1.  **Legacy (Python):** OOP-based, easier to debug.
    2.  **Numba (Compiled):** High-performance JIT kernels (`model/solver_kernels.py`) operating on flat Numpy arrays.
* **Runtime Toggle:** Users can switch backends live (F9) to benchmark performance.

### 5.2 The Simulation (`engine/simulation.py`)

The particle engine uses Data-Oriented Design (DOD) with flat arrays.
* **Integration:** Verlet integration with spatial hashing.
* **Optimization:** Designed for Numba JIT compilation.

### 5.3 The Interaction Model (The "Servo")

We do not use "Forces" to move geometry with the mouse. We use **Interaction Constraints**.
* **Concept:** The Mouse Cursor is treated as a temporary constraint target with infinite mass.
* **The Loop:** Every frame, the `SelectTool` injects `interaction_data` (Target Pos, Handle Parameter `t`) into the solver.
* **Behavior:** The solver negotiates the Mouse position against geometric constraints (Length, Anchors). This allows for physical behaviors like **Torque** and **Rotation** (pivoting around an anchor) while maintaining 1:1 cursor responsiveness.

### 5.4 The Compiler (The Bridge)

The `Compiler` (`engine/compiler.py`) is responsible for the transition from CAD to Physics.

1. **Input:** Reads vector data from the `Sketch`.
2. **Process:** Discretizes lines and curves into individual static particles ("atoms").
3. **Output:** Writes these atoms into the `is_static` arrays of the `Simulation`.
4. **Rebuild:** When CAD geometry changes (via Command), the `Scene` triggers `compiler.rebuild()` to refresh the physics representation.

---

## 6. UI & Input Management

The project employs a custom UI framework and an explicit input handling chain.

### 6.1 Hierarchical UI Tree (`ui/ui_manager.py`)

The UI is not immediate mode; it is a retained object tree. The `UIManager` constructs a hierarchy:

1. **Root Container**
2. **Menu Bar** (File, Edit, etc.)
3. **Middle Region**
* *Left Panel:* Physics controls (Sliders for Gravity, Time Step).
* *SceneViewport:* The rendering area for the game world.
* *Right Panel:* Editor tools (Brush, Line, Constraint buttons).
4. **Status Bar**: Footer information.

The `SceneViewport` class acts as a UI widget that captures mouse events specifically for the simulation/editor view.

### 6.2 Input Chain of Responsibility (`ui/input_handler.py`)

Input is handled via a strict 4-layer protocol to ensure events are consumed by the correct system. The `InputHandler` processes events in this order:

1. **System Layer:** `QUIT`, `VIDEORESIZE`.
2. **Global Layer:** Hotkeys (e.g., `Ctrl+Z` for Undo, `B` for Brush).
3. **Modal Layer:** Context Menus, Property Dialogs (blocks lower layers).
4. **HUD Layer:** Passes events to the UI Tree (which eventually reaches the `SceneViewport`).

### 6.3 Smart Batching
Tools are designed to be "Polymorphic" and "Batch-Aware":
* **Unary (H/V/Fix):** Applies to *all* selected entities.
* **Binary (Equal/Parallel):** Treats the first selection as "Master" and subsequent selections as "Followers."

---

## 7. The Orchestration Loop

The order of operations in `Scene.update` is critical:

1.  **Update Drivers:** Animate motors or dynamic parameters.
2.  **Snapshot:** Capture constraint values to detect changes.
3.  **Solver Step:**
    * Inject `interaction_data` (Mouse) as a constraint.
    * Iterate `solver.solve()` (Geometric Constraints).
    * *Note:* Solver runs if constraints exist **OR** if user is interacting.
4.  **Rebuild:** If geometry changed, recompile static atoms for physics.
5.  **Physics Step:** Run the particle simulation integration.

---

## 8. Developer Cheatsheet

| Component | File Path | Responsibility |
| --- | --- | --- |
| **Command Factory** | `core/commands.py` | **CRITICAL:** The only legal way to mutate the Model. |
| **Orchestrator** | `core/scene.py` | Owns Sketch/Sim, manages updates & I/O. |
| **Solver (Bridge)** | `model/solver.py` | Manages constraints & calls kernels. |
| **Solver (Math)** | `model/solver_kernels.py` | Numba-optimized PBD math functions. |
| **CAD Data** | `model/sketch.py` | Geometric entities & constraints. |
| **Physics Data** | `engine/simulation.py` | Particle arrays & integration. |
| **UI Builder** | `ui/ui_manager.py` | Layouts, panels, and widget tree. |
| **Tools** | `ui/tools.py` | Mouse interaction logic (Select, Line, etc.). |

*Welcome to the codebase. Please ensure any changes to geometry logic are wrapped in Commands to maintain synchronization with the Undo Stack and the physics engine.*