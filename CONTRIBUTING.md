# 🔬 Contributing to Flow State

Welcome to the lab! **Flow State** is not just a software project; it is a computational physics engine wrapped in a CAD interface.

This guide is for human engineers and physicists. It explains the "Mental Model" of the engine—the math, the physics, and the philosophy.

> **⚠️ Before You Code:**
> We adhere to a strict architectural constitution. Please read [CLAUDE.md](./CLAUDE.md) for our **Coding Standards**, **Architectural Patterns**, and the **"Addition via Generalization"** principle.

---

## 1. The Core Philosophy: "Skin & Bone"

Most particle simulators treat boundaries as static mathematical walls (`if x < 0: flip velocity`). Flow State is different. We implement **Bi-Directional Momentum Transfer**.

To achieve this, every physical object is a composite of two systems:

1.  **The Bone (Geometry):** A high-level Python object (e.g., `Circle`, `Line`) managed by a Position-Based Dynamics (PBD) solver. It holds the "Truth" of the object’s position ($P$), rotation ($\theta$), and mass.
2.  **The Skin (Atoms):** A low-level collection of particles in the Numba arrays. These act as the sensory interface.

### The Lifecycle of a Collision
1.  **Impact:** A fluid particle strikes a "Skin" particle.
2.  **Force:** The Numba kernel calculates a collision force ($F$).
3.  **Transfer:** The "Skin" particle is tethered to the "Bone," so it transfers $F$ back to the Entity.
4.  **Reaction:** The Entity integrates $F$ into torque ($\tau$) and acceleration ($a$), moving the entire chassis.

---

## 2. The Physics Engine (`engine/`)

The physics core is built on **Data-Oriented Design**. We do not use objects for particles; we use flat NumPy arrays (Structure of Arrays).

### The Particle States (`is_static` Array)
The engine differentiates particles using the `is_static` integer array:

| Value | State | Description |
| :--- | :--- | :--- |
| **0** | **Fluid** | Standard dynamic particles obeying gravity and Lennard-Jones potentials. |
| **1** | **Wall** | Infinite mass, zero velocity. Purely reflective boundaries. |
| **3** | **Tethered** | The "Skin." They move like fluid but are constrained to an anchor point on a Bone. |

### The Tether Math
Tethered particles are governed by a Hookean spring force:

$$F_{tether} = -k \cdot (P_{particle} - P_{anchor})$$

Where $k$ is `TETHER_STIFFNESS` (defined in `core/config.py`). This high stiffness allows the skin to feel "hard" but requires our simulation to run at **20 sub-steps per frame** to prevent numerical explosions.

---

## 3. The Compiler (`engine/compiler.py`)

The "Compiler" is the bridge between the CAD domain and the Physics domain. It runs whenever geometry is modified.

1.  **Discretization:** It walks along the vector geometry (Lines/Circles) and calculates how many particles are needed to cover the surface based on `material.spacing`.
2.  **Mapping:** It assigns every tethered particle a `tether_entity_idx`. This is the link back to the parent CAD object.
3.  **Exclusion:** It flags atoms belonging to the same object so they ignore each other's Lennard-Jones forces. This prevents the object from "exploding" due to internal pressure.

---

## 4. Setting Up Your Environment

Flow State requires a specific environment to handle the Numba JIT compilation.

### Prerequisites
* Python 3.8+
* **Visual C++ Build Tools** (Windows) or `build-essential` (Linux) — required for compiling Numba dependencies.

### Installation

```bash
# 1. Clone the repo
git clone [https://github.com/whharris917/flow-state.git](https://github.com/whharris917/flow-state.git)

# 2. Create a virtual env (Recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt