# To Do List

*Actionable items identified during sessions. Not part of QMS or any official tracking.*

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
