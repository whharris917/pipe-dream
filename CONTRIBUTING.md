This **Developer Guide** is designed to provide deep-tissue context for engineers and physicists looking to contribute to **Flow State**. It covers the internal mechanics of our custom physics engine, the data lifecycle from CAD to Kernel, and the "Skin & Bone" architecture that powers our rigid-body dynamics.

---

# 🛠 Flow State: Developer Guide

Welcome to the internal architecture of Flow State. This project is a hybrid of a **CAD Drawing Suite** and a **Numba-Accelerated Physics Engine**. Contributing requires an understanding of how high-level Python objects interface with low-level JIT-compiled kernels.

---

## 1. The Physics Philosophy: "Skin & Bone"

In Flow State, every physical object is a composite of two systems:

1. **The Bone (Rigid Body):** A Python-side `Entity` object (Circle or Line) that holds the "Truth" of the object’s position (), rotation (), velocity, and mass.
2. **The Skin (Tethered Particles):** A collection of particles in the Numba arrays where `is_static == 3`. These act as the sensory interface for the object.

### The Lifecycle of a Collision

* **Step A:** A fluid particle strikes a "Skin" particle.
* **Step B:** The Numba kernel calculates the collision force.
* **Step C:** The "Skin" particle, being tethered, transfers that force back to its "Bone" (Entity).
* **Step D:** The Entity integrates those forces into torque and linear acceleration, moving the entire chassis.

---

## 2. Numba Kernels & Particle States

The engine relies on `physics_core.py`, which contains the JIT-compiled kernels. The `is_static` array is the most critical data structure in the engine:

| Value | State | Description |
| --- | --- | --- |
| **0** | **Fluid** | Standard dynamic particles obeying gravity and LJ potentials. |
| **1** | **Wall** | Infinite mass, zero velocity; purely reflective boundaries. |
| **3** | **Tethered** | The "Skin" particles. They integrate like fluid but are constrained to an anchor. |

### The Tether Physics

Tethered particles () are governed by a Hookean spring force:



Where  is the `TETHER_STIFFNESS` (Default: **5000.0**). This high stiffness allows the skin to feel "hard," but requires the high temporal resolution (**20 sub-steps**) we have implemented to prevent divergence.

---

## 3. Rigid Body Integration

Forces are converted to movement in `model/geometry.py`. When an entity is "Dynamic," it calculates its own motion based on the sum of forces () and torques () reported by its atoms.

### Torque Calculation

For every atom in an entity, the torque contributed is the cross-product of the displacement vector () and the force vector ():



The total torque is then used to update the angular velocity:



Where  is the **Inertia**, which we artificially boost by a factor of **5.0** to ensure rotational stability during high-energy collisions.

---

## 4. The Compiler: From CAD to Atoms

When a user clicks "Atomize," the `engine/compiler.py` takes over. This module is responsible for:

1. **Discretization:** Calculating how many particles are needed to cover a line or circle based on `material.spacing`.
2. **Mapping:** Every tethered particle is assigned a `tether_entity_idx`. This is the "ID" of the parent CAD object.
3. **Intra-Entity Exclusion:** The compiler flags these atoms so the Numba kernel can skip Lennard-Jones calculations between atoms of the same parent. This is vital; without it, the atoms would repel each other and "shatter" the geometry.

---

## 5. Coding Standards & Performance

* **Avoid Python Loops in Physics:** Any code that runs per-particle must be inside a `@njit` decorated function in `physics_core.py`.
* **Memory Management:** We use pre-allocated NumPy arrays for particles. Avoid resizing arrays during the simulation loop (`Scene.rebuild()` is the only place for allocation).
* **Magic Numbers:** **Never** hardcode constants. Use `core/config.py`. If a value needs to be tuned (like Gravity or Damping), it should be there.

---

## 6. Developing UI Components

We use `DearPyGui` (or your ImGui wrapper) for the interface.

* **Material Sync:** When adding new sliders to the `MaterialPropertyWidget`, ensure you implement "Live Sync." Changes to the slider should immediately update the `active_material` in the `Session` and, if an object is selected, the `entity.material` directly.

---

## 7. Current Technical Debt & Roadmap

* **The Phase Lag:** Currently, the Entity integrates its position *before* the atoms calculate their new anchors. This creates a 1-frame lag (the "jellyfish" effect). Future contributors should look into a semi-implicit integration scheme to sync these perfectly.
* **Motor Torque:** We are moving toward "Active Power." The next major task is implementing a `motor_speed` property that overrides angular velocity for revolute-jointed entities.

---