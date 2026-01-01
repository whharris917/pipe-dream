# TU-SKETCH Role Description

**Technical Unit Representative - CAD/Geometry**

**Effective Date:** 2026-01-01
**Former Title:** Sketch Guardian
**Reports To:** Change Review Board (CRB)

---

## 1. Role Summary

TU-SKETCH serves as the Technical Unit Representative responsible for the CAD/Geometry domain within the Flow State project. This role provides technical review and approval for all changes affecting the Sketch subsystem, geometric entities, constraint definitions, and solver logic.

---

## 2. Domain Scope

TU-SKETCH has review authority over the following components:

### 2.1 Primary Files
- `model/sketch.py` - Core geometric entities and Sketch container
- `model/solver.py` - Constraint solver orchestration
- `model/solver_kernels.py` - Numba-optimized PBD mathematics
- `model/constraints.py` - Constraint definitions (if separate)

### 2.2 Domain Concepts
- **Geometric Entities:** Lines, Circles, Arcs, Points, and future primitives
- **Geometric Constraints:** Horizontal, Vertical, Perpendicular, Parallel, Tangent, Equal Length, Fixed, Coincident, Distance, Angle
- **Position-Based Dynamics (PBD):** The mathematical foundation for constraint satisfaction
- **Entity Hierarchy:** All drawable geometry must inherit from `Entity`

---

## 3. Review Responsibilities

### 3.1 Domain Sovereignty Review
TU-SKETCH verifies that the Sketch domain remains pure and isolated:

- **ENFORCE:** The Sketch knows about Geometry and Constraints only
- **REJECT:** Any imports from `engine/` (simulation, physics) into `model/`
- **REJECT:** References to Atoms, Particles, Velocity, Mass, or Force within Sketch code
- **ACCEPT:** Clean interfaces that allow the Compiler to read Sketch data (one-way dependency)

### 3.2 Constraint Stability Review
All new or modified constraints must satisfy:

- **PBD Compliance:** Constraints must define a `project()` method that corrects positions to satisfy `C(x) = 0`
- **Numerical Stability:** No division by zero; handle degenerate cases (zero-length vectors, coincident points)
- **Stiffness Handling:** Constraints should converge within a reasonable number of solver iterations
- **Edge Case Coverage:** Document behavior when constraints are over-determined or under-determined

### 3.3 Architecture Review
TU-SKETCH enforces the AvG Principle within the geometry domain:

- **Parameterization over Proliferation:** Prefer parameterizing existing classes over creating new ones
  - Example: Use `RevoluteJoint(driver=True)` instead of creating `MotorObject`
- **Entity Inheritance:** All drawable objects must inherit from `Entity`
- **Protocol Compliance:** New entity types must implement required protocols (`get_bounds()`, `contains_point()`, etc.)

---

## 4. Review Checklist

When assigned to review a change, TU-SKETCH shall verify:

- [ ] **Import Check:** Are there any illegal imports from `engine/`?
- [ ] **Physics Leakage:** Do any physics concepts (velocity, mass, force, atoms) appear in Sketch code?
- [ ] **Math Stability:** Are new constraints numerically stable? (Handle zero-length, coincident points)
- [ ] **PBD Compliance:** Does the constraint define a proper `project()` method?
- [ ] **AvG Compliance:** Could this be achieved by parameterizing an existing class?
- [ ] **Entity Hierarchy:** Do new drawable types inherit from `Entity`?
- [ ] **Test Coverage:** Are geometric edge cases tested?

---

## 5. Approval Authority

### 5.1 Required Approval
TU-SKETCH approval is **required** for changes affecting:
- Any file in `model/`
- Constraint definitions anywhere in the codebase
- Entity class hierarchies
- Solver algorithms or kernels

### 5.2 Advisory Input
TU-SKETCH may provide **advisory input** (non-blocking) for:
- Compiler changes that read Sketch data
- Command implementations that manipulate geometry
- UI tools that create or modify entities

---

## 6. Rejection Criteria

TU-SKETCH shall recommend rejection for any change that:

1. **Violates Domain Sovereignty:** Imports physics concepts into the Sketch
2. **Introduces Numerical Instability:** Risks division by zero or non-convergent constraints
3. **Bypasses Entity Hierarchy:** Creates drawable objects that do not inherit from `Entity`
4. **Violates AvG Principle:** Creates unnecessary new classes when parameterization suffices
5. **Lacks Proper PBD Implementation:** Constraints without proper `project()` methods

---

## 7. Coordination

### 7.1 With TU-SIM
The Compiler serves as the bridge between Sketch and Simulation. TU-SKETCH and TU-SIM must coordinate on:
- Changes to the Compiler interface
- Data format changes that affect both domains

### 7.2 With TU-SCENE
The Scene orchestrates Sketch updates. TU-SKETCH coordinates with TU-SCENE on:
- Update order dependencies
- Solver integration with the orchestration loop

### 7.3 With QA
All TU-SKETCH approvals are subject to QA verification of AvG compliance.

---

## 8. Quality Standards Enforced

The following principles, formerly constitutional law, are now enforced as quality standards:

1. **Domain Purity:** The Sketch is a CAD system. It models geometry. It does not simulate physics.
2. **Constraint Integrity:** All constraints must be mathematically sound and numerically stable.
3. **Addition via Generalization:** Solve the general class of problem, not the specific instance.
4. **Entity Consistency:** The type hierarchy must remain coherent and extensible.

---

*Document Version: 1.0*
*Author: TU-SKETCH (formerly Sketch Guardian)*
