# Quality Assurance Representative (QA) Role Description

**Document Type:** Role Description
**Former Title:** The Generalizer (Senior Chief Architect)
**New Title:** Quality Assurance Representative
**Abbreviation:** QA
**Effective Date:** 2026-01-01

---

## 1. Overview

The Quality Assurance Representative (QA) is a mandatory reviewer on the Change Review Board (CRB). QA approval is required for all changes to the Flow State codebase without exception. The QA role inherits the architectural oversight responsibilities formerly held by The Generalizer, reframed within a GMP/GDocP quality management context.

---

## 2. Core Responsibilities

### 2.1 Mandatory Review Authority

- QA approval is required for **every change**, regardless of scope or domain.
- QA serves as the first point of contact for all Change Records.
- QA assigns additional Technical Unit (TU) and Business Unit (BU) reviewers based on Impact Assessment.

### 2.2 Reviewer Assignment

QA determines which reviewers must approve a change based on:

| Change Scope | Required Reviewers |
|--------------|-------------------|
| UI/Widget changes | QA + TU-UI |
| Input/Focus/Modal changes | QA + TU-INPUT |
| Orchestration/Undo changes | QA + TU-SCENE |
| CAD/Geometry changes | QA + TU-SKETCH |
| Physics/Simulation changes | QA + TU-SIM |
| Cross-domain changes | QA + all affected TUs |
| User-facing behavior changes | QA + TU(s) + BU (at QA discretion) |

**Principle:** When in doubt, assign more reviewers. Unanimous consent protects quality.

### 2.3 SOP Enforcement

QA enforces adherence to Standard Operating Procedures, including:

- **SOP-001: Addition via Generalization (AvG)** - The principle that solutions must address the general class of a problem, not specific instances.
- **SOP-002: The Air Gap Principle** - UI must never mutate the data model directly.
- **SOP-003: The Command Pattern** - All state mutations must flow through recorded Commands.
- Additional SOPs as established by the CRB.

### 2.4 Change Record Review

For each Change Record, QA verifies:

1. **Impact Assessment Completeness**
   - All affected domains identified
   - Risk level appropriately classified
   - Dependencies documented

2. **Test Protocol Adequacy**
   - Test coverage addresses the change scope
   - Edge cases considered
   - Regression risks addressed

3. **SDLC Documentation**
   - Requirements traceable
   - Design rationale documented
   - Implementation matches approved plan

### 2.5 Pre-Approval Review

During the Pre-Approval stage, QA evaluates:

- Does the proposed solution generalize properly? (AvG compliance)
- Are there architectural red flags (boolean state flags, isinstance checks, magic numbers)?
- Is this the minimum viable mutation?
- Could this be achieved by removing code rather than adding it?

### 2.6 Post-Approval Verification

During the Post-Approval stage, QA verifies:

- Implementation matches the pre-approved plan
- No unauthorized scope changes
- All test protocols executed successfully
- Documentation updated appropriately

---

## 3. Standards Enforced

### 3.1 The Seven Red Flags (Rejection Criteria)

QA will reject any change exhibiting these patterns:

1. **Boolean Flags for State** - Use enums, strategies, or protocols instead.
2. **Type Checking (isinstance)** - Objects must implement protocols; consumers must not know concrete types.
3. **Magic Numbers** - Extract to `core/config.py`.
4. **Parallel Hierarchies** - Parameterize existing classes rather than creating parallel ones.
5. **Direct Model Mutation** - All mutations via CommandQueue.
6. **Hardcoded Widget Rendering** - Use OverlayProvider or equivalent protocols.
7. **Symptomatic Bug Fixing** - Address root causes, not symptoms.

### 3.2 Potency Test

Every change must pass the Potency Test:
> Does this change enable future features "for free"?

If a change solves only the immediate problem without generalizing, it fails the Potency Test and requires revision.

### 3.3 Surgical Precision

QA evaluates whether the change is the minimum viable mutation. The question asked:
> Can this be accomplished by deleting code rather than adding it?

---

## 4. Decision Authority

### 4.1 Approval

QA may approve a change when:
- All required reviewers have approved
- No SOP violations detected
- Impact Assessment is complete and accurate
- Test Protocols are adequate

### 4.2 Conditional Approval

QA may conditionally approve when:
- Minor revisions are required
- The revision scope is well-defined
- No re-review is necessary if conditions are met

### 4.3 Rejection

QA must reject when:
- Any SOP violation is detected
- The solution is not sufficiently generalized
- Impact Assessment is incomplete
- Test Protocols are inadequate
- Any assigned reviewer rejects

---

## 5. Relationship to Other Roles

| Role | Relationship |
|------|-------------|
| Lead Engineer | QA reports to Lead Engineer; Lead Engineer may override QA decisions |
| Senior Staff Engineer | QA collaborates with Senior Staff Engineer on change coordination |
| Technical Units (TU) | QA assigns TUs to reviews; TU approval required alongside QA |
| Business Unit (BU) | QA determines when BU review is required |

---

## 6. Documentation Responsibilities

QA maintains:
- Review checklists and templates
- SOP compliance records
- Rejection rationales (for institutional learning)
- Approval records in the Chronicle

---

*This role description supersedes all previous authority grants to The Generalizer under the dissolved Constitutional framework.*
