# Project State

*Last updated: Session-2026-03-05-001 (continued 2026-03-06)*

---

## 1. Where We Are Now

**Architectural decision made: graph-based workflow engine.** After a week of prototyping and research (Sessions 2026-03-03 through 2026-03-05), the Lead drove decomposition of the workflow engine down to three bedrock primitives: **Slot** {name, type, value?, writable}, **Node** {id, slots, edges, prompt?}, **Edge** {to, when?}. Everything else — prompts, schemas, gates, templates, documents — is emergent from these three.

**Key design decisions (finalized):**
- Fork semantics: multiple true outgoing edges all fire (AND-join downstream)
- Acyclic constraint: DAG always valid, no cycles, no deadlocks
- Two modes: construction (modify graph structure) and execution (fill slots)
- Replication (not cycles) for repeating steps
- YAML storage: definitions separate from instances
- Home node as universal navigation root; start nodes as workflow entry points
- QMS document types map to workflows: CR, INV, VAR, TP, ER — each is a start node
- "One verb: execute" — writing a template = executing the write-template template
- Agent surface via tool/function calling, not raw text parsing

**CR-108 (DocuBuilder Genesis Sandbox) closing.** Sandbox explored, decision made, docu-builder deleted. Artifacts preserved in git history. Currently in post-review.

**CR-109 (qms-workflow-engine submodule) drafted.** Brings the new repo under formal change control from commit zero. In workspace, ready for checkin/review.

65 CRs CLOSED (CR-042 through CR-105, CR-108, plus CR-091-ADD-001). 5 INVs CLOSED (INV-010 through INV-014). 687 tests, SDLC-QMS-RS v22.0, SDLC-QMS-RTM v27.0.

---

## 2. The Arc

**Foundation through Quality Manual** (Feb 1-24, CR-042 through CR-105). See previous PROJECT_STATE versions.

**Document Lifecycle & System Governance** (Feb 25-26, CR-107 + CR-106 — design complete, on hold).

**Interaction Architecture Exploration** (Feb 27 - Mar 2). Multiple competing approaches explored.

**DocuBuilder Genesis Sandbox** (Mar 3, CR-108). Table-primitive model. Prototype built (20 usability tests). Proved the concept but revealed design limitations.

**Workflow Engine Design** (Mar 3-6, Sessions 2026-03-03 through 2026-03-05).
- DocuBuilder prototype: table-primitive model, 20 usability tests
- QMS Graph prototype-2: Python class inheritance, 137 tests, 7 templates, acyclic DAG
- Bedrock primitives distilled: Slot, Node, Edge — everything else emergent
- Agent interface research: 30+ sources, SWE-agent ACI, EBR systems, BPMN, Rasa slot-filling, CrewAI task model
- Construction/execution mode duality, replication pattern, YAML storage
- CR-109 drafted to bring engine repo under formal control

---

## 3. What's Built

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v22.0 EFFECTIVE | 143 requirements |
| SDLC-QMS-RTM | v27.0 EFFECTIVE | 687 tests, qualified commit 918984d |
| SDLC-CQ-RS | v2.0 EFFECTIVE | 6 requirements |
| SDLC-CQ-RTM | v2.0 EFFECTIVE | Inspection-based, qualified commit d3c34e5 |
| Qualified Baseline | CLI-18.0 | qms-cli commit 309f217 (main) |

### Controlled Document State

| Document | Version |
|----------|---------|
| SOP-001 | v21.0 EFFECTIVE |
| SOP-002 | v16.0 EFFECTIVE |
| SOP-003 | v3.0 EFFECTIVE |
| SOP-004 | v9.0 EFFECTIVE |
| SOP-005 | v7.0 EFFECTIVE |
| SOP-006 | v5.0 EFFECTIVE |
| SOP-007 | v2.0 EFFECTIVE |
| TEMPLATE-CR | v10.0 EFFECTIVE |
| TEMPLATE-VAR | v3.0 EFFECTIVE |
| TEMPLATE-ADD | v2.0 EFFECTIVE |
| TEMPLATE-VR | v3.0 EFFECTIVE |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| CR-109 | DRAFT v0.1 | Add qms-workflow-engine submodule under formal change control. Checked in, ready for review. |
| CR-107 | DRAFT v0.1 (content v1.0) | Unified Document Lifecycle. On hold — interaction design superseded. |
| CR-106 | DRAFT v0.1 (content v0.4) | System Governance. Depends on CR-107. On hold. |
| CR-091-ADD-001-VAR-001 | PRE_APPROVED v1.0 | Type 2 VAR. VR title bug + SOP-004/TEMPLATE-VR alignment gap. |
| CR-001 | IN_EXECUTION v1.0 | Legacy. Candidate for cancellation. |
| CR-020 | DRAFT v0.1 | Legacy test document. Candidate for cancellation. |
| INV-002 | IN_EXECUTION v1.0 | Legacy — SOP-005 missing revision summary. |
| INV-003 | PRE_REVIEWED v0.1 | Legacy — CR-012 workflow deficiencies. |
| INV-004 | IN_EXECUTION v1.0 | Legacy — CR-019 template loading. |
| INV-005 | IN_EXECUTION v1.0 | Legacy — locked section edit during execution. |
| INV-006 | IN_EXECUTION v1.0 | Legacy — incorrect code modification target. |
| CR-036-VAR-002 | IN_EXECUTION v1.0 | Legacy — documentation drift. |
| CR-036-VAR-004 | IN_EXECUTION v1.0 | Legacy — partial test coverage analysis. |

---

## 5. Forward Plan

### Immediate: CR-109 — Bring qms-workflow-engine Under Control

CR-109 is drafted. After CR-108 closes: checkin CR-109, route for review/approval, execute (create GitHub repo, add submodule).

### Next: Build the Engine Core

With the repo established, begin implementation under formal change control:
1. Define the DAG scheduler (node readiness, edge evaluation, fork/join, dead path elimination)
2. Define the tool surface (construction and execution tool signatures)
3. Build one real workflow (likely CR) in YAML and execute it to validate the model
4. Build the rendering layer (the ACI that translates graph state to agent view)

### On Hold: CR-107 / CR-106

CR-107's Jinja2/source infrastructure may become a rendering layer for the workflow engine. CR-106's system governance becomes workflow steps and gates. Both CRs may need revision or cancellation once the engine materializes.

### Design Artifacts

| Artifact | Location | Status |
|----------|----------|--------|
| **Workflow Engine Forward Plan** | `.claude/sessions/Session-2026-03-05-001/workflow-engine-plan.md` | **Active** — bedrock primitives, modes, storage, agent surface |
| **Agent Interface Research** | `.claude/sessions/Session-2026-03-05-001/agent-interface-research.md` | **Active** — 9 sections, 30+ sources |
| Workflow Engine Design (superseded) | `.claude/sessions/Session-2026-03-04-001/workflow-engine-design.md` | Superseded by forward plan (5-primitive model replaced by 3-primitive model) |
| QMS Graph prototype 2 | `.claude/sessions/Session-2026-03-04-001/qms-graph-prototype-2/` | Exploratory — 137 tests, informed design decisions |
| DocuBuilder prototype | git history at `20a7719` | Archived — 20 tests, informed decision to pursue graph-based approach |

---

## 6. Code Review Status

Comprehensive audit Session-2026-02-14-001. 27 findings, 8 fixed (CR-077 + CR-088).

### Open — Critical (1)
| ID | Finding | Bundle |
|----|---------|--------|
| C3 | Container runs as root | Agent Hub Robustness |

### Open — High (2)
| ID | Finding | Bundle |
|----|---------|--------|
| H4 | No Hub shutdown on GUI exit | Agent Hub Robustness |
| H6 | Agent action errors not surfaced to user | GUI Polish |

### Open — Medium/Low/Note (13)
See Session-2026-02-14 notes. Grouped into Agent Hub Robustness, GUI Polish, and Identity Hardening bundles.

---

## 7. Backlog

### Ready (no blockers)

| Item | Effort | Source |
|------|--------|--------|
| Fix CLI title metadata propagation in interactive engine | Small | CR-091-ADD-001-VAR-001 |
| Align SOP-004 Section 9C.4 with TEMPLATE-VR v5 | Small | CR-091-ADD-001-VAR-001 |
| Govern checkin.py bug fix (commit `532e630`) via CR | Trivial | INV-012 |
| Interactive document write protection (REQ-INT-023) | Medium | Session-2026-02-21-001 |
| Fix stale help text in `qms.py:154` | Trivial | To-do 2026-01-17 |
| Remove stdio transport option from MCP servers | Small | To-do 2026-02-16 |
| Delete `.QMS-Docs/` | Trivial | CR-103 |
| Propagate Quality Manual cleanup from workshop | Medium | Session-2026-02-24-003 |
| Standardize metadata timestamps to UTC ISO 8601 | Small | Session-2026-02-26-001 |

### Bundleable

**Identity & Access Hardening** (~1 session) — proxy header validation, Git MCP access control
**Agent Hub Robustness** (~1-2 sessions) — C3, H4, M6, M8, M9, M10
**GUI Polish** (~1-2 sessions) — H6, M3, M4, M5, M7, L3, L4, L5, L6

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value |
| Metadata injection into viewable rendition | No current pain point |
| Consolidate SDLC namespaces into system registry | Depends on CR-106 |

---

## 8. Gaps & Risks

**checkin.py bug fix needs governance.** Commit `532e630` fixed an `UnboundLocalError` in interactive checkin. Needs a proper CR.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**Container security.** C3 (root user) remains the last critical code review finding.

**Hub/GUI test coverage.** Hub 42 tests, GUI 0%. QMS CLI well-tested at 687.

**Claude Code deny rules non-functional.** Platform bug. PreToolUse hooks provide actual enforcement.

**SOP-004/TEMPLATE-VR alignment gap.** Documented in CR-091-ADD-001-VAR-001, corrective CR pending.

**CR-107/CR-106 stale.** Both CRs are on hold. Their interaction design content is superseded by the workflow engine. May need cancellation or significant revision once the engine materializes.
