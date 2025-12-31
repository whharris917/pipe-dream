# Flow State: Technical Architecture & Onboarding Guide

## 1. Project Overview & Philosophy

**Flow State** (codenamed *Pipe Dream*) is a hybrid interactive application that combines a **Geometric Constraint Solver (CAD)** with a **Particle-Based Physics Engine**.

### 1.1 The "Addition via Generalization" (AvG) Principle (Global SOP-001)
**Rule:** When fixing a bug or adding a feature, do not solve the *specific instance* of the problem. Solve the *general class* of the problem. 

#### The Philosophy
* **The Anti-Pattern:** "The text field in the 'Material Properties' dialog is not losing focus." -> *Fix:* Add a check in `MaterialDialog.update()` to un-focus that specific field.
* **The AvG Approach:** "Text fields in general lack a robust way to relinquish focus." -> *Fix:* Implement `on_focus_lost()` in the base `UIElement` class and have the global `InputHandler` manage focus transitions for *all* widgets.

#### Canonical Case Studies (Do This)
1.  **UI Modularity (The Overlay Protocol):**
    * *Problem:* The `UIManager` needed to render dropdowns from the Material Widget.
    * *Bad Fix:* Hardcoding `if material_widget.is_open: draw(material_widget)`.
    * *AvG Fix:* Created an `OverlayProvider` protocol. The `UIManager` now iterates over *any* registered overlay provider. New widgets get overlay support for free.

2.  **Input Handling (The Modal Stack):**
    * *Problem:* We needed to block input when the "Save File" dialog was open.
    * *Bad Fix:* Checking `if save_dialog.is_active or settings_dialog.is_active` in the input loop.
    * *AvG Fix:* Implemented a central `modal_stack` in `AppController`. Input is blocked whenever `modal_stack` is not empty.

3.  **Focus Management:**
    * *Problem:* Multiple widgets fighting for keyboard focus.
    * *Bad Fix:* Manually setting `widget.active = False` inside other widgets.
    * *AvG Fix:* Centralized `focused_element` tracking in `Session`. The `InputHandler` manages focus switching, and widgets implement `wants_focus()` and `on_focus_lost()` to handle their own state changes.

4.  **Interaction State (Stale Clicks):**
    * *Problem:* Buttons clicked just before a modal opened would sometimes re-trigger when it closed.
    * *Bad Fix:* Manually resetting the specific button's flag in the specific dialog's close logic.
    * *AvG Fix:* Implemented a recursive `reset_interaction_state()` on `UIContainer`. When *any* modal opens via `push_modal()`, the engine wipes the interaction state of the entire UI tree automatically.

5.  **Material Management (Single Source of Truth):**
    * *Problem:* Material definitions were scattered, with widgets directly mutating properties like color or mass.
    * *Bad Fix:* Hardcoding "Steel" properties into specific widgets and modifying `material.color` directly from the UI event loop.
    * *AvG Fix:* Implemented a centralized `MaterialManager`. The UI acts only as a view; it submits `MaterialModificationCommands` to the CommandQueue to request changes.

6.  **Rendering Hierarchy (Relative Z-Order):**
    * *Problem:* Dropdown menus were being clipped (hidden) by subsequent UI elements drawn later in the frame.
    * *Bad Fix:* A global hack to "render all dropdowns last" at the end of the `draw()` loop.
    * *AvG Fix:* Established a relative depth rule. Overlays are rendered with a Z-order of `parent.z + 1`. This solves the specific clipping issue by enforcing a general hierarchical rule rather than patching the render loop.

7.  **Configuration (The "No Magic Numbers" Rule):**
    * *Problem:* Physics constants and UI layout values were buried in local scripts.
    * *Bad Fix:* Manually hunting down every instance of `0.5` when tuning friction.
    * *AvG Fix:* All constants are extracted to `core/config.py`. The code now references `config.DEFAULT_FRICTION`, allowing global tuning.

---

### 1.2 Key Domains (Separation of Concerns)

The application is strictly divided into two distinct domains to maintain a Separation of Concerns (SoC):

1.  **The Sketch (CAD Domain):** High-level vector geometry (lines, circles), logical constraints (parallel, perpendicular), and material properties.
2.  **The Simulation (Physics Domain):** Low-level arrays of particle data (positions, velocities). It has **no knowledge** of high-level geometry.

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
* **Focused Element:** The specific UI widget currently capturing keyboard input.
* **Interaction Data:** Live data for the constraint solver regarding mouse drag targets.

---

## 3. The Command Architecture & The "Air Gap"

To ensure stability, replayability, and reliable undo/redo, the application enforces a strict **Air Gap** between the UI and the Data Model.

### 3.1 The "Air Gap" Principle (The Prime Directive)

The UI (Tools, Widgets, Inputs) is **strictly forbidden** from modifying the Data Model (`Sketch` or `Simulation`) directly.
* **ILLEGAL:** `select_tool.py` directly setting `line.end_point = (10, 10)`.
* **LEGAL:** `select_tool.py` constructing a `SetEntityGeometryCommand` (or `SetPointCommand`) and submitting it to `scene.execute()`.

**Why:** If a state change does not happen via a Command, it is not recorded in history. If it isn't in history, the simulation state is corrupted upon replay or undo.

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

1.  **Input:** Reads vector data from the `Sketch`.
2.  **Process:** Discretizes lines and curves into individual static particles ("atoms").
3.  **Output:** Writes these atoms into the `is_static` arrays of the `Simulation`.
4.  **Rebuild:** When CAD geometry changes (via Command), the `Scene` triggers `compiler.rebuild()` to refresh the physics representation.

---

## 6. UI & Input Management

The project employs a custom UI framework with a focus on **Modularity** and **Generic Protocols**.

### 6.1 Hierarchical UI Tree & Overlays (`ui/ui_manager.py`)

The UI is a retained object tree managed by `UIManager`.
* **Main Tree:** Root -> Panels -> Widgets -> Elements.
* **The Overlay Protocol:** Widgets that need to spawn floating elements (Dropdowns, Tooltips) must implement the `OverlayProvider` protocol.
    * The `UIManager` automatically iterates registered providers and renders their overlays *after* the main tree to ensure correct Z-ordering.
    * **Rule:** Never hardcode widget-specific rendering calls in the UIManager (e.g., `if dropdown.is_open: draw()`). Rely on the protocol.

### 6.2 Input Chain of Responsibility (`ui/input_handler.py`)

Input is handled via a strict 4-layer protocol to ensure events are consumed by the correct system.

1.  **System Layer:** `QUIT`, `VIDEORESIZE`.
2.  **Global Layer:** Hotkeys (e.g., `Ctrl+Z` for Undo, `B` for Brush).
3.  **Modal Layer (Blocking):**
    * Checks the **Central Modal Stack** in `AppController`.
    * If `modal_stack` is not empty, all lower layers are blocked.
    * Dialogs are managed via `push_modal()` and `pop_modal()`.
4.  **HUD Layer (Generic Focus):**
    * Passes events to the UI Tree.
    * Manages **Generic Focus**: Checks `wants_focus()` on widgets and updates `session.focused_element`.
    * Triggers `on_focus_lost()` on widgets when they lose focus to ensure clean state transitions.

### 6.3 Smart Batching
Tools are designed to be "Polymorphic" and "Batch-Aware":
* **Unary (H/V/Fix):** Applies to *all* selected entities.
* **Binary (Equal/Parallel):** Treats the first selection as "Master" and subsequent selections as "Followers."

### 6.4 Interaction State & Reset
To prevent "Ghost Inputs" (e.g., a button click registering immediately after a modal closes):
* **Rule:** When the modal stack changes (open or close), the entire UI tree must be reset.
* **Mechanism:** `push_modal()` triggers a recursive `reset_interaction_state()` on the Root Container, clearing `is_hovered`, `is_clicked`, and `hot` states from all widgets.

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

---

## 9. Claude's Thinking Checklist

*Before every code generation, I must pause and verify:*

### 🚦 Pre-Flight (The Surgeon's Prep)
* [ ] **AvG Check (The Generalizer):** Is this a hack, or a first-principles improvement of the code's genome?
    * *Action:* Stop. Generalize the solution (e.g., "Add protocol" instead of "Add if-statement").
* [ ] **Air Gap Check (The Law):** Does this UI action strictly avoid mutating the Model directly?
    * *Action:* If No, refactor to use a `Command`.
* [ ] **Surgical Precision (The Potency Test):** Is this the *minimum viable mutation* to achieve the maximum result?
    * *Question:* Can I do this by deleting code rather than adding it?
* [ ] **Root Cause Analysis:** Am I treating a symptom (e.g., "reset button state") or curing the disease (e.g., "reset interaction state globally")?
* [ ] **Dependency Check:** Am I introducing a circular dependency or hard-coded import?
    * *If Yes:* Use a protocol, event, or the central `Session` to decouple.

### 🏁 Post-Flight (The Recovery Room)
* [ ] **No Scar Tissue:** Did I remove all unused imports, debug prints, and commented-out blocks?
* [ ] **Config Hygiene:** Did I extract new magic numbers/strings to `core/config.py`?
* [ ] **Undo Safety:** Did I implement `undo()` for any new Commands I created?
* [ ] **Focus Hygiene:** If I added a new widget, did I implement `on_focus_lost()`?
* [ ] **Potency Check:** Does this change enable future features "for free" (e.g., a new protocol that all future widgets can use)?

Remember: Reusability first. Generalization second. New code last.