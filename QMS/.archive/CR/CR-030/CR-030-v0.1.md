---
title: Restructure pipe-dream into submodules
revision_summary: Initial draft
---

# CR-030: Restructure pipe-dream into submodules

## 1. Purpose

Restructure the pipe-dream repository to separate concerns between the QMS Project, the QMS CLI tool, and the Flow State application by extracting qms-cli and flow-state into independent git repositories managed as submodules within pipe-dream.

This restructuring solves the testing paradox: agents can branch flow-state for code testing without affecting the governance layer (SOPs, inboxes, CRs).

---

## 2. Scope

### 2.1 Context

Independent improvement identified during architectural review. The current monolithic structure prevents qms-cli reusability and creates governance instability during code testing.

- **Parent Document:** None

### 2.2 Changes Summary

- Extract `qms-cli/` into a standalone git repository
- Extract Flow State code (`core/`, `engine/`, `model/`, `ui/`, `main.py`, etc.) into a standalone git repository named `flow-state`
- Convert pipe-dream from a monolithic repo to a QMS Project containing submodule references
- Preserve all git history (no history loss)

### 2.3 Files Affected

- `.gitmodules` - Create (submodule configuration)
- `qms-cli/` - Convert to submodule reference
- `flow-state/` - Create as submodule (containing extracted code)
- `core/`, `engine/`, `model/`, `ui/`, `main.py`, etc. - Remove from direct tracking (moved to flow-state)
- `CLAUDE.md` - Update with new project structure

---

## 3. Current State

The pipe-dream repository is a monolithic git repo containing:
- QMS CLI tool code (`qms-cli/`)
- Flow State application code (`core/`, `engine/`, `model/`, `ui/`, `main.py`)
- QMS controlled documents (`QMS/`)
- QMS project configuration (`.claude/users/`, `.claude/agents/`)

All components share a single git history. Branching for code testing affects the governance layer.

---

## 4. Proposed State

The pipe-dream repository serves as the QMS Project root, containing:
- QMS controlled documents (`QMS/`)
- QMS project configuration (`.claude/`)
- Submodule reference to `qms-cli` (standalone git repo)
- Submodule reference to `flow-state` (standalone git repo)

Each component has independent git history. Agents can branch flow-state without affecting QMS documents or inbox state.

---

## 5. Change Description

### 5.1 Repository Structure

**Before:**
```
pipe-dream/                     # Single git repo
├── qms-cli/                    # Tool code (tracked directly)
├── QMS/                        # Controlled documents
├── .claude/                    # Users, agents, config
├── core/                       # Flow State code (tracked directly)
├── engine/
├── model/
├── ui/
└── main.py
```

**After:**
```
pipe-dream/                     # Git repo (QMS Project)
├── .gitmodules                 # Submodule configuration
├── qms-cli/                    # Submodule → github.com/.../qms-cli
├── flow-state/                 # Submodule → github.com/.../flow-state
├── QMS/                        # Stays in pipe-dream
└── .claude/                    # Stays in pipe-dream
```

### 5.2 History Extraction

Use `git subtree split` or `git filter-repo` to extract subdirectories with their history:

**qms-cli extraction:**
- Extract commits touching `qms-cli/` files
- Rewrite paths (`qms-cli/qms.py` → `qms.py`)
- Push to new `qms-cli` repository

**flow-state extraction:**
- Extract commits touching `core/`, `engine/`, `model/`, `ui/`, `main.py`, and related files
- Rewrite paths to root level
- Push to new `flow-state` repository

### 5.3 History Preservation

- pipe-dream retains complete original history (all commits from day 1)
- Extracted repos contain copies with rewritten paths (different commit hashes)
- Old CRs reference pipe-dream commits; new CRs reference respective repo commits
- No information is lost; navigation requires knowing the transition point

### 5.4 SDLC-QMS Location

SDLC-QMS (QMS CLI qualification documents) remains in `QMS/SDLC-QMS/` within pipe-dream. The QMS Project governs qms-cli externally via submodule.

### 5.5 Submodule Workflow

After restructuring:
- Clone pipe-dream with `--recurse-submodules` to get all code
- Work on flow-state: `cd flow-state && git checkout -b feature-branch`
- QMS documents in pipe-dream remain on main branch, unaffected
- Update submodule pointer when ready: `cd .. && git add flow-state && git commit`

---

## 6. Justification

- **Testing paradox:** Currently, branching for code testing moves SOPs and inbox tasks. Agents cannot safely test code changes without governance instability.
- **qms-cli reusability:** The tool is hardcoded to pipe-dream's structure. Extraction enables future portability to other projects.
- **Separation of concerns:** Code changes and governance changes should have independent commit streams.
- **Impact of not changing:** Continued inability to test code safely; qms-cli remains non-portable; interleaved history grows increasingly complex.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `.gitmodules` | Create | Submodule configuration for qms-cli and flow-state |
| `qms-cli/` | Modify | Convert from directory to submodule reference |
| `flow-state/` | Create | New submodule containing extracted code |
| `core/` | Delete | Moved to flow-state repo |
| `engine/` | Delete | Moved to flow-state repo |
| `model/` | Delete | Moved to flow-state repo |
| `ui/` | Delete | Moved to flow-state repo |
| `main.py` | Delete | Moved to flow-state repo |
| `CLAUDE.md` | Modify | Update project structure documentation |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| CLAUDE.md | Modify | Update to reflect new structure, submodule workflow |

### 7.3 Other Impacts

- **Clone instructions:** Contributors must use `git clone --recurse-submodules`
- **CI/CD:** May need updates if any automation assumes monolithic structure
- **Commit references:** Old CRs reference pipe-dream commits; transition documented in this CR

---

## 8. Testing Summary

- Verify pipe-dream clone with `--recurse-submodules` populates all directories
- Verify flow-state can be branched independently without affecting QMS/ or .claude/
- Verify qms-cli functions correctly from submodule location
- Verify old commits in pipe-dream can still be checked out (pre-transition state)
- Verify SDLC-QMS documents remain accessible and functional

---

## 9. Implementation Plan

### 9.1 Preparation

1. Create new empty repositories for qms-cli and flow-state (GitHub/remote)
2. Document the current HEAD commit of pipe-dream as the pre-transition reference point

### 9.2 Extract qms-cli

1. Clone pipe-dream to a working directory (preserve original)
2. Use `git filter-repo --subdirectory-filter qms-cli/` to extract qms-cli history
3. Push extracted history to new qms-cli repository
4. Tag the extraction point in qms-cli repo

### 9.3 Extract flow-state

1. Clone pipe-dream to a fresh working directory
2. Use `git filter-repo` with path filters for core/, engine/, model/, ui/, main.py, and related files
3. Push extracted history to new flow-state repository
4. Tag the extraction point in flow-state repo

### 9.4 Convert pipe-dream to submodules

1. In pipe-dream, remove qms-cli/ and flow-state code directories from tracking
2. Add qms-cli as submodule: `git submodule add <qms-cli-url> qms-cli`
3. Add flow-state as submodule: `git submodule add <flow-state-url> flow-state`
4. Commit the restructuring

### 9.5 Update Documentation

1. Update CLAUDE.md with new project structure
2. Document transition point and commit hash mapping
3. Update clone instructions

### 9.6 Validation

1. Fresh clone with `--recurse-submodules`
2. Verify all functionality works
3. Test branching flow-state independently

---

## 10. Execution

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Create remote repositories for qms-cli and flow-state | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Extract qms-cli history to new repository | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Extract flow-state history to new repository | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Convert pipe-dream to use submodules | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Update CLAUDE.md with new structure | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Validate clone and functionality | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

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
- **SOP-005:** Code Governance
- **Session notes:** `.claude/notes/Session-2026-01-17-001/restructuring-plan.md`
- **Session notes:** `.claude/notes/Session-2026-01-17-001/qms-cli-reusability-vision.md`

---

**END OF DOCUMENT**
