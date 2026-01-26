---
title: Add qms-cli initialization and bootstrapping functionality
revision_summary: Initial draft
---

# CR-036: Add qms-cli initialization and bootstrapping functionality

## 1. Purpose

Enable new users to bootstrap a fully functional QMS project from a fresh clone of qms-cli. Currently, qms-cli requires pre-existing infrastructure (QMS/ directory, user workspaces, templates, SOPs) that does not exist when the repository is cloned. This CR adds initialization functionality that creates all necessary infrastructure, making qms-cli immediately usable for new projects.

---

## 2. Scope

### 2.1 Context

Independent improvement identified during evaluation of qms-cli usability for external users. A developer cloning qms-cli today cannot use it without manually creating significant infrastructure.

- **Parent Document:** None

### 2.2 Changes Summary

1. Add `qms.config.json` discovery mechanism for project root identification
2. Add `qms init` command to bootstrap new QMS projects
3. Add user management via agent definition files (`.claude/agents/`)
4. Seed new projects with sanitized SOPs and document templates
5. Update RS to move "Project initialization" from exclusions to requirements
6. Update RTM with verification evidence for new requirements

### 2.3 Files Affected

**qms-cli code changes (on development branch):**
- `qms-cli/qms.py` - Add init command entry point
- `qms-cli/commands/init.py` - New file: init command implementation
- `qms-cli/commands/user.py` - New file: user management commands
- `qms-cli/qms_config.py` - Extend for config file discovery
- `qms-cli/qms_auth.py` - Modify to read groups from agent files
- `qms-cli/commands/__init__.py` - Register new commands
- `qms-cli/seed/` - New directory: sanitized SOPs and templates for seeding
- `qms-cli/tests/qualification/test_init.py` - New file: qualification tests for init
- `qms-cli/README.md` - Update with init usage and project structure guidance

**QMS documents (in production pipe-dream/QMS):**
- `QMS/SDLC-QMS/SDLC-QMS-RS.md` - Add initialization requirements
- `QMS/SDLC-QMS/SDLC-QMS-RTM.md` - Add verification evidence

**pipe-dream agent files (backward compatibility migration):**
- `.claude/agents/qa.md` - Add `group: quality` to frontmatter
- `.claude/agents/bu.md` - Add `group: reviewer` to frontmatter
- `.claude/agents/tu_ui.md` - Add `group: reviewer` to frontmatter
- `.claude/agents/tu_scene.md` - Add `group: reviewer` to frontmatter
- `.claude/agents/tu_sketch.md` - Add `group: reviewer` to frontmatter
- `.claude/agents/tu_sim.md` - Add `group: reviewer` to frontmatter

Note: `lead` and `claude` are hardcoded as administrators in qms_auth.py and do not require agent definition files.

---

## 3. Current State

- qms-cli requires pre-existing QMS/ directory structure to function
- qms-cli requires pre-existing user workspace/inbox directories
- qms-cli requires pre-existing document templates
- User permissions are hardcoded in qms_auth.py
- Project root discovery relies on finding QMS/ directory
- The RS explicitly excludes "Project initialization" from CLI scope (Section 5.4)

---

## 4. Proposed State

- qms-cli can bootstrap a complete QMS project via `qms init` command
- Project root is identified by `qms.config.json` file (created by init, or pre-existing)
- User permissions are defined in `.claude/agents/{user}.md` files with `group:` frontmatter
- New projects are seeded with sanitized SOPs (v1.0, no project-specific references) and document templates
- The RS includes initialization requirements; exclusion is removed
- qms-cli remains continuously qualified through atomic version transition

---

## 5. Change Description

### 5.1 Config File Discovery

Add `qms.config.json` as the authoritative project root marker:

```json
{
  "version": "1.0",
  "created": "2026-01-24T12:00:00Z",
  "sdlc_namespaces": []
}
```

**Discovery Algorithm:**
1. Start from current working directory
2. Walk upward looking for `qms.config.json`
3. If found, use that directory as project root
4. If not found, fall back to existing QMS/ directory discovery (backward compatibility)

### 5.2 The `init` Command

```bash
python qms-cli/qms.py init
python qms-cli/qms.py init --root /path/to/project
```

**Project Root Location:**

By default, `init` creates all QMS infrastructure in the **current working directory**. This is the intended usage pattern:

```
my-project/                     # User's project directory (cwd when running init)
├── qms-cli/                    # Cloned qms-cli repository (the tool)
├── qms.config.json             # Created by init
├── QMS/                        # Created by init
│   ├── SOP/
│   ├── CR/
│   └── ...
└── .claude/                    # Created by init
    ├── users/
    └── agents/
```

The `--root` flag allows specifying an alternate location:
```bash
python qms-cli/qms.py init --root /path/to/my-project
```

**Important:** The project root should be **one level above** (or completely separate from) the `qms-cli/` directory. Placing the project root inside `qms-cli/` is strongly discouraged because it mixes the tool's source code with the documents it operates on, creating confusion and potential git conflicts. The qms-cli README will document this guidance.

**Safety Checks (must ALL pass before any changes):**

All checks are performed against the target root directory (cwd or `--root` path):
- No `QMS/` directory exists
- No `.claude/users/` directory exists
- No `.claude/agents/qa.md` exists
- No `qms.config.json` exists

If any check fails, abort with error message identifying the blocking item.

**Creation Sequence (only if all checks pass):**
1. Create `qms.config.json` at project root
2. Create `QMS/` directory structure:
   - `QMS/.meta/` (empty, subdirs created on demand)
   - `QMS/.audit/` (empty, subdirs created on demand)
   - `QMS/.archive/` (empty, subdirs created on demand)
   - `QMS/SOP/` with seeded SOPs
   - `QMS/CR/` (empty)
   - `QMS/INV/` (empty)
   - `QMS/TEMPLATE/` with document templates
3. Create `.claude/users/` structure:
   - `.claude/users/lead/workspace/` and `.claude/users/lead/inbox/`
   - `.claude/users/claude/workspace/` and `.claude/users/claude/inbox/`
   - `.claude/users/qa/workspace/` and `.claude/users/qa/inbox/`
4. Create `.claude/agents/` with default agent file:
   - `.claude/agents/qa.md` (group: quality)

### 5.3 User Management Model

**Hardcoded Users:**

The users `lead` and `claude` are hardcoded as administrators in `qms_auth.py`. They do not require agent definition files. This recognizes their special status as the human lead and the orchestrating AI agent.

**Agent-Based Users:**

All other users are defined via agent definition files in `.claude/agents/`. The agent file's frontmatter specifies group membership:

```yaml
---
name: tu_sketch
group: reviewer
description: Technical Unit for Sketch/Geometry domain
---

# TU-SKETCH Agent

[Agent behavioral directives...]
```

**Group values:** `administrator`, `initiator`, `quality`, `reviewer`

**qms_auth.py modifications:**
1. On user lookup, first check if user is `lead` or `claude` → return `administrator` (hardcoded)
2. Otherwise, check `.claude/agents/{user}.md` for group assignment
3. If agent file exists with valid `group:` frontmatter, use that group
4. If agent file missing, return error: "User {user} not found. Create .claude/agents/{user}.md or run qms user --add {user}"

### 5.4 User Add Command

```bash
python qms.py user --add alice --group reviewer
```

Creates:
- `.claude/agents/alice.md` with specified group
- `.claude/users/alice/workspace/`
- `.claude/users/alice/inbox/`

### 5.5 SOP Sanitization

SOPs are copied from `qms-cli/seed/sops/` with the following transformations:
- `revision_summary:` set to "Initial release"
- All CR/INV references in revision_summary removed
- Version set to 1.0 in corresponding .meta files
- Status set to EFFECTIVE in .meta files

### 5.6 Qualified State Continuity

Development workflow ensures continuous qualification:

| Time | main branch | RS/RTM Status | Qualified Release |
|------|-------------|---------------|-------------------|
| Before CR | Current commit | EFFECTIVE | CLI-1.0 |
| During execution | Unchanged | DRAFT (checked out) | CLI-1.0 (unchanged) |
| Post-approval | Merged from cr-036-init | EFFECTIVE v2.0 | CLI-2.0 |

Anyone cloning qms-cli from GitHub always gets the qualified `main` branch. The development branch (`cr-036-init`) is not qualified until merged.

---

## 6. Justification

- **Problem:** New users cannot use qms-cli without extensive manual setup
- **Impact of not making this change:** qms-cli remains unusable for external adoption; the tool is effectively locked to projects with pre-existing infrastructure
- **Solution addresses root cause:** By adding `init`, users can bootstrap a complete QMS in one command, making qms-cli a standalone tool rather than a component of a larger system

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `qms-cli/qms.py` | Modify | Add init and user command registration |
| `qms-cli/commands/init.py` | Create | Init command implementation |
| `qms-cli/commands/user.py` | Create | User management commands |
| `qms-cli/qms_config.py` | Modify | Add config file discovery |
| `qms-cli/qms_auth.py` | Modify | Read groups from agent files |
| `qms-cli/commands/__init__.py` | Modify | Register new commands |
| `qms-cli/seed/sops/*.md` | Create | Sanitized SOP copies |
| `qms-cli/seed/templates/*.md` | Create | Document templates |
| `qms-cli/seed/agents/qa.md` | Create | Default qa agent definition |
| `qms-cli/tests/qualification/test_init.py` | Create | Qualification tests |
| `qms-cli/README.md` | Modify | Add init usage, project structure guidance |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RS | Modify | Add REQ-INIT-* requirements; remove initialization exclusion |
| SDLC-QMS-RTM | Modify | Add verification evidence for new requirements |

### 7.3 pipe-dream Agent Files (Migration)

| File | Change Type | Description |
|------|-------------|-------------|
| `.claude/agents/qa.md` | Modify | Add `group: quality` to frontmatter |
| `.claude/agents/bu.md` | Modify | Add `group: reviewer` to frontmatter |
| `.claude/agents/tu_ui.md` | Modify | Add `group: reviewer` to frontmatter |
| `.claude/agents/tu_scene.md` | Modify | Add `group: reviewer` to frontmatter |
| `.claude/agents/tu_sketch.md` | Modify | Add `group: reviewer` to frontmatter |
| `.claude/agents/tu_sim.md` | Modify | Add `group: reviewer` to frontmatter |

Note: `lead` and `claude` are hardcoded as administrators and do not require agent files.

### 7.4 Other Impacts

- Existing qms-cli installations require agent file migration (adding `group:` field to non-hardcoded users)
- Projects with existing QMS/ directories continue to work (config file discovery falls back to QMS/ discovery)

---

## 8. Testing Summary

**Full qualification test suite execution:**
- All existing qualification tests must pass at the qualified commit
- New qualification tests for init functionality must pass
- All unit tests must pass

**Specific verification for new functionality:**
- Test init on clean directory (success case)
- Test init with existing QMS/ (blocked, error message)
- Test init with existing .claude/users/ (blocked, error message)
- Test init with existing agent files (blocked, error message)
- Test init with existing qms.config.json (blocked, error message)
- Test user --add creates correct structure
- Test user group assignment from agent files
- Test unknown user produces helpful error
- Test seeded SOPs have correct metadata (v1.0, EFFECTIVE)
- Test full document lifecycle in initialized project

---

## 9. Implementation Plan

### 9.1 Phase 1: Test Environment Setup

1. Create `.test-env/test-project/` directory in pipe-dream (gitignored)
2. Clone qms-cli from GitHub into `.test-env/test-project/qms-cli/`
3. Create and checkout branch `cr-036-init` in the cloned repo
4. Verify clean test environment

### 9.2 Phase 2: Config Discovery Implementation

1. Modify `qms_config.py` to support `qms.config.json` discovery
2. Implement fallback to existing QMS/ discovery for backward compatibility
3. Add unit tests for config discovery

### 9.3 Phase 3: Init Command Implementation

1. Create `commands/init.py` with safety checks
2. Implement directory structure creation
3. Implement agent file creation for default users
4. Add init command to CLI entry point
5. Add qualification tests for init

### 9.4 Phase 4: User Management Implementation

1. Modify `qms_auth.py` to read groups from agent files
2. Create `commands/user.py` for user management
3. Implement `user --add` command
4. Add error handling for unknown users
5. Add qualification tests for user management

### 9.5 Phase 5: SOP and Template Seeding

1. Create `seed/sops/` directory with sanitized SOP copies
2. Create `seed/templates/` directory with document templates
3. Create `seed/agents/qa.md` (the only agent file shipped by default)
4. Implement seeding logic in init command
5. Add qualification tests for seeded content

### 9.6 Phase 6: RS and RTM Updates

1. Checkout SDLC-QMS-RS in production QMS
2. Add REQ-INIT-* requirements for initialization
3. Add REQ-USER-* requirements for user management
4. Remove "Project initialization" from exclusions (Section 5.4)
5. Checkout SDLC-QMS-RTM in production QMS
6. Add verification entries for new requirements

### 9.7 Phase 7: Qualification

1. Run full qualification test suite against development branch
2. Run all unit tests
3. Document test results
4. Verify all requirements have passing verification evidence

### 9.8 Phase 8: Finalization

1. Checkin RS and RTM, route for review and approval
2. Once RS/RTM approved, create PR to merge `cr-036-init` to main
3. Merge PR
4. Update qms-cli submodule pointer in pipe-dream
5. Verify qms-cli version transitions from CLI-1.0 to CLI-2.0

---

## 10. Execution

<!--
EXECUTION PHASE INSTRUCTIONS
============================
NOTE: Do NOT delete this comment block. It provides guidance for execution.

- Sections 1-9 are PRE-APPROVED content - do NOT modify during execution
- Only THIS TABLE and the comment sections below should be edited during execution phase
-->

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Create test environment (.test-env/test-project/) and clone qms-cli | Created `.test-env/test-project/` directory. Cloned qms-cli from GitHub (commit eff3ab7, CLI-1.0 qualified state). Verified clean environment: no pre-existing QMS/, .claude/, or qms.config.json. | Pass | claude - 2026-01-25 |
| EI-2 | Create and checkout branch cr-036-init | Created branch `cr-036-init` from main (eff3ab7) in `.test-env/test-project/qms-cli/`. Branch is checked out and ready for development. Main branch remains at qualified CLI-1.0 state. | Pass | claude - 2026-01-25 |
| EI-3 | Implement config file discovery in qms_config.py | Added `find_config_file()`, `load_config()`, and `get_project_root_from_config()` to qms_config.py. Updated `find_project_root()` in qms_paths.py to prioritize qms.config.json over QMS/ directory discovery. Backward compatibility maintained. Commit: 6619e6c | Pass | claude - 2026-01-25 |
| EI-4 | Implement init command with safety checks | Created `commands/init.py` with safety checks (blocks if QMS/, .claude/users/, qa.md, or config exists). Creates qms.config.json, QMS/ structure, user workspaces, qa agent. Made --user optional for init. Tested: init succeeds on clean directory, blocked with proper errors on second run. Commit: 1db323a | Pass | claude - 2026-01-25 |
| EI-5 | Implement agent-based user management in qms_auth.py | Hardcoded lead/claude as administrators. Added `read_agent_group()` to read group from `.claude/agents/{user}.md`. Updated `get_user_group()` and `verify_user_identity()` with agent file lookup and helpful error messages. Removed legacy VALID_USERS/USER_GROUPS fallback per Lead direction. Tested: hardcoded admins work, qa agent file works, unknown users show helpful guidance. Commits: 5672b3c, 4ac0786 | Pass | claude - 2026-01-25 |
| EI-6 | Implement user --add command | Created `commands/user.py` with `user --add <name> --group <group>` (creates agent file + workspace/inbox) and `user --list` (shows all users). Requires --user and administrator privileges. Validates duplicates, missing group, invalid group, hardcoded admins. Tested: permission denied for non-admins, works for lead/claude. Commits: ff7f72c, e08c113 | Pass | claude - 2026-01-25 |
| EI-7 | Create seed directory with sanitized SOPs, templates, and agent definitions | Created `seed/` directory with: `sops/` (7 SOPs), `templates/` (7 templates), `agents/qa.md`. Sanitized: revision_summary to "Initial release", removed "Flow State"/"pipe-dream" references, replaced TU agent names with generic "reviewer1/2", removed historical INV reference from SOP-001 Section 14. Commits: dfc7c96, 86d849c, b916416 | Pass | claude - 2026-01-25 |
| EI-8 | Implement SOP/template seeding in init command | Added seeding functions to init command: `get_seed_dir()`, `create_meta_file()`, `create_audit_file()`, `seed_sops()`, `seed_templates()`, `seed_agents()`. Seeded documents get EFFECTIVE v1.0 status with system audit entry. Tested: init seeds 7 SOPs, 7 templates, 1 agent with proper .meta and .audit files. Commit: 114bf9c | Pass | claude - 2026-01-25 |
| EI-9 | Add qualification tests for init and user management | Created `test_init.py` with 15 tests: init creates complete structure, seeds SOPs/templates/agent, blocked by existing infrastructure (4 cases), user add creates structure, user add requires admin, hardcoded admins work, unknown user error, agent group assignment, full lifecycle in initialized project, init with --root flag. Also fixed module-level path constants to support clean directories (qms_paths.py, qms_meta.py, qms_audit.py, namespace.py). Updated conftest.py to create agent files for test users. All 113 qualification tests pass. Commit: 93ec72a | Pass | claude - 2026-01-25 |
| EI-10 | Update qms-cli README with init usage and project structure guidance | Updated README with Quick Start section (init command), Project Structure, User Management section (hardcoded admins, user --add, groups table). Also performed comprehensive audit and fix of seed document discrepancies: README (user groups, doc types, generic examples), SOP-001 (Section 4 user groups, directory structure, naming conventions), SOP-006 (removed OQ/CS/DS references), SOP-007 (generic role descriptions). Created CR-037-DRAFT-SCOPE.md documenting production cleanup needed. All 113 qualification tests pass. Commits: 6fde053, 256820b | Pass | claude - 2026-01-25 |
| EI-11 | Checkout and update SDLC-QMS-RS with new requirements | Checked out RS v1.0, created v1.1. Added: REQ-INIT-001 through REQ-INIT-008 (project initialization), REQ-USER-001 through REQ-USER-005 (user management). Updated: REQ-CFG-001 (config file discovery), REQ-CFG-004 (agent-based user registry). Removed "Project initialization" from exclusions (Section 5.4). Updated Section 2 scope and Section 5.1 assumptions. Checked in as v1.1. | Pass | claude - 2026-01-25 |
| EI-12 | Checkout and update SDLC-QMS-RTM with verification evidence | Checked out RTM v1.0, created v1.1. Added: REQ-INIT-001 through REQ-INIT-008, REQ-USER-001 through REQ-USER-005 with test_init.py verification. Updated: Section 2 scope (84 requirements), Section 3.3 test organization (added test_init.py), REQ-CFG-001 (config file discovery), REQ-SEC-002 test description (administrator group check), Section 6 test counts (113 tests). Added Sections 5.11 (REQ-INIT) and 5.12 (REQ-USER) traceability details. Checked in as v1.1. | Pass | claude - 2026-01-25 |
| EI-13 | Run full qualification test suite and all unit tests | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-14 | Route RS and RTM for review and approval | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-15 | Create PR and merge cr-036-init to main | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-16 | Update qms-cli submodule pointer in pipe-dream | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-17 | Update pipe-dream agent files with group assignments (add group: to qa, bu, tu_* files) | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-18 | Verify qms-cli works in pipe-dream with updated agent files | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Add rows as needed. When adding rows, fill columns 3-5 during execution.
-->

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| During EI-10, discovered discrepancies between qualified code/RS and seed documentation (SOPs, README, agent files). Fixed in dev branch: User Groups table didn't match code, non-existent doc types (CAPA, OQ, CS, DS) referenced, hardcoded project-specific users in examples. RS discrepancy noted: REQ-SEC-002 says administrator gets `fix` but code hardcodes `{"qa", "lead"}`. Created CR-037-DRAFT-SCOPE.md documenting what needs to change in production pipe-dream. | claude - 2026-01-25 |
| Created CR-036-VAR-001 (Type 1): Scope expansion to fix the `fix` command permissions. The code used hardcoded usernames `{"qa", "lead"}` instead of checking administrator group per REQ-SEC-002. VAR expands CR-036 scope to include code fix, test fix, and RTM update. Code and test changes committed (b913ffc). VAR-001 must close before CR-036 can close. | claude - 2026-01-25 |
| Created CR-036-VAR-002 (Type 2): Corrective action for documentation drift and qualification gap. Documents two issues: (1) production pipe-dream documentation doesn't match code/RS, (2) REQ-SEC-002 passed qualification despite incorrect test. Corrective actions: create CR for documentation fixes, create INV into qualification gap. Pre-approval unblocks CR-036; actual corrective work tracked as future items. | claude - 2026-01-25 |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during execution.
Add rows as needed.
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
- **SOP-005:** Code Governance
- **SOP-006:** SDLC Governance
- **SDLC-QMS-RS:** QMS CLI Requirements Specification
- **SDLC-QMS-RTM:** QMS CLI Requirements Traceability Matrix

---

**END OF DOCUMENT**
