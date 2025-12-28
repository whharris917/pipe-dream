Here is a comprehensive technical overview of the Flow State project.

---

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

* **Sketch:** Stores entities and constraints.
* **Simulation:** Stores particle arrays and physics logic.
* **Compiler:** A one-way bridge that translates Sketch geometry into Simulation atoms.
* **ProcessObjects:** Dynamic entities like Emitters (Sources) or Drains (Sinks) that bridge the two domains.
* **CommandQueue:** Manages Undo/Redo operations specifically for CAD actions.

### 2.3 The Session (`core/session.py`)

While the `Scene` holds the persistent data (what is saved to disk), the `Session` holds the **transient application state**. This includes:

* Current Camera view (Pan/Zoom).
* Active Tool (Brush, Line, Select).
* Selection state (highlighted entities).
* Editor modes (Paused/Playing, Show/Hide Constraints).

---

## 3. Core Systems Detail

### 3.1 The Sketch (CAD Engine)

Located in `model/sketch.py`, the Sketch maintains a list of vector entities and geometric constraints.

* **Entities:** `Line`, `Circle`, `Point`.
* **Constraints:** Defined in `model/constraints.py`. Includes `Length`, `EqualLength`, `Angle`, `Parallel`, `Perpendicular`, `Coincident`.
* **Solver:** The application uses an iterative geometric solver (`model/solver.py`) to satisfy constraints when entities are moved.

### 3.2 The Simulation (Physics Engine)

Located in `engine/simulation.py`, the physics engine is designed for performance using NumPy arrays.

* **Data Structure:** Particles are stored in flat, contiguous arrays (`pos_x`, `pos_y`, `vel_x`, `vel_y`) rather than object instances. This is a Data-Oriented Design (DOD) approach.
* **Integration:** Uses a Verlet integration step with spatial hashing (Neighbor Lists) for collision detection.
* **Numba Optimization:** The system is designed to use Numba JIT compilation for high-performance physics loops.

### 3.3 The Compiler (The Bridge)

The `Compiler` (`engine/compiler.py`) is responsible for the transition from CAD to Physics.

1. **Input:** Reads vector data from the `Sketch`.
2. **Process:** Discretizes lines and curves into individual static particles ("atoms").
3. **Output:** Writes these atoms into the `is_static` arrays of the `Simulation`.
4. **Rebuild:** When CAD geometry changes, the `Scene` triggers `compiler.rebuild()` to refresh the physics representation.

---

## 4. UI & Input Management

The project employs a custom UI framework and an explicit input handling chain.

### 4.1 Hierarchical UI Tree (`ui/ui_manager.py`)

The UI is not immediate mode; it is a retained object tree. The `UIManager` constructs a hierarchy:

1. **Root Container**
2. **Menu Bar** (File, Edit, etc.)
3. **Middle Region**
* *Left Panel:* Physics controls (Sliders for Gravity, Time Step).
* *SceneViewport:* The rendering area for the game world.
* *Right Panel:* Editor tools (Brush, Line, Constraint buttons).


4. **Status Bar**: Footer information.

The `SceneViewport` class acts as a UI widget that captures mouse events specifically for the simulation/editor view.

### 4.2 Input Chain of Responsibility (`ui/input_handler.py`)

Input is handled via a strict 4-layer protocol to ensure events are consumed by the correct system. The `InputHandler` processes events in this order:

1. **System Layer:** `QUIT`, `VIDEORESIZE`.
2. **Global Layer:** Hotkeys (e.g., `Ctrl+Z` for Undo, `B` for Brush).
3. **Modal Layer:** Context Menus, Property Dialogs (blocks lower layers).
4. **HUD Layer:** Passes events to the UI Tree (which eventually reaches the `SceneViewport`).

---

## 5. File Formats & I/O

The system supports two distinct file types, managed by `core/scene.py` and `core/file_io.py`.

### 5.1 `.mdl` (Model File)

* **Scope:** Contains **only** the Sketch (Entities, Constraints, Materials).
* **Use Case:** Saving reusable components or geometry snippets.
* **Structure:** JSON serialization of `scene.sketch`.

### 5.2 `.scn` (Scene File)

* **Scope:** The full state. Includes the Sketch, the compiled Simulation state (particles), Process Objects, and View state (Camera).
* **Use Case:** Saving the exact state of a simulation or project.
* **Structure:** JSON wrapper containing `sketch`, `simulation`, `process_objects`, and `view` blocks.

---

## 6. The Orchestration Loop

The main application loop (`FlowStateApp.run`) delegates to `FlowStateApp.update_physics`, which calls `Scene.update`. The order of operations in a single frame is critical:

1. **Drivers:** Update animated constraints (e.g., motors).
2. **Solver:** Solve geometric constraints to position lines/circles.
3. **Rebuild:** If geometry moved, recompile static atoms.
4. **Process Objects:** Run logic for Sources/Emitters (spawn particles).
5. **Physics Step:** Run the integration for dynamic particles.

---

## 7. Developer Cheatsheet

| Component | File Path | Responsibility |
| --- | --- | --- |
| **Orchestrator** | `core/scene.py` | Owns Sketch/Sim, manages updates & I/O. |
| **CAD Data** | `model/sketch.py` | Geometric entities & constraints. |
| **Physics Data** | `engine/simulation.py` | Particle arrays & integration. |
| **UI Builder** | `ui/ui_manager.py` | Layouts, panels, and widget tree. |
| **Input** | `ui/input_handler.py` | Event routing & hotkeys. |
| **Entry** | `main.py` | CLI args & App bootstrapping. |

*Welcome to the codebase. Please ensure any changes to geometry logic are reflected in the Compiler to maintain synchronization with the physics engine.*