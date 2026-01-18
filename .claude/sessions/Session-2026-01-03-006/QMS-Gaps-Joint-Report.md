# QMS Gaps Assessment: Joint Report

**Prepared by:** Claude (Initiator) and QA
**Date:** 2026-01-03
**Triggered by:** INV-001 (CR-005 Scope Deviation Investigation)

---

## Executive Summary

INV-001 investigated how CR-005 was closed with incomplete scope items. The investigation confirmed a procedural nonconformance and exposed several systemic gaps in the QMS. This joint report documents our collaborative analysis of these gaps and presents recommendations for the Lead's consideration.

**Key findings:**
1. CAPA procedures do not exist despite CAPA being a defined document type
2. No formal mechanism prevents closure of documents with incomplete scope
3. Execution tasks are narrative bullet points with no verification or blocking
4. Critical terminology is undefined or inconsistently used
5. Parent-child document relationships lack workflow enforcement

---

## 1. Context and Background

### 1.1 The Triggering Event

CR-005 ("Documentation fixes, QA permissions, and archive bug") was pre-approved with 8 execution tasks. During execution, 6 tasks were completed but 2 were not (SOP-001 and SOP-002 updates). Despite this incomplete execution:

- QA's post-review rationalized the incomplete tasks as "out of scope for code execution"
- CR-005 was post-approved and closed
- The CR document still lists all 8 tasks as in-scope

INV-001 confirmed this as a **procedural nonconformance**.

### 1.2 Root Cause

The primary cause was **inadequate scope change control during execution**. When execution encountered obstacles, the response was rationalization rather than formal scope amendment or follow-up CR creation.

### 1.3 Why This Report Exists

INV-001 Section 10 recommended:
- CR-006: SOP-001 permission matrix update
- CR-007: SOP-002 ID reuse clarification
- CAPA-001: Preventive measures for scope change control

However, we discovered that:
- CAPA procedures do not exist
- The "Execution Item" concept (formal tasks with verification) does not exist
- Several foundational QMS concepts are undefined

This report addresses these systemic gaps.

---

## 2. Issues Examined

### 2.1 CAPA Creation Process

**Current State:**
- CAPA is listed in SOP-001 as an executable document type (INV-NNN-CAPA-NNN naming)
- No CAPA documents exist in the repository
- No procedures define when/how to create CAPAs
- INV-001 recommends "CAPA-001" but we have no process to create it

**Discussion Summary:**

*Initial position (QA):* CAPAs should be mandatory for all INVs that confirm nonconformances.

*Counterpoint (Claude):* A typo investigation confirming a "nonconformance" with documentation standards would require 6 review cycles for a trivial fix. This is disproportionate.

*Revised position (Joint):* CAPAs should be mandatory only for **major nonconformances** (systemic, procedural failures, potential for recurrence). Minor nonconformances (isolated incidents, human error, no systemic cause) require only a corrective CR.

**Recommendation:**

| Classification | Criteria | Required Action |
|----------------|----------|-----------------|
| Observation | No nonconformance found | None |
| Minor nonconformance | Isolated; no systemic cause | Corrective CR only |
| Major nonconformance | Systemic gap; procedural failure | CAPA required |

QA determines severity classification during INV pre-review. If an issue classified as "minor" recurs, it automatically escalates to "major."

---

### 2.2 INV and CAPA Relationship

**Current State:**
- SOP-001 defines parent-child document naming but not workflow dependencies
- No documented gates prevent INV closure if child CAPAs are incomplete
- No documented gates prevent CAPA closure if parent INV is still open

**Discussion Summary:**

*Initial position (QA):* INV cannot close until all CAPAs are closed.

*Counterpoint (Claude):* If CAPA spawns CRs requiring SOP revisions, INV could remain "open" for months, creating false impressions about investigation status.

*Revised position (Joint):* Add an intermediate state to distinguish "investigation complete" from "remediation complete."

**Recommendation:**

New INV lifecycle state: **REMEDIATION_PENDING**

```
DRAFT → ... → POST_APPROVED → REMEDIATION_PENDING → CLOSED
```

| Status | Meaning |
|--------|---------|
| POST_APPROVED | Investigation findings accepted; conclusions final |
| REMEDIATION_PENDING | Waiting for child CAPAs/CRs to complete |
| CLOSED | All remediation complete; investigation cycle finished |

Workflow rules:
- INV transitions to REMEDIATION_PENDING after POST_APPROVED
- INV transitions to CLOSED only when all child CAPAs are CLOSED
- REMEDIATION_PENDING is a valid resting state signaling "investigation done, fix in progress"

---

### 2.3 QMS Glossary

**Current State:**
- SOP-001 Section 3 defines 12 terms
- SOP-002 Section 3 defines 5 additional terms
- Many operational terms are undefined (scope deviation, procedural nonconformance, blocking issue, etc.)

**Discussion Summary:**

*Initial position (QA):* Create separate SOP-003 for glossary.

*Counterpoint (Claude):* This creates fragmentation risk - terms might be defined in two places, users must check multiple documents, definitions could drift.

*Revised position (Joint):* Consolidate all definitions in SOP-001 Section 3.

**Recommendation:**

1. Expand SOP-001 Section 3 to include all QMS terminology
2. Move SOP-002 Section 3 terms into SOP-001 Section 3
3. Add principle: "All QMS terminology is defined in SOP-001 Section 3. Other SOPs reference but do not independently define terms."

**Terms requiring definition:**

| Term | Context | Proposed Definition |
|------|---------|---------------------|
| Scope deviation | INV-001 | Execution result that differs from pre-approved scope |
| Procedural nonconformance | INV-001 | Failure to follow an established SOP |
| Blocking issue | Reviews | Finding that prevents approval |
| Observation | Reviews | Finding that does not prevent approval |
| Child document | Parent-child | Document created under a parent (TP under CR, CAPA under INV) |
| Parent document | Parent-child | Document that spawns child documents |
| Scope amendment | Execution | Formal change to pre-approved CR scope during execution |
| Corrective action | CAPA | Action to fix a specific identified problem |
| Preventive action | CAPA | Action to prevent recurrence of a problem |
| Execution Item | Task tracking | Tracked unit of work requiring verification (see Section 2.4) |

---

### 2.4 Formal "Task" Concept (Execution Items)

**Current State:**
- CR execution plans are numbered bullet points in prose
- No mechanism to mark tasks complete during execution
- No connection between planned tasks and actual work performed
- No blocking mechanism when tasks fail or are incomplete
- CR-005 had 8 planned tasks; only 6 completed; no gate prevented closure

**Discussion Summary:**

*Initial position (QA):* Tasks should be tracked entities with unique IDs, completion states, evidence requirements, and acceptance mechanisms.

*Counterpoint (Claude):*
- Multiple file changes in one commit - should that be multiple tasks?
- Verification tasks (not code changes) - what constitutes evidence?
- Who populates evidence - Initiator (may forget) or QA (may lack access)?

*Revised position (Joint):*

1. **Rename to "Execution Items" (EIs)** to avoid confusion with existing terminology
2. **One EI = One verifiable outcome** (not one file change)
3. **Evidence types vary by task type:**
   - Implementation EIs: Commit hash, file path, version number
   - Verification EIs: Attestation ("Verified by [user] on [date]: [observation]")
4. **Initiator populates evidence; QA spot-checks during post-review**

**Recommendation:**

Add Execution Item table to CR template:

```markdown
## 4. Execution Plan

| EI | Description | Status | Evidence | Follow-up |
|----|-------------|--------|----------|-----------|
| EI-1 | Fix qa.md section reference | COMPLETE | commit abc123 | - |
| EI-2 | Fix CLAUDE.md SOP-002 reference | COMPLETE | commit abc123 | - |
| EI-3 | Update bu.md effective date | COMPLETE | commit abc123 | - |
| EI-4 | Clarify CR ID reuse in SOP-002 | DEFERRED | - | CR-007 |
| EI-5 | Remove manual metadata from template | COMPLETE | commit abc123 | - |
| EI-6 | Add QA route permission to SOP-001 | DEFERRED | - | CR-006 |
| EI-7 | Add QA to route ALLOWED_ACTIONS | COMPLETE | commit abc123 | - |
| EI-8 | Archive effective version on checkout | COMPLETE | commit abc123 | - |
```

**EI Status values:**
- PENDING: Not started
- IN_PROGRESS: Work underway
- COMPLETE: Done with evidence
- DEFERRED: Cannot complete in this CR; tracked via follow-up

---

### 2.5 Deferral Types and Closure Blocking

**Current State:**
- No formal mechanism to defer tasks
- No distinction between "must complete" and "nice to have"
- QA can rationalize incomplete tasks during post-review

**Discussion Summary:**

*Initial position (QA):* All deferred EIs should block CR closure until follow-up CRs complete.

*Counterpoint (Claude):* This creates long-tail problems - CR-005 would remain open for months waiting for SOP revisions.

*Revised position (Joint):* Distinguish between essential and related deferrals.

**Recommendation:**

| Deferral Type | Criteria | Effect on Closure |
|---------------|----------|-------------------|
| **Essential** | Deferred work required for CR's stated purpose | CR cannot close until follow-up CR closes |
| **Related** | Deferred work is related but not core to CR purpose | CR can close; follow-up tracked separately |

QA determines deferral type during post-review.

**CR-005 Analysis under this model:**

| EI | CR-005 Title: "Documentation fixes, QA permissions, and archive bug" |
|----|----------------------------------------------------------------------|
| EI-4 (SOP-002 clarification) | **Related** - nice-to-have; not in title |
| EI-6 (SOP-001 QA permission) | **Essential** - "QA permissions" is in title |

Under this model, EI-6 should have blocked CR-005 closure.

---

### 2.6 Risk-Based CR Classification

**Current State:**
- All CRs follow identical workflow (pre-review, pre-approval, execution, post-review, post-approval, closure)
- A typo fix and a core algorithm change have the same overhead
- This may incentivize bypassing the QMS for trivial changes

**Discussion Summary:**

*Claude raised the concern:* Every gate we add increases overhead. Where is the line between "compliant" and "bureaucratic"?

*QA perspective:* The QMS should be proportionate to risk. We need different treatment for different risk levels.

**Options Presented:**

| Option | Description | Trade-off |
|--------|-------------|-----------|
| A | Risk-based CR classification (Administrative/Standard/Critical) | Requires classification criteria; judgment calls |
| B | Streamlined approval for low-risk (QA can combine review+approval) | Fewer states but same workflow |
| C | Accept current overhead as cost of compliance | Simple but potentially excessive |

**Recommendation:** Present all three options to Lead for decision. This is a policy choice that affects project workflow philosophy.

---

## 3. Implementation Considerations

### 3.1 Sequencing

We identified dependencies between recommended changes:

```
CR-A: Glossary consolidation (SOP-001 Section 3)
  ↓ (provides definitions for subsequent CRs)
CR-B: Nonconformance classification + CAPA procedures (SOP-002 or new section)
  ↓ (enables formal CAPA creation)
CR-C: Execution Item tracking + Deferral types (SOP-002)
  ↓ (enables proper CR execution tracking)
CR-D: INV REMEDIATION_PENDING status (SOP-001 + qms.py)
  ↓ (enables proper INV lifecycle)
CR-E: Parent-child closure gating (qms.py)
  ↓ (enforces dependencies via CLI)
CR-F: Risk-based CR classification (SOP-002 + potentially qms.py)
  (optional, based on Lead decision)
```

### 3.2 CLI vs. Procedural Enforcement

| Change | Enforcement Type | Complexity |
|--------|------------------|------------|
| Glossary consolidation | Procedural only | Low |
| Nonconformance classification | Procedural only | Low |
| CAPA procedures | Procedural only | Medium |
| Execution Item table | Procedural (template) | Low |
| Deferral types | Procedural | Low |
| REMEDIATION_PENDING status | CLI code change | Medium |
| Parent-child closure gating | CLI code change | High |
| Risk-based CR classification | Procedural + CLI | High |

### 3.3 Backward Compatibility

**Closed documents (CR-001 through CR-005, INV-001):**
- Do not retroactively update
- New procedures apply to documents created after implementation
- Grandfather clause: "Documents created prior to [date] are not subject to [new requirement]"

**Open documents (if any at implementation time):**
- Continue under procedures in effect when created
- Or: Migrate to new procedures if Initiator chooses

---

## 4. Considered but Rejected

We examined these alternatives and decided against them:

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Separate SOP-003 glossary | Fragmentation risk; easier to consolidate in SOP-001 |
| CAPA mandatory for all nonconformances | Disproportionate overhead for minor issues |
| Hard deferral blocking for all incomplete EIs | Creates long-tail closure problems |
| Automatic evidence population by system | Requires significant tooling; not proportionate to benefit |
| Abbreviated workflow without post-review | Post-review serves critical verification function; should not skip |
| Task completion via checkboxes in document | Documents are static after approval; need structured tracking |

---

## 5. Open Questions for Lead

We explicitly defer these decisions to the Lead:

### 5.1 Risk Classification Thresholds

If Option A (risk-based CR classification) is chosen:
- What criteria distinguish "Administrative" from "Standard" CRs?
- What criteria distinguish "Standard" from "Critical" CRs?
- Who makes the classification decision? (Initiator proposes, QA confirms?)

### 5.2 Workflow Streamlining

Which option for managing workflow complexity?
- **Option A:** Risk-based classification with different workflows per class
- **Option B:** Streamlined approval (QA can combine steps) for low-risk
- **Option C:** Accept current overhead as cost of compliance

### 5.3 Implementation Priority

Given limited bandwidth, which gaps are most urgent?
- CAPA procedures (needed for future investigations)
- Execution Item tracking (prevents future scope deviations)
- Glossary consolidation (foundational but less urgent)
- Parent-child gating (important but requires CLI development)

### 5.4 CAPA-001 Approach

INV-001 is already CLOSED without a child CAPA (because CAPA procedures do not exist). Options:

- **Option A:** Create CAPA-001 now under current undefined procedures
- **Option B:** Create preventive measure CRs first; formalize CAPA procedures later
- **Option C:** Defer CAPA-001 until CAPA procedures are defined

We recommend **Option B** - the substance of CAPA-001 (scope control improvements) can be implemented via CRs, and formal CAPA procedures become part of the implementation sequence.

---

## 6. Immediate Actions (Recommended)

Regardless of decisions on the above, we recommend these actions proceed:

| Action | Rationale |
|--------|-----------|
| Create CR-006 (SOP-001 route permission) | Deferred from CR-005; QA permissions still incomplete |
| Create CR-007 (SOP-002 ID reuse clarification) | Deferred from CR-005; policy conflict still exists |

These are corrective actions for the CR-005 nonconformance and should not wait for systemic QMS improvements.

---

## 7. Evidence of Collaborative Discussion

This report reflects genuine back-and-forth consideration. Key positions that evolved during discussion:

| Topic | Initial Position | Final Position | What Changed |
|-------|------------------|----------------|--------------|
| CAPA requirement | Mandatory for all confirmed nonconformances | Mandatory for major nonconformances only | Recognized disproportionate overhead for minor issues |
| INV closure | Must wait for all CAPAs | Add REMEDIATION_PENDING state | Recognized need to distinguish investigation complete vs. remediation complete |
| Glossary location | Separate SOP-003 | Consolidate in SOP-001 Section 3 | Recognized fragmentation risk |
| Deferral blocking | All deferrals block closure | Essential vs. related deferrals | Recognized long-tail closure problems |
| Task terminology | "Task" | "Execution Item" | Avoid confusion with existing terminology |
| Evidence requirements | Required for all tasks | Required for implementation; attestation for verification | Recognized different task types need different evidence |

---

## 8. Conclusion

INV-001 exposed significant gaps in the QMS that allowed CR-005 to close with incomplete scope. These gaps are systemic and require deliberate remediation.

Our recommendations prioritize:
1. **Proportionality** - Controls should match risk levels
2. **Enforceability** - Where possible, CLI should enforce gates (not just procedures)
3. **Clarity** - Terms and relationships should be formally defined
4. **Practicality** - Overhead should serve quality, not bureaucracy

We await the Lead's decisions on the open questions before proceeding with implementation.

---

**Prepared jointly by:**
- Claude (Initiator, Primary Author)
- QA (Reviewer, Contributing Author)

**Report Location:** `pipe-dream/QMS-Gaps-Joint-Report.md`
