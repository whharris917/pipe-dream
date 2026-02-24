---
title: Relocate QMS Manual to standalone repo at Quality-Manual/
revision_summary: Initial draft
---

# CR-105: Relocate QMS Manual to standalone repo at Quality-Manual/

## 1. Purpose

Move the QMS operational manual (38 files) from `qms-cli/manual/` to a standalone repository (`whharris917/quality-manual`), included as a submodule at `Quality-Manual/` in both `claude-qms` and `pipe-dream`. This gives end users and developers identical directory structures and places the manual at a prominent, distribution-level location.

---

## 2. Scope

### 2.1 Context

Independent improvement. The manual describes how to operate a QMS, not how to use the CLI tool. It belongs at the distribution level, not inside the tooling repo.

- **Parent Document:** None

### 2.2 Changes Summary

1. Create `whharris917/quality-manual` repo with the 38 manual files
2. Remove `manual/` from qms-cli (in `.test-env/qms-cli`) and update all internal references
3. Add `Quality-Manual` submodule to `claude-qms` and `pipe-dream`
4. Rename `pipe-dream/QMS-Docs/` to `.QMS-Docs/` (hidden, retained)
5. Update all pipe-dream references (CLAUDE.md, agent definitions)
6. Revise SDLC documents (RS/RTM for both QMS and CQ namespaces)

### 2.3 Files Affected

**New repo: `quality-manual`**
- All 38 files from `qms-cli/manual/` (root `.md` files, `guides/`, `types/`)

**qms-cli (developed in `.test-env/qms-cli`):**
- `manual/` — Delete (38 files)
- `seed/claude.md` — Update 4 path references
- `commands/init.py` — Update success message
- `docs/README.md` — Update cross-reference
- `docs/getting-started.md` — Update cross-reference
- `seed/agents/tu.md` — Update 3 path references
- `tests/qualification/test_init.py` — Remove `test_manual_directory_exists()`

**claude-qms:**
- `.gitmodules` — Add Quality-Manual submodule
- `README.md` — Update project structure and paths

**pipe-dream:**
- `.gitmodules` — Add Quality-Manual submodule
- `QMS-Docs/` — Rename to `.QMS-Docs/`
- `CLAUDE.md` — Update 5 path references
- `.claude/agents/qa.md` — Update 4 path references
- `.claude/agents/bu.md` — Update 3 path references
- `.claude/agents/tu_ui.md` — Update 3 path references
- `.claude/agents/tu_scene.md` — Update 3 path references
- `.claude/agents/tu_sketch.md` — Update 3 path references
- `.claude/agents/tu_sim.md` — Update 3 path references

---

## 3. Current State

The QMS operational manual (38 markdown files covering policy, glossary, numbered guides, operational guides, and document type references) lives at `qms-cli/manual/`. CR-103 placed it there after splitting `seed/docs/` into `docs/` (software docs) and `manual/` (operational docs).

`pipe-dream/QMS-Docs/` contains a stale copy of the same content from before CR-103.

End users who clone `claude-qms` see the manual at `qms-cli/manual/` — nested inside the tooling submodule.

---

## 4. Proposed State

The manual lives in its own repository (`whharris917/quality-manual`), included as a git submodule at `Quality-Manual/` in both `claude-qms` and `pipe-dream`.

End users who clone `claude-qms` see `Quality-Manual/` at their project root — a cleaner, more prominent location. `pipe-dream` mirrors this structure identically.

`qms-cli` no longer ships the manual. Its `docs/` directory remains for software documentation. `pipe-dream/QMS-Docs/` is hidden as `.QMS-Docs/` with no active references.

---

## 5. Change Description

### 5.1 New Repository: quality-manual

Create `whharris917/quality-manual` (public) containing all 38 files currently at `qms-cli/manual/`:
- Root: `QMS-Policy.md`, `QMS-Glossary.md`, `START_HERE.md`, `README.md`, `FAQ.md`, numbered guides `01-Overview.md` through `12-CLI-Reference.md`
- `guides/`: 9 operational guides
- `types/`: 12 document type references

### 5.2 qms-cli: Remove manual/ and Update References

All work in `.test-env/qms-cli` on branch `cr-105/exec`.

Delete `manual/` directory. Update all references from `qms-cli/manual/...` to `Quality-Manual/...`:
- `seed/claude.md`: Session start checklist paths
- `commands/init.py`: Success message after `qms init`
- `docs/README.md`: Cross-reference to manual (relative link becomes prose reference to `Quality-Manual/` at project root)
- `docs/getting-started.md`: Same treatment
- `seed/agents/tu.md`: Agent reading directives

Remove `test_manual_directory_exists()` from qualification tests.

### 5.3 claude-qms: Add Quality-Manual Submodule

Work in `.test-env/claude-qms`. Add `quality-manual` as a submodule at path `Quality-Manual/`. Update `README.md` to reflect new project structure and documentation paths.

### 5.4 pipe-dream: Add Submodule and Clean Up References

Add `quality-manual` as a submodule at path `Quality-Manual/`. Rename `QMS-Docs/` to `.QMS-Docs/`. Update all references in `CLAUDE.md` and agent definitions from `QMS-Docs/...` to `Quality-Manual/...`.

---

## 6. Justification

- **Separation of concerns:** The manual describes QMS operations, not CLI tool usage. It belongs at the distribution level, not inside the tooling repo.
- **Path consistency:** End users and pipe-dream developers see identical `Quality-Manual/` at their project root.
- **Reusability:** As a standalone repo, the manual can be included by any QMS-governed project without pulling the full CLI.
- **Prominence:** `Quality-Manual/` at the project root is more discoverable than `qms-cli/manual/` nested inside a submodule.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `quality-manual/*` (38 files) | Create | New repo with manual content |
| `qms-cli/manual/*` (38 files) | Delete | Remove from CLI repo |
| `qms-cli/seed/claude.md` | Modify | Update 4 path references |
| `qms-cli/commands/init.py` | Modify | Update success message |
| `qms-cli/docs/README.md` | Modify | Update cross-reference |
| `qms-cli/docs/getting-started.md` | Modify | Update cross-reference |
| `qms-cli/seed/agents/tu.md` | Modify | Update 3 path references |
| `qms-cli/tests/qualification/test_init.py` | Modify | Remove 1 test function |
| `claude-qms/.gitmodules` | Modify | Add submodule entry |
| `claude-qms/README.md` | Modify | Update structure and paths |
| `pipe-dream/.gitmodules` | Modify | Add submodule entry |
| `pipe-dream/QMS-Docs/` | Rename | → `.QMS-Docs/` |
| `pipe-dream/CLAUDE.md` | Modify | Update 5 path references |
| `pipe-dream/.claude/agents/*.md` (6 files) | Modify | Update path references |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RS | Modify | Revise REQ-INIT-006 (remove manual/ clause) |
| SDLC-QMS-RTM | Modify | Remove test mapping, update baseline |
| SDLC-CQ-RS | Modify | Add Quality-Manual submodule requirement |
| SDLC-CQ-RTM | Modify | Add verification evidence |

### 7.3 Other Impacts

- All existing projects using `qms-cli/manual/` paths (seeded from `seed/claude.md`) will have stale references until they update their `CLAUDE.md`. New projects seeded after this CR will have correct paths.
- Projects must clone with `--recurse-submodules` to get the manual (already required for `qms-cli`).

### 7.4 Development Controls

This CR implements changes to **qms-cli**, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in `.test-env/qms-cli` (local). No direct writes to production `qms-cli/` submodule.
2. **Branch isolation:** All development on branch `cr-105/exec`
3. **Write protection:** PreToolUse hook blocks direct writes to `qms-cli/`
4. **Qualification required:** All modified requirements must have passing tests before merge
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR after RS/RTM approval
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | f6f82db | EFFECTIVE v21.0/v26.0 | CLI-17.0 |
| During execution | Unchanged | DRAFT (checked out) | CLI-17.0 (unchanged) |
| Post-approval | Merged from cr-105/exec | EFFECTIVE v22.0/v27.0 | CLI-18.0 |

---

## 8. Testing Summary

<!--
NOTE: Do NOT delete this comment. It provides guidance during document authoring.

For code CRs, address both categories per SOP-002 Section 6.8:
1. Automated verification: unit tests, qualification tests, CI
2. Integration verification: what will be exercised through user-facing levers
   in a running system to demonstrate the change is effective

For document-only CRs, a description of procedural verification is sufficient.
Delete the subsections below and use a simple list.
-->

### Automated Verification

- Full qms-cli test suite must pass in `.test-env/qms-cli` with `manual/` removed and `test_manual_directory_exists` removed
- Expect test count to drop by 1 (from 688 to 687)
- No new tests needed — removal is the change

### Integration Verification

- Clone `claude-qms` with `--recurse-submodules` into `/tmp` and verify `Quality-Manual/` is populated with all 38 files
- Verify `pipe-dream/Quality-Manual/` is populated after submodule add
- Grep pipe-dream working tree for stale references to `QMS-Docs/` and `qms-cli/manual/` — must find zero in active files

---

## 9. Implementation Plan

### 9.1 Phase 1: Pre-execution Baseline

1. Commit and push pipe-dream to capture pre-execution state

### 9.2 Phase 2: Create quality-manual Repo

1. Create `whharris917/quality-manual` (public) via `gh repo create`
2. Populate with all 38 files from `qms-cli/manual/`
3. Push initial commit

### 9.3 Phase 3: Test Environment Setup (qms-cli)

1. Verify `.test-env/qms-cli` exists and is on main
2. Create and checkout branch `cr-105/exec`
3. Verify clean baseline (688 tests)

### 9.4 Phase 4: Implementation (qms-cli)

All work in `.test-env/qms-cli` on branch `cr-105/exec`:

1. Delete `manual/` directory
2. Update `seed/claude.md` path references
3. Update `commands/init.py` success message
4. Update `docs/README.md` cross-reference
5. Update `docs/getting-started.md` cross-reference
6. Update `seed/agents/tu.md` path references
7. Remove `test_manual_directory_exists()` from test suite

### 9.5 Phase 5: Qualification (qms-cli)

1. Run full test suite in `.test-env/qms-cli` — expect 687 pass
2. Push to `cr-105/exec`
3. Verify GitHub Actions CI passes
4. Document qualified commit hash

### 9.6 Phase 6: SDLC Updates

1. Checkout SDLC-QMS-RS: revise REQ-INIT-006 (remove manual/ clause)
2. Route RS for review and approval → EFFECTIVE
3. Checkout SDLC-QMS-RTM: remove `test_manual_directory_exists` from REQ-INIT-006, update baseline
4. Route RTM for review and approval → EFFECTIVE
5. Checkout SDLC-CQ-RS: add requirement for Quality-Manual submodule
6. Route CQ-RS for review and approval → EFFECTIVE
7. Checkout SDLC-CQ-RTM: add verification evidence
8. Route CQ-RTM for review and approval → EFFECTIVE

### 9.7 Phase 7: Merge and Submodule Updates

**Prerequisite:** RS and RTM must both be EFFECTIVE before proceeding.

1. Create PR for qms-cli `cr-105/exec` → main, merge (merge commit, not squash)
2. Verify qualified commit is reachable on main
3. In `.test-env/claude-qms`: add Quality-Manual submodule, update README, push
4. In pipe-dream: add Quality-Manual submodule
5. Rename `QMS-Docs/` → `.QMS-Docs/`
6. Update pipe-dream CLAUDE.md and all agent definitions
7. Update pipe-dream submodule pointers (qms-cli, claude-qms)

### 9.8 Phase 8: Post-execution

1. Commit and push pipe-dream to capture post-execution state

---

## 10. Execution

<!--
EXECUTION PHASE INSTRUCTIONS
============================
NOTE: Do NOT delete this comment block. It provides guidance for execution.

PRE-EXECUTION: After releasing for execution, the first execution item is to
commit and push the project repository (including all submodules) to capture
the pre-execution baseline (per SOP-004 Section 5). Record the commit hash
in EI-1's execution summary.

POST-EXECUTION: The final execution item is to commit and push the project
repository (including all submodules) to capture the post-execution state
(per SOP-004 Section 5). Record the commit hash in the final EI's execution
summary.

- Sections 1-9 are PRE-APPROVED content - do NOT modify during execution
- Only THIS TABLE and the comment sections below should be edited during execution phase

COLUMNS:
- EI: Execution item identifier
- Task Description: What to do (static, from Implementation Plan)
- VR: "Yes" if integration verification required (static, set during planning);
  replaced with VR ID during execution (editable). Blank if no VR needed.
  See SOP-004 Section 9C.
- Execution Summary: Narrative of what was done, evidence, observations (editable)
- Task Outcome: Pass or Fail (editable)
- Performed By - Date: Signature (editable)

TASK OUTCOME:
- Pass: Task completed as planned
- Fail: Task could not be completed as planned - attach VAR with explanation

VAR TYPES (see VAR-TEMPLATE):
- Type 1: Use when the failed task is critical to CR objectives
- Type 2: Use when impact is contained and CR can conceptually close

EXECUTION SUMMARY EXAMPLES:
- "Implemented per plan. Commit abc123."
- "Modified src/module.py:45-67. Unit tests passing."
- "Created SOP-007 (now EFFECTIVE)."
-->

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution baseline commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Create `whharris917/quality-manual` repo, populate with 38 files from `qms-cli/manual/` | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Set up `.test-env/qms-cli` test environment, create branch `cr-105/exec` | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | In `.test-env/qms-cli`: delete `manual/` directory | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | In `.test-env/qms-cli`: update references (seed/claude.md, commands/init.py, docs/README.md, docs/getting-started.md, seed/agents/tu.md) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | In `.test-env/qms-cli`: remove `test_manual_directory_exists` from tests | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | Run full qms-cli test suite in `.test-env/qms-cli`, push branch, verify CI | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-8 | Update SDLC-QMS-RS (revise REQ-INIT-006) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-9 | Update SDLC-QMS-RTM (remove test mapping, update baseline) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-10 | Update SDLC-CQ-RS (add Quality-Manual submodule requirement) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-11 | Update SDLC-CQ-RTM (add verification evidence) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-12 | Merge qms-cli PR (`cr-105/exec` → main) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-13 | In `.test-env/claude-qms`: add Quality-Manual submodule, update README, push | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-14 | Add Quality-Manual submodule to pipe-dream | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-15 | Rename `QMS-Docs/` → `.QMS-Docs/` in pipe-dream | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-16 | Update pipe-dream CLAUDE.md and all agent definitions | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-17 | Update pipe-dream submodule pointers (qms-cli, claude-qms) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-18 | Post-execution commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Add rows as needed. When adding rows, fill columns 3-5 during execution.
-->

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during execution.
Add rows as needed.

This section is the appropriate place to attach VARs that do not apply
to any individual execution item, but apply to the CR as a whole.
-->

---

## 11. Execution Summary

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Complete this section after all EIs are executed.
Summarize the overall outcome and any deviations from the plan.
-->

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-005:** Software Development Lifecycle
- **SOP-006:** Requirements and Traceability
- **CR-103:** Established docs/ and manual/ directories in qms-cli
- **CR-104:** Created claude-qms distribution repo

---

**END OF DOCUMENT**
