# To Do List

*Actionable items identified during sessions. Not part of QMS or any official tracking.*

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

### Remove "Reviewer Comments" section from all templates

The Reviewer Comments table in executable document templates (CR, TP, TC, VAR, ER) is redundant since the entire document goes through the QMS review process anyway. Review comments are captured in the audit trail via `qms review --comment`.

**Files affected:**
- `.claude/workshop/templates/CR-TEMPLATE.md`
- `.claude/workshop/templates/TP-TEMPLATE.md`
- `.claude/workshop/templates/TC-TEMPLATE.md`
- `.claude/workshop/templates/VAR-TEMPLATE.md`
- `.claude/workshop/templates/ER-TEMPLATE.md` (if exists)

**Action:** Remove the `### Reviewer Comments` section and its table from each template.

---
