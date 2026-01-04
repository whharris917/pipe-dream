# Architectural Assessment of the Flow State QMS and a Proposal for Remediation

## A Critical Reflection Triggered by INV-001

**Prepared by:** Claude (Initiator) with QA Consultation
**Date:** 2026-01-04
**Triggering Event:** INV-001 (CR-005 Scope Deviation Investigation)
**Classification:** Strategic Planning Document (Non-QMS)

---

## Executive Summary

INV-001 exposed a procedural nonconformance in CR-005, but the subsequent analysis revealed something more significant: **the QMS architecture, if extended along its current trajectory, will collapse under its own weight**. This document provides a critical assessment of that trajectory and proposes a remediated architecture.

**Core finding:** The current QMS conflates two distinct concerns:
1. **Artifacts requiring independent expert review** (documents)
2. **Work items requiring completion tracking** (tasks)

By treating everything as a document, we create exponential overhead without proportional quality benefit.

**Proposed remedy:** A two-tier model distinguishing **Documents** (decision boundaries requiring independent review) from **Tracked Items** (work units validated as part of their parent's review).

---

## Part I: The Problem

### 1.1 The Proliferation Trajectory

The QMS defines five executable document types: CR, INV, CAPA, TP, ER. Under current architecture, a single investigation with corrective actions creates:

```
INV-001 (12 workflow states, 14+ audit events)
  └── INV-001-CAPA-001 (12 workflow states, 14+ audit events)
        ├── CR-006 (12 workflow states, 14+ audit events)
        │     └── CR-006-TP (12 workflow states, 14+ audit events)
        └── CR-007 (12 workflow states, 14+ audit events)
              └── CR-007-TP (12 workflow states, 14+ audit events)
```

**Total:** 6 documents, 72 workflow states, 84+ audit events, 12+ review cycles.

Now consider Test Protocols. A TP with 50 test steps would, under naive extension of current thinking, require 50 child documents for test results. This is obviously absurd—but it reveals the architectural flaw.

### 1.2 The Agent Orchestration Burden

Each review cycle currently requires:
- Spawning a QA agent (15-60 second cold start)
- Context loading (re-reading relevant documents)
- Review execution
- Agent termination
- Repeat for approval phase

A single CR with one revision cycle requires 4+ agent spawns. A CR with child TP requires 8+ spawns. The INV-001 → CAPA → CR cascade would require 24+ agent spawns.

**This is not sustainable.** Agent spawns are expensive in time, tokens, and cognitive coherence. The current model treats agents as stateless function calls rather than participants in an ongoing conversation.

### 1.3 The Compliance Paradox

The QMS was designed for FDA/GMP compliance—a domain where:
- Human reviewers have limited availability
- Documents have legal standing
- Audit trails must withstand regulatory scrutiny
- Errors have patient safety implications

But our context differs:
- AI agents have unlimited availability
- Documents are internal engineering artifacts
- Audit trails serve project integrity, not regulators
- Errors affect software quality, not patient safety

**The paradox:** By importing pharmaceutical rigor wholesale, we created overhead that doesn't serve our actual quality objectives. We're compliant with procedures that don't match our domain.

---

## Part II: The Analysis

### 2.1 What Actually Requires a Document?

A document should exist when:

| Criterion | Rationale |
|-----------|-----------|
| **Independent expert judgment required** | The artifact's correctness cannot be validated by reviewing its parent |
| **Scope may change independently** | The artifact has its own lifecycle that may diverge from parent |
| **Different responsible party** | Someone other than the parent owner is accountable |
| **Decision boundary** | Approval represents a distinct commitment |

**Test:** Can this artifact's quality be fully assessed during its parent's review?
- If **yes** → Tracked Item (embedded in parent)
- If **no** → Document (independent lifecycle)

### 2.2 Applying the Test

| Artifact | Parent Review Sufficient? | Recommendation |
|----------|---------------------------|----------------|
| CAPA action items | Yes—INV review validates the action plan | **Tracked Item** |
| Test steps in TP | Yes—TP review validates test design | **Tracked Item** |
| Execution Items in CR | Yes—CR review validates execution plan | **Tracked Item** |
| Exception Report for failed test | No—requires independent judgment on acceptability | **Document** |
| Test Protocol itself | No—test design requires independent review | **Document** |
| Change Record | No—change rationale requires independent review | **Document** |

### 2.3 The Economics of Agent Invocation

Current model: **Stateless, per-action invocation**
```
[spawn agent] → [single action] → [terminate]
[spawn agent] → [single action] → [terminate]
[spawn agent] → [single action] → [terminate]
```

Problems:
- Cold start overhead on every invocation
- No context preservation between invocations
- Fragmented conversation history
- Cognitive discontinuity for the agent

Alternative models:

**A. Batch Processing Model**
```
[spawn agent] → [process entire inbox] → [terminate]
```
- Single invocation handles multiple documents
- Context preserved within session
- Natural for async workflows where human time passes between stages

**B. Session-per-Document Model**
```
[spawn agent for CR-007] → [all CR-007 actions] → [terminate on CR-007 close]
```
- Agent persists across a document's lifecycle
- Maximum context preservation
- Requires agent persistence infrastructure

**C. Delegated Authority Model**
```
[spawn agent] → [pre-authorize class of actions] → [Claude executes authorized actions without re-consulting]
```
- Agent establishes policy, Claude executes
- Minimal invocations for routine operations
- Requires clear authorization boundaries

### 2.4 QA's Analysis: Key Insights

From the QA consultation (agent aa14ccf), the following principles emerged:

1. **Document = Decision Boundary**
   > "An artifact requires full document lifecycle if and only if it represents a decision boundary requiring independent expert review."

2. **Blocking Without Documents**
   > "Blocking semantics require only: enumeration, state machine, closure gate, deferral linkage. This does not require separate document files."

3. **Risk-Calibrated Review**
   > "Not all changes carry equal risk. The review cycle's intensity should match the change's risk level."

4. **Embedded vs. Referenced**
   > "The key insight: The *actions* are what need separate review (via CRs). The *tracking structure* does not need its own review cycle."

---

## Part III: The Proposal

### 3.1 Two-Tier Artifact Model

**Tier 1: Documents**
- Full lifecycle (12 states for executable, 7 for non-executable)
- Independent review and approval cycles
- Dedicated .meta, .audit, and .archive entries
- Used for: CR, INV, TP, ER, SOP, and other decision-boundary artifacts

**Tier 2: Tracked Items**
- Embedded tables within parent documents
- Status tracked per item (PENDING → IN_PROGRESS → COMPLETE | DEFERRED | BLOCKED)
- Validated during parent's review cycle
- Closure-gating logic validates completion before parent can close
- Used for: Execution Items (in CR), CAPA Items (in INV), Test Steps (in TP)

### 3.2 Revised Document Relationships

**Current (Proliferative):**
```
INV-001
  └── INV-001-CAPA-001 (document)
        └── CR-006 (document)
```

**Proposed (Streamlined):**
```
INV-001
  └── [CAPA Items table - embedded]
        └── CA-1: "Update SOP-001" → spawns CR-006 (document)
        └── PA-1: "Add EI tracking" → spawns CR-007 (document)
```

The CAPA *structure* is embedded. The CAPA *actions* spawn CRs when implementation is needed. The CRs are documents because they represent independent decision boundaries.

### 3.3 Tracked Item Specification

All tracked items share a common structure:

```markdown
| ID | Description | Status | Evidence | Follow-up |
|----|-------------|--------|----------|-----------|
```

**Status Values (Universal):**
- `PENDING` - Not started
- `IN_PROGRESS` - Work underway
- `COMPLETE` - Done with evidence
- `DEFERRED` - Cannot complete here; tracked via follow-up
- `BLOCKED` - Cannot proceed; requires resolution

**Closure Gate (Universal):**
Parent document cannot transition to terminal state (CLOSED for executable, EFFECTIVE for non-executable) if any item is PENDING, IN_PROGRESS, or BLOCKED.

**Type-Specific Variations:**

| Context | Item Type | Additional Status | Closure Requirement |
|---------|-----------|-------------------|---------------------|
| CR | Execution Item (EI) | — | All COMPLETE or DEFERRED-with-followup |
| INV | CAPA Item (CA/PA) | — | All COMPLETE or DEFERRED-with-followup |
| TP | Test Step (TS) | `PASS`, `FAIL` | All PASS or FAIL-with-approved-ER |

### 3.4 Agent Orchestration Model

**Recommended: Hybrid Batch + Delegation**

1. **Batch Processing for Review/Approval**
   - QA agent invoked periodically (or on-demand) to process inbox
   - Single session handles all pending reviews and approvals
   - Reduces spawn count by 60-80%

2. **Delegated Authority for Routine Operations**
   - QA pre-establishes policy for risk classification
   - Administrative changes (documentation-only, no code, no procedure changes) proceed with abbreviated review
   - Claude can execute pre-authorized patterns without per-instance QA consultation

3. **Session Continuity for Complex Documents**
   - For CRs affecting architecture or critical systems, QA agent persists across pre-review → approval → post-review → closure
   - Context preserved; no re-explanation needed
   - Agent ID (resume parameter) used for continuity

**Implementation:**

```
# Batch review session
Claude: /qms --user qa inbox
QA: Reviews all pending items, provides recommendations/approvals
Claude: Processes results, routes as appropriate

# Delegated authority (pre-established)
QA: "Administrative CRs (doc-only, no code) may proceed with QA review only, no TU assignment"
Claude: Creates administrative CR, routes for review
QA: Reviews, approves (single invocation covers both)

# Complex document continuity
Claude: Creates CR-010 (architecture change), routes for review
[spawn QA agent, store agent ID]
QA: Reviews, requests updates
Claude: Revises, routes again
[resume same QA agent]
QA: Reviews, recommends
Claude: Routes for approval
[resume same QA agent]
QA: Approves
```

### 3.5 Risk-Based Review Calibration

| Risk Level | Criteria | Review Team | Agent Pattern |
|------------|----------|-------------|---------------|
| Administrative | Doc-only, no code, no procedure | QA only | Single invocation |
| Standard | Code with tests, minor procedure | QA + 1 TU | Batch processing |
| Critical | Architecture, security, safety, new procedures | QA + all TUs | Session continuity |

**Classification:** Initiator proposes, QA confirms during routing. QA may escalate.

### 3.6 INV Lifecycle Revision

To support embedded CAPA items without child documents:

```
DRAFT → PRE_REVIEW → PRE_APPROVED → IN_EXECUTION → POST_REVIEW → POST_APPROVED → REMEDIATION_PENDING → CLOSED
```

| State | Meaning |
|-------|---------|
| POST_APPROVED | Investigation findings accepted |
| REMEDIATION_PENDING | CAPA items in progress; waiting for follow-up CRs |
| CLOSED | All CAPA items COMPLETE or DEFERRED-with-followup |

### 3.7 TP Test Step Pattern

```markdown
## 5. Test Procedure

| TS | Description | Expected | Status | Actual | Evidence |
|----|-------------|----------|--------|--------|----------|
| TS-1 | Login as admin | Dashboard shown | PASS | As expected | Screenshot-1 |
| TS-2 | Invalid input | Error message | FAIL | No error | Screenshot-2, ER-001 |
```

**Closure rules:**
- TP cannot close if any TS is FAIL without linked ER
- ER (Exception Report) IS a document because it represents a decision: "Is this failure acceptable?"
- TP closure requires all TS: PASS or (FAIL + approved-ER)

---

## Part IV: Implementation Path

### 4.1 Sequencing

```
Phase 1: Glossary & Definitions (SOP-001 revision)
  - Define Tracked Item, Execution Item, CAPA Item, Test Step
  - Consolidate all terminology in SOP-001 Section 3

Phase 2: Tracked Item Procedures (SOP-002 revision)
  - Define EI table structure and status values
  - Define closure gate validation
  - Define deferral handling

Phase 3: Risk Classification (SOP-002 revision)
  - Define risk levels and criteria
  - Define review team composition per level

Phase 4: CAPA Embedding (SOP-001/002 revision)
  - Remove CAPA as standalone document type
  - Define CAPA section structure within INV
  - Add REMEDIATION_PENDING state

Phase 5: TP/ER Patterns (new TP template, ER procedures)
  - Define test step table structure
  - Define ER creation triggers
  - Define TP closure rules

Phase 6: CLI Enforcement (qms.py changes)
  - Validate closure gates
  - Support REMEDIATION_PENDING state
  - Support risk classification metadata
```

### 4.2 Backward Compatibility

- Existing documents (CR-001 through CR-005, INV-001) remain unchanged
- New procedures apply to documents created after effective date
- No retroactive application of tracked item requirements

### 4.3 Agent Orchestration Changes

| Change | Implementation | Complexity |
|--------|----------------|------------|
| Batch inbox processing | Procedural (invoke QA with "process inbox") | Low |
| Agent session continuity | Use resume parameter with stored agent IDs | Low |
| Delegated authority | Document in CLAUDE.md as pre-authorized patterns | Low |
| Risk classification | Metadata in .meta JSON + QA confirmation | Medium |
| Closure gate validation | qms.py code changes | Medium |

---

## Part V: Critical Reflection

### 5.1 What We Got Wrong

The initial QMS design imported pharmaceutical compliance patterns without adapting them to our context:

1. **Assumed human reviewers** - Designed for scarce human attention, not unlimited AI availability
2. **Document-centric** - Treated every work item as a document requiring independent lifecycle
3. **Stateless agents** - Treated AI agents as function calls rather than conversation participants
4. **One-size-fits-all workflow** - Applied identical overhead to trivial and critical changes

### 5.2 What We Got Right

1. **Separation of concerns** - Three-tier architecture (content, workflow, audit) is sound
2. **Audit trail** - Immutable append-only logs provide traceability
3. **Air gap** - QA approval required for progression maintains integrity
4. **Blocking semantics** - State machine prevents invalid transitions

### 5.3 The Path Forward

The QMS should evolve from **document proliferation** to **intelligent tracking**:

- Documents for decision boundaries
- Tracked items for work units
- Risk-calibrated review intensity
- Agent orchestration optimized for continuity, not statelessness

---

## Part VI: Open Questions for Lead Decision

### 6.1 Risk Classification Thresholds

If risk-based classification is adopted:
- What distinguishes Administrative from Standard?
- What distinguishes Standard from Critical?
- Examples for each category?

### 6.2 Agent Orchestration Preference

- **Batch processing:** QA processes inbox periodically (simpler, async-friendly)
- **Session continuity:** QA persists per-document (richer context, more complex)
- **Hybrid:** Both patterns available, selected by document complexity

### 6.3 Closure Gate Enforcement

- **Procedural:** QA verifies item completion during post-review
- **Automated:** CLI validates closure gate before allowing close command
- **Hybrid:** CLI warns, QA confirms

### 6.4 CAPA Document Type

- **Remove entirely:** CAPAs are always embedded sections, never standalone
- **Retain optionally:** Major investigations may spawn standalone CAPA if QA determines necessary
- **Remove and grandfather:** Existing CAPA references in SOP-001 become deprecated

### 6.5 Immediate vs. Phased Implementation

- **Big bang:** All changes in single CR, higher risk but faster
- **Phased:** Sequential CRs per phase, lower risk but slower
- **Hybrid:** Phase 1-3 together (foundation), Phase 4-6 separately (application)

---

## Appendix A: Current vs. Proposed Document Overhead

| Scenario | Current Documents | Current States | Proposed Documents | Proposed States |
|----------|-------------------|----------------|--------------------|-----------------|
| Simple CR | 1 | 12 | 1 | 12 |
| CR + TP | 2 | 24 | 2 | 24 |
| INV + CAPA | 2 | 24 | 1 | 13* |
| INV + CAPA + 2 CRs | 4 | 48 | 3 | 37 |
| INV + CAPA + 2 CRs + 2 TPs | 6 | 72 | 5 | 61 |

*13 = 12 standard + 1 REMEDIATION_PENDING

**Reduction:** 17% fewer documents, 15% fewer states in complex scenarios. More importantly: 60-80% fewer agent invocations through batch processing.

---

## Appendix B: Agent Invocation Comparison

| Scenario | Current Invocations | Proposed (Batch) | Reduction |
|----------|---------------------|------------------|-----------|
| Simple CR (no revision) | 4 | 2 | 50% |
| Simple CR (one revision) | 6 | 2-3 | 50-67% |
| CR + TP | 8 | 3-4 | 50-63% |
| INV + follow-up CRs | 12+ | 4-5 | 58-67% |

---

## Appendix C: Tracked Item State Diagram

```
                    ┌─────────────┐
                    │   PENDING   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
              ┌─────│ IN_PROGRESS │─────┐
              │     └──────┬──────┘     │
              │            │            │
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌─────────┐
       │ COMPLETE │ │ DEFERRED │ │ BLOCKED │
       └──────────┘ └────┬─────┘ └────┬────┘
                         │            │
                         ▼            │
                   [Follow-up ref     │
                    required]         │
                                      ▼
                              [Resolution
                               required]
```

**Closure Gate Logic:**
```
can_close = all(item.status in {COMPLETE, DEFERRED} for item in items)
           and all(item.followup is not None for item in items if item.status == DEFERRED)
```

---

## Conclusion

INV-001 revealed not just a procedural nonconformance but an architectural trajectory toward unsustainable overhead. This assessment proposes a remediated architecture that:

1. **Distinguishes documents from tracked items** based on whether independent review is required
2. **Embeds work items** (EIs, CAPAs, test steps) within parent documents
3. **Optimizes agent orchestration** through batch processing and session continuity
4. **Calibrates review intensity** to change risk level

The proposal preserves the QMS's core strengths (separation of concerns, audit trails, approval gates) while eliminating unnecessary proliferation.

We await the Lead's decisions on the open questions before proceeding with implementation.

---

**Document Location:** `pipe-dream/Architectural-Assessment-QMS-Remediation-Proposal.md`

**Consultation:** QA agent aa14ccf provided architectural analysis incorporated in Part II and Part III.

**Status:** Ready for Lead review and decision.
