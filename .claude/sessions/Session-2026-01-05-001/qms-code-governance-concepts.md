# QMS Code Governance Concepts

**Date:** 2026-01-05
**Session:** 010
**Status:** Discussion notes (not implemented)

---

## Overview

Discussion of how to formally govern the QMS infrastructure code (Python scripts) within the change control framework, while maintaining appropriate separation between documents and code.

---

## The Problem

The QMS CLI (`qms.py` and related scripts) is critical infrastructure that governs document control. These scripts need formal change control, but:

- They should NOT live inside `QMS/` — that directory is for controlled documents
- Code and documents have fundamentally different version control needs
- Mixing them creates conceptual confusion about what the QMS "is"

---

## GMP Analogy: Equipment vs. Documentation

In a GMP manufacturing environment:

| Asset Type | Where It Lives | Version Control |
|------------|----------------|-----------------|
| SOPs, batch records, specifications | Document QMS (e.g., Veeva, MasterControl) | Document lifecycle (draft → review → effective) |
| PLC code, equipment software | Asset management system (e.g., FactoryTalk AssetCentre) | Code version control, qualified separately |

The QMS *references* equipment by ID, but doesn't *contain* the equipment or its code. Equipment undergoes its own qualification process.

---

## Proposed Approach: Git as the Code QMS

For Flow State, we take a similar approach:

| Asset Type | Location | Version Control |
|------------|----------|-----------------|
| SOPs, CRs, INVs, specifications | `QMS/` directory | QMS document lifecycle |
| QMS scripts, application code | Outside `QMS/` (e.g., `.claude/`, `src/`) | Git commits |

**Git becomes the "qualified system" for code**, analogous to FactoryTalk AssetCentre in manufacturing.

---

## Key Principles

### 1. Separation of Concerns

- `QMS/` contains documents (human-readable policy and records)
- Code directories contain scripts (machine-executable implementation)
- Each has its own governance appropriate to its nature

### 2. Traceability via Reference

- CRs that modify QMS scripts reference the affected files and commits
- The CR provides the "change control wrapper" around the code change
- Git provides the detailed version history and diff capability

### 3. Git as Qualified Infrastructure

- Git commit history = audit trail for code changes
- Commits should reference their authorizing CR
- The combination of CR + git commit provides full traceability

---

## Decisions

### 1. Single Repository, Dual SDLC Tracks

Both QMS infrastructure code and application code live in the same git repo (`pipe-dream/`), but have separate SDLC documentation:

| Code Type | Location | SDLC Documentation |
|-----------|----------|-------------------|
| QMS infrastructure (CLI, scripts) | `pipe-dream/qms-cli/` | `QMS/SDLC-QMS/` |
| Application (Flow State) | `pipe-dream/src/`, etc. | `QMS/SDLC-FLOW/` |

### 2. QMS Scripts Directory

Move QMS scripts from `.claude/` to a top-level directory:

```
pipe-dream/
├── qms-cli/           # QMS infrastructure code (NEW - package)
│   ├── __init__.py
│   ├── __main__.py    # Entry point
│   ├── commands/      # Command implementations
│   ├── models/        # Data models (metadata, audit, etc.)
│   └── ...
├── QMS/               # Controlled documents
│   ├── SDLC-QMS/      # RS, DS, RTM for QMS infrastructure
│   └── SDLC-FLOW/     # RS, DS, RTM for application
├── src/               # Application code
└── ...
```

### 2a. Package Structure

The current `qms.py` is monolithic and too long. It should be reorganized into a proper Python package with:

- Separation of concerns (commands, models, utilities)
- Modular architecture for maintainability
- Clear entry point via `__main__.py`

This reorganization will be part of the migration work.

### 3. Code Reference Format

References to code in GMP documentation shall use:

```
{file_path} @ {commit_hash}
```

**Example:**
```
qms-cli/commands/checkout.py @ a1b2c3d
```

This provides:
- **Location:** Which file
- **Version:** Which exact state of that file
- **Reproducibility:** Anyone can checkout that commit and see the exact code

### 4. Bootstrap Problem

Not a blocker. We are not officially GMP-ready yet, so historical code changes without CRs are acceptable. Governance begins when we declare it begins.

---

## Production vs. Test Environments

### 5. Two-Environment Model

Formalize the distinction between Production and Test environments for both systems:

| Environment | Purpose | Governance Level |
|-------------|---------|------------------|
| **Production** | Live, controlled, qualified code | Full GMP compliance |
| **Test** | Isolated, experimental, development | Relaxed — freedom to iterate |

This applies to both:
- QMS infrastructure (`qms-cli`)
- Application code (Flow State)

### 6. Test Environment Characteristics

- **Isolation:** Changes have no impact on Production
- **Freedom:** Big refactors, experiments, breaking changes allowed
- **No GMP overhead:** Development can move fast without CR ceremony
- **Goal:** Get code working, tested, and qualified

### 7. Qualification Gate

Code is "qualified" when:
- It exists in a controlled state
- Full SDLC documentation suite is complete (RS, RTM, etc.)
- Testing is complete and documented
- Ready for controlled use

**Only qualified code may enter Production.**

### 8. The qms-cli Migration Strategy

The refactored `qms-cli` package will be developed entirely in the Test Environment:

```
Test Environment (test/qms-cli-001)     Production Environment (main)
──────────────────────────────────      ──────────────────────────────
qms-cli/                                .claude/qms.py (current)
├── __init__.py
├── __main__.py
├── commands/
├── models/
└── ...

(NO QMS documents in Test)              QMS/SDLC-QMS/
                                        ├── SDLC-QMS-RS.md
                                        ├── SDLC-QMS-DS.md
                                        ├── SDLC-QMS-RTM.md
                                        └── ...
```

**Key insight:** Test Environment is free-form — no QMS documentation lives there. All SDLC documentation is created in Production via GMP workflows.

### 9. Implementation via Git Branches

| Branch Pattern | Role | Example |
|----------------|------|---------|
| `main` | Production Environment | — |
| `test/qms-cli-NNN` | Test Environment for QMS CLI | `test/qms-cli-001` |
| `test/pipe-dream-NNN` | Test Environment for application | `test/pipe-dream-001` |

Zero-padded numbering allows multiple parallel Test Environments.

### 10. No Dependencies Between Test and Production

- Test code does NOT reference Production QMS documents
- Test Environment is completely isolated
- Dependencies would create coupling that defeats the purpose of isolation

### 11. Qualification Terminology

**Critical distinction:**

| Term | Meaning | Where |
|------|---------|-------|
| **Qualification Ready** | Code is developed, tested, ready for formal qualification | Test Environment |
| **Qualification Pending** | Qualification process has begun but not complete | Transition |
| **Qualification Complete** | SDLC approved in QMS, code in Production | Production Environment |

**A Test Environment can NEVER be "Qualification Complete."**

At best, Test code is "Qualification Ready" — meaning it's ready to undergo the formal qualification process.

### 12. The Qualification Process

When Test code is Qualification Ready:

1. **SDLC Documentation:** Create RS, DS, RTM, etc. in Production QMS via GMP workflows (CRs, reviews, approvals)

2. **Code Migration:** Move code from Test to Production via controlled, documented, compliant means per SOPs

3. **Acceptance Testing:** Verify Production code is identical to the Qualification-Ready version from Test

4. **Qualification Complete:** Only true when:
   - Full SDLC suite is APPROVED in official QMS
   - Code exists in Production environment
   - Acceptance testing confirms identity with Test version

```
Test Environment          Qualification Process           Production Environment
────────────────          ─────────────────────           ──────────────────────

[Code: Qualification      1. Create SDLC docs via CR      [SDLC docs: APPROVED]
 Ready]                   2. Migrate code via CR          [Code: Qualified]
                          3. Acceptance testing           [Status: Qualification
                                                           Complete]
```

---

## Open Questions

- Acceptance testing procedure (hash comparison? functional tests?)
- Whether multiple Test Environments can feed into one qualification effort
- Rollback procedure if qualification fails mid-process

---

## Discussion Points

[Awaiting further input from Lead]

---

**End of Notes**
