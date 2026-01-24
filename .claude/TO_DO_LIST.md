# To Do List

*Actionable items identified during sessions. Not part of QMS or any official tracking.*

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

- [ ] Derive TRANSITIONS from WORKFLOW_TRANSITIONS in qms-cli
  - Currently `qms_config.TRANSITIONS` and `workflow.WORKFLOW_TRANSITIONS` encode the same state machine edges
  - Risk: If they diverge, transition validation bugs result
  - Simplification: Generate `TRANSITIONS` dict from `WORKFLOW_TRANSITIONS` list at module load
  - Location: `qms-cli/qms_config.py` imports from `workflow.py`, or refactor to single source of truth
  - Priority: Low (code works, but worth doing if workflow engine is touched by future CR)
  - Reference: Session-2026-01-19-004 formalization analysis

---

## 2026-01-17

- [ ] Correct SOP-001 Section 4.2 fix permission
  - Current: Shows "fix (admin): lead only" for Initiators and "Yes" for QA
  - Should be: fix is Initiators only (not QA)
  - Update Permission Matrix in SOP-001 Section 4.2
  - Note: Identified during SDLC-QMS-RS requirements review

---

## 2026-01-11

- [ ] Remove in-memory fallback for inbox prompts in qms-cli
  - CR-027 added YAML file-based prompts; legacy hard-coded fallback is no longer needed
  - Remove: DEFAULT_FRONTMATTER_CHECKS, DEFAULT_STRUCTURE_CHECKS, DEFAULT_CONTENT_CHECKS, etc.
  - Remove: DEFAULT_REVIEW_CONFIG, DEFAULT_APPROVAL_CONFIG, CR_POST_REVIEW_CONFIG, SOP_REVIEW_CONFIG
  - Remove: _register_defaults() method in PromptRegistry
  - Update: get_config() to only use file-based loading
  - Update: Tests that rely on in-memory configs

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
