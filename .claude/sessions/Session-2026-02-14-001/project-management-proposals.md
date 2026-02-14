# Project Management Proposals

*Session-2026-02-14-001 — Discussion Notes*

This document captures proposals for improving project tracking and reducing the cognitive burden on the Lead. These emerged from a discussion about the gap between the QMS (which governs execution) and the planning layer (which governs what to execute and in what order).

---

## The Problem

The QMS pipeline — CRs, reviews, approvals, investigations — is strong at governing change once a decision to change has been made. However, there is no structured layer for:

- **Discovery:** What needs doing?
- **Prioritization:** What order?
- **Dependencies:** What blocks what?
- **Bundling:** Which items naturally group into a single CR?

The existing tools (TO_DO_LIST.md, idea tracker, session notes) are append-only and flat. They capture information but don't organize it for decision-making. The burden of synthesizing across 20+ TO_DO items, dozens of session notes, and open QMS documents falls entirely on the Lead — and this synthesis is the most cognitively taxing part of the development process.

---

## Proposal 1: Living Project State Document

**What:** A single persistent file (e.g., `.claude/PROJECT_STATE.md`) maintained by Claude, updated at the end of every session.

**Answers three questions:**

1. **What's open right now?** — Open QMS documents, active investigations, unresolved CAPAs, in-progress work
2. **What's ready to work on?** — TO_DO items grouped into proposed work packages, with dependencies noted
3. **What was deferred and why?** — Preserves rationale so past decisions don't need re-litigation

**How it helps:** Shifts the synthesis burden from the Lead to Claude. At session start, the Lead reads one document instead of mentally reconstructing state from scattered sources.

**Maintenance cadence:** Updated at the end of each session as part of session wrap-up.

---

## Proposal 2: Structured Backlog (Replace Flat TO_DO List)

**What:** Restructure the TO_DO list from chronological (when items were discovered) to actionable (what can be done, what's blocked, what bundles together).

**Proposed structure:**

```
## Ready (no blockers)
- Items that can be picked up immediately
- Annotated with estimated effort and whether standalone or part of a bundle

## Bundleable (natural CR groupings)
- Items that share a theme and should be addressed together
- Each bundle = a potential CR, with constituent items listed

## Blocked
- Items with explicit blockers identified
- Blockers linked to specific open QMS documents or prerequisites

## Deferred (conscious decision, with rationale)
- Items deliberately postponed
- One-line rationale for each deferral decision
```

**How it helps:** The Lead no longer needs to mentally group, prioritize, and sequence items. The backlog presents items in decision-ready form. The Lead approves or adjusts, rather than constructing from scratch.

**Migration:** Claude performs a one-time restructuring of the existing TO_DO_LIST.md, then maintains the new structure going forward.

---

## Proposal 3: Task-Bundling as a Deliberate Activity

**What:** Make bundling analysis a routine activity rather than an ad-hoc effort. When the Lead asks "what should we work on next?", Claude produces a structured bundling proposal that maps TO_DO items, code review findings, and open QMS items into proposed CRs.

**Output format for each proposed bundle:**

- **Bundle name** (e.g., "Git MCP Hardening")
- **Constituent items** (TO_DO items, code review findings, open issues)
- **Estimated effort** (session count)
- **Dependencies** (what must be done first)
- **QMS implications** (new CR? VAR on existing? SOP revision?)

**How it helps:** The Lead reviews and approves bundles rather than constructing them. This is the specific cognitive task the Lead identified as most taxing.

**When to perform:** At the start of any session where the agenda is open-ended, or when explicitly requested.

---

## Proposal 4: Lightweight Decision Log

**What:** A running list of decisions made during the project, capturing what was considered, what was decided, and why. Not a full QMS document — a simple append-only log.

**Format:**

```
| Date | Decision | Rationale | Reference |
|------|----------|-----------|-----------|
| 2026-02-14 | Deferred CAPA-003 (ADD doc type) | QMS usage patterns not yet stable enough to design the right solution | Session-2026-02-10-005 |
| 2026-02-14 | Prioritize C1 shell injection fix before Phase A | Integration tests on a system with shell injection would produce unreliable results | code-review.md |
```

**How it helps:** Prevents the recurring cost of re-evaluating deferred items. Some TO_DO items from January are still open with no record of why they haven't been addressed. A one-liner per decision eliminates this ambiguity.

**Location:** `.claude/DECISIONS.md` or a section within the Project State document.

---

## Recommended Implementation Order

1. **Project State document** — Highest impact, lowest overhead. Claude maintains it; Lead reads it. Immediately reduces session-start cognitive load.
2. **Backlog restructuring** — Natural second step. One-time migration of existing TO_DO list, then ongoing maintenance.
3. **Decision log** — Can start immediately as a simple file; grows in value over time.
4. **Task-bundling as routine** — Becomes natural once the backlog is structured; the bundling analysis draws from the structured backlog.

---

## Relationship to the QMS

These proposals operate in the **pre-CR planning space** — the layer between "someone noticed something" and "a CR is created to address it." They do not replace or modify any QMS procedures. They feed into the QMS by producing well-defined, pre-analyzed work packages that can be translated into CRs with minimal additional effort.

If formalization is desired in the future, this planning layer could be codified in a Work Instruction (WI) or added as guidance in SOP-002 (Change Control). For now, these are informal process aids maintained by Claude as part of session management.
