# To Do List

*Actionable items identified during sessions. Not part of QMS or any official tracking.*

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
