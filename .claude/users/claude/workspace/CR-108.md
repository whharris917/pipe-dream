---
title: DocuBuilder Genesis Sandbox
revision_summary: Emphasize exploratory nature, no required outcomes, scope restriction
---

# CR-108: DocuBuilder Genesis Sandbox

## 1. Purpose

Authorize a genesis sandbox for exploratory prototyping of DocuBuilder — a Python library for authoring and executing controlled documents. This is a rapid iteration exercise with no required outcomes. The sandbox may be closed at any time regardless of the state of its contents. The sole restriction is that this CR does not authorize modifications to any existing controlled submodules, QMS documents, or anything outside the genesis sandbox directory.

---

## 2. Scope

### 2.1 Context

- **Parent Document:** None — this CR originates from the design exploration in Sessions 2026-03-02-001 and 2026-03-03-001, which identified the need for a table-primitive-based document authoring and execution engine.

### 2.2 Changes Summary

Create a git-ignored `docu-builder/` directory containing a standalone Python module and an informal requirements specification. All contents are exempt from QMS document control.

### 2.3 Files Affected

- `docu-builder/` — New directory (git-ignored), containing:
  - `docu-builder/rs.md` — Informal requirements specification
  - `docu-builder/docubuilder/` — Python package
- `.gitignore` — Add `docu-builder/` entry

---

## 3. Current State

The QMS interactive document system (CR-091) uses a prompt-graph engine with annotation parsing, a custom compiler, and CLI-driven interaction. Multiple sessions of design exploration for CR-107 have produced extensive analysis but no implementation. The design complexity continues to grow without empirical validation.

---

## 4. Proposed State

A git-ignored `docu-builder/` directory exists containing an exploratory Python library and informal requirements specification. The contents represent whatever state the prototyping has reached — there is no required end state. The sandbox may contain a working library, a partial prototype, or merely notes and experiments. All contents are disposable and may be superseded by a future CR that brings DocuBuilder under formal governance.

---

## 5. Change Description

### 5.1 Sandbox Directory

A `docu-builder/` directory at the project root, excluded from git tracking. This directory is entirely outside QMS control — its contents may be freely created, modified, and deleted without change records, reviews, or approvals.

### 5.2 Scope Restriction

This CR authorizes work exclusively within `docu-builder/` and the `.gitignore` entry that excludes it. It does not authorize modifications to:
- Any QMS-controlled document
- The `qms-cli/` submodule
- The `flow-state/` submodule
- Any file outside `docu-builder/` (except `.gitignore`)

### 5.3 Exploratory Nature

All contents of the sandbox are informal and disposable. The informal RS, Python code, and any other artifacts are working documents that may be rewritten, discarded, or refactored at any time. There are no deliverables, no milestones, and no required outcomes. The CR may be closed at any time in any state.

---

## 6. Justification

- Multiple design sessions have produced extensive plans but no working code. The design space is complex enough that further planning without implementation risks continued indecision. The only way to make progress is to start building.
- A sandbox approach allows rapid iteration without QMS overhead. The authorizing CR maintains traceability without constraining exploration.
- No required outcomes means the CR can be closed at any time — if the approach proves unfruitful, nothing is lost. If it proves valuable, a subsequent CR can formalize the results.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `.gitignore` | Modify | Add `docu-builder/` entry |
| `docu-builder/` | Create | Git-ignored sandbox directory |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| None | — | No QMS documents are modified |

### 7.3 Other Impacts

None. The sandbox is entirely isolated from the QMS, qms-cli, and flow-state.

---

## 8. Testing Summary

No formal testing. The sandbox is validated through interactive REPL exploration. Correctness is assessed empirically during experimentation.

---

## 9. Implementation Plan

This is exploratory work. The implementation plan is intentionally minimal — direction will be determined through experimentation.

1. Add `docu-builder/` to `.gitignore` and create directory structure
2. Write informal RS based on design principles from Session 2026-03-03-001
3. Begin prototyping the core data model in Python
4. Iterate freely based on discoveries

---

## 10. Execution

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Create sandbox: add docu-builder/ to .gitignore, create directory structure | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Write informal RS | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Post-execution commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

---

## 11. Execution Summary

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **Session 2026-03-03-001:** Design principles for authoring and executing controlled documents
- **authoring-and-executing-controlled-documents.md:** Core principles document (session artifact)
- **document_dna.json:** Document data model prototype (session artifact)

---

**END OF DOCUMENT**
