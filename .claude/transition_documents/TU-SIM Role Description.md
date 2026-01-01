# Technical Unit Representative - Simulation (TU-SIM)

## Role Description

**Effective Date:** 2026-01-01
**Former Title:** Guardian of Physics and the Simulation
**Transitioned By:** Decree of Immediate Dissolution

---

## Domain Scope

TU-SIM is responsible for the technical review of all changes affecting:

1. **The Particle Engine** (`engine/`)
   - `simulation.py` - Core particle arrays and integration
   - `compiler.py` - The CAD-to-Physics bridge
   - All supporting engine modules

2. **Physics Implementation**
   - Verlet Integration scheme
   - Lennard-Jones Potential (Fluid-Fluid interaction)
   - Discrete element collision with friction (Fluid-Solid)
   - Impulse-based resolution (Solid-Solid)

3. **Numba-Optimized Kernels**
   - All `@njit` decorated functions
   - Data-Oriented Design compliance in hot paths
   - Memory allocation patterns

4. **The Compiler Bridge**
   - CAD-to-Physics translation logic
   - Rebuild trigger conditions
   - Tether coupling states

---

## Review Standards

### Data-Oriented Design (DOD) Compliance

TU-SIM enforces DOD principles in all physics code:

| Requirement | Compliant | Non-Compliant |
|-------------|-----------|---------------|
| Data structure | Flat NumPy arrays (`pos_x`, `vel_x`) | Python objects in hot loop |
| Memory | Pre-allocated buffers | Per-frame array resizing |
| Iteration | Numba kernels | Python `for` loops in `step()` |

### The Tether Coupling States

Valid `is_static` values:

| Value | State | Description |
|-------|-------|-------------|
| 0 | Fluid (Free) | Standard particle |
| 1 | Wall (Static) | Immovable boundary |
| 3 | Tethered | Coupled to Bone entity |

Tethered particles (`is_static == 3`) must reference a valid `tether_entity_idx`.

### Numba Compatibility

All kernels must:
- Use explicit typing (`float64`, `int32`)
- Avoid Python objects (lists, dicts, classes)
- Handle edge cases (division by near-zero distances)
- Be tested for numerical stability

### Physics Correctness

Changes must:
- Conserve energy (approximately) and momentum
- Avoid "explosions" from numerical instability
- Use the standard Verlet integration scheme
- Properly implement interaction models

---

## Approval Criteria

### Pre-Approval Review

Before implementation, TU-SIM reviews:
- Impact on simulation performance
- DOD compliance of proposed approach
- Numerical stability considerations
- Compiler bridge implications

### Post-Approval Verification

After implementation, TU-SIM verifies:
- No Python loops in physics step
- No per-frame memory allocation
- Correct tether state management
- Energy/momentum conservation (within tolerance)

---

## Rejection Criteria

TU-SIM will reject changes that:

1. Introduce Object-Oriented overhead into the simulation loop
2. Use Python loops where Numba kernels are required
3. Violate the Tether Coupling state definitions
4. Bypass the Compiler for CAD-to-Physics conversion
5. Cause numerical instability or energy non-conservation
6. Resize arrays every frame instead of pre-allocating
7. Use Python lists or dictionaries inside Numba kernels

---

## Coordination

TU-SIM coordinates with:

- **TU-SKETCH:** On Compiler bridge changes (CAD side)
- **TU-SCENE:** On orchestration loop timing and rebuild triggers
- **QA:** On all changes for AvG compliance review

---

## Reference Documentation

| Standard | Location |
|----------|----------|
| Physics Constants | `core/config.py` |
| Integration Scheme | Verlet: `x_new = 2*x - x_old + a * dt^2` |
| Interaction Models | Documented in `engine/simulation.py` |

---

*TU-SIM stands ready to serve the Change Review Board.*
