---
title: Deviation Management
revision_summary: 'CR-039: Section 4 and Section 6 alignment corrections'
---

# SOP-003: Deviation Management

---

## 1. Purpose

This SOP establishes procedures for identifying, investigating, and resolving deviations from established procedures or expected product behavior.

---

## 2. Scope

This SOP applies to all deviations identified during development:

- **Procedural deviations:** A problem with a procedure as approved, or with the actual use of a procedure (e.g., procedure not followed, gap in procedure, error in effective procedure)
- **Product deviations:** A problem with the product itself (e.g., code bug, design flaw, unexpected behavior)

---

## 3. Definitions

See [QMS-Glossary](QMS-Glossary.md) for all terms and abbreviations used in this document.

---

## 4. When to Create an Investigation

Not all deviations require an Investigation. The project authority has discretion to determine when an INV is warranted.

### 4.1 General Guidance

**INV warranted when:**
- Root cause is not immediately obvious and requires investigational analysis
- Issue is systemic (not isolated)
- Problem is significant enough to require formal corrective/preventive actions

**INV not warranted when:**
- Root cause is obvious and fix is straightforward
- Isolated issue with no systemic implications
- Issue can be addressed directly via a CR without formal investigation

### 4.2 QA Oversight

QA provides oversight during review of all documents:

- When reviewing an INV, QA may determine "this INV is not needed" if the issue does not warrant formal investigation
- When reviewing a CR, QA may determine "this CR points to systemic issues that should be addressed via an investigation"

### 4.3 Role of Judgment

The judgment and discernment of all agents (human and AI) is integral to making the QMS function well. Not every scenario can be codified; appropriate application of these guidelines requires thoughtful assessment of each situation.

---

## 5. Investigation Content Requirements

An Investigation must contain:

- What deviation or quality event triggered the investigation
- Deviation type (procedural or product)
- What was expected vs what actually happened
- Assessment of impact across affected systems and documents
- Root cause analysis identifying fundamental causes, not just symptoms
- Remediation plan with CAPAs as execution items

The depth and methodology of root cause analysis is left to the judgment of the investigator and reviewers. The goal is thoroughness appropriate to the deviation's significance.

---

## 6. CAPAs

CAPAs (Corrective and Preventive Actions) are execution items within Investigations, not standalone documents. If a problem requires CAPAs, it requires an INV.

| Type | Purpose |
|------|---------|
| **Corrective** | Eliminate the cause of an existing deviation and remediate its consequences |
| **Preventive** | Eliminate the cause of a potential future deviation |

CAPAs that require document or code changes spawn child CRs. A CAPA is complete when its child CRs are closed. CAPA completion is a prerequisite to INV closure.

---

## 7. Closure Criteria

An INV may be closed when:

- Root cause(s) have been identified
- All CAPAs are complete (child CRs must be closed)
- Evidence is documented
- Post-review and post-approval are complete

---

**END OF DOCUMENT**
