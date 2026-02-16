# To Do List

*Actionable items identified during sessions. Not part of QMS or any official tracking.*

---

## 2026-02-16

- [ ] Discuss automating RTM generation
  - RTM is large, repetitive, and error-prone to maintain manually
  - Consider: Script that reads RS requirements + test docstrings/markers to generate the traceability matrix
  - Consider: What remains manual vs. what can be derived from code
  - Reference: Session-2026-02-16-002 feedback

- [ ] Improve RTM readability: one test per line with row-spanning REQ IDs
  - Current format flattens all test references into a single row, which is hard to read
  - Proposed: Each test on its own line, with gaps in the REQ column (gap = same REQ as above)
  - Similar to the "CR Chain" table in PROJECT_STATE.md

- [ ] Integrate ALCOA+ concepts into QMS execution documentation
  - EI execution summaries should be recorded contemporaneously, not backfilled
  - Extend signature format from `performer - date` to `performer - YYYY-MM-DD HH:MM UTC`
  - Consider: SOP-004, TEMPLATE-CR, TEMPLATE-VAR updates
  - Reference: Session-2026-02-16-002 feedback on CR-087 execution

- [ ] Update SOPs/templates for branch protection and merge strategy
  - Document that `gh pr merge --merge --auto` is the standard merge approach
  - Explicitly prohibit overriding branch protection (`--admin` flag)
  - Clarify that merge commits always produce a new hash (qualified baseline = branch commit, not merge commit)
  - Consider: SOP-005, TEMPLATE-CR updates

- [ ] Consider adding a commit column to the EI execution table
  - Current table has: EI, Task Description, Execution Summary, Task Outcome, Performed By - Date
  - Proposed: Add a Commit column for traceability
  - Would reduce the need to embed commit hashes in narrative text

- [ ] Stop tracking total counts of tests, REQs, and other accounting numbers
  - Maintaining exact counts (e.g., "107 requirements", "403 tests") across documents is a maintenance burden
  - Numbers drift and cause unnecessary review findings
  - Consider: Remove hard-coded counts from RTM scope section, rely on automated verification instead

---

## 2026-02-15

- [x] ~~Update QMS document creation confirmation message to remind user the document is auto-checked-out to their workspace~~ DONE (CR-087)
  - Added "Document is checked out and ready for editing." to create command output

- [ ] Add granular start/stop commands to agent-hub CLI
  - Currently only `stop-all` exists for shutdown; no way to start/stop individual components
  - Add commands to start/stop individual MCP servers (QMS, Git) independently
  - Add command to start/stop the agent-hub server itself without affecting MCP servers
  - Consider: `agent-hub stop qms-mcp`, `agent-hub stop git-mcp`, `agent-hub stop hub`, `agent-hub start hub`, etc.
  - Location: `agent-hub/agent_hub/cli.py` or equivalent CLI entry point

- [x] ~~Update CR and VAR templates to make integration/UAT testing mandatory for code changes~~ DONE (CR-084)
  - SOP-002 v10.0, SOP-004 v5.0, TEMPLATE-CR v5.0, TEMPLATE-VAR v2.0 all EFFECTIVE
  - Seed copies aligned in qms-cli/seed/templates/

---

## 2026-02-14

- [ ] Unify Agent Hub logging and close observability gaps
  - Ensure every segment of the MCP chain (container -> stdio proxy -> HTTP -> host MCP server -> QMS backend) is observable in persistent log files
  - Stdio proxy logs currently go to container stderr/tmux scrollback — not persisted
  - Fix health check protocol mismatch: `agent-hub services` uses GET to probe MCP endpoints, but MCP protocol expects POST — results in `406 Not Acceptable` noise in logs
  - Make identity management logging verbose: authentication, authorization, identity resolution, collision detection, lock acquisition/release should all be logged at INFO level with clear context
  - Consider unified log format across all services (QMS MCP, Git MCP, Hub, proxy)
  - Reference: Session-2026-02-14-002, Phase A.1 integration testing

---

## 2026-02-11

- [x] ~~Formalize UAT as a stage gate for CRs that affect code~~ DONE (CR-084)
  - Implemented as integration verification (not formal UAT) — practical demonstration through user-facing levers
  - SOP-002 Section 6.8, SOP-004 Section 9A.3, TEMPLATE-CR Phase 5 + Section 8, TEMPLATE-VAR Resolution Work Instructions

---

## 2026-02-10

- [ ] Surface identity mismatch warning to the caller, not just the server log
  - When a container passes `user="tu_sim"` but its `X-QMS-Identity` header says `tu_ui`, the server silently overrides to `tu_ui`
  - The caller sees no indication that its `user` parameter was ignored — it believes it queried tu_sim's inbox when it actually got tu_ui's
  - **Confusion cascade observed in UAT:** tu_ui container tested `user=""`, `user="not_a_real_username"`, and omitted `user` entirely — all returned "Inbox is empty". The agent concluded "the QMS inbox endpoint doesn't validate whether the username exists" which is completely wrong: enforced mode was ignoring the parameter in all cases and always returning tu_ui's inbox. The agent was reasoning about phantom behavior and drawing false conclusions about system capabilities.
  - This is not just a UX issue — silent identity override causes agents to form incorrect mental models of the system, which could lead to flawed decisions in more consequential operations (e.g., checkout, create, route)
  - Proposal: Return the resolved identity in the tool response (e.g., `"resolved_as": "tu_ui"`) or include a warning in the result text when a mismatch occurs
  - Reference: Session-2026-02-10-005 UAT, P1-T3 observation

- [ ] Investigate whether the defensive fallback in `resolve_identity()` is still needed
  - After CR-075 (single-authority MCP), all connections go through HTTP — the `except (AttributeError, LookupError)` fallback for "no request context" should never fire in production
  - Question: Can we remove the fallback entirely, or does it serve a legitimate purpose (e.g., unit testing with mocked contexts)?
  - If removable: simplify `resolve_identity()` to only handle HTTP paths, remove fallback tests (`test_resolve_identity_no_context_default`, `test_resolve_identity_no_context_custom_user`, `test_resolve_identity_attribute_error_defensive_fallback`, `test_identity_collision_enforced_locks_fallback`)
  - If keeping: document why in a code comment
  - Reference: Session-2026-02-10-004, RTM line 1408

---

## 2026-02-08

- [x] ~~Prevent multiple instances of the same QMS user running simultaneously~~ DONE (CR-074)
  - Implemented via identity collision prevention: in-memory registry, TTL-based locks, UUID instance tracking
  - Reference: Session-2026-02-08-001

---

## 2026-02-07

- [x] ~~Add prerequisite to always commit and push pipe-dream as the first EI of a CR~~ DONE (CR-085, refined CR-086)
  - CR-085: Initial implementation as pre-release prerequisite
  - CR-086: Repositioned as first EI (after release), added post-execution commit as final EI, fixed "QMS repository" language

---

## 2026-02-02

- [x] ~~Investigate why checking out an INV in IN_PRE_REVIEW didn't cancel ongoing workflows and transition back to DRAFT~~ DONE (CR-087)
  - Implemented REQ-WF-022: checkout from active workflow states now auto-withdraws first
  - Implemented REQ-WF-023: route while checked out now auto-checks-in first

---

## 2026-01-31

- [x] ~~Fix unit test assertion in test_qms_auth.py for improved error message~~ RESOLVED
  - Test already asserts `"not found" in captured.out` which matches current CLI output
  - No action needed — was fixed at some point after the to-do was written

---

## 2026-01-26

- [x] ~~Create CR to add ASSIGN to REQ-AUDIT-002 required event types~~ DONE (CR-087)
  - REQ-AUDIT-002 now lists 16 event types (added ASSIGN and WITHDRAW)
  - test_audit_completeness.py verifies all 16 types are logged

- [x] ~~Add owner-initiated withdrawal command for documents in review~~ DONE (CR-048 + CR-087)
  - CR-048: Added `qms withdraw` command (REQ-WF-018)
  - CR-087: Added auto-withdraw on checkout from active workflows (REQ-WF-022)

- [x] ~~Update SOP-005 (Code Governance) to thoroughly explain qualification process~~ DONE (CR-083, CR-086)
  - CR-083: Codified merge gate, qualified commit convention, merge type requirements (Section 7.1.1-7.1.4)
  - CR-086: Added rollback procedures (Section 7.1.5) — execution branch and main branch scenarios, git revert mandated, git reset prohibited

---

## 2026-01-25

- [ ] Code safety review: production/test environment isolation
  - Review ways to programmatically enforce stricter separation between production (pipe-dream/qms-cli submodule) and test (.test-env/test-project/qms-cli) environments
  - Consider: Git hooks/guards to prevent accidental commits to production during CR execution
  - Consider: Path validation in scripts/tools to ensure operations target correct environment
  - Consider: Environment variables or config flags to declare active environment
  - Consider: Warnings or blocks when running commands from unexpected directories
  - Context: CR-036 uses isolated test clone for development; need to ensure no cross-contamination
  - Reference: Session-2026-01-25-001

---

## 2026-01-24

- [ ] Implement comments visibility restriction during active workflows
  - Hide review comments when document is in IN_REVIEW or IN_APPROVAL status
  - Prevents reviewers from being influenced by other reviewers' comments
  - Was REQ-QRY-007; removed from RS to enable qualification
  - If re-implemented: add requirement back to RS, update RTM, remove xfail from tests
  - Reference: Session-2026-01-24 qualification work

---

## 2026-01-19

- [x] ~~Derive TRANSITIONS from WORKFLOW_TRANSITIONS in qms-cli~~ DONE (CR-087)
  - Consolidated full state machine into workflow.py (WORKFLOW_TRANSITIONS is single source of truth)
  - TRANSITIONS, WITHDRAW_TRANSITIONS, CHECKOUT_TRANSITIONS all derived via _derive_transitions_dict() and _derive_action_map()
  - Added CHECKOUT and WITHDRAW to Action enum with 8 new StatusTransition entries

---

## 2026-01-17

- [x] ~~Correct SOP-001 Section 4.2 fix permission~~ RESOLVED
  - Permission matrix now correctly shows fix as Administrator-only

- [ ] Fix stale help text in `qms.py:154` — says "(QA/lead only)" but fix is Administrator-only
  - Cosmetic, low priority

---

## 2026-01-11

- [x] ~~Remove in-memory fallback for inbox prompts in qms-cli~~ DONE (CR-087)
  - Removed 11 in-memory constants, _register_defaults(), fallback chain from prompts.py
  - YAML is sole config source; get_config() raises ValueError on lookup failure

---

## 2026-01-10

- [x] ~~Remove CR ID requirement from revision_summary frontmatter field~~ ✓ DONE (CR-033)
  - Implemented via CR-033 (CLOSED)
  - SOP-001 v17.0, SOP-002 v7.0 now EFFECTIVE with relaxed requirement
  - Updated QA agent definition and 5 review/approval prompt files

- [ ] Audit and fix CR document path references
  - Agents often attempt `QMS/CR/CR-XYZ.md` instead of correct `QMS/CR/CR-XYZ/CR-XYZ.md`
  - Check SOPs, CLAUDE.md, agent definition files, and templates for incorrect path examples
  - Consider: If no other document types will live in `QMS/CR/CR-XYZ/`, simplify to flat structure `QMS/CR/CR-XYZ.md`

---

## 2026-01-09

- [ ] Simplify existing SOPs to behavioral baselines
  - Review SOP-001 through SOP-006 for tooling-dependent language
  - Rewrite requirements in behavioral terms where possible ("agents shall..." not "CLI shall...")
  - Offload specific implementation details to RSs (Requirements Specifications) and/or WIs (Work Instructions)
  - Enables SOP approval without infrastructure prerequisites
  - See: Session-2026-01-09-001 notes on behavioral vs. tooling-dependent SOPs

---

## 2026-01-08

- [ ] Figure out a way to remind Claude to spawn and reuse/resume agents
  - Currently spinning up completely new agents each time instead of resuming existing ones
  - Consider: CLAUDE.md instruction, hook reminder, or agent ID tracking mechanism

- [ ] Proceduralize how to add new documents to the QMS
  - Problem: Can't check out a document that doesn't exist yet
  - v1.0 of documents have dubious QA oversight (created directly, not through checkout/checkin cycle)
  - Consider: CR-driven document creation workflow, or initial review gate before v1.0 becomes EFFECTIVE

---

## 2026-01-07

- [x] ~~Create an SOP template~~ ✓ DONE
  - Added to `.claude/workshop/templates/SOP-TEMPLATE.md`
  - Follows same conventions as CR template (template notice, usage guide, placeholders)

- [ ] Remove document status EFFECTIVE as an option; rename to APPROVED
  - Simplify non-executable document workflow: APPROVED is the terminal success state
  - Update SOP-001 status definitions and state machine diagrams
  - Update QMS CLI to use APPROVED instead of EFFECTIVE

- [ ] Metadata injection into viewable rendition of QMS documentation
  - Inject version, revision history, document status into rendered view
  - Consider header/footer display or frontmatter expansion
  - Enables viewing complete document state without running `qms status`

---

## 2026-01-06

### Handle "pass with exception" scenario

**Context:** During TC/ER template development, identified a scenario not explicitly covered:

> If the Actual Results match the Expected Results, but at the time of testing a problem is discovered with the system or the expected results, then the test step passes with exception.

**Current state:** TC Instructions and SOP-004 only trigger ER workflow when a step fails. A passing step with a discovered problem isn't explicitly handled.

**Possible approaches:**
1. Codify in SOP-004 as a distinct outcome type
2. Handle via Test Execution Comments + protocol-level ER (per existing note)
3. Add "Pass with Exception" as a valid Pass/Fail value in TC template

**Action:** Revisit when codifying test execution procedures more formally.

---

### ~~Remove "Reviewer Comments" section from all templates~~ ✓ DONE

*Completed: Session-2026-01-07-001*

Removed `### Reviewer Comments` sections from CR-TEMPLATE, TC-TEMPLATE, VAR-TEMPLATE, ER-TEMPLATE, and the reference in TP-TEMPLATE.

---
