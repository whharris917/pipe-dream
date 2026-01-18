# SOP Landscape Analysis: Consistency and Completeness

**Date:** 2026-01-06
**Session:** 001
**Status:** Analysis for decision-making

---

## 1. Question: Do We Need a Test Protocol SOP?

### 1.1 The Question

With SOP-006 (SDLC Governance) introducing the two-verification-type model (Unit Test / Qualitative Proof), do we need a separate SOP governing test development and execution?

### 1.2 Analysis

**What SOP-006 already covers:**
- Unit tests are verification evidence referenced in the RTM
- Qualitative proofs are authored inline in the RTM
- Human-in-the-loop verification is a type of qualitative proof
- Tests link to requirements via markers (e.g., `@verifies("REQ-SIM-001")`)
- Evidence format: test file reference + commit hash + PASS

**What a Test SOP would add:**
- Test naming conventions
- Test marker syntax standardization
- Test execution environment requirements
- Test coverage expectations

**Arguments AGAINST a separate Test SOP:**

1. **Tests are code.** They are already governed by SOP-005 (Code Governance). Test files live in the codebase, are modified via CRs, and follow the same code governance rules as application code.

2. **Tests are verification evidence.** Their role in qualification is already defined by SOP-006. The RTM documents which tests verify which requirements.

3. **Minimal documentation principle.** Adding another SOP increases maintenance burden and risks inconsistency.

4. **The two-type model is simple.** Unit Test or Qualitative Proof. If it can be scripted, it's a unit test. If it requires judgment, it's a qualitative proof. No further elaboration needed.

**What MIGHT be needed (not a full SOP):**
- A brief note in SOP-006 about test marker conventions, OR
- Leave marker conventions to system-specific documentation (e.g., CLAUDE.md)

### 1.3 Recommendation

**No separate Test SOP.** Tests are code (SOP-005) and verification evidence (SOP-006). The existing framework is sufficient.

If test marker syntax needs standardization, add a subsection to SOP-006 Section 6.3.1 (Unit Test Entries) specifying the marker convention.

---

## 2. Current SOP Inventory

| SOP | Title | Has revision_summary? | Notes |
|-----|-------|----------------------|-------|
| SOP-001 | Document Control | Yes (CR-006) | References DS, CS, OQ — now stale |
| SOP-002 | Change Control | Yes (CR-008) | References TP — may need update |
| SOP-003 | Deviation Management | **NO** | Missing frontmatter field |
| SOP-004 | Document Execution | **NO** | Missing frontmatter field; references TP |
| SOP-005 | Code Governance | Yes (CR-010) | References DS — now stale |
| SOP-006 | SDLC Governance | N/A (draft) | New, streamlined model |

---

## 3. Identified Inconsistencies

### 3.1 Frontmatter Gaps

**SOP-003** and **SOP-004** are missing the `revision_summary` field in their frontmatter. Per SOP-001 Section 5.1, this field is required.

**Fix:** Update frontmatter via CR.

### 3.2 Stale Document Type References

**SOP-001 Section 2 (Scope)** lists:
> "System Development Lifecycle Documents (RS, DS, CS, RTM, OQ)"

**SOP-001 Section 6.1 (Document Naming)** includes entries for:
- Design Specification (DS)
- Configuration Specification (CS)
- Operational Qualification (OQ)

**SOP-006** eliminates DS, CS, and OQ as required document types. Only RS and RTM are needed.

**Fix:** Update SOP-001 to reflect the streamlined SDLC model.

### 3.3 DS References in SOP-005

**SOP-005 Section 5** (Repository Structure) shows:
```
QMS/SDLC-SYS-A/
├── RS.md
├── DS.md      ← stale
└── RTM.md
```

**SOP-005 Section 9.4** mentions:
> "SDLC documents must reference the System Release version they describe"

With example referencing DS:
```yaml
# In SDLC-SYS-A-DS.md frontmatter or header
```

**Fix:** Update SOP-005 to remove DS references, align with SOP-006.

### 3.4 Test Protocol (TP) as Document Type

**SOP-002 Section 9** defines Test Protocol as a child document of CRs:
> "If QA determines that a CR requires comprehensive testing, a Test Protocol shall be created as a child document of the CR."

**SOP-004 Section 2 (Scope)** lists TP as an executable document type.

**SOP-006's model** replaces formal TPs with:
- Unit tests (code, governed by SOP-005)
- Qualitative proofs (inline in RTM)
- Human-in-the-loop verification (documented in RTM)

**Question:** Should TP be removed as a document type entirely?

**Analysis:**
- The TP concept was designed for formal test protocols requiring pre-approval, execution, and post-review
- SOP-006's model achieves the same goal more simply: tests are code, results are evidence in RTM
- However, there may be edge cases where a formal test protocol document is warranted (e.g., complex multi-system integration testing, hardware-in-the-loop scenarios)

**Recommendation:** Keep TP as an *optional* document type for exceptional cases, but clarify that the standard verification model is Unit Test / Qualitative Proof per SOP-006. Most CRs will NOT need a TP.

### 3.5 Exception Report (ER) References

**SOP-004 Section 9** defines Exception Reports for when execution encounters unexpected issues.

**SOP-001 Section 6.1** includes ER in document naming.

**Status:** ERs remain a valid concept. No inconsistency — they serve a clear purpose (documenting scope deviations during execution).

---

## 4. Proposed Final SOP Structure

Six SOPs forming a coherent, internally consistent framework:

| SOP | Title | Purpose |
|-----|-------|---------|
| **SOP-001** | Document Control | Core QMS mechanics: document types, lifecycle, users, permissions |
| **SOP-002** | Change Control | CR lifecycle: creation, review, approval, execution, closure |
| **SOP-003** | Deviation Management | INV/CAPA: when to investigate, root cause analysis, corrective actions |
| **SOP-004** | Document Execution | Executable block, execution items, evidence, scope integrity |
| **SOP-005** | Code Governance | Code in QMS: git as qualified system, development models, traceability |
| **SOP-006** | SDLC Governance | RS + RTM: requirements, verification, qualification |

### 4.1 Coverage Analysis

| Concern | Covered By |
|---------|-----------|
| Document creation, review, approval | SOP-001, SOP-002 |
| Change authorization | SOP-002 |
| Deviation handling | SOP-003 |
| Execution tracking | SOP-004 |
| Code governance | SOP-005 |
| Requirements and verification | SOP-006 |
| Agent roles and permissions | SOP-001 (Section 4) |

### 4.2 What About a 7th SOP?

Possible candidates:
- **Agent Governance** — But agent roles are already in SOP-001 Section 4
- **Test Governance** — But tests are covered by SOP-005 (code) and SOP-006 (verification)

**Conclusion:** Six SOPs are sufficient. Adding more risks documentation proliferation without added value.

---

## 5. Cleanup Actions Required

To achieve internal consistency, the following updates are needed:

### 5.1 High Priority (Blocking SOP-006 Approval)

| Action | Target | Description |
|--------|--------|-------------|
| A1 | SOP-001 | Remove DS, CS, OQ from document type lists (Sections 2, 6.1) |
| A2 | SOP-005 | Remove DS references (Sections 5, 9.4) |

### 5.2 Medium Priority (Frontmatter Compliance)

| Action | Target | Description |
|--------|--------|-------------|
| A3 | SOP-003 | Add `revision_summary` field |
| A4 | SOP-004 | Add `revision_summary` field |

### 5.3 Low Priority (Clarification)

| Action | Target | Description |
|--------|--------|-------------|
| A5 | SOP-002 | Clarify that TP is optional; standard model is Unit Test / Qualitative Proof |
| A6 | SOP-004 | Clarify TP is optional in Section 2 |

---

## 6. Implementation Path

### Option A: Single Omnibus CR

One CR to update SOP-001, SOP-002, SOP-003, SOP-004, SOP-005, and formalize SOP-006.

**Pros:** Single review cycle, all updates coordinated
**Cons:** Large scope, complex review

### Option B: Staged CRs

1. **CR-A:** Formalize SOP-006 (SDLC Governance)
2. **CR-B:** Update SOP-001 and SOP-005 to align with SOP-006 (remove DS/CS/OQ)
3. **CR-C:** Fix frontmatter on SOP-003 and SOP-004
4. **CR-D:** Clarify TP optionality in SOP-002 and SOP-004

**Pros:** Smaller, focused changes; easier review
**Cons:** Multiple review cycles

### Recommendation

**Option B (Staged CRs)** is preferred. It allows:
- SOP-006 to be established first as the authoritative SDLC model
- Subsequent CRs to reference SOP-006 when cleaning up older SOPs
- Smaller, reviewable changes

---

## 7. Summary

1. **No separate Test SOP needed.** Tests are code (SOP-005) and verification evidence (SOP-006).

2. **Six SOPs are sufficient** for the complete QMS framework.

3. **Inconsistencies exist** between newer SOPs (SOP-005, SOP-006) and older SOPs (SOP-001, SOP-003, SOP-004).

4. **Cleanup actions identified** — primarily removing stale references to DS/CS/OQ and fixing missing frontmatter.

5. **Staged CRs recommended** for the cleanup effort.

---

**End of Analysis**
