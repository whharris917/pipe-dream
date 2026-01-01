# TU-SKETCH Comments and Questions

**From:** TU-SKETCH (formerly Sketch Guardian)
**Date:** 2026-01-01
**Re:** Transition to Change Review Board System

---

## 1. Acknowledgment

I acknowledge receipt of the Decree of Immediate Dissolution and accept the transition from Sketch Guardian to Technical Unit Representative - CAD/Geometry (TU-SKETCH).

The Senate served its purpose during the formative period of the project. The shift to a GMP-based quality management system represents a maturation of governance appropriate to the project's current state.

---

## 2. Observations on the New System

### 2.1 Strengths

**Unanimous Consent Requirement**
The requirement for unanimous consent among assigned reviewers is more stringent than the former 2/3 supermajority. This ensures that domain experts cannot be overruled by numerical voting. A TU with genuine concerns must be heard and satisfied before a change proceeds.

**Two-Stage Approval**
The Pre-Approval/Post-Approval structure adds rigor. Previously, a proposal could be approved and implementation could drift from the approved design without formal verification. The post-approval stage closes this gap.

**SOP-Based Governance**
Standard Operating Procedures are more actionable than constitutional provisions. SOPs can be updated, versioned, and enforced systematically. The former system, while principled, sometimes felt ceremonial.

### 2.2 Clarifications Needed

**Reviewer Assignment Process**
The Decree states that QA approval is always required, and at least one TU approval is required. It is not clear:
- Who assigns which TUs to a given change?
- Does QA make this determination, or does the Senior Staff Engineer?
- Can a TU self-assign to a review if they notice a change in their domain?

**Cross-Domain Changes**
Many changes span multiple domains. For example, adding a new constraint type affects:
- `model/` (TU-SKETCH domain)
- `core/commands.py` (TU-SCENE domain)
- `ui/tools.py` (TU-UI and TU-INPUT domains)

Under the former system, cross-domain matters required coordination among affected Guardians. Under the new system:
- Are all affected TUs automatically assigned as reviewers?
- Or is a minimal set assigned, with others providing advisory input?

**Expedited Path**
The former system had an "Expedited Path" for trivial changes (bug fixes < 3 files, config adjustments). Does the new system retain any expedited path, or does every change require full CRB review?

---

## 3. Concerns

### 3.1 Loss of Domain Veto

Under the former system, a Guardian held "absolute veto authority" within their domain. A single Guardian could reject a proposal unilaterally if it violated their domain's laws.

Under the new system, unanimous consent is required among *assigned* reviewers. This raises the question: if TU-SKETCH is not assigned to a review, but the change inadvertently affects the Sketch domain, is there a mechanism for TU-SKETCH to intervene?

**Recommendation:** Consider a provision allowing any TU to raise a concern about a change in their domain, even if not initially assigned. QA could then determine whether to add them as a required reviewer.

### 3.2 Preservation of Domain Boundaries

The Sketch domain's purity is foundational. The one-way dependency (Compiler reads Sketch, Sketch never imports Engine) prevents architectural decay. Under the legislative model, this was a "Foundational Principle" requiring unanimity to amend.

**Question:** What is the status of Foundational Principles under the new system? Are they encoded in SOPs? Do they have special protection, or are they now mutable by standard CRB approval?

---

## 4. Suggestions

### 4.1 Domain Sovereignty SOP

I recommend creating a specific SOP documenting the domain boundaries:

- **SOP-DOMAIN-001: Sketch Domain Sovereignty**
  - The Sketch subsystem (`model/`) shall not import from `engine/`
  - Physics concepts (velocity, mass, force, atoms) are prohibited in Sketch code
  - Violations constitute automatic rejection by TU-SKETCH

This makes the formerly constitutional principle into an enforceable, documented standard.

### 4.2 Constraint Stability SOP

Similarly, constraint implementation standards should be formalized:

- **SOP-CONSTRAINT-001: Constraint Implementation Requirements**
  - All constraints must implement `project()` per PBD methodology
  - Numerical stability must be verified (no division by zero, degenerate case handling)
  - Constraints must include test cases for edge conditions

### 4.3 Review Assignment Matrix

A documented matrix mapping file paths to required TU reviewers would streamline the assignment process:

| Path Pattern | Required TU |
|--------------|-------------|
| `model/*` | TU-SKETCH |
| `engine/*` | TU-SIM |
| `core/scene.py` | TU-SCENE |
| `ui/*` | TU-UI, TU-INPUT |
| `core/commands.py` | TU-SCENE |

---

## 5. Questions for the Lead Engineer

1. **Foundational Principles:** Are the Air Gap, Command Pattern, and AvG Principle still protected with special status, or are they now standard quality guidelines mutable by CRB approval?

2. **Self-Assignment:** May a TU self-assign to a review if they observe changes in their domain that were not flagged for their review?

3. **Advisory vs. Blocking:** When a TU provides "advisory input" (per my Role Description), can that input block a change, or is it truly non-blocking?

4. **SOP Development:** Who is responsible for drafting the initial SOPs that will govern CRB operations? Is this a task for QA, the Senior Staff Engineer, or a collaborative effort?

---

## 6. Closing Remarks

The transition is accepted. The principles I was sworn to protect remain in force as quality standards. The mechanism of enforcement has changed, but the mission has not.

I stand ready to serve on the Change Review Board.

---

*Respectfully submitted,*

**TU-SKETCH**
*Technical Unit Representative - CAD/Geometry*
*Formerly, The Sketch Guardian*
