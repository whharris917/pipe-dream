# Project State

*Last updated: Session-2026-03-09-001 (2026-03-09)*

---

## 1. Where We Are Now

**WFE redesign in progress — UI-driven development.** The v1 CLI-based workflow engine is being redesigned from first principles. A Kneat-like web UI (`qms-workflow-engine/wfe-ui/`) is now the primary development driver. The engine primitives will be rebuilt to serve what the UI needs, not the other way around.

**The pivot:** Design discussions revealed fundamental problems with v1 (context gap, phase tangle, meta-workflows as wrong pattern). Rather than continuing abstract redesign, the Lead decided to build a visual UI and let concrete interaction drive the architecture.

**What's running now:** Flask web app at `http://127.0.0.1:5000` with:
- Sidebar navigation (Home, QMS, Workspace, Inbox, Templates, Workflow Sandbox, Quality Manual, Agent Portal)
- Quality Manual browser rendering actual markdown files with working cross-references
- Initiate Workflow page with interactive decision tree + direct document creation buttons
- CR authoring form with all pre-approval sections and authoring guidance
- Template Editor and Workflow Sandbox for engine experimentation
- **Agent Portal** — proof-of-concept for AI agent workflow interaction:
  - Agent Observer with SSE live state streaming and pluggable renderers (Raw JSON, Map, Terminal, Workflow)
  - CR creation workflow driven by YAML definition (`data/agent_create_cr.yaml`) — fields, stages, visibility rules, and metadata are declarative
  - Affordance model: every action is a complete API call the agent picks and sends verbatim
  - 1:1 projection principle: rendered view faithfully maps every key in the raw JSON

**CR-110** is IN_EXECUTION (v1.1). EI-1–4 Pass. Remaining EIs (5–7) will need to be scoped to reflect the redesign pivot.

**65 CRs CLOSED. 5 INVs CLOSED.**

---

## 2. The Arc

**Foundation through Quality Manual** (Feb 1-24, CR-042 through CR-105).

**Workflow Engine v1** (Mar 3-7, CR-108 through CR-110). CLI-based graph engine with hooks, templates, compile. Proved concepts but revealed design limits: meta-workflows create phase confusion, context gap for agent execution, rendering hints leak into data model.

**Workflow Engine v2 — UI-Driven Redesign** (Mar 8 - present). Building a Kneat-like web UI as the primary development artifact. The UI embodies the process knowledge previously scattered across SOPs and YAML workflows. Key principles: layered guidance (canvas/authoring/execution), template enforcement (add but can't delete), filled graph IS the document.

---

## 3. What's Built

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v22.0 EFFECTIVE | 143 requirements |
| SDLC-QMS-RTM | v27.0 EFFECTIVE | 687 tests, qualified commit 918984d |
| SDLC-CQ-RS | v2.0 EFFECTIVE | 6 requirements |
| SDLC-CQ-RTM | v2.0 EFFECTIVE | Inspection-based, qualified commit d3c34e5 |
| SDLC-WFE-RS | v0.1 DRAFT | 30 requirements (needs rewrite for v2) |
| Qualified Baseline | CLI-18.0 | qms-cli commit 309f217 (main) |

### Controlled Document State

| Document | Version |
|----------|---------|
| SOP-001 through SOP-007 | v21.0 / v16.0 / v3.0 / v9.0 / v7.0 / v5.0 / v2.0 EFFECTIVE |
| TEMPLATE-CR | v10.0 EFFECTIVE |
| TEMPLATE-VAR | v3.0 EFFECTIVE |
| TEMPLATE-ADD | v2.0 EFFECTIVE |
| TEMPLATE-VR | v3.0 EFFECTIVE |

### WFE v1 (Experimental/Provisional — being superseded by v2)

CLI-based graph engine in `qms-workflow-engine/wfe/`. Still functional but design is being replaced by UI-driven approach.

### WFE v2 UI (Active Development)

| Component | Description |
|-----------|-------------|
| `wfe-ui/app.py` | Flask app — routes, Quality Manual renderer with link rewriting |
| `wfe-ui/templates/base.html` | Layout with sidebar (Home, QMS, Workspace, Inbox, Quality Manual) |
| `wfe-ui/templates/index.html` | Home page with project info + Quick Start |
| `wfe-ui/templates/initiate.html` | Decision tree + direct create buttons for document initiation |
| `wfe-ui/templates/create_cr.html` | CR authoring form — all pre-approval sections with guidance |
| `wfe-ui/templates/manual_*.html` | Quality Manual browser with cross-reference navigation |
| `wfe-ui/templates/agent_observer.html` | Agent Observer — SSE live view with pluggable renderers |
| `wfe-ui/data/agent_create_cr.yaml` | Declarative CR workflow definition (fields, stages, visibility) |
| Placeholder pages | QMS, Workspace, Inbox — ready for content |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| CR-110 | IN_EXECUTION v1.1 | Workflow engine development. EI-1–4 Pass. UI-driven redesign is within scope — all work in the authorized sandbox repo. |
| CR-107 | DRAFT v0.1 | Unified Document Lifecycle. On hold — superseded by engine. |
| CR-106 | DRAFT v0.1 | System Governance. Depends on CR-107. On hold. |
| CR-091-ADD-001-VAR-001 | PRE_APPROVED v1.0 | Type 2 VAR. VR title bug + SOP-004/TEMPLATE-VR alignment gap. |
| CR-001 | IN_EXECUTION v1.0 | Legacy. Candidate for cancellation. |
| CR-020 | DRAFT v0.1 | Legacy test document. Candidate for cancellation. |
| INV-002 through INV-006 | Various | Legacy investigations. Low priority. |
| CR-036-VAR-002, CR-036-VAR-004 | IN_EXECUTION v1.0 | Legacy. Low priority. |

---

## 5. Forward Plan

### Immediate: WFE v2 UI Development

All focus is on the web UI. Build out the complete document lifecycle visually:

1. **CR authoring flow** — form submission, preview, next steps after "Continue"
2. **Execution view** — EI table with fill/advance interaction
3. **Document lifecycle** — review, approval, rejection flows in the UI
4. **Workspace & Inbox** — wire up to actual QMS state
5. **Other document types** — INV, VAR, ADD creation flows

The UI will surface what the engine needs to support. Engine primitives will be rebuilt as the UI demands them.

### CR-110 Remaining EIs

CR-110 authorized workflow engine development in the `qms-workflow-engine` submodule. The UI-driven redesign is fully within that scope — same sandbox repo, same objective. EI-5 (RS update), EI-6 (push + pointer), EI-7 (post-exec) remain valid; the RS will reflect v2 when the time comes.

### On Hold: CR-107 / CR-106

Both superseded by the engine. May need cancellation or significant revision.

---

## 6. Backlog

### Ready (no blockers)

| Item | Effort | Source |
|------|--------|--------|
| Fix CLI title metadata propagation | Small | CR-091-ADD-001-VAR-001 |
| Align SOP-004 Section 9C.4 with TEMPLATE-VR | Small | CR-091-ADD-001-VAR-001 |
| Govern checkin.py bug fix (commit `532e630`) via CR | Trivial | INV-012 |
| Delete `.QMS-Docs/` | Trivial | CR-103 |
| Standardize metadata timestamps to UTC ISO 8601 | Small | Session-2026-02-26-001 |

### Bundleable

**Identity & Access Hardening** (~1 session) — proxy header validation, Git MCP access control
**Agent Hub Robustness** (~1-2 sessions) — C3 (root user), H4 (no hub shutdown on GUI exit), M6/M8/M9/M10
**GUI Polish** (~1-2 sessions) — H6, M3/M4/M5/M7, L3-L6

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value |
| Metadata injection into viewable rendition | No current pain point |
| Consolidate SDLC namespaces into system registry | Depends on CR-106 |
| Interactive document write protection (REQ-INT-023) | Deferred pending UI-based interaction design |
| Remove stdio transport option from MCP servers | Low priority |
| Propagate Quality Manual cleanup from workshop | Medium effort, not blocking |

---

## 7. Gaps & Risks

**WFE v2 is greenfield.** The UI exists but has no backend persistence yet. CR authoring form collects data but doesn't save it. The engine primitives that will back the UI haven't been designed yet.

**v1 engine is in limbo.** Functional but being superseded. No clear deprecation plan yet.

**SOPs are being phased out.** The UI will eventually replace SOPs as the authoritative source of process knowledge. During transition, both exist.

**SDLC-WFE-RS needs full rewrite.** v1 requirements don't apply to v2.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**qms-workflow-engine has unpushed commits.** Head at `e5e3df4`; pipe-dream submodule pointer stale.
