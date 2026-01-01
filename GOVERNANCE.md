# Flow State: Governance Procedures

*Ratified by the Constitutional Convention of 2025-12-31*

This document codifies the procedural rules for the Senate of Guardians. It is subordinate to CLAUDE.md (the Constitution) and may be amended by simple majority vote of the Senate with User approval.

---

## 1. Session Procedures

### 1.1 Request for Comments (RFC)

**Purpose:** Gather Guardian input on a proposal before formal vote.

**Convened By:** The Secretary, at the request of the Primus or User.

**Quorum:** 2 Guardians minimum.

**Procedure:**
1. The Secretary announces the RFC with proposal details
2. The Generalizer is ALWAYS included (per standing order)
3. Affected domain Guardians are summoned based on proposal scope
4. Guardians provide position statements (no binding vote)
5. The Secretary compiles a Consolidated Review

**Output:** Position statements grouped by Guardian, with blockers highlighted.

**Duration:** Open-ended until the proposer calls for Vote or withdraws.

---

### 1.2 Vote Session

**Purpose:** Render a binding ruling on a reviewed proposal.

**Convened By:** The Secretary, at the request of the Primus or User.

**Quorum:** 4 Guardians.

**Prerequisite:** The proposal must have undergone at least one RFC. The Secretary shall verify this before proceeding.

**Procedure:**
1. The Secretary announces the Vote with proposal reference
2. Each Guardian casts a vote: APPROVED or REJECTED
3. Rejections must include specific violation citations
4. The Secretary tallies votes and announces the ruling

**Thresholds:**
- **APPROVED:** 4 of 6 Guardians (2/3 supermajority)
- **CONDITIONALLY APPROVED:** 4 of 6 with specified modifications
- **REJECTED:** Fewer than 4 approvals, OR any domain Guardian rejects within their jurisdiction

**Output Format:**
```
# Senate Ruling: [Proposal Name] (v0.x)

## Tally
| Guardian | Vote | Reasoning |
|----------|------|-----------|
| ... | ... | ... |

## Final Verdict: [APPROVED / CONDITIONALLY APPROVED / REJECTED]

## Conditions (if applicable)
[Specific modifications required]

## Minutes
[Summary of deliberation]
```

---

### 1.3 Special Session

**Purpose:** Address matters that are not code proposals (audits, investigations, policy discussions).

**Convened By:** The Secretary or Primus.

**Quorum:** 3 Guardians.

**Procedure:**
1. The convening authority states the purpose
2. Guardians deliberate as appropriate to the matter
3. The Secretary records proceedings
4. Output varies by session purpose

**Examples:**
- Codebase audits
- Action item review
- Architectural discussions
- Conflict resolution between Guardians

---

### 1.4 Constitutional Convention

**Purpose:** Amend CLAUDE.md or other foundational documents.

**Convened By:** User only. The Senate may petition the User to convene a Convention, but cannot convene one unilaterally.

**Quorum:** All 6 Guardians (mandatory full attendance).

**Procedure:**
1. User declares the Convention open
2. The Secretary facilitates document review (Phase I)
3. Guardians deliberate on proposed amendments (Phase II)
4. The Senate votes on each amendment
5. User ratifies or vetoes each amendment
6. The Secretary produces amended documents (Phase III)

**Threshold:** 2/3 supermajority (4 of 6) + User Ratification.

**Special Rule for Foundational Principles:** Amendments to the AvG Principle, Air Gap, Command Pattern, or User Sovereignty require unanimous Guardian consent + User Ratification.

---

### 1.5 Emergency Session

**Purpose:** Address urgent matters requiring immediate action (critical bugs, security issues).

**Convened By:** The Primus.

**Quorum:** 2 Guardians minimum.

**Procedure:**
1. The Primus declares an emergency and summons available Guardians
2. User must be notified within 1 hour (or immediately if available)
3. Guardians deliberate under expedited rules
4. Decisions are provisional pending full Senate ratification within 24 hours

**Threshold:** Unanimous consent of present Guardians.

**Post-Session:** The full Senate must review and ratify emergency decisions at the next regular session. Unratified decisions are void.

---

## 2. Proposal Standards

### 2.1 Naming Convention

Proposals are identified using a domain prefix and sequential number:

```
PREFIX-NNN
```

**Standard Prefixes:**

| Domain | Prefix | Primary Guardian |
|--------|--------|------------------|
| Governance/Constitution | `GOV` | All (Constitutional matters) |
| UI/Widgets/Rendering | `UI` | UI Guardian |
| Input/Focus/Modals | `INPUT` | Input Guardian |
| Scene/Orchestration/Undo | `SCN` | Scene Guardian |
| Sketch/CAD/Geometry | `SKETCH` | Sketch Guardian |
| Physics/Simulation/Compiler | `PHYS` | Physics & Simulation Guardian |
| Architecture (AvG) | `ARCH` | The Generalizer |

New prefixes may be invented as needed for novel domains. Generic terms like `MULTI` or `CROSS` are discouraged; prefer semantically meaningful prefixes that reflect the orchestrating domain.

### 2.2 Versioning

Proposals use parenthetical version notation:

| State | Version | Transition |
|-------|---------|------------|
| Initial submission | v0.1 | — |
| After each review round | v0.x+1 | RFC feedback incorporated |
| Approved | v1.0 | Vote passes |
| Rejected (returns to draft) | v0.x+1 | Vote fails; revision continues |
| Reopened after approval | v1.1 | Modification requested |
| Re-approved | v2.0 | Second vote passes |

**Example lifecycle:**
```
PHYS-003 (v0.1) → PHYS-003 (v0.2) → PHYS-003 (v0.3) → PHYS-003 (v1.0)
                                                            ↓
                                              [reopened] PHYS-003 (v1.1)
                                                            ↓
                                            [re-approved] PHYS-003 (v2.0)
```

### 2.3 Required Metadata

Every proposal must include:

1. **Identifier:** `PREFIX-NNN (vX.Y)`
2. **Title:** A concise descriptive name
3. **Assigned Guardians:** At minimum, the domain Guardian(s) relevant to the proposal scope. The Generalizer is always included per standing order.

**Example Header:**
```
# Proposal UI-007 (v0.1): Implement Tooltip Overlay System

**Assigned Guardians:** UI Guardian, The Generalizer
```

---

## 3. Voting Rules

### 3.1 Standard Voting

| Matter | Threshold | Quorum |
|--------|-----------|--------|
| Code Proposals | 2/3 Supermajority (4 of 6) | 4 Guardians |
| Procedural Matters | Simple Majority (4 of 6) | 4 Guardians |
| Constitutional Amendments | 2/3 Supermajority + User Ratification | All 6 Guardians |
| Foundational Principles | Unanimity + User Ratification | All 6 Guardians |

### 3.2 Domain Veto

A Guardian holds **absolute veto authority** within their domain. If a proposal violates a Guardian's domain laws, that Guardian may reject unilaterally.

**Domain Veto Override:** A domain veto can only be overridden by:
1. Unanimous consent of all OTHER Guardians (5 of 5), AND
2. Explicit User authorization

This ensures domain expertise is respected while preventing absolute deadlock.

### 3.3 Abstention

A Guardian may abstain from voting on a matter outside their domain. Abstentions do not count toward quorum but do not count against passage thresholds.

### 3.4 Tie-Breaking

With 6 Guardians, ties are possible. In the event of a 3-3 tie:
1. The matter is tabled for further deliberation
2. If deadlock persists after second vote, the User is consulted
3. The User's decision is final

---

## 4. Expedited Path

Certain changes may proceed without Senate review:

### 4.1 Qualifying Changes

- Bug fixes contained within a single domain (< 3 files)
- Documentation-only changes (comments, docstrings, README)
- Configuration value adjustments (existing keys only)
- Test additions that do not modify production code
- Changes explicitly pre-approved by the affected domain Guardian

### 4.2 Procedure

1. The Primus identifies a change as qualifying for Expedited Path
2. The affected domain Guardian is notified (not convened)
3. If the Guardian does not object within a reasonable time, the change proceeds
4. The change is logged for Senate awareness at the next session

### 4.3 Retroactive Review

Any Guardian may call for **Retroactive Review** of an Expedited Path change. This triggers a full Senate session to evaluate whether the change should be reverted or modified.

---

## 5. Conditionally Approved Rulings

When the Senate issues a "CONDITIONALLY APPROVED" ruling:

### 5.1 Definition

The proposal is approved subject to specific, enumerated modifications.

### 5.2 Procedure

1. The Secretary documents all required modifications
2. The proposer implements the modifications
3. The Secretary verifies compliance
4. If modifications are satisfactory, implementation proceeds
5. If modifications are disputed, the matter returns to the Senate for clarification

### 5.3 No Re-Vote Required

A compliant implementation of conditions does not require a new vote. The original approval stands.

---

## 6. Conflict Resolution

### 6.1 Inter-Guardian Conflict

When two Guardians hold opposing positions on a cross-domain matter:

1. Each Guardian states their domain-specific concerns
2. The Secretary facilitates direct negotiation
3. If no resolution, the full Senate votes
4. If deadlock persists (3-3), the User arbitrates

### 6.2 Primus-Senate Conflict

If the Primus disagrees with a Senate ruling:

1. The Primus may petition the User for review
2. The User's decision is final and binding on both parties
3. The Primus may not unilaterally override a Senate ruling

### 6.3 User Override

The User may override any Senate ruling at any time. This is the sovereign prerogative and is not subject to appeal.

---

## 7. Record Keeping

### 7.1 Session Transcripts

All sessions are recorded in the Chronicle:
- Automated transcripts: `.claude/chronicles/`
- Manual transcripts: `.claude/transcripts/`

### 7.2 Rulings Archive

All Senate rulings are preserved for precedent. The Secretary maintains an index of rulings.

### 7.3 Action Item Tracker

Outstanding items are tracked in `.claude/secretary/ACTION_ITEM_TRACKER.md`.

---

## 8. Amendment of This Document

This document (GOVERNANCE.md) may be amended by:
- Simple majority vote of the Senate (4 of 6), AND
- User approval

Changes to GOVERNANCE.md do not require a Constitutional Convention.

---

*End of Governance Procedures*
