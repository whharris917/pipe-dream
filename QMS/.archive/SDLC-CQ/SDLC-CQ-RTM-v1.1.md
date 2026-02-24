---
title: claude-qms Requirements Traceability Matrix
revision_summary: 'CR-105: Added REQ-REPO-004 (Quality-Manual submodule) verification.
  Updated qualified baseline. Updated RS reference to v2.0.'
---

# SDLC-CQ-RTM: claude-qms Requirements Traceability Matrix

## 1. Purpose

This document provides traceability between the requirements specified in SDLC-CQ-RS v2.0 and their verification evidence. Since `claude-qms` is a static repository (no executable code), verification is by inspection rather than automated tests.

---

## 2. Scope

This RTM covers all 6 requirements defined in SDLC-CQ-RS v2.0 across the following domains:

- REQ-REPO (Repository Structure): 4 requirements
- REQ-DOC (Documentation): 2 requirements

---

## 3. Traceability Summary

| Requirement | Short Name | Verification Method | Result |
|-------------|-----------|---------------------|--------|
| REQ-REPO-001 | Marker File | Inspection | PASS |
| REQ-REPO-002 | QMS CLI Submodule | Inspection | PASS |
| REQ-REPO-003 | Gitignore | Inspection | PASS |
| REQ-REPO-004 | Quality Manual Submodule | Inspection | PASS |
| REQ-DOC-001 | README | Inspection | PASS |
| REQ-DOC-002 | No Seed Duplication | Inspection | PASS |

---

## 4. Verification Evidence

### 4.1 Repository Structure (REQ-REPO)

#### REQ-REPO-001: Marker File

**Requirement:** The repository shall contain a `.claude-qms` marker file at the root. This file signals to `qms init` that the directory is a valid QMS project root.

**Evidence:** Repository `whharris917/claude-qms` contains `.claude-qms` at root (commit `6b22747`). File is empty, serving as a marker for `qms init` root detection.

---

#### REQ-REPO-002: QMS CLI Submodule

**Requirement:** The repository shall include `qms-cli/` as a git submodule pointing to `whharris917/qms-cli`. The submodule shall reference a qualified commit on the `main` branch.

**Evidence:** `.gitmodules` in `whharris917/claude-qms` defines `qms-cli` submodule pointing to `https://github.com/whharris917/qms-cli.git` (commit `d3c34e5`). The submodule reference points to `main` branch commit `309f217` which is the current qualified baseline of qms-cli.

---

#### REQ-REPO-003: Gitignore

**Requirement:** The repository shall contain a `.gitignore` file that excludes QMS runtime artifacts (e.g., `.claude/users/`, `QMS/.meta/`, `QMS/.audit/`, `QMS/.archive/`, `__pycache__/`).

**Evidence:** `.gitignore` in `whharris917/claude-qms` excludes `.claude/users/`, `QMS/.meta/`, `QMS/.audit/`, `QMS/.archive/`, `__pycache__/`, and other runtime artifacts (commit `6b22747`).

---

#### REQ-REPO-004: Quality Manual Submodule

**Requirement:** The repository shall include `Quality-Manual/` as a git submodule pointing to `whharris917/quality-manual`. This provides the QMS operational documentation at the project root.

**Evidence:** `.gitmodules` in `whharris917/claude-qms` defines `Quality-Manual` submodule pointing to `https://github.com/whharris917/quality-manual.git` (commit `d3c34e5`). Cloning with `--recurse-submodules` populates `Quality-Manual/` with 38 operational documentation files.

---

### 4.2 Documentation (REQ-DOC)

#### REQ-DOC-001: README

**Requirement:** The repository shall contain a `README.md` with quick-start instructions covering: cloning with `--recurse-submodules`, running `qms init`, and basic QMS CLI usage.

**Evidence:** `README.md` in `whharris917/claude-qms` includes: clone command with `--recurse-submodules`, `cd qms-cli && python qms.py init` instructions, and basic CLI usage examples (commit `6b22747`).

---

#### REQ-DOC-002: No Seed Duplication

**Requirement:** The repository shall NOT contain any files that are created by `qms init` (e.g., `QMS/`, `.claude/users/`, `CLAUDE.md`, `qms.config.json`). These are generated at init time from `qms-cli/seed/`.

**Evidence:** Repository at commit `6b22747` contains only: `.claude-qms`, `.gitmodules`, `.gitignore`, `README.md`, and `qms-cli/` submodule. No `QMS/`, `.claude/users/`, `CLAUDE.md`, or `qms.config.json` present.

---

## 5. Qualified Baseline

| Attribute | Value |
|-----------|-------|
| Requirements Spec | SDLC-CQ-RS v2.0 |
| Repository | whharris917/claude-qms |
| Branch | main |
| Commit | d3c34e5 |

---

## 6. References

- **SDLC-CQ-RS:** claude-qms Requirements Specification
- **CR-104:** Create claude-qms Starter Repo, Harden qms init

---

**END OF DOCUMENT**
