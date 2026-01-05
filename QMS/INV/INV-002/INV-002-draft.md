---
title: SOP-005 Missing Revision Summary
---

# INV-002: SOP-005 Missing Revision Summary

## 1. Purpose

Investigate how SOP-005 was approved and made EFFECTIVE without the required `revision_summary` field in its frontmatter, in violation of SOP-001 and SOP-002 requirements.

---

## 2. Scope

This investigation examines:
- The requirements for document frontmatter in SOP-001
- The revision summary requirements in SOP-002 Section 8
- The SOP-005 approval process under CR-010
- Why the nonconformance was not detected during QA review
- Corrective and preventive actions

---

## 3. Background

CR-010 was created to establish SOP-005: Code Governance. The CR proceeded through the full change control lifecycle:
- Pre-review: PASSED
- Pre-approval: APPROVED
- Execution: All 5 items COMPLETE
- Post-review: PASSED
- Post-approval: APPROVED
- Closed: 2026-01-05

SOP-005 v1.0 became EFFECTIVE. However, the document's frontmatter is missing the required `revision_summary` field.

---

## 4. Evidence Review

### 4.1 SOP-005 Frontmatter (As Approved)

```yaml
---
title: Code Governance
---
```

The frontmatter contains only `title:`. No `revision_summary` field is present.

### 4.2 SOP-001 Section 5.2 Requirements

SOP-001 specifies the required frontmatter fields, including:

> - **revision_summary**: Updated each revision cycle to describe changes. Must begin with the authorizing CR ID for traceability (e.g., `CR-004: Add traceability requirement`). Exception: initial document creation (v0.1) does not require a CR ID.

Note: While initial v0.1 creation does not require a CR ID in the revision_summary, this exception does not waive the requirement for the field itself. More importantly, SOP-005 was approved as v1.0 (not v0.1), meaning it had already transitioned through a revision cycle and the full requirement applies.

### 4.3 SOP-002 Section 8 Requirements

SOP-002 Section 8 states:

> All document revisions made under a Change Record must reference the CR ID in their `revision_summary` frontmatter field.

And provides the format:

```yaml
revision_summary: "CR-XXX: Description of changes"
```

### 4.4 Compliant Example (SOP-001)

For comparison, SOP-001's frontmatter correctly includes:

```yaml
---
title: Document Control
revision_summary: 'CR-006: Grant QA route permission in Section 4.2'
---
```

### 4.5 QA Review and Approval

QA reviewed SOP-005 and recommended approval, then approved it. The missing `revision_summary` field was not flagged during either review or approval.

---

## 5. Findings

### Finding 1: Document Nonconformance

SOP-005 v1.0 is missing the required `revision_summary` field, in violation of:
- SOP-001 Section 5.2 (document frontmatter requirements)
- SOP-002 Section 8 (CR traceability requirements)

### Finding 2: Initiator Oversight

The initiator (claude) drafted SOP-005 without including the `revision_summary` field in the frontmatter. This was an oversight during document creation.

### Finding 3: QA Oversight

QA reviewed and approved SOP-005 without detecting the missing required field. The QA review criteria included "Document follows SOP format conventions" which was marked PASS despite the nonconformance.

### Finding 4: No Checklist Verification

Neither the initiator nor QA had a systematic checklist to verify frontmatter completeness. The review relied on implicit knowledge of requirements rather than explicit verification steps.

---

## 6. Root Cause Analysis

### Primary Cause

**No systematic verification of document frontmatter requirements.** Both initiator and QA relied on implicit knowledge rather than explicit checklists, leading to oversight of a required field.

### Contributing Factors

1. **Template deficiency** - The document creation template in qms.py produces only `title:` in the frontmatter, not prompting for other required fields
2. **Review criteria ambiguity** - "Document follows SOP format conventions" is not specific enough to ensure frontmatter completeness
3. **No automated validation** - The QMS CLI does not validate required frontmatter fields before approval

---

## 7. Corrective Actions

### CAPA-001: Add Revision Summary to SOP-005

**Type:** Corrective

**Description:** Create a CR to add the missing `revision_summary` field to SOP-005.

**Proposed Change:**
```yaml
---
title: Code Governance
revision_summary: 'CR-010: Initial creation of Code Governance SOP'
---
```

**Owner:** claude

---

## 8. Preventive Actions

### CAPA-002: Enhance QA Review Checklist

**Type:** Preventive

**Description:** Update QA review procedures to include explicit verification of required frontmatter fields:
- [ ] `title` present
- [ ] `revision_summary` present and references authorizing CR

This could be implemented as:
- A procedural update to SOP-001 or SOP-002
- A checklist document for QA reviewers
- An enhancement to QA agent instructions

**Owner:** QA

### CAPA-003: Enhance Document Template (Future)

**Type:** Preventive

**Description:** Consider updating the qms.py document creation template to include placeholder or prompt for `revision_summary` field.

**Owner:** TBD (requires code change via CR)

---

## 9. Impact Assessment

### Document Impact

SOP-005 is EFFECTIVE but nonconforming. The document's content is valid; only the frontmatter traceability metadata is missing.

### Process Impact

Low. The missing field does not affect the operational use of SOP-005. The authorizing CR (CR-010) is properly documented and closed.

### Traceability Impact

Moderate. Without `revision_summary`, the SOP-005 document does not internally reference its authorizing CR. Traceability is still maintained through CR-010's records, but not within the document itself as required.

---

## 10. Execution Plan

| EI | Description | Status | Evidence | Follow-up |
|----|-------------|--------|----------|-----------|
| EI-1 | Document findings (this INV) | COMPLETE | INV-002 v1.0 | - |
| EI-2 | Obtain QA acknowledgment of findings | COMPLETE | QA acknowledged Finding 3 during pre-review | - |
| EI-3 | Create CR for CAPA-001 (add revision_summary to SOP-005) | COMPLETE | CR-011 created | CR-011 |
| EI-4 | Execute CAPA-001 | COMPLETE | SOP-005 v2.0 EFFECTIVE with revision_summary | CR-011 CLOSED |
| EI-5 | Implement CAPA-002 (QA review checklist enhancement) | PENDING | - | - |
| EI-6 | Implement CAPA-003 (template enhancement) | PENDING | - | - |

---

## 11. Associated Documents

- **CR-010**: Authorizing CR for SOP-005 (CLOSED)
- **CR-011**: CAPA-001 corrective action (CLOSED)
- **SOP-005**: Subject document (EFFECTIVE, v2.0 compliant)
- **SOP-001**: Defines frontmatter requirements
- **SOP-002**: Defines revision_summary CR traceability requirements

---

**END OF DOCUMENT**
