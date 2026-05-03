# Exploration CR Pattern — Converged Design v0.4

**Session:** Session-2026-05-03-001
**Author:** claude (orchestrator), with QA collaboration
**Status:** CONVERGED — incorporated into CR-115 DRAFT
**Origin:** Lead request 2026-05-03; Lead reframe mid-design ("just permit loose-scope, don't add new variant"); Lead pushback on v0.2 QA artifact proposals ("artifact proliferation was an early QMS principle to avoid"); Two Lead amendments post-CR-115-draft: (1) TU REQ-candidacy observations are advisory only — Lead alone initiates Nail Down CRs; (2) Out-of-bound work in an Exploration CR is handled via VAR — the VAR may authorize a new CR for legitimate scope expansion, but does not itself expand the bound

---

## 1. Problem

CR-114 shipped a small Flow State change but cost 7 pre-review cycles + 4 RTM cycles + a subagent rate-limit hit. The pre-approval gate cost is disproportionate to small, uncontroversial work. Lead wants rapid, free-form development possible inside the QMS for an upcoming beach trip — with rigor concentrated at post-approval rather than pre-approval.

---

## 2. The Insight

The QMS merge gate (SOP-005 §7.1.3 + SOP-006 §7.4) requires CI green + RS EFFECTIVE + RTM EFFECTIVE + PR-merged. **It does not require that the RS *changed* during this CR.** A CR making code changes fully covered by existing REQs satisfies the gate by:

- Leaving RS untouched
- Advancing the RTM's Qualified Baseline pointer to the new head commit
- TU-review of the updated RTM evidence to confirm every existing REQ still holds at the new commit
- CI green, standard PR/merge

The RS is the contract; an exploration is constrained to live within that contract; verification at post-approval proves the contract still holds — using existing review machinery.

---

## 3. The Pattern

An **Exploration CR** is a regular CR whose author chose loose specificity, accompanied by structural bounds in §2 Scope and an explicit "Exploratory" declaration in §1 Purpose. No new template, no new variant, no new artifacts. The QMS already permits this; the additions below clarify it explicitly.

### 3.1 What it looks like

- **§1 Purpose** — declares "Exploratory CR"
- **§2 Scope** — includes the four required bounds (target submodule(s), execution branch, RS-immutability declaration, anti-scope) inside the existing §6.2 structure
- **§5 Change Description** — "specific changes will be discovered during execution; bounds in §2 govern what is in/out of scope"
- **§9 Implementation Plan** — single execution EI ("Conduct exploratory development per §2 bounds"), plus standard pre/post baseline EIs and standard RTM/merge EIs
- **§11 Execution Summary** (post-execution) — narrative log of what was actually done, including which existing REQs the work touches

### 3.2 Pre-approval

- QA receives, evaluates the bounds in §2 (not the absent design specifics)
- Per the SOP-002 §7.1 clarification, QA may forgo TU assignment at pre-review when the CR is explicitly Exploratory and includes the required §2 bounds
- QA recommends + approves
- CR transitions to PRE_APPROVED → IN_EXECUTION

### 3.3 Execution

- Author works freely on the named branch within the named submodule(s)
- Per existing SOP-004 §9A and the scope-change-guide addition, work that would exit the bounds is handled via the standard VAR mechanism. The VAR documents the deviation; the VAR's resolution may be (a) revert / stop in-bound, OR (b) authorize a new CR for legitimate scope expansion. The VAR itself does not expand the bound.
- Author maintains a lightweight arc log in Execution Comments
- When ready to close: CI green, RTM Qualified Baseline + line citations updated, Execution Summary written

### 3.4 Post-approval (where rigor concentrates)

- QA assigns TUs based on the **actual diff** (not the pre-approval plan) — this is QA's standing SOP-002 §7.1 discretion
- Standard post-review work, no parallel checklist:
  - QA verifies scope integrity per SOP-002 §7.3 ("did the diff stay within the §2 bounds?" — QA can run `git diff` themselves)
  - TUs verify existing-REQ satisfaction at head per SOP-006 §6 ("are all existing REQs still satisfied at head?") — TU's existing RTM-review responsibility
- **Existing-REQ violation at head** (a TU finds an existing REQ broken at the qualified commit): TUs REQUEST_UPDATES; author either (a) reverts the violating change, (b) attaches a Type 1 VAR, or (c) opens a paired CR that legitimately changes the REQ. This is qualification-gate territory and TUs have full block authority.
- **Un-REQ'd new behavior in the diff** (per Lead amendment): TUs may flag this as an observation in their review comments but shall RECOMMEND, not REQUEST_UPDATES. The decision to initiate a Nail Down CR (or any other RS update) for a flagged behavior is the **Lead's exclusive prerogative**. RS evolution is Lead-driven, not reviewer-driven. The principle: the RS represents what the system *must* do; implementation may legitimately exceed the RS without breaking the qualification contract, so long as no existing REQ is violated.
- Standard merge gate, PR, submodule pointer update

### 3.5 The Nail Down CR (optional follow-up)

If post-approval REQ-coverage check identifies new behaviors that should be REQs, a follow-up standard CR adds the REQs to RS and updates RTM. The implementation already exists — this CR is mostly RS authoring + RTM evidence update. High success probability because the code has been sitting in main with real usage.

The Nail Down is **optional** — many explorations produce work fully covered by existing REQs and need no follow-up.

---

## 4. Required QMS Additions (Final)

| Document | Change |
|---|---|
| **QMS-Policy §6** | Add paragraph: scope specificity is the author's judgment call. Loose-scope CRs are permitted when explicitly identified as Exploratory in §1 Purpose and accompanied by structural bounds in §2 Scope. The adherence-to-plan rule applies to whatever specificity was committed to — loose plans are not a license to do anything; they are a license to do anything *within the stated bounds*. |
| **SOP-002 §6.2** | Add note: when scope is intentionally loose ("Exploratory CR"), the Scope section MUST include explicit bounds — target submodule(s), execution branch, RS-immutability declaration ("no RS modifications by this CR"), and anti-scope (what is NOT in scope). Without these bounds, loose scope is rejected at pre-review under existing §6.2. |
| **SOP-002 §7.1** | Add: "When a CR is explicitly identified as Exploratory in §1 Purpose and contains the required bounds in §2 Scope, QA may forgo TU assignment at pre-review. TU assignment at post-review is mandatory and is determined by the actual diff. QA shall not invoke this discretion for non-exploratory CRs." |
| **qa.md** | Three additions: (a) loose scope is not by itself grounds for REQUEST_UPDATES on Exploration CRs that include the §2 bounds; (b) **appropriateness rejection criterion**: reject Exploration CRs whose Purpose describes work better served by a standard CR (architectural / cross-system / well-specified-already); (c) post-review for Exploration CRs verifies bounds adherence (QA's existing scope-integrity work per SOP-002 §7.3) and existing-REQ satisfaction at head (TU's existing RTM review work per SOP-006 §6) — no new artifacts required. **TU REQ-candidacy observations are advisory only**: TU shall RECOMMEND with comments, not REQUEST_UPDATES, when flagging un-REQ'd new behavior; Nail Down CR initiation is the Lead's exclusive prerogative. |
| **Quality-Manual/guides/scope-change-guide.md** | Add note: out-of-bound work in an Exploration CR is handled via standard VAR mechanism (per SOP-004 §9A). The VAR documents the deviation; resolution may either (a) revert / stop in-bound, OR (b) authorize a new CR for legitimate scope expansion. The VAR itself does not expand the bound — the new CR (if needed) is the legitimate scope-expansion mechanism. |
| **The meta-CR itself** | Include explicit "Trade-offs accepted" section + rollback criterion: if post-review of the first three Exploration CRs reveals systemic abuse patterns or inadequate REQ coverage, the pattern is suspended pending an INV. |

**That is the entire surface change.** Six clarifying additions across four files plus the meta-CR's own self-imposed rollback criterion. No new template, no new SOP, no new variant, no new artifacts.

---

## 5. What's Explicitly NOT in the Design

These were considered and rejected:

- **No new "Exploration CR" template variant** — standard TEMPLATE-CR is sufficient; the Exploratory framing lives in §1 Purpose and §2 Scope content, not in template structure.
- **No new "Exploration Bounds" §2.4 subsection** — bounds live inside the existing §2 Scope structure under SOP-002 §6.2; clarity is QA's existing pre-review responsibility.
- **No "Exploration Bounds Verification" artifact** in the Execution Summary — the diff is the evidence; QA's existing SOP-002 §7.3 scope-integrity check covers this.
- **No "REQ-Coverage Walk" artifact** — the RTM update IS the gap check; TU review of RTM evidence per SOP-006 §6 covers this.
- **No CLI changes** — `qms create CR` is unchanged; the Exploratory framing is purely in the document content.
- **No new SOP** — the pattern fits within SOP-002 + SOP-005 + SOP-006 with the §4 clarifications.

The Lead's principle (rejected QA's v0.2 artifact proposals): artifact proliferation is what the QMS was structured to avoid; concerns about bounds/REQ-coverage are reviewer responsibilities under existing SOPs, not justifications for parallel artifacts. QA accepted this principle and confirmed no specific failure mode in the existing review machinery justified the artifacts.

---

## 6. Trade-offs Accepted

### What we gain
- Pre-approval cycles drop from 3-7 to 1 (QA only)
- No per-cycle TU fan-out at pre-approval
- Rapid commit-and-iterate workflow during execution
- Same qualification rigor at the gate
- Clear escape valve for "I want to try things" without bypassing QMS

### What we give up
- **Pre-approval architectural review.** TUs no longer catch design problems before code is written. Discovery moves to post-approval, where revert cost is high. This is the central trade-off.
- **Pre-approval scope-contract specificity.** Pre-approved scope is a *bound* rather than an itemized plan; reviewers have less to react to at the start.
- **Lead's mid-execution intervention surface.** Currently the Lead can shape direction by reacting to drafted plans; with exploration, the Lead sees results, not plans (Lead is choosing this trade-off explicitly).
- **TU veto on REQ candidacy.** Per Lead amendment: TUs may flag observed un-REQ'd behavior but cannot block on REQ-candidacy grounds. RS evolution is Lead-initiated only. Trade-off: faster Exploration CR closure, at the cost of a slower-feedback REQ growth loop where un-REQ'd behavior can persist in main if the Lead doesn't act on TU recommendations.

### Pattern is opt-in per CR
Lead chooses Exploration vs Standard at draft time. Standard CRs are unchanged.

**Exploration is the right tool when:**
- Work is genuinely exploratory (don't know yet what the right answer is)
- Existing REQs adequately cover the design space
- Cost of pre-approval ≥ cost of potential post-approval rework
- Time pressure or session-shape favors free-form work

**Standard CRs remain right when:**
- Architectural direction is consequential
- New REQs are obviously needed
- Multiple teams or systems are touched
- Reviewer pre-look has demonstrably saved time historically

The qa.md (b) appropriateness rejection criterion is the gatekeeper: QA rejects Exploration CRs whose Purpose describes work that should be a standard CR.

---

## 7. Rollback Criterion (in the meta-CR)

If post-review of the first three Exploration CRs reveals systemic abuse patterns or inadequate REQ coverage, the pattern is suspended pending an INV. This is a self-imposed safety rail — the pattern is novel and deserves an early-warning escape valve. The QMS principle: when a procedure proves inadequate, investigate and improve it (CAPA), don't bolt on parallel procedures.

---

## 8. Collaboration Record

- **v0.1 (claude):** heavier-touch new-variant approach (dedicated SOP §6.13, new template section, new workflow phase). Demoted to alternative-considered after Lead reframe.
- **v0.2 (claude, post-Lead-reframe):** lighter-touch approach with three new artifacts proposed by QA (named §2.4 subsection, Bounds Verification, REQ-Coverage Walk). Lead rejected all three on artifact-proliferation principle.
- **v0.3 (this document, claude+QA converged):** lighter-touch approach with no new artifacts; six clarifying additions across QMS-Policy + SOP-002 + qa.md + scope-change-guide; rollback criterion in meta-CR. QA accepted in full and confirmed no specific failure mode in existing review machinery justified the artifacts.

---

## 9. Next Step

Draft the meta-CR (CR-NNN: Permit Exploration CRs under existing scope-integrity machinery) authorizing the §4 changes. The meta-CR is itself a standard CR — it governs QMS evolution, not exploratory work. Per qa.md (b), the appropriateness criterion explicitly applies: this is a deliberate process change with foreseeable consequences and standard pre-review machinery is the right mechanism.

---

## 10. Appendix — Example Exploration CR Skeleton

```markdown
# CR-NNN: Flow State exploration — beach trip session

## 1. Purpose
**Exploratory CR.** Conduct exploratory development on Flow State during the
2026-05-XX beach trip. Specific changes will be discovered during execution;
this CR is intentionally loose-scope per QMS-Policy §6 (scope-specificity-is-
author-judgment clause) with structural bounds in §2 below.

## 2. Scope
### 2.1 Context
Lead-driven exploratory session; rapid feedback loop preferred over upfront design.

### 2.2 Changes Summary
Free-form Flow State development within the bounds in §2.3.

### 2.3 Files Affected and Bounds
- **Target submodule:** flow-state (single submodule)
- **Execution branch:** cr-NNN-beach-exploration
- **RS-immutability:** no RS modifications by this CR
- **Anti-scope:** no architectural changes to engine/compiler.py
  (geometry-to-physics bridge stays as-is for this exploration)
- **Optional bounds:** time-box 2026-05-XX through 2026-05-YY;
  commit-box ≤ 100 commits on execution branch

## 3. Current State
flow-state main at FLOW-STATE-1.2 (commit `da012b4`).
SDLC-FLOW-RS v3.0 EFFECTIVE. SDLC-FLOW-RTM v3.0 EFFECTIVE (qualified at f69455f).

## 4. Proposed State
Some unknown set of changes within the bounds in §2.3. Final state documented
in §11 Execution Summary post-execution.

## 5. Change Description
Specific changes will be discovered during execution. Per the adherence-to-plan
rule, work must stay within the §2.3 bounds. If execution encounters work that
would exit the bounds, attach a VAR per SOP-004 §9A; the VAR's resolution may
either record a revert or authorize a new CR for legitimate scope expansion.

## 6. Justification
CR-114 demonstrated the QMS pre-approval cost is disproportionate to small Flow
State work. This CR shifts rigor to post-approval where the actual diff can be
evaluated against existing REQs, rather than predicted at pre-approval time.

## 7. Impact Assessment
Diff entirely within flow-state submodule. RS unchanged. RTM updated to advance
Qualified Baseline to head commit and refresh line citations. Possible follow-up
Nail Down CR if new REQs emerge from the post-approval REQ-coverage check.

## 8. Testing Summary
Per-commit integration verification at developer discretion. Final qualified
commit must pass CI; all existing REQs verified at head per RTM update; standard
post-review TU coverage of the diff.

## 9. Implementation Plan
EI-1: Pre-execution baseline (standard).
EI-2: Conduct exploratory development per §2.3 bounds. Maintain arc log in
      Execution Comments.
EI-3: Update SDLC-FLOW-RTM to advance Qualified Baseline to head commit;
      verify all existing REQs satisfied; route RTM through normal review cycle
      to EFFECTIVE.
EI-4: Open PR, regular merge to main, advance submodule pointer in pipe-dream.
EI-5: Post-execution baseline (standard).

## 10-12. [standard]
```

---

**END OF DESIGN PROPOSAL v0.3 — CONVERGED. Ready to inform meta-CR draft pending Lead approval.**
