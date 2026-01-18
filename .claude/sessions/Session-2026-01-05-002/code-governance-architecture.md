# Code Governance Architecture

**Date:** 2026-01-05
**Session:** 002
**Status:** Consolidated framework (supersedes Session-001 notes on this topic)

---

## Overview

This note consolidates the governance model for code within the Flow State project, integrating concepts from Session-001 with refinements from Session-002.

---

## 1. Separation of Concerns: Code vs. Documents

### The Problem

The QMS CLI and application code need formal change control, but:
- They should NOT live inside `QMS/` — that directory is for controlled documents
- Code and documents have fundamentally different version control needs
- Mixing them creates conceptual confusion about what the QMS "is"

### The GMP Analogy

In a GMP manufacturing environment:

| Asset Type | Where It Lives | Version Control |
|------------|----------------|-----------------|
| SOPs, batch records, specifications | Document QMS (e.g., Veeva, MasterControl) | Document lifecycle (draft → review → effective) |
| PLC code, equipment software | Asset management system (e.g., FactoryTalk AssetCentre) | Code version control, qualified separately |

The QMS *references* equipment by ID, but doesn't *contain* the equipment or its code.

### Our Approach

| Asset Type | Location | Version Control |
|------------|----------|-----------------|
| SOPs, CRs, INVs, specifications | `QMS/` directory | QMS document lifecycle |
| QMS scripts, application code | Code directories (`qms-cli/`, `src/`, etc.) | Git commits wrapped by CRs |

**Git becomes the "qualified system" for code**, analogous to FactoryTalk AssetCentre in manufacturing.

---

## 2. Repository Structure

**Pipe Dream** is the overarching project encompassing both the Flow State application and the QMS framework.

```
pipe-dream/                   # The Pipe Dream project (repo root)
│
├── flow-state/               # Flow State application code
│   ├── core/
│   ├── model/
│   ├── engine/
│   ├── ui/
│   └── ...
│
├── qms-cli/                  # QMS infrastructure code (Python package)
│   ├── __init__.py
│   ├── __main__.py           # Entry point
│   ├── commands/             # Command implementations
│   ├── models/               # Data models (metadata, audit, etc.)
│   └── ...
│
├── QMS/                      # Controlled documents (NO CODE)
│   ├── SOP/                  # Standard Operating Procedures
│   ├── CR/                   # Change Records
│   ├── INV/                  # Investigations
│   ├── SDLC-FLOW/            # SDLC docs for Flow State
│   │   ├── SDLC-FLOW-RS.md
│   │   ├── SDLC-FLOW-DS.md
│   │   └── SDLC-FLOW-RTM.md
│   └── SDLC-QMS/             # SDLC docs for QMS CLI
│       ├── SDLC-QMS-RS.md
│       ├── SDLC-QMS-DS.md
│       └── SDLC-QMS-RTM.md
│
└── .claude/                  # Claude Code configuration and session data
    ├── qms.py                # Current QMS CLI (to be migrated to qms-cli/)
    ├── users/                # User workspaces and inboxes
    ├── chronicles/           # Session chronicles
    └── notes/                # Session notes
```

### Naming Hierarchy

| Term | Meaning | Location |
|------|---------|----------|
| **Pipe Dream** | The overarching project | `pipe-dream/` (repo root) |
| **Flow State** | The game/application | `pipe-dream/flow-state/` |
| **QMS CLI** | QMS infrastructure code | `pipe-dream/qms-cli/` |
| **QMS** | Controlled documents | `pipe-dream/QMS/` |

### Key Principles

1. **One repo, multiple systems:** Both Flow State and QMS CLI live in `pipe-dream/`
2. **Separate SDLC tracks:** Each system has its own SDLC documentation in `QMS/`
3. **Bidirectional traceability:** CRs reference code files and commits; SDLC documents (DS, RTM) reference the code version under which the System Release was qualified

---

## 3. Code Reference Format

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

---

## 4. The Two Development Models

### 4.1 Execution Branch (Standard Model — Frequent)

For all evolutionary work on existing systems, code changes happen within the CR lifecycle:

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
│  5. Document work in CR (files, commits)│
│                                         │
└─────────────────────────────────────────┘
    │
    ▼
Route for Post-Review
    │
    ├──► Problems found? ──► git revert, fix, iterate
    │
    ▼
Post-Approval ──► Close
```

**This IS GMP.** The git branch is merely the technical substrate; governance is fully present.

**Used for:**
- Adding features to Flow State
- Adding commands to QMS CLI
- Bug fixes
- Refactoring
- Any modification to existing code

### 4.2 Genesis Sandbox (Rare — New Systems Only)

For bringing an entirely new, self-contained system into existence:

- Long-running, free-form development
- Outside the QMS workflow (no CR governs it yet)
- Git branch pattern: `genesis/{system-name}` (e.g., `genesis/python-linter`)
- Ends when foundation and structural beams are in place

**Used for:**
- Initial creation of a wholly new tool
- Building the foundation of a new independent subsystem

**NOT used for:**
- Adding modules to existing systems
- Any work that would benefit from QA/TU review

**Adoption into Production:** See Section 5 for the formal QMS process by which a Genesis Sandbox's results are incorporated into the Production Environment.

### The Line Where GMP Begins

> **The line beyond which you would expect to learn real lessons and make discoveries/breakthroughs in our GMP-Inspired Recursive Governance Loop experiment.**

If the work would benefit from diverse perspectives, review, or documented rationale—GMP begins.

---

## 5. Adopting a Genesis Sandbox System into Production

When a Genesis Sandbox produces code that is ready for adoption, the process follows standard GMP—it's just a CR whose execution involves creating a new code directory rather than modifying existing code.

### 5.1 The Adoption CR

Create a CR to adopt the new system:

**CR Scope:**
- Create new code directory in Production (main branch)
- Create SDLC documentation (RS, DS, RTM)
- Establish initial qualified state

**CR Execution:**
1. Copy code from genesis branch to main branch (new directory)
2. Create SDLC documents via standard document workflows
3. Run acceptance testing
4. Document evidence in CR

### 5.2 Workflow Diagram

```
Genesis Sandbox                    Adoption Process                   Production
───────────────                    ────────────────                   ──────────

genesis/new-tool                   CR-XXX: Adopt new-tool             main branch
├── src/                           ────────────────────────
├── tests/                         Pre-Review
└── README.md                        ↓
                                   Pre-Approval
       │                             ↓
       │                           IN_EXECUTION
       │                           ┌─────────────────────────┐
       └──────────────────────────►│ 1. Create new-tool/     │──────► new-tool/
                                   │ 2. Create SDLC-NEWTOOL/ │        ├── src/
                                   │ 3. Run acceptance tests │        ├── tests/
                                   │ 4. Document evidence    │        └── README.md
                                   └─────────────────────────┘
                                             ↓                        QMS/SDLC-NEWTOOL/
                                   Post-Review                        ├── RS.md
                                             ↓                        ├── DS.md
                                   Post-Approval                      └── RTM.md
                                             ↓
                                   CLOSED
```

### 5.3 Rollback if Adoption Fails

If problems are discovered during post-review:

| Incremental CR (normal) | Adoption CR |
|-------------------------|-------------|
| `git revert` the commits | Delete the new code directory |
| Fix issues, re-execute | Fix in genesis branch, re-execute adoption |

The "revert" for an adoption is simply removing the new directory from Production. The genesis branch remains intact for fixes and re-adoption.

### 5.4 Key Insight

The adoption CR is not special—it follows the same workflow as any CR. The only difference is:
- **Normal CR:** Changes existing files
- **Adoption CR:** Creates a new directory (and its SDLC docs)

Both are governed by pre-review, pre-approval, execution, post-review, post-approval, close.

---

## 6. System Release Versioning

Each qualified system (Flow State, QMS-CLI, etc.) has a **System Release version** that tracks its qualified state over time.

### 6.1 Version Format

```
{SYSTEM}-{MAJOR}.{MINOR}
```

**Examples:**
- `FLOW-1.0` — First qualified release of Flow State
- `QMS-CLI-1.0` — First qualified release of QMS CLI
- `FLOW-1.3` — Third incremental update to Flow State after initial qualification

### 6.2 Version Lifecycle

| Event | Version Change | Trigger |
|-------|----------------|---------|
| Initial adoption from Genesis Sandbox | → 1.0 | Adoption CR closes |
| Subsequent CR affecting code | N.X → N.(X+1) | CR closes |
| Major architectural change | N.X → (N+1).0 | CR closes (at initiator discretion) |

### 6.3 Version Assignment

- **1.0:** Assigned when a system is first adopted, qualified, and released via an Adoption CR
- **Incremental (N.X+1):** Assigned when any CR affecting that system's code is closed
- **Major (N+1.0):** Assigned at initiator discretion for significant architectural changes

### 6.4 SDLC Document References

SDLC documents must reference the System Release version they describe:

```yaml
# In SDLC-FLOW-DS.md frontmatter or header
System Release: FLOW-1.3
Qualified Commit: a1b2c3d4e5f6
```

This ensures that:
- The DS describes a specific, reproducible state of the code
- Anyone can checkout the exact commit and see what was qualified
- Updates to the system trigger updates to SDLC documents

### 6.5 Relationship to CRs

Each CR that modifies a system's code:
1. References the **current** System Release version in scope
2. Upon closure, increments the version
3. SDLC documents are updated (if needed) to reflect the new version

```
CR-025: Add particle collision detection
  System: Flow State
  Current Version: FLOW-1.2

  [CR closes]

  New Version: FLOW-1.3
  SDLC-FLOW-DS updated to reference FLOW-1.3 @ commit abc1234
```

---

## 7. Traceability Model

### Code → Documentation

Every code change is traceable to its authorizing CR:
- Git commit message references CR ID
- CR execution section documents files modified and commit hashes

### Documentation → Code

SDLC documents reference the code they describe:
- RS requirements trace to code locations
- RTM maps requirements to test cases and code
- DS references implementation files

### Format

```
CR-015 execution:
  - Modified: src/core/commands.py @ a1b2c3d
  - Created: src/core/new_feature.py @ a1b2c3d
  - Tests: tests/test_new_feature.py @ a1b2c3d
```

---

## 8. Bootstrap Acknowledgment

We are not yet fully GMP-ready. Historical code changes without CRs are acceptable. Governance begins when we declare it begins.

This is not a problem—it's the natural state of any system before formal governance is established.

---

## 9. Summary: When to Use What

| Scenario | Approach |
|----------|----------|
| New feature for Flow State | CR with Execution Branch |
| New command for QMS CLI | CR with Execution Branch |
| Bug fix | CR with Execution Branch |
| Refactoring | CR with Execution Branch |
| Building foundation of entirely new tool | Genesis Sandbox |
| Adopting genesis tool into Production | CR (adoption CR) |
| Continued development of adopted tool | CR with Execution Branch |

---

## Superseded Content

This note supersedes the following sections from Session-001 notes (`qms-code-governance-concepts.md`):

- Sections 5-12 (Production vs. Test Environments) — replaced by refined Genesis Sandbox / Execution Branch model
- Open Questions — answered by adoption CR process

The following content from Session-001 remains valid and is incorporated above:
- Sections 1-4 (Separation of Concerns, Git as QMS, Directory Structure, Code Reference Format)
- GMP Analogy
- Bootstrap Problem acknowledgment

---

**End of Notes**
