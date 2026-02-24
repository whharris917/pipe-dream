---
title: claude-qms Requirements Specification
revision_summary: 'CR-104: Initial requirements for the claude-qms canonical starter
  repository'
---

# SDLC-CQ-RS: claude-qms Requirements Specification

## 1. Purpose

This document defines the requirements for the `claude-qms` repository — the canonical starter template for new QMS projects. The repository provides the minimum scaffolding needed for a user to clone and immediately initialize a fully functional QMS project using `qms init`.

---

## 2. Scope

This RS covers the 5 requirements for the `claude-qms` repository across 2 domains:

- REQ-REPO (Repository Structure): 3 requirements
- REQ-DOC (Documentation): 2 requirements

These requirements govern the contents of `whharris917/claude-qms` on GitHub.

---

## 3. Requirements

### 3.1 Repository Structure (REQ-REPO)

| ID | Requirement |
|----|-------------|
| REQ-REPO-001 | **Marker File.** The repository shall contain a `.claude-qms` marker file at the root. This file signals to `qms init` that the directory is a valid QMS project root. |
| REQ-REPO-002 | **QMS CLI Submodule.** The repository shall include `qms-cli/` as a git submodule pointing to `whharris917/qms-cli`. The submodule shall reference a qualified commit on the `main` branch. |
| REQ-REPO-003 | **Gitignore.** The repository shall contain a `.gitignore` file that excludes QMS runtime artifacts (e.g., `.claude/users/`, `QMS/.meta/`, `QMS/.audit/`, `QMS/.archive/`, `__pycache__/`). |

---

### 3.2 Documentation (REQ-DOC)

| ID | Requirement |
|----|-------------|
| REQ-DOC-001 | **README.** The repository shall contain a `README.md` with quick-start instructions covering: cloning with `--recurse-submodules`, running `qms init`, and basic QMS CLI usage. |
| REQ-DOC-002 | **No Seed Duplication.** The repository shall NOT contain any files that are created by `qms init` (e.g., `QMS/`, `.claude/users/`, `CLAUDE.md`, `qms.config.json`). These are generated at init time from `qms-cli/seed/`. |

---

## 4. References

- **CR-104:** Create claude-qms Starter Repo, Harden qms init
- **SDLC-QMS-RS:** QMS CLI Requirements Specification (defines `qms init` behavior)

---

**END OF DOCUMENT**
