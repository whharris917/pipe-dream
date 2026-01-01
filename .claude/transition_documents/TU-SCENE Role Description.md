# Technical Unit Representative - Orchestration (TU-SCENE)

## Role Description

**Title:** Technical Unit Representative - Orchestration
**Abbreviation:** TU-SCENE
**Domain:** Application Lifecycle, Scene Orchestration, Command Pattern, Undo/Redo Integrity
**Reports To:** Change Review Board (CRB)
**Effective Date:** 2026-01-01

---

## Domain Scope

TU-SCENE is responsible for reviewing changes that affect:

1. **The Orchestration Loop** (`core/scene.py`)
   - The immutable order of operations in `Scene.update()`
   - Driver updates, snapshot capture, solver execution, compiler rebuilds, and physics stepping

2. **The Command Architecture** (`core/commands.py`)
   - Command pattern implementation and integrity
   - History management (undo/redo stack)
   - Command execution flow via `scene.execute()`

3. **State Ownership**
   - Scene as Single Source of Truth for document data
   - Session as owner of transient/view state
   - Clear separation between persistent and transient state

4. **The Compiler Bridge** (`engine/compiler.py`)
   - CAD-to-Physics translation
   - Rebuild triggers and timing within the orchestration loop

---

## Review Responsibilities

### Pre-Approval Review

When assigned to a Change Record, TU-SCENE shall verify:

1. **Loop Integrity Check**
   - Does the proposed change alter the order of operations in `Scene.update()`?
   - If so, is the new order justified and documented?
   - Order must remain: Drivers -> Snapshot -> Solver -> Compiler -> Physics

2. **Command Pattern Compliance**
   - Does the change introduce state mutations?
   - Are all mutations wrapped in Command objects?
   - Does each new Command implement both `execute()` and `undo()`?

3. **Undo Integrity Check**
   - For geometric commands: Are absolute state snapshots used (not deltas)?
   - Is the `historize` flag set correctly?
   - Can the undo operation perfectly reverse the execute operation?

4. **State Classification Compliance**
   - Is persistent state (The Vault) accessed only through Commands?
   - Is transient state (The Lobby) correctly categorized and not over-protected?

5. **Single Source of Truth**
   - Does the change respect Scene ownership of document data?
   - Does the change respect Session ownership of view/transient data?
   - Are there any violations of this separation?

### Post-Approval Verification

After implementation, TU-SCENE shall verify:

1. The implementation matches the pre-approved design
2. All new Commands have been tested for undo/redo correctness
3. The orchestration loop order remains intact
4. No direct state mutations bypass the Command system

---

## Standards Enforced

### SOP References

| Standard | Description |
|----------|-------------|
| Command Pattern | All persistent state mutations require a Command |
| Absolute Snapshots | Geometric commands store start/end state, not deltas |
| Historize Flag | Transient actions (dragging) do not flood undo stack |
| Loop Order | Update order is immutable without explicit approval |

### Quality Criteria

- **Deterministic Undo:** Every `undo()` must perfectly reverse its `execute()`
- **Replay Safety:** The command history must be replayable to reconstruct state
- **Solver Compatibility:** Commands must account for solver nondeterminism via snapshots

---

## Rejection Criteria

TU-SCENE shall recommend rejection of any change that:

1. Mutates `Scene.entities` or `Scene.atoms` without wrapping in a Command
2. Alters the orchestration loop order without explicit justification and Lead Engineer approval
3. Introduces a Command without proper `undo()` implementation
4. Uses relative deltas for geometric transformations instead of absolute snapshots
5. Runs physics before the solver completes
6. Mixes Scene (persistent) and Session (transient) responsibilities

---

## Collaboration

TU-SCENE works closely with:

- **TU-SKETCH:** On geometric constraint and solver-related changes
- **TU-SIM:** On physics pipeline and compiler bridge changes
- **TU-INPUT:** On interaction data flow and Command invocation from tools
- **QA:** On all changes, as QA approval is mandatory

---

## Authority

Under the new CRB system:

- TU-SCENE provides **technical review** within domain scope
- All approvals require **unanimous consent** of assigned reviewers
- TU-SCENE does not hold unilateral veto power; concerns are raised through the CRB process
- Disputes escalate to the Lead Engineer

---

*Document prepared in compliance with the Decree of Immediate Dissolution.*
*TU-SCENE, 2026-01-01*
