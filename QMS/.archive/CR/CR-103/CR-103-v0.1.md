---
title: Establish docs/ and manual/ directories in qms-cli
revision_summary: Fix file count (6 → 7) per QA review
---

# CR-103: Establish docs/ and manual/ directories in qms-cli

## 1. Purpose

Separate qms-cli's documentation into two distinct packages: `docs/` for standard software documentation ("how to use the tool") and `manual/` for the QMS Manual ("how to operate a quality management system"). Currently both are mixed together in `seed/docs/` and duplicated into each project via `qms init`.

---

## 2. Scope

### 2.1 Context

- **Parent Document:** None — independent improvement identified during Session-2026-02-23-002 design discussion.

The realization: `seed/docs/` conflates two fundamentally different document packages that serve different audiences and change for different reasons. The CLI Reference changes when the code changes. The QMS Policy changes when the governance philosophy evolves. Mixing them in one directory and copying them into every project creates the same drift risk that caused INV-013 (template divergence).

### 2.2 Changes Summary

1. Create `qms-cli/docs/` with new software documentation (7 files)
2. Move `qms-cli/seed/docs/` to `qms-cli/manual/` (38 files)
3. Remove `seed_docs()` from init — projects no longer get a `QMS-Docs/` copy
4. Update `seed/claude.md` to reference `manual/` instead of `QMS-Docs/`
5. Update tests and SDLC documents

This CR does **not** touch `pipe-dream/QMS-Docs/`. That migration is deferred to a follow-up CR.

### 2.3 Files Affected

**New files (qms-cli):**

- `docs/README.md` — Docs index, scope boundary (docs vs manual)
- `docs/getting-started.md` — Installation, init, first document lifecycle
- `docs/cli-reference.md` — Every command, flag, option, permission matrix, MCP mapping
- `docs/project-structure.md` — Directory layout, three-tier metadata, naming conventions
- `docs/configuration.md` — qms.config.json, namespaces, environment variables
- `docs/users-and-permissions.md` — Groups, hierarchy, agent definitions
- `docs/mcp-server.md` — Transports, client config, container access

**Moved files (qms-cli):**

- `seed/docs/*` (38 files) → `manual/*`

**Modified files (qms-cli):**

- `commands/init.py` — Remove `seed_docs()`, remove QMS-Docs blocker
- `seed/claude.md` — Update QMS-Docs references to `manual/` path
- `tests/qualification/test_init.py` — Remove QMS-Docs tests, add structure tests

**Modified QMS documents (pipe-dream):**

- `SDLC-QMS-RS` — Revise REQ-INIT-006
- `SDLC-QMS-RTM` — Update REQ-INIT-006 verification

---

## 3. Current State

All qms-cli documentation (38 files) lives in `seed/docs/`. The `qms init` command copies these files to `{project}/QMS-Docs/` at the project root. This creates two independent copies that can drift. The documentation mixes two distinct concerns: software tool documentation and QMS operational methodology.

---

## 4. Proposed State

qms-cli has two documentation directories:

- **`docs/`** — Standard software documentation. How to install, configure, and use the CLI tool. 7 files covering getting started, CLI reference, project structure, configuration, users/permissions, and MCP server setup.
- **`manual/`** — The QMS Manual. Policy, governance philosophy, operational guidance, deviation management, evidence standards, review expectations. 38 files (the former `seed/docs/` contents).

`qms init` no longer copies documentation to the project root. Projects read the manual from the submodule path (e.g., `qms-cli/manual/`). The `seed/` directory retains templates, agents, hooks, and the starter CLAUDE.md.

---

## 5. Change Description

### 5.1 New: docs/ directory

Seven new files drafted from the actual codebase (argparse definitions, qms_config.py, init.py, MCP server). Content is self-contained — does not depend on or link into the manual. The README establishes the boundary: "For how to operate a QMS, see the Manual."

### 5.2 Move: seed/docs/ → manual/

All 38 existing files relocate from `seed/docs/` to `manual/`. Internal cross-references use relative paths (`[Workflows](03-Workflows.md)`) and remain valid. The `README.md` updates its heading from "QMS Documentation" to "QMS Manual" and removes the `../` reference to streamlined SOPs.

### 5.3 Modify: init.py

- Remove `seed_docs()` function (lines 178-192)
- Remove QMS-Docs blocker from `check_clean_runway()` (lines 59-60)
- Remove `seed_docs(root)` call from `cmd_init()` (line 351)
- Update docstring to remove "QMS-Docs/ educational documentation"
- Update success message: remove "Review QMS-Docs/" line, add note pointing to `qms-cli/manual/`

### 5.4 Modify: seed/claude.md

Update session start checklist paths:
```
QMS-Docs/QMS-Policy.md    →  qms-cli/manual/QMS-Policy.md
QMS-Docs/START_HERE.md     →  qms-cli/manual/START_HERE.md
QMS-Docs/QMS-Glossary.md   →  qms-cli/manual/QMS-Glossary.md
```

### 5.5 Modify: tests

- Remove `test_init_seeds_docs` (init no longer seeds docs)
- Remove `test_init_blocked_by_existing_qms_docs` (no QMS-Docs blocker)
- Update `test_init_with_root_flag` to remove QMS-Docs assertion
- Add `test_docs_directory_exists` — smoke test that `docs/` has expected core files
- Add `test_manual_directory_exists` — smoke test that `manual/` has expected core files

### 5.6 SDLC impact

**REQ-INIT-006** currently reads: "The init command shall seed a QMS-Docs/ directory at the project root with educational documentation from qms-cli/seed/docs/."

Revise to: "qms-cli shall provide a manual/ directory containing QMS operational documentation and a docs/ directory containing software documentation."

This changes from a runtime behavior (init seeds docs) to a structural requirement (directories exist in the distribution). The corresponding RTM test changes from verifying init output to verifying directory contents.

---

## 6. Justification

- **Eliminates drift risk.** Two copies of the same content (seed/docs/ and project/QMS-Docs/) inevitably diverge. INV-013 proved this with templates. A single canonical location prevents the problem.
- **Clarifies documentation purpose.** Software docs and operational methodology serve different audiences and change at different rates. Mixing them confuses both.
- **Simplifies init.** One fewer directory to copy, one fewer blocker to check, one fewer thing to go wrong.
- **Establishes the standard layout.** `docs/` follows the universal convention for software documentation. `manual/` is a clear, distinct name for the methodology layer.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `docs/` (7 files) | Create | New software documentation directory |
| `manual/` (38 files) | Create (move) | QMS Manual, relocated from seed/docs/ |
| `seed/docs/` (38 files) | Delete | Replaced by manual/ |
| `commands/init.py` | Modify | Remove seed_docs, remove QMS-Docs blocker |
| `seed/claude.md` | Modify | Update documentation paths |
| `tests/qualification/test_init.py` | Modify | Update test expectations |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RS | Modify | Revise REQ-INIT-006 |
| SDLC-QMS-RTM | Modify | Update REQ-INIT-006 verification evidence |

### 7.3 Other Impacts

- **Existing projects:** Projects already initialized with `QMS-Docs/` at root are unaffected. The old directory stays in place. Migration is a separate concern (deferred).
- **pipe-dream specifically:** `pipe-dream/QMS-Docs/` is untouched. A follow-up CR will update pipe-dream's CLAUDE.md and agent definitions to point to `qms-cli/manual/` and remove the redundant copy.
- **New projects:** After this CR, `qms init` no longer creates `QMS-Docs/`. The seeded `CLAUDE.md` points to `qms-cli/manual/` instead.

### 7.4 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in `.test-env/` (local) or `/projects/` (containerized agents). No other locations are permitted.
2. **Branch isolation:** All development on branch `cr-103/exec`
3. **Write protection:** `.claude/settings.local.json` blocks direct writes to `qms-cli/`
4. **Qualification required:** All new/modified requirements must have passing tests before merge
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR after RS/RTM approval
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | Current commit (6e73be8) | EFFECTIVE v19.0 / v24.0 | CLI-15.0 |
| During execution | Unchanged | DRAFT (checked out) | CLI-15.0 (unchanged) |
| Post-approval | Merged from cr-103/exec | EFFECTIVE v20.0 / v25.0 | CLI-16.0 |

---

## 8. Testing Summary

### Automated Verification

- Existing test suite (677 tests) must continue to pass
- Remove tests for deleted functionality (QMS-Docs seeding, QMS-Docs blocker)
- Add tests verifying `docs/` and `manual/` directory structure
- CI must pass on execution branch

### Integration Verification

- Run `qms init` in a clean directory and verify:
  - `QMS-Docs/` is NOT created
  - Seeded `CLAUDE.md` references `qms-cli/manual/` paths
  - All other init artifacts are created as before
- Verify `docs/` and `manual/` contents are complete and accessible

---

## 9. Implementation Plan

### 9.1 Phase 1: Test Environment Setup

1. Verify/create `.test-env/` development directory
2. Clone/update qms-cli from GitHub
3. Create and checkout branch `cr-103/exec`
4. Run baseline tests (expect 677 pass)

### 9.2 Phase 2: Requirements (RS Update)

1. Checkout SDLC-QMS-RS in production QMS
2. Revise REQ-INIT-006 to reflect new directory structure
3. Checkin RS, route for review and approval

### 9.3 Phase 3: Implementation — Create docs/

1. Create `docs/` directory with 7 files (from Session-2026-02-23-002 docs-draft)
2. Commit

### 9.4 Phase 4: Implementation — Move seed/docs/ to manual/

1. Move all 38 files from `seed/docs/` to `manual/`
2. Update `manual/README.md` heading and remove stale cross-reference
3. Remove empty `seed/docs/` directory
4. Commit

### 9.5 Phase 5: Implementation — Update init and seed

1. Remove `seed_docs()` function from `commands/init.py`
2. Remove QMS-Docs blocker from `check_clean_runway()`
3. Remove `seed_docs(root)` call from `cmd_init()`
4. Update init docstring and success message
5. Update `seed/claude.md` to reference `qms-cli/manual/` paths
6. Commit

### 9.6 Phase 6: Implementation — Update tests

1. Remove `test_init_seeds_docs`
2. Remove `test_init_blocked_by_existing_qms_docs`
3. Update `test_init_with_root_flag` to remove QMS-Docs assertion
4. Add `test_docs_directory_exists`
5. Add `test_manual_directory_exists`
6. Run full test suite, verify all tests pass
7. Commit

### 9.7 Phase 7: Qualification

1. Push to cr-103/exec branch
2. Verify GitHub Actions CI passes
3. Document qualified commit hash

### 9.8 Phase 8: Integration Verification

1. Run `qms init` in a clean temporary directory
2. Verify `QMS-Docs/` is NOT created
3. Verify seeded `CLAUDE.md` references `qms-cli/manual/`
4. Verify all other init artifacts are correct

### 9.9 Phase 9: RTM Update and Approval

1. Checkout SDLC-QMS-RTM in production QMS
2. Update REQ-INIT-006 verification evidence
3. Checkin RTM, route for review and approval
4. **Verify RTM reaches EFFECTIVE status before proceeding to Phase 10**

### 9.10 Phase 10: Merge and Submodule Update

**Prerequisite:** RS and RTM must both be EFFECTIVE.

1. Verify RS is EFFECTIVE
2. Verify RTM is EFFECTIVE
3. Create PR to merge cr-103/exec to main
4. Merge PR using merge commit (not squash)
5. Verify qualified commit is reachable on main
6. Update submodule pointer in pipe-dream
7. Verify functionality in production context

---

## 10. Execution

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution commit (baseline) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Phase 1: Test environment setup, baseline tests (677) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Phase 2: RS update — revise REQ-INIT-006 | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Phase 3: Create docs/ directory (7 files) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Phase 4: Move seed/docs/ to manual/ (38 files) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Phase 5: Update init.py and seed/claude.md | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | Phase 6: Update tests, run full suite | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-8 | Phase 7: Push, CI verification, document qualified commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-9 | Phase 8: Integration verification — qms init in clean dir | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-10 | Phase 9: RTM update and approval | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-11 | Phase 10: Merge, submodule update, production verification | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-12 | Post-execution commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

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
- **SOP-006:** SDLC
- **INV-013:** Template divergence investigation (precedent for drift risk)
- **CR-102:** Bootstrap overhaul that created seed/docs/ structure
- **Session-2026-02-23-002:** Design discussion and docs-draft artifacts

---

**END OF DOCUMENT**
