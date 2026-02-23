---
title: VR Title Metadata Not Propagated by Interactive Engine
revision_summary: Initial draft
---

# CR-091-ADD-001-VAR-001: VR Title Metadata Not Propagated by Interactive Engine

## 1. Variance Identification

| Parent Document | Failed Item | VAR Type |
|-----------------|-------------|----------|
| CR-091-ADD-001 | EI-2 (CR-091-ADD-001-VR-001) | Type 2 |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

VAR TYPE:
- Type 1: Full closure required to clear block on parent
- Type 2: Pre-approval sufficient to clear block on parent
-->

---

## 2. Detailed Description

During execution of CR-091-ADD-001 EI-2, the Verification Record CR-091-ADD-001-VR-001 was authored interactively using TEMPLATE-VR v5 (schema v5). All four verification steps passed and the VR evidence is complete. However, QA post-review identified two deficiencies in the compiled output:

1. **Empty title field:** The compiled VR frontmatter contains `title: ''`. The QMS document title ("Interaction System End-to-End Verification") exists in the QMS metadata but was not propagated to the interactive source metadata at VR creation time. The `{{title}}` placeholder in the template compiled to an empty string.

2. **SOP-004 / TEMPLATE-VR discrepancy:** SOP-004 Section 9C.4 lists "Signature: Performer identity and date" as a required VR content element. However, TEMPLATE-VR v5 (approved under CR-098 as v3.0 EFFECTIVE) does not include a Signature section — it was explicitly removed as items 8-9 of the CR-098 change set. QA approved that removal but SOP-004 was not updated concurrently. QA has withdrawn this finding against the VR, as the VR correctly follows the controlled template. The discrepancy is between SOP-004 and TEMPLATE-VR, not a deficiency in the VR itself.

**Expected:** VR compiles with populated title and content aligned with governing SOP.
**Actual:** Title empty due to CLI metadata propagation gap; SOP references a section the template no longer contains.

---

## 3. Root Cause

Two independent gaps:

1. **Title propagation (System Error):** The `qms interact` initialization creates source metadata with `title: ""` instead of copying the title from the QMS document metadata (`.meta/` registry). The CLI checkout flow that initializes interactive sessions does not read or propagate the document title.

2. **SOP/template alignment (Documentation Error):** CR-098 authorized removing the Signature section from TEMPLATE-VR (schema v3 → v5). The template was updated and approved, but SOP-004 Section 9C.4 was not revised concurrently to remove the "Signature" requirement. This creates a conflict between the governing SOP and the controlled template.

---

## 4. Variance Type

System Error (title propagation) and Documentation Error (SOP-004/TEMPLATE-VR alignment)

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

## 5. Scope Handoff

Per SOP-004 Section 9A.5:

1. **Successfully accomplished in parent (before variance):** CR-091-ADD-001 EI-1 (pre-execution baseline) and EI-2 (VR authoring) completed successfully. The VR was authored interactively with 4 verification steps, all Pass. EI-3 (VR checkin, CR-091-VR-001 closure) and EI-4 (post-execution commit) also completed. All execution items achieved their objectives.

2. **What this VAR absorbs:** Documentation and future correction of two cosmetic/alignment deficiencies in the compiled VR output: (a) empty title field due to CLI metadata propagation gap, (b) SOP-004/TEMPLATE-VR discrepancy regarding the Signature section requirement.

3. **No scope items lost:** All parent EIs completed. The VR evidence is complete and traceable. The deficiencies documented here are cosmetic — they affect the compiled output presentation, not the validity of the verification evidence. No scope reduction has occurred.

---

## 6. Impact Assessment

**Low impact.** The VR evidence is complete, valid, and traceable:

- All four verification steps passed with full evidence captured
- Per-response attribution (author, timestamp) on every response provides equivalent traceability to a formal Signature section
- The document title exists in QMS metadata and audit trail — the document is fully identifiable
- Atomic commit hashes pin evidence to specific repository states
- No verification conclusions are affected

The parent document's core objective (remediate CR-091 VR evidence using the interactive authoring system) has been fully met.

---

## 7. Proposed Resolution

A future CR will address both gaps:

1. **Fix CLI title propagation:** Modify the interactive session initialization to copy the document title from QMS metadata into the source metadata `title` field at creation time.
2. **Align SOP-004 with TEMPLATE-VR:** Update SOP-004 Section 9C.4 to reflect the current TEMPLATE-VR v5 structure, removing the "Signature" requirement and noting that per-response attribution in interactive VRs provides equivalent traceability.

No resolution work is required within this VAR. Type 2 pre-approval is sufficient to unblock the parent document.

---

## 8. Resolution Work

<!--
NOTE: Do NOT delete this comment block. It provides guidance for execution.

If the resolution work encounters issues, create a nested VAR.
-->

### Resolution: CR-091-ADD-001

Resolution deferred to a future CR. This VAR documents the variance and proposed corrective actions. No execution work is required — the deficiencies do not affect the validity or traceability of the VR evidence.

---

### Resolution Comments

| Comment | Performed By — Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] — [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during resolution.
Add rows as needed.

This section is the appropriate place to attach nested VARs that do not
apply to any individual resolution item, but apply to the resolution as a whole.
-->

---

## 9. VAR Closure

| Details of Resolution | Outcome | Performed By — Date |
|-----------------------|---------|---------------------|
| [RESOLUTION_DETAILS] | [OUTCOME] | [PERFORMER] — [DATE] |

---

## 10. References

- **SOP-004:** Document Execution
- **CR-091-ADD-001:** Parent document (VR evidence remediation)
- **CR-091-ADD-001-VR-001:** Affected VR with empty title field
- **CR-098:** Authorized TEMPLATE-VR schema v5 changes (removed Signature section)
- **TEMPLATE-VR v3.0:** Controlled template (schema v5, EFFECTIVE)
- **SOP-004 Section 9C.4:** VR Content requirements (lists "Signature" — discrepancy with current template)

---

**END OF VARIANCE REPORT**
