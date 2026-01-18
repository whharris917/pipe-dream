# Test Exception Concepts

**Date:** 2026-01-06
**Session:** 002
**Status:** Provisional wording for future SOP/template inclusion

---

## Definition

An exception is a non-conformance encountered during execution or review of a test. All exceptions must be documented and resolved.

---

## Exception Workflow

If an exception occurs, the executor of the test must create an Exception Report (ER) and link it directly to the failed test step.

---

## Pass/Fail Rules

### Actual ≠ Expected → Fail

For any test case, if the Actual Results do not match the Expected Results, the test case fails. This holds true even when the Actual Results are correct and the Expected Results are not correct.

### Actual = Expected but Problem Discovered → Pass with Exception

If the Actual Results match the Expected Results, but at the time of testing a problem is discovered with the system or the expected results, then the test step passes with exception.

---

## Re-testing Within ER

Any additional testing or re-testing performed as part of the exception process can be created within the ER as a new section.

**Design Decision:** Re-execution lives exclusively in the ER, not in the TC. The TC shows original execution only—failed steps remain as evidence. This keeps TCs clean and makes ERs self-contained units that own exceptions end-to-end.

**Handling Subsequent Steps After Failure:**

When a step fails (e.g., step 3 in a 10-step TC):
- Steps 1-2: Pass (as executed)
- Step 3: Fail (documented, signed, ER attached)
- Steps 4-10: Mark as **N/A** with ER reference in Actual Result (e.g., "N/A — See ER-001")

**Full Re-execution in ER:**

The ER contains a complete re-execution of the test case, not just the failed step. This is because:
- The test script itself might be the defect (poorly written, wrong expected results)
- The re-test may have different, more, or fewer steps than the original
- A one-to-one step match cannot be assumed

## Nested ERs

If an exception occurs during re-testing within an ER, a nested ER is created (e.g., ER-001-ER-001). This recursive structure:

- Is conceptually sound
- Works well in practice (per pharma industry experience)
- Has less cognitive burden than expected
- Mirrors the QMS's own recursive governance model

---

## ER Closure Requirements

Before the ER is post-approved, all impacted documents must be verified as being revised and approved and required re-executions must be completed, reviewed, and approved with passing results.

---

## Expanded Acceptance Criteria (Post-Approval Gate)

Post-approval of this test case / protocol cannot be performed until all of the following criteria have been met:

1. Test cases have been successfully executed or have been appropriately addressed through the test exception process, including retesting if necessary.

2. Supporting documentation is available, labeled, annotated, and properly cross-referenced.

3. Exceptions, if applicable, have been closed.

4. Test cases have been signed by the test executor and reviewer.

---

**End of Note**
