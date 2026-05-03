---
title: Permit Exploration CRs under existing scope-integrity machinery
revision_summary: 'QA pre-review cycle 1 corrections: (1) §5.4 — replaced "subsection
  numbering TBD at execution" with definite placement (new top-level `## Exploration
  CRs` section between existing `## Reviewer Assignment for Pipe Dream` and `## Review
  Criteria` sections in qa.md); locked (a)/(b)/(c) labels as immutable identifiers;
  provided verbatim section content for the executor; (2) §9.4 Phase 4 step 1 — replaced
  TBD language with definite placement instruction; (3) §10 EI-9 task description
  — same fix. Earlier history preserved: two Lead amendments incorporated in the prior
  revision (TU REQ-candidacy advisory only; out-of-bound work handled via VAR per
  SOP-004 §9A).'
---

# CR-115: Permit Exploration CRs under existing scope-integrity machinery

## 1. Purpose

Clarify under existing QMS rules that an Initiator may author a CR at intentionally low specificity ("Exploration CR") when the Scope section includes structural bounds and the Purpose explicitly identifies the CR as exploratory. The clarification reduces pre-approval cost for genuinely exploratory work without modifying any qualification, merge-gate, or post-review machinery. This is itself a Standard CR (not exploratory) — it is a deliberate process change with foreseeable consequences.

---

## 2. Scope

### 2.1 Context

CR-114 (CLOSED 2026-05-02) shipped a small Flow State change but consumed seven pre-review cycles plus four RTM cycles plus a subagent rate-limit hit. The Lead's verdict at session end: *"the sheer number of tokens we've burned through on a minor update to Flow State is absolutely untenable."*

Diagnosis: pre-approval gate cost is disproportionate to the work for small, uncontroversial CRs. The QMS today implicitly assumes worst-case CR risk and applies the same pre-approval rigor regardless. The Lead requested a path enabling rapid, free-form development inside the QMS for an upcoming beach-trip session.

A two-round design collaboration with QA (`.claude/sessions/Session-2026-05-03-001/exploration-cr-design.md`) converged on a minimal-surface clarification of existing rules. The collaboration is documented; this CR authorizes its outcome.

- **Parent Document:** None (process improvement initiated by Lead direction)

### 2.2 Changes Summary

Six clarifying additions across four files: a new paragraph in QMS-Policy §6, two notes in SOP-002, three additions to qa.md, and one note in scope-change-guide.md. No new artifacts. No new template. No new SOP. No new variant. No CLI changes.

### 2.3 Files Affected

- `Quality-Manual/QMS-Policy.md` — add paragraph in §6 Scope Integrity recognizing scope specificity as the author's judgment call (Quality-Manual submodule)
- `Quality-Manual/guides/scope-change-guide.md` — add note that out-of-bound work in an Exploration CR is handled via VAR; the VAR's resolution may authorize a new CR for legitimate scope expansion (Quality-Manual submodule)
- `QMS/SOP/SOP-002.md` — add note in §6.2 mandating bounds in Scope for Exploration CRs; add note in §7.1 clarifying QA discretion to forgo TU pre-review for Exploration CRs (main repo, controlled document)
- `.claude/agents/qa.md` — add three checklist items: (a) loose scope is not by itself REQUEST_UPDATES grounds; (b) appropriateness rejection criterion; (c) post-review uses existing scope-integrity (§7.3) and RTM (§6) machinery, no parallel checklist (main repo, agent definition)

---

## 3. Current State

QMS-Policy §6 says "the scope of execution must match the scope of the pre-approved plan" without addressing how specific the plan must be. SOP-002 §6.2 enumerates Scope content (Context, Changes Summary, Files Affected) but does not address loose-scope CRs. SOP-002 §7.1 grants QA discretion in TU assignment but has no clarifying guidance for cases where there is no specific design for TUs to evaluate. qa.md has no Exploration-CR guidance. scope-change-guide.md has no guidance on bound expansion.

In practice, the implicit assumption across these documents is that every CR carries an itemized plan reviewable by TUs at pre-approval. Loose-scope CRs are not explicitly forbidden but are also not explicitly permitted, and authoring one today would face uncertain reviewer reception.

---

## 4. Proposed State

QMS-Policy §6 explicitly recognizes scope specificity as the author's judgment call. SOP-002 §6.2 mandates that loose-scope ("Exploratory") CRs include four bounds in the Scope section: target submodule(s), execution branch, RS-immutability declaration, and anti-scope. SOP-002 §7.1 explicitly permits QA to forgo TU assignment at pre-review when these bounds are present, with mandatory TU coverage at post-review based on the actual diff. qa.md gives QA the explicit grounds to (a) accept loose scope without REQUEST_UPDATES when bounds are present, (b) reject Exploration CRs whose work belongs in a Standard CR, and (c) verify bounds adherence and existing-REQ satisfaction at post-review using existing SOP-002 §7.3 and SOP-006 §6 machinery. TU observations that the diff introduces new behavior which "should be" a REQ are advisory only — TUs RECOMMEND with such observations as comments; the decision to initiate a Nail Down CR for any flagged behavior is the Lead's exclusive prerogative. scope-change-guide.md clarifies that out-of-bound work is handled via the standard VAR mechanism: the VAR documents the deviation, and its resolution may either record a revert (bound honored) or authorize a new CR for legitimate scope expansion (the VAR itself does not expand the bound).

The merge gate (SOP-005 §7.1.3 + SOP-006 §7.4) is unchanged. RS unchanged from pre-approval baseline + RTM EFFECTIVE at advanced qualified commit + CI green + PR-merged is the same gate as today; the Exploration CR pattern simply produces a CR whose pre-approval scope was a bound rather than an itemization.

---

## 5. Change Description

### 5.1 QMS-Policy §6 — recognize scope specificity as author judgment

After the existing §6 paragraphs, append:

> Scope specificity is the author's judgment call. A CR may be authored at low specificity ("Exploration CR") when the Purpose explicitly identifies it as exploratory and the Scope section includes structural bounds (per SOP-002 §6.2). The adherence-to-plan rule applies to whatever specificity was committed to: a loose plan is a license to do anything *within the stated bounds*, not a license to do anything. Work that would exit the bounds is handled via the standard VAR mechanism (per scope-change-guide); the VAR documents the deviation and may authorize a new CR if legitimate scope expansion is warranted.

### 5.2 SOP-002 §6.2 — bounds requirement for Exploratory CRs

Add a note at the end of §6.2:

> **Exploratory CRs.** When a CR is intentionally loose-scope (identified as "Exploratory" in §1 Purpose), the Scope section MUST include the following bounds:
>
> - **Target submodule(s):** which governed system(s) may be modified
> - **Execution branch:** explicit branch name
> - **RS-immutability declaration:** "no RS modifications by this CR"
> - **Anti-scope:** what is explicitly NOT in scope (e.g., named files or subsystems off-limits to the exploration)
>
> Exploratory CRs lacking these bounds shall be rejected at pre-review under existing §6.2 deficiency grounds.

### 5.3 SOP-002 §7.1 — QA discretion clarification for Exploratory CRs

Add a note at the end of §7.1:

> **Exploratory CRs.** When a CR is explicitly identified as Exploratory in §1 Purpose and contains the required bounds in §2 Scope (per §6.2), QA may forgo TU assignment at pre-review. TU assignment at post-review is mandatory and is determined by the actual diff. QA shall not invoke this discretion for non-Exploratory CRs.

### 5.4 qa.md — three additions in a new "Exploration CRs" top-level section

Insert a new top-level section titled `## Exploration CRs` between the existing `## Reviewer Assignment for Pipe Dream` section and the existing `## Review Criteria` section (i.e., between lines 138 and 140 of the current qa.md, immediately before the `---` separator that precedes Review Criteria). The new section opens with one short framing sentence, followed by three items labeled (a), (b), (c). The labels (a)/(b)/(c) are immutable identifiers — post-review will verify the qa.md text uses these exact labels and order — and the executor shall not renumber or reorder them.

Section content (verbatim — the executor shall use this exact text, modulo trivial markdown formatting):

> ## Exploration CRs
>
> When a CR self-identifies as Exploratory in §1 Purpose and includes the structural bounds required by SOP-002 §6.2 in §2 Scope, the following review behaviors apply:
>
> **(a) Loose scope is not by itself grounds for REQUEST_UPDATES.** When a CR self-identifies as Exploratory in §1 Purpose and includes the required bounds in §2 Scope (per SOP-002 §6.2), QA evaluates the bounds — not the (absent) specificity.
>
> **(b) Appropriateness rejection criterion.** QA shall reject an Exploration CR at pre-review when its Purpose describes work that belongs in a Standard CR — architectural changes, cross-system changes, or work where the design is already known. The Exploratory framing is for genuinely exploratory work, not a shortcut around upfront design review.
>
> **(c) Post-review uses existing machinery, with one prerogative split.** Bounds adherence is QA's existing scope-integrity check per SOP-002 §7.3 (verify the diff stays within the §2 bounds; QA may run `git diff` directly). Existing-REQ verification at the qualified commit is the assigned TU(s)' existing RTM-review work per SOP-006 §6 — TUs verify that every REQ in the current EFFECTIVE RS remains satisfied at head, and shall REQUEST_UPDATES if any existing REQ is broken (standard remediation paths: revert, Type 1 VAR, or paired CR that legitimately changes the REQ). **However:** a TU's observation that the diff introduces new behavior which "should be" a REQ is advisory only — the TU shall RECOMMEND and may include the observation as a review comment, but shall NOT REQUEST_UPDATES on REQ-candidacy grounds. The decision to initiate a Nail Down CR (or any other RS update) for a flagged behavior is the Lead's exclusive prerogative. No parallel post-review checklist is created.

### 5.5 scope-change-guide.md — out-of-bound work in Exploration CRs

Add a note in the relevant scope-expansion section (likely "Scope Is Too Narrow" or equivalent):

> **Out-of-bound work in an Exploration CR is handled via VAR.** When execution in an Exploration CR encounters work that would exit the bounds declared in §2 Scope, the standard VAR mechanism applies (per SOP-004 §9A): the VAR documents the deviation and its resolution. Two resolution paths:
>
> 1. **Revert / stop in-bound.** The VAR resolves by recording that the executor chose not to do the out-of-bound work; bound is honored; Exploration CR proceeds within its original scope.
> 2. **New CR for legitimate scope expansion.** The VAR identifies that the out-of-bound work is genuinely needed; the VAR's resolution authorizes (and references) a new CR that takes the expanded work through standard pre-approval.
>
> The VAR itself does NOT expand the Exploration CR's bounds — it documents the deviation and surfaces the question. The bound expansion (if warranted) happens via the new CR's pre-approval, preserving the scope-integrity principle that pre-approved scope is a contract.

### 5.6 Trade-offs accepted

This CR ships an explicit acknowledgement (in §7.3 below) of four trade-offs the pattern accepts:

- **Pre-approval architectural review surface lost.** TUs no longer catch design problems before code is written for Exploration CRs. Discovery moves to post-approval, where revert cost is high.
- **Pre-approval scope-contract specificity reduced.** Pre-approved scope is a bound rather than an itemized plan; reviewers have less to react to at the start.
- **Lead's mid-execution intervention surface reduced.** Currently the Lead can shape direction by reacting to drafted plans; with exploration, the Lead sees results, not plans.
- **TU veto on REQ candidacy removed; Lead alone owns RS evolution.** Per qa.md (c), TUs may flag observed un-REQ'd behavior as a recommendation but shall not REQUEST_UPDATES on REQ-candidacy grounds. The decision to initiate a Nail Down CR (or any other RS update) for a flagged behavior is the Lead's exclusive prerogative. This makes RS evolution a Lead-driven, not reviewer-driven, process — consistent with the QMS principle that the RS represents what the system *must* do, while implementation may legitimately exceed REQs without breaking the qualification contract (so long as no existing REQ is violated).

These trade-offs are real and named, not glossed over.

### 5.7 Rollback criterion (self-imposed safety rail)

This CR commits to a rollback criterion: if post-review of the first three Exploration CRs (the first three CRs whose §1 Purpose identifies them as Exploratory) reveals systemic abuse patterns or persistently un-acted-on REQ-coverage gaps, the pattern is suspended pending an Investigation. The criteria are intentionally judgment-based and Lead-invoked: "systemic abuse" includes bound violations going undetected at post-review, Exploratory framing being applied to work that should have been a Standard CR, or QA's appropriateness rejection criterion (qa.md (b)) being routinely overridden. "Persistently un-acted-on REQ-coverage gaps" describes a pattern where TU recommendations to add REQs accumulate without Lead-initiated Nail Down CRs, producing a growing un-tracked surface in shipped code. The QMS's recursive governance loop expects that if the procedure proves inadequate, an INV produces concrete CAPAs; this CR does not pre-specify what those would be.

---

## 6. Justification

CR-114 token cost was disproportionate to the work delivered. Root cause analysis surfaced two contributing patterns: (1) per-cycle reviewer fan-out where each TU re-loads the full document and re-greps the codebase for narrow line-citation updates, and (2) the QA-as-sole-assignee auto-close pattern (already separately queued for a process-improvement CR). This CR addresses (1) for the subset of CRs where the work is genuinely exploratory and existing REQs adequately cover the design space.

The structural insight enabling this with minimal QMS surface change: the QMS merge gate (SOP-005 §7.1.3 + SOP-006 §7.4) does not require the RS to *change* during a CR — only that it be EFFECTIVE. A CR making code changes fully covered by existing REQs satisfies the gate by leaving RS untouched, advancing the RTM Qualified Baseline to the new head commit, and passing CI. So an Exploration CR's qualification is the same qualification standard CRs already meet — the reviewer cost shifts from pre-approval to post-approval, where the actual diff is concrete and can be evaluated against actual REQs rather than against a predicted plan.

The design collaboration with QA (two rounds, recorded in `.claude/sessions/Session-2026-05-03-001/exploration-cr-design.md`) initially produced three new artifact proposals from QA that the Lead rejected on the principle that "artifact proliferation was one of the early principles of this QMS [to avoid]." QA was asked to confirm whether existing review SOPs (§6.2, §7.3, §6, §7.4) cover the concerns the artifacts addressed, or whether a specific failure mode in the existing machinery justified the artifacts. QA confirmed in writing that no specific failure mode could be named, and accepted the streamlined design in full. This CR is the streamlined design.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `Quality-Manual/QMS-Policy.md` | Modify | Add paragraph in §6 |
| `Quality-Manual/guides/scope-change-guide.md` | Modify | Add note about Exploration CR bound expansion |
| `QMS/SOP/SOP-002.md` | Modify | Add notes in §6.2 and §7.1 |
| `.claude/agents/qa.md` | Modify | Add three Exploration CR items |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| QMS-Policy | Modify | Existing EFFECTIVE document; revision needed (Quality-Manual submodule) |
| SOP-002 | Modify | Existing EFFECTIVE document; revision via standard checkout/checkin/review/approval |
| qa.md (agent definition) | Modify | Direct git commit, CR-authorized; no QMS document control |
| scope-change-guide.md | Modify | Quality-Manual submodule file; revision via submodule workflow |

### 7.3 Other Impacts and Trade-offs Accepted

**Trade-offs the pattern explicitly accepts (per §5.6 above):**
- Pre-approval architectural review surface lost for Exploration CRs (TU pre-review skipped)
- Pre-approval scope-contract specificity reduced (bound vs itemization)
- Lead's mid-execution intervention surface reduced

**Rollback criterion (per §5.7):** First three Exploration CRs serve as a probation period; if systemic abuse patterns or inadequate REQ coverage emerge, the pattern is suspended pending an INV.

**SDLC impact:** None. The qualification gate, merge gate, and qualification evidence model are unchanged. RS-EFFECTIVE + RTM-EFFECTIVE at qualified commit + CI green + PR-merged remains the qualification contract.

**RTM impact:** None. RTM Maintenance per SOP-006 §6.5 already covers the "RS unchanged but qualified commit advanced" case (it is the standard pattern when code changes do not introduce new requirements).

**CLI impact:** None. `qms create CR` is unchanged. The Exploratory framing lives entirely in document content.

**Backward compatibility:** Standard CRs are unchanged. The pattern is opt-in per CR; existing CRs in flight are unaffected.

---

## 8. Testing Summary

This is a document-only CR. Verification is procedural:

- **QMS-Policy revision:** confirm the new §6 paragraph is present at the EFFECTIVE version after submodule merge.
- **SOP-002 revision:** confirm the new §6.2 and §7.1 notes are present in the EFFECTIVE version.
- **qa.md revision:** confirm the three new Exploration-CR items are present in the file at HEAD on pipe-dream main.
- **scope-change-guide.md revision:** confirm the new note is present in the EFFECTIVE Quality-Manual at the merged commit.
- **Cross-document consistency:** confirm the wording in SOP-002 §6.2 (bounds requirement), qa.md (a/b/c), and scope-change-guide (out-of-bound work handled via VAR, possibly authorizing a new CR) are mutually consistent and reference each other where appropriate.

No automated tests apply. No integration verification required (no behavioral change in the CLI or any code system).

---

## 9. Implementation Plan

### 9.1 Phase 1: Pre-Execution Baseline

1. Commit and push pipe-dream (including all submodules' current state) to capture the pre-execution baseline. Record commit hash in EI-1.

### 9.2 Phase 2: Quality-Manual Submodule Changes

Per CR-113 precedent, Quality-Manual changes follow SOP-005 §7.1 execution-branch + PR + regular-merge workflow inside the submodule.

1. Cut execution branch `cr-115-exploration-cr-pattern` from Quality-Manual main.
2. Edit `Quality-Manual/QMS-Policy.md` — append the §6 paragraph per §5.1 above. Commit on the execution branch.
3. Edit `Quality-Manual/guides/scope-change-guide.md` — add the note per §5.5 above in the appropriate scope-expansion subsection. Commit on the execution branch.
4. Push the execution branch to the Quality-Manual remote.
5. Open PR on Quality-Manual repository, merge with regular merge commit (`--no-ff`). Verify the qualified commit is reachable from main.
6. Update the Quality-Manual submodule pointer in pipe-dream (commit + push).

### 9.3 Phase 3: SOP-002 Revision (Main Repo, QMS Document Control)

1. `qms checkout SOP-002`.
2. Edit `QMS/SOP/SOP-002.md` — add the §6.2 note per §5.2 above and the §7.1 note per §5.3 above.
3. `qms checkin SOP-002`.
4. `qms route SOP-002 --review` (QA only — per CR-113 precedent, SOP revisions do not require TU review).
5. Address any reviewer feedback; iterate.
6. `qms route SOP-002 --approval`. Confirm SOP-002 reaches EFFECTIVE.

### 9.4 Phase 4: qa.md Update (Main Repo, Direct Edit)

1. Edit `.claude/agents/qa.md` — insert a new top-level section `## Exploration CRs` between the existing `## Reviewer Assignment for Pipe Dream` section and the existing `## Review Criteria` section. The section content is the verbatim text given in §5.4 above, including the immutable (a)/(b)/(c) labels.
2. Commit + push pipe-dream.

### 9.5 Phase 5: Post-Execution Baseline

1. Commit and push pipe-dream (including the advanced Quality-Manual submodule pointer) to capture the post-execution baseline. Record commit hash in the final EI.

### 9.6 EI Table Outline

| EI | Phase | Description |
|----|-------|-------------|
| EI-1 | 1 | Pre-execution baseline commit + push |
| EI-2 | 2 | Cut Quality-Manual execution branch `cr-115-exploration-cr-pattern` |
| EI-3 | 2 | Edit QMS-Policy.md §6 paragraph; commit on execution branch |
| EI-4 | 2 | Edit scope-change-guide.md note; commit on execution branch; push branch |
| EI-5 | 2 | Open Quality-Manual PR, regular merge to main, verify qualified commit reachable |
| EI-6 | 2 | Update Quality-Manual submodule pointer in pipe-dream; commit + push |
| EI-7 | 3 | SOP-002 checkout, edit (§6.2 + §7.1 notes), checkin |
| EI-8 | 3 | SOP-002 route through review/approval to EFFECTIVE |
| EI-9 | 4 | Edit qa.md (three Exploration-CR items); commit + push pipe-dream |
| EI-10 | 5 | Post-execution baseline commit + push |

---

## 10. Execution

<!--
EXECUTION PHASE INSTRUCTIONS
============================
Sections 1-9 are PRE-APPROVED content - do NOT modify during execution.
Only the EI table and Execution Comments below should be edited during execution.
-->

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution baseline: commit and push pipe-dream (including all submodules' current state) per SOP-004 §5. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Cut Quality-Manual execution branch `cr-115-exploration-cr-pattern` from QM main. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Edit `Quality-Manual/QMS-Policy.md` — append §6 paragraph per §5.1 of this CR. Commit on execution branch. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Edit `Quality-Manual/guides/scope-change-guide.md` — add note per §5.5 of this CR. Commit on execution branch. Push branch to Quality-Manual remote. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Open PR on Quality-Manual repository, merge with regular merge commit (`--no-ff`). Verify the qualified commit is reachable from main. Record merge commit hash. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Update the Quality-Manual submodule pointer in pipe-dream to the QM merge commit. Commit + push pipe-dream. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | `qms checkout SOP-002`. Edit `QMS/SOP/SOP-002.md` — add §6.2 note per §5.2 and §7.1 note per §5.3 of this CR. `qms checkin SOP-002`. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-8 | Route SOP-002 through review and approval (QA only per CR-113 precedent). Confirm EFFECTIVE. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-9 | Edit `.claude/agents/qa.md` — insert a new top-level section `## Exploration CRs` between the existing `## Reviewer Assignment for Pipe Dream` and `## Review Criteria` sections, with the verbatim content (including immutable (a)/(b)/(c) labels) given in §5.4 of this CR. Commit + push pipe-dream. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-10 | Post-execution baseline: commit and push pipe-dream (including advanced Quality-Manual submodule pointer) per SOP-004 §5. | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

---

## 11. Execution Summary

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control (this CR modifies §6.2 and §7.1)
- **SOP-005:** Code Governance (Quality-Manual submodule workflow per §7.1; relied upon by EI-2 through EI-6)
- **SOP-006:** SDLC (qualification gate per §7.4; unchanged by this CR but referenced as the structural foundation)
- **QMS-Policy.md** (Quality-Manual): this CR modifies §6
- **scope-change-guide.md** (Quality-Manual/guides/): this CR adds a note
- **qa.md** (.claude/agents/): this CR adds three items
- **CR-113:** Agent definition and Quality Manual cleanup — established the Quality-Manual submodule workflow precedent (execution-branch + PR + regular-merge inside the QM submodule with submodule pointer advanced in pipe-dream after merge); also established the qa.md §5.3 rule that SOP/QM revisions do not require TU review
- **CR-114:** Resize World UX fixes — the cost incident motivating this CR; Lead's "absolutely untenable" verdict
- **Design collaboration record:** `.claude/sessions/Session-2026-05-03-001/exploration-cr-design.md` (v0.3 CONVERGED)

---

**END OF DOCUMENT**
