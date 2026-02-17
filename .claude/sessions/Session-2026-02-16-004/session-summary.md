# Session-2026-02-16-004: VR Design Discussion and QMS Testing Framework

**Date:** 2026-02-16
**Context:** Design discussion session — no code changes, no QMS documents modified

---

## Summary

Extended design discussion establishing the concept of Verification Records (VRs) as a new QMS document type, plus related concepts including testing taxonomy, signature types, periodic reviews, and a grab bag of future QMS improvements. No implementation work — this session was pure design and documentation.

---

## Key Concepts Established

### Testing Taxonomy
- Core four elements: instruction, expected result, actual result, outcome
- Three script types: scripted (precise steps), unscripted (flexible path, defined goal), exploratory (lab notebook)
- Automated vs. manual as orthogonal axis
- Identified that unscripted testing had no QMS home — VRs fill this gap

### Verification Records (VRs)
- Lightweight child documents of CRs for unscripted behavioral testing
- "Pre-approved forms" — template is the approval (batch record analogy from GMP)
- Evidence must be observational (what was done/observed), not assertional (test script printed PASS)
- Reviewed during parent CR post-review, not via their own workflow
- Lightest document type in the QMS — no pre-review, no pre-approval, no release
- VR is the "pinnacle of proof" — what you show an auditor

### Signature Types (from GMP)
- Performer: executes the steps
- Witness: observes contemporaneously
- Verifier: independently reproduces
- Reviewer: reviews executed document without executing
- Current practice: Performer + Reviewer; Witness and Verifier are future possibilities
- VRs must be detailed enough for a Verifier to reproduce without project background knowledge

### The Mandate Escalation Cycle
- Recurring QMS pattern: failure → mandate → technically satisfiable with weak compliance → failure → stronger mandate
- VRs break the cycle by providing *form* instead of *mandate*
- Key insight: when a mandate fails, ask "does this need a form?" not "does this need a stronger mandate?"

---

## Design Decisions (13 total)

1. VRs are a new document type (lightweight child documents)
2. Reviewed as part of parent CR post-review
3. Pre-approved via template (batch record model)
4. Observational + committed test evidence acceptable; ad hoc scripts are not
5. Four signature types formalized
6. Performer + Reviewer current; Witness + Verifier future
7. CR EI table gains a VR column (static flag → VR ID)
8. VR requirement is per-EI, approved as part of CR scope
9. VR is a third RTM verification type
10. VR form includes pre-conditions section
11. VR column applies to all EI tables (CR, VAR, ADD)
12. CR-084 integration verification language to be simplified to reference VRs
13. VR scope defaults to forest-level (capabilities, not mechanisms)

---

## Additional Concepts Discussed

### Periodic Reviews
- Blind, independent verification of existing claims (without referencing RTM or existing tests)
- Three types: requirement spot-check, CR evidence audit, INV root cause review
- Produces VRs as evidence; findings may spawn INVs or CRs
- Trigger/schedule deferred

### Idea Grab Bag (10 items)
1. Acceptance criteria as first-class CR field
2. Negative testing in VRs
3. Pre-mortem as CR planning step
4. Evidence taxonomy (which evidence types for which claims)
5. Exploration Records (XR) for investigative/debugging work
6. Dual-path verification for high-risk changes
7. Right-first-time metrics for process health
8. Traceability completeness automation
9. Configuration baseline records
10. Adversarial review mode

---

## Files Created

- `.claude/sessions/Session-2026-02-16-004/discussion-verification-records.md` — Full design discussion
- `.claude/sessions/Session-2026-02-16-004/session-summary.md` — This file

## Files Modified

None. This was a design discussion session with no code or QMS document changes.

---

## Next Steps

Implementation of VRs will require a CR covering:
- TEMPLATE-VR design and creation
- QMS CLI support for VR document type
- SOP updates (SOP-002, SOP-004, SOP-006)
- Template updates (TEMPLATE-CR, TEMPLATE-VAR, TEMPLATE-ADD — VR column in EI tables)
- RTM structure update (third verification type)
