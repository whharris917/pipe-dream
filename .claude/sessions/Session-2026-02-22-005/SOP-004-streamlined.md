---
title: Document Execution
revision_summary: 'CR-091: Add Section 11 (Interactive Document Authoring)'
---

# SOP-004: Document Execution

---

## 1. Purpose

This SOP governs the execution phase of executable documents, including scope management, evidence requirements, and failure handling.

---

## 2. Scope

This SOP applies to the execution phase of all executable documents: CR, INV, TP, ER, VAR, ADD, VR.

---

## 3. Definitions

See [QMS-Glossary](QMS-Glossary.md) for all terms and abbreviations used in this document.

---

## 4. The Executable Block

Executable documents are divided into two blocks:

- **Static fields:** Defined during planning, locked after pre-approval (e.g., task descriptions, test instructions, VR flags).
- **Editable fields:** Completed during execution (e.g., execution summaries, outcomes, signatures).

Pre-approval reviews verify the plan. Post-approval reviews verify that execution matched the plan.

If an execution item is flagged for VR (behavioral verification), a VR child document must be created and completed before the item can be marked complete.

---

## 5. Scope Integrity

Pre-approved scope items must be completed. This is non-negotiable.

If obstacles arise during execution:
1. Complete the item as planned, OR
2. Document an exception via VAR (non-test) or ER (test) with rationale and resolution path

"Different execution mechanism" is not a scope exclusion. Scope items cannot be silently dropped. If an item cannot be completed as originally planned, this must be formally documented.

---

## 6. Evidence Standards

Each execution item requires evidence sufficient for a reviewer who was not present to independently confirm the work was completed. Evidence must be:

- **Contemporaneous:** Recorded at the time of execution, not reconstructed afterward
- **Traceable:** Linked to specific artifacts (commit hashes, document IDs, test results)
- **Observational:** Based on what was done and observed, not assertions that something worked

Failed items require an attached VAR (non-test) or ER (test) explaining what occurred and how it will be resolved.

---

## 7. Execution Failure Handling

### 7.1 ER vs VAR vs ADD vs INV

| Document | Use Case | Timing |
|----------|----------|--------|
| **ER** | Test step failures within TP/TC | During test execution |
| **VAR** | Non-test execution failures | During execution of CR/INV |
| **ADD** | Post-closure corrections | After parent has closed |
| **INV** | Systemic quality events requiring root cause analysis | Any time |

### 7.2 Exception Reports (ER)

When a test step fails, subsequent steps are marked N/A. An ER is created containing a full re-execution of the entire test case (not just the failed step), because the test script itself may be defective. If the re-test also fails, a nested ER is created.

### 7.3 Variance Reports (VAR)

VARs encapsulate resolution work in an independent review/approval cycle, keeping the parent document's execution log clean.

**Type 1 vs Type 2:**
- **Type 1** (full closure required): The variance directly threatens the parent's objectives. Default when in doubt.
- **Type 2** (pre-approval sufficient): The variance is contained, the resolution plan is sound, and the parent can close without waiting for the full resolution cycle.

### 7.4 Addendum Reports (ADD)

ADDs correct or supplement a parent that has already closed. The parent's closure was legitimate at the time; the ADD supplements it without invalidating it.

### 7.5 Scope Handoff

When a VAR or ADD is created, it must explicitly confirm:
1. What the parent accomplished (before the variance or closure)
2. What the child document absorbs
3. That no scope items were lost in the handoff

---

## 8. Verification Records (VR)

VRs are pre-approved evidence forms for structured behavioral verification. They follow a truncated lifecycle: born IN_EXECUTION at v1.0, with no pre-approval cycle. The approved VR template serves as the authorization.

VRs must be filled contemporaneously with the verification activity — not backfilled after the fact.

**VR evidence must be:**
- Observational (what was done and what was observed)
- Reproducible (someone with terminal access could follow the procedure and confirm results)

**VR evidence must not be:**
- Assertional ("test passed" without supporting observations)

VRs are reviewed as part of the parent document's post-review and closed automatically when the parent closes.

---

## 9. Interactive Authoring

VR documents are authored interactively rather than edited as freehand markdown. The template defines a prompt flow; the author provides content; the system guarantees structural conformance.

**Key principles:**
- The template encodes methodology. The author provides content. No section can be skipped or left blank.
- Responses follow an append-only model: amendments add new entries with reasons; originals are never modified or deleted. This creates a visible amendment trail.
- Evidence-capture prompts trigger automatic git commits, pinning the project state at the moment of observation.
- The source data is the authoritative record. The compiled markdown is a derived artifact that can be regenerated.

---

## 10. Post-Review Requirements

A document may only be routed for post-review when:

- All execution items have a recorded outcome (Pass or Fail)
- All failed items have an attached VAR or ER
- All Type 1 VARs are closed; all Type 2 VARs are at least pre-approved
- All VR-flagged items have a completed VR with evidence per Section 8
- All controlled documents modified during execution are EFFECTIVE

---

**END OF DOCUMENT**
