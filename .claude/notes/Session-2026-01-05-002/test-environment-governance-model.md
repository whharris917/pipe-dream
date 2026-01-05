# Test Environment Governance Model

**Date:** 2026-01-05
**Session:** 002
**Status:** Agreed conceptual framework

---

## Overview

This note documents the agreed model for when and how "Test Environments" are used in the Flow State project, distinguishing between two fundamentally different concepts that share the name.

---

## Two Meanings of "Test Environment"

### 1. Genesis Sandbox (Rare, Outside GMP)

**Purpose:** Bring an entirely new system into existence from nothing.

**Characteristics:**
- Long-running, free-form development
- Outside the QMS workflow (no CR governs it)
- Used only for wholly new, self-contained systems
- Ends when foundation and structural beams are in place

**Examples of appropriate use:**
- Initial creation of a new tool (e.g., a custom Python linter)
- Building the foundation of a new subsystem independent from existing systems

**NOT appropriate for:**
- Adding a module to Flow State (that's evolution of an existing system)
- Adding a command to QMS CLI (that's evolution of an existing system)
- Any modification to existing code or systems

**Rationale:** GMP procedures are designed for CHANGING existing processes, not bringing them into existence from scratch. You cannot "change control" what doesn't exist yet.

### 2. Execution Branch (Frequent, Inside GMP)

**Purpose:** Technical implementation of pre-approved changes within a controlled CR workflow.

**Characteristics:**
- Short-lived, per-CR
- Fully inside the QMS workflow (CR is IN_EXECUTION)
- Git branch serves as the technical substrate for safe execution
- All learning and decisions captured in CR lifecycle

**Workflow:**
```
CR Pre-Approved
    │
    ▼
┌─────────────────────────────────────────┐
│  EXECUTION PHASE (CR IN_EXECUTION)      │
│                                         │
│  1. Create git branch                   │
│  2. Make code changes                   │
│  3. Run tests, validate                 │
│  4. Merge to main                       │
│  5. Document work in CR                 │
│                                         │
└─────────────────────────────────────────┘
    │
    ▼
Route for Post-Review
    │
    ├──► Problems found? ──► git revert, iterate
    │
    ▼
Post-Approval ──► Close
```

**Key insight:** This is not escaping GMP—it IS GMP. The git branch is merely the technical mechanism; governance is fully present throughout.

---

## The Line Where GMP Begins

When transitioning from Genesis Sandbox to GMP-governed development, the criterion is:

> **The line beyond which you would expect to learn real lessons and make discoveries/breakthroughs in our GMP-Inspired Recursive Governance Loop experiment.**

If the work would benefit from:
- QA catching a procedural gap
- A TU raising an architectural concern
- A review forcing articulation of rationale
- A rejection teaching something that was missed
- Diverse perspectives improving the outcome

...then the line has been crossed. GMP begins.

---

## Decision Matrix

| Scenario | Approach |
|----------|----------|
| Building a brand new tool from nothing | Genesis Sandbox (foundational work only) |
| Continuing work on new tool after foundation exists | CR with Execution Branch |
| Adding a feature to Flow State | CR with Execution Branch |
| Adding a command to QMS CLI | CR with Execution Branch |
| Fixing a bug | CR with Execution Branch |
| Refactoring existing code | CR with Execution Branch |

---

## Comparison Table

| Aspect | Genesis Sandbox | Execution Branch |
|--------|-----------------|------------------|
| **Frequency** | Rare | Every code change |
| **Duration** | Long-running | Short-lived (per-CR) |
| **Governance** | Outside QMS | Fully inside QMS |
| **Purpose** | Bring new system into existence | Implement pre-approved changes |
| **CR Status** | No CR exists yet | CR is IN_EXECUTION |
| **Learning Capture** | Deferred until qualification | Captured in CR lifecycle |
| **Git Usage** | Feature branch, informal | Execution branch, formal |

---

## Why This Matters

The alternative—using a "Test Environment" as a convenient escape hatch from GMP—would undermine the core purpose of the QMS:

1. **Knowledge loss:** Design decisions, problems solved, and rationale not recorded
2. **No diverse perspectives:** QA and TU insights missed during development
3. **COTS problem:** Production receives a "black box" without understanding its genesis
4. **Weakened organizational learning:** Problems solved don't strengthen the QMS

By limiting Genesis Sandbox to truly foundational work on new systems, and using Execution Branches for all evolutionary work, we preserve the learning and governance benefits of GMP while maintaining practical development velocity.

---

**End of Notes**
