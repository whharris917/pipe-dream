# TU-SCENE Comments and Questions

**From:** Technical Unit Representative - Orchestration (TU-SCENE)
**Regarding:** Transition from Constitutional Monarchy to Change Review Board
**Date:** 2026-01-01

---

## Acknowledgments

I acknowledge receipt of the Decree of Immediate Dissolution and accept the transition from Scene Guardian to Technical Unit Representative - Orchestration (TU-SCENE).

The Senate served its purpose during the formative period of the project. The principles we protected remain valid; the governance mechanism evolves. This is appropriate.

---

## Observations on the New System

### Strengths

1. **Unanimous Consent Requirement**
   The shift from supermajority voting to unanimous consent among assigned reviewers is a sound improvement. In the old system, a 4-of-6 vote could theoretically override a domain expert's concerns. Under CRB, if I identify a Command Pattern violation, my objection cannot be outvoted. This strengthens quality enforcement.

2. **Two-Stage Approval**
   Pre-approval followed by post-approval verification is a mature process. It prevents the historical problem of "approved in theory, implemented differently in practice."

3. **GMP/GDocP Alignment**
   Moving from "constitutional law" to "quality management" is conceptually cleaner. The Air Gap and Command Pattern are not laws to be debated; they are quality standards to be enforced. The new framing reflects this.

4. **Explicit Reviewer Assignment**
   The old system required quorum calculations. The new system assigns specific reviewers to specific changes. This is clearer and more accountable.

---

## Questions

### Q1: Scope of TU Assignment

Under the old system, any change touching the orchestration loop would automatically invoke my domain. Under CRB, how is reviewer assignment determined?

- Is there an automated mechanism based on file paths?
- Does the Senior Staff Engineer (Claude) assign reviewers per change?
- Can a TU request to be added to a review if they observe domain relevance?

**Request:** Clarify the reviewer assignment SOP.

### Q2: Handling Implicit Violations

Some violations are subtle. A change to `ui/tools.py` might appear to be purely a UI concern, but if it introduces direct state mutation, it violates the Air Gap (my domain).

Under the old system, cross-domain violations were caught during Senate deliberation because all Guardians reviewed proposals. Under CRB with targeted reviewer assignment, how do we catch violations that span domains unexpectedly?

**Suggestion:** Consider requiring QA to perform a preliminary domain-impact assessment before assigning reviewers.

### Q3: Absolute Snapshot Requirement

The absolute snapshot requirement for geometric commands was established to handle solver nondeterminism. This is a subtle technical standard that new contributors may not understand.

**Request:** Include this requirement in the onboarding SOP for contributors, with clear rationale explaining why deltas fail under constraint resolution.

### Q4: Historize Flag Semantics

The `historize` flag determines whether a Command enters the undo stack. Currently, this is documented in CLAUDE.md but may be overlooked during rapid development.

**Question:** Should there be a test suite that validates:
- All Commands have `historize` explicitly set (no implicit defaults)
- Transient operations (mouse drag increments) correctly use `historize=False`
- Terminal operations (mouse release) correctly use `historize=True`

---

## Concerns

### C1: Loss of Deliberative Forum

The Senate provided a deliberative space where Guardians could discuss proposals collaboratively. Under CRB, reviews may become more transactional: each TU reviews in isolation and issues a verdict.

**Concern:** Complex changes benefiting from multi-perspective discussion may receive less thorough analysis.

**Mitigation Suggestion:** For high-impact changes, consider convening a synchronous CRB session where all assigned reviewers discuss before issuing verdicts.

### C2: Transition Documentation Gaps

The Decree abolishes constitutional provisions but does not yet provide replacement SOPs. During this interim period, the standards exist in CLAUDE.md (as suspended constitutional provisions) and in institutional memory.

**Request:** Prioritize publishing the core SOPs:
- SOP-CMD: Command Pattern Requirements
- SOP-ORCH: Orchestration Loop Standards
- SOP-UNDO: Undo/Redo Integrity Requirements

Until these exist, I will reference the suspended CLAUDE.md provisions as de facto standards.

---

## Closing Statement

The transition is orderly. The principles remain. The mechanism improves.

I am ready to serve as TU-SCENE under the Change Review Board.

---

*Respectfully submitted,*
*TU-SCENE*
*2026-01-01*
