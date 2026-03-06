# Project State

*Last updated: Session-2026-03-04-001*

---

## 1. Where We Are Now

**Major design pivot: document-centric → workflow-centric.** Session 2026-03-04-001 produced a comprehensive design proposal for a Unified Workflow Engine that reframes DocuBuilder from a document editor to a workflow builder and execution platform. The design was driven by deep research across 5 parallel agents analyzing all SOPs, 100+ CRs, 14 INVs, 9 templates, audit trails, and 10+ external workflow systems (BPMN, Temporal.io, Dagster, XState, Petri nets, GMP electronic batch records, 21 CFR Part 11, ALCOA+, van der Aalst workflow patterns, AWS Step Functions).

**Core insight:** QMS documents are workflow instances, not documents. The engine should enforce ordering constraints, prerequisite gates, and evidence requirements programmatically — eliminating the entire category of "agent didn't follow the process" failures by construction. Five primitives (WorkflowTemplate, WorkflowInstance, Step, Gate, Signal) replace the document primitives (sections, tables, text blocks, columns).

**DocuBuilder prototype still operational** (20 passing usability tests) but the design direction has shifted from document editing to workflow execution. The prototype's key concepts (enforce/locked, prerequisites, sequential execution, cascade revert, audit trails) carry forward as workflow primitives.

**CR-107 and CR-106 remain in DRAFT.** CR-107's Jinja2/source infrastructure becomes the rendering layer for the workflow engine. CR-106's system governance becomes workflow steps and gates in the code-CR template.

64 CRs CLOSED (CR-042 through CR-105, plus CR-091-ADD-001). 5 INVs CLOSED (INV-010 through INV-014). 687 tests, SDLC-QMS-RS v22.0, SDLC-QMS-RTM v27.0, SDLC-CQ-RS v2.0, SDLC-CQ-RTM v2.0.

---

## 2. The Arc

**Foundation through Quality Manual** (Feb 1-24, CR-042 through CR-105). See previous PROJECT_STATE versions for detailed arc.

**Unified Document Lifecycle & System Governance** (Feb 25-26, CR-107 + CR-106 — design complete). Grand unification of three document architectures into single Jinja2-based system. CR-106 builds system governance on top.

**Interaction Architecture Exploration** (Feb 27 - Mar 2, design sessions). Multiple competing approaches explored: frontmatter-driven interaction, three-artifact separation, graph-based engine with Python dataclasses. No decisions finalized.

**DocuBuilder Paradigm Shift** (Mar 3, Session-2026-03-03-001). Kneat eVal-inspired pivot. Table as universal interactive primitive. Column types replace graph nodes. Prerequisites replace graph edges. Composable sections replace zone markers. Property namespaces replace schema declarations. Work Instructions replace sequential prompt workflows. CR-108 authorizes genesis sandbox.

**Workflow Engine Design Pivot** (Mar 4-5, Session-2026-03-04-001). After building and testing the DocuBuilder prototype (20 usability tests), Lead identified that the document metaphor was constraining workflow thinking. Comprehensive research effort (5 parallel agents, 10+ external systems analyzed) produced a design proposal that reframes DocuBuilder from document editor to workflow engine. Key design decisions: 5 primitives (WorkflowTemplate, WorkflowInstance, Step, Gate, Signal), template inheritance with invariant steps, three-layer mutability model (template → instance drafting → instance execution), multi-workflow orchestration with lifecycle policies, ALCOA+ by construction.

**QMS Graph Prototyping** (Mar 4-5, Session-2026-03-04-001, continued). Exploratory prototyping of graph-based workflow engine. Two prototypes built: `qms-graph-prototype` (YAML-based, 19 tests) and `qms-graph-prototype-2` (Python class inheritance, 137 tests, 7 templates). Prototype-2 uses native Python inheritance for templates (the "Copernican insight" — inheritance is the hard problem, and Python solves it natively). Features: gate conditions, acyclic DAG enforcement with forward-only retry spawning, deep diff, template locking, fill-based extension points, evidence schemas with typed validation. Five rounds of agent usability testing plus critical analysis against real QMS structures (interact_engine, TEMPLATE-CR/VR, SOPs). Analysis identified structural DNA as sound (inheritance, fill points, schemas, diff, acyclic invariant) with operational gaps (amendments, append-only responses, compilation, child documents). **All provisional/exploratory** — no design decisions finalized, no production code affected.

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
| CR-108 | IN_EXECUTION v1.1 | DocuBuilder Genesis Sandbox. EI-3 in progress: RS + prototype operational, 20 usability tests passed. |
| CR-107 | DRAFT v0.1 (content v1.0) | Unified Document Lifecycle. Non-interaction content valid; interaction design superseded by DocuBuilder paradigm. Future TBD. |
| CR-106 | DRAFT v0.1 (content v0.4) | System Governance. Depends on CR-107. Unchanged. |
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

### Immediate: Lead Review of Workflow Engine Design

The design document at `.claude/sessions/Session-2026-03-04-001/workflow-engine-design.md` proposes a fundamental reframe of DocuBuilder. Awaiting Lead feedback before proceeding with implementation.

**Key decisions needed:**
- Does the five-primitive model (WorkflowTemplate, WorkflowInstance, Step, Gate, Signal) capture the full problem?
- Is the three-layer mutability model (template → drafting → execution) correct?
- Should the prototype pivot to the workflow model, or continue refining the document model?
- How does deviation handling (inline minor vs. child workflow major) interact with current VAR/INV processes?

### CR-108 EI-3: Prototype Direction Depends on Design Decision

If workflow-centric direction is confirmed, the prototype pivots from document primitives (sections, tables, text blocks) to workflow primitives (steps, gates, signals). The existing prototype's audit trail, prerequisite logic, and enforce/locked concepts carry forward.

If document-centric direction continues, remaining RS items: calculated columns, section visibility, work instructions, cross-document refs, property namespaces, duplicatable sections, amendability flag.

### CR-107 / CR-106: On Hold

CR-107's Jinja2/source infrastructure becomes the rendering layer for the workflow engine (if confirmed). CR-106's system governance becomes workflow steps and gates. Both CRs may need revision once the design direction is settled.

### Design Artifacts

| Artifact | Location | Status |
|----------|----------|--------|
| **Workflow Engine Design** | `.claude/sessions/Session-2026-03-04-001/workflow-engine-design.md` | **Active** — 14 sections, comprehensive proposal |
| Core principles (DocuBuilder) | `.claude/sessions/Session-2026-03-03-001/authoring-and-executing-controlled-documents.md` | Partially superseded by workflow design |
| Document DNA | `.claude/sessions/Session-2026-03-03-001/document_dna.json` | Partially superseded — audit trail and enforce/locked concepts carry forward |
| DocuBuilder prototype | `docu-builder/docubuilder/` | Operational (20 tests) — direction depends on design decision |
| QMS Graph prototype 1 | `.claude/sessions/Session-2026-03-04-001/qms-graph-prototype/` | Exploratory — YAML-based, 19 tests, subgraph support |
| QMS Graph prototype 2 | `.claude/sessions/Session-2026-03-04-001/qms-graph-prototype-2/` | Exploratory — Python templates, 137 tests, 7 templates, acyclic DAG, critical analysis complete |
| Workspace mockup | `prompt.txt` (project root) | Partially superseded by workflow rendered view concept |

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

**CR-107 interaction design superseded.** The graph-based interaction engine design explored across four sessions is superseded by the DocuBuilder paradigm. CR-107's non-interaction content remains valid but the CR needs revision once DocuBuilder prototyping yields results.
