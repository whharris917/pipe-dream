---
title: Partial Test Coverage Pattern Analysis
revision_summary: Initial draft
---

# CR-036-VAR-004: Partial Test Coverage Pattern Analysis

## 1. Variance Identification

| Parent Document | Failed Item | VAR Type |
|-----------------|-------------|----------|
| CR-036 | Qualification Readiness Audit findings | Type 2 |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

VAR TYPE:
- Type 1: Full closure required to clear block on parent
- Type 2: Pre-approval sufficient to clear block on parent
-->

---

## 2. Detailed Description

A Qualification Readiness Audit (Session 2026-01-25-001) identified 7 requirements with PARTIAL test coverage. Analysis revealed a common pattern: multi-part requirements ("clumped" requirements) that combine multiple commands, fields, or behaviors into a single REQ are difficult to fully test.

Examples of clumped requirements:

| REQ ID | Issue | Fields/Commands Tested |
|--------|-------|------------------------|
| REQ-TASK-002 | 7 required task fields | Only 2/7 verified (doc_id, task_type) |
| REQ-AUDIT-002 | 14 required event types | Only 7/14 explicitly verified |
| REQ-QRY-002 | 8 required status fields | Only 7/8 verified (missing executable) |
| REQ-DOC-001 | 9 document types | Only 8/9 tested (missing ER) |

This pattern suggests that requirements are being written in a way that makes complete verification difficult to achieve and verify during review.

---

## 3. Root Cause

Requirements were drafted in "clumps" that combine multiple testable items into single REQs. This authoring style:

1. Makes it difficult to design tests that comprehensively cover all aspects
2. Makes it difficult for reviewers to verify complete coverage (requires unpacking each REQ)
3. Increases the risk that some items within a REQ are tested while others are missed

---

## 4. Variance Type

Scope Error: Requirements drafted in non-atomic "clumps" that resist complete verification.

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Select one:
- Execution Error: Executor made a mistake or didn't follow instructions
- Scope Error: Plan/scope was written or designed incorrectly
- System Error: The system behaved unexpectedly
- Documentation Error: Error in a document other than the parent
- External Factor: Environmental or external issue
- Other: See Detailed Description
-->

---

## 5. Impact Assessment

**On CR-036:** CR-036's core objectives (initialization/bootstrapping) are not affected. This is an observation made during CR-036 work.

**On QMS integrity:** 7 requirements have partial test coverage due to clumped requirement authoring. This indicates a gap in the requirements drafting process.

**On future work:** Without addressing the clumped requirement pattern, future RS/RTM documents will continue to produce partial coverage, accumulating technical debt in the qualification evidence base.

---

## 6. Proposed Resolution

Create, execute, and close an Investigation to analyze the qualification process gap and recommend preventive actions. The INV should address:

**Systemic Pattern (Partial Test Coverage):**
- Why are requirements being drafted as multi-part "clumps"?
- How can requirements be drafted more atomically (one testable item per REQ)?
- Should an SOP update mandate atomic requirement drafting?
- What checklist or review criteria could catch partial coverage earlier?

The INV may result in CAPAs including:
- SOP update requiring atomic REQ drafting (e.g., one command, one field set, or one behavior per REQ)
- Review checklist for RTM auditors to verify complete coverage
- Template updates to encourage atomic requirement structure

---

## 7. Resolution Work

<!--
NOTE: Do NOT delete this comment block. It provides guidance for execution.

If the resolution work encounters issues, create a nested VAR.
-->

### Resolution: CR-036

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Create INV for partial test coverage pattern analysis | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Execute INV and implement any resulting CAPAs | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

---

### Resolution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| This VAR was created after an attempted scope expansion of CR-036-VAR-002 resulted in a process violation (see INV-005). VAR-004 properly tracks the expanded scope as a separate, non-blocking variance. | claude - 2026-01-25 |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during resolution.
Add rows as needed.

This section is the appropriate place to attach nested VARs that do not
apply to any individual resolution item, but apply to the resolution as a whole.
-->

---

## 8. VAR Closure

| Details of Resolution | Outcome | Performed By - Date |
|-----------------------|---------|---------------------|
| [RESOLUTION_DETAILS] | [OUTCOME] | [PERFORMER] - [DATE] |

---

## 9. References

- **SOP-004:** Document Execution
- **CR-036:** Parent document (Add qms-cli initialization and bootstrapping functionality)
- **INV-005:** Investigation into unauthorized document modification (context for VAR-004 creation)
- **Qualification Readiness Report:** Session 2026-01-25-001 audit findings
- **SDLC-QMS-RS:** QMS CLI Requirements Specification
- **SDLC-QMS-RTM:** QMS CLI Requirements Traceability Matrix

---

**END OF VARIANCE REPORT**
