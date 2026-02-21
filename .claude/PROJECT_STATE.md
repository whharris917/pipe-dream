# Project State

*Last updated: Session-2026-02-21-001*

---

## 1. Where We Are Now

**CR-091 CLOSED.** Interaction system engine implemented — template-driven interactive authoring for VR documents. 5 new modules, 182 new tests, 22 new requirements (REQ-INT). All controlled documents EFFECTIVE. 49 CRs CLOSED (CR-042 through CR-091).

**Pending:** CR-091-VR-001 is inadequate (freehand, not interactive). Next session creates CR-091-ADD-001 with a proper VR authored through the interaction system.

---

## 2. The Arc

**Foundation (Feb 1-5, CR-042 through CR-055).** Remote MCP transport, container infrastructure, streamable-HTTP, process improvements from INV-007 through INV-010.

**Multi-Agent Infrastructure (Feb 6-7, CR-056 through CR-063).** Unified launcher, Agent Hub, port-based discovery, agent permissions.

**Feature Build (Feb 8-9, CR-064 through CR-072).** PTY manager, WebSocket endpoint, Tauri GUI, demand-driven bootstrap.

**Identity and Security (Feb 9-10, CR-073 through CR-076).** Four-phase identity system, 396 tests, RS v12.0/RTM v14.0.

**Audit, Hardening, and Verification (Feb 14, CR-077 through CR-081).** Code review (27 findings, 4 fixed), Phase A integration testing (2 containerized agents, full QMS lifecycle), GUI terminal hardening.

**QMS Process Evolution (Feb 15-16, CR-082 through CR-088).** ADD document type. Merge gate. Integration verification mandate. Pre/post-execution commits. Rollback procedures. CLI quality and workflow enforcement. Agent Hub observability.

**Testing & Evidence Framework (Feb 16-18, CR-089).** VR document type — CLI support (424 tests), SDLC docs (RS v15.0, RTM v19.0), TEMPLATE-VR, 4 SOP updates, 3 template updates.

**Deficiency Resolution (Feb 19, CR-090).** MCP health checks switched from HTTP POST to TCP connect, eliminating 406 log noise.

**Interaction System (Feb 19-21, CR-091).** Design across five sessions (Feb 19-20), implementation and execution (Feb 21). Template parser, source data model, interaction engine, compilation engine, CLI command, MCP tool. 22 requirements (REQ-INT-001 through REQ-INT-022), 611 tests. SOP-004 Section 11 (Interactive Document Authoring), TEMPLATE-VR v2.0 (interactive v3).

---

## 3. What's Built

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v16.0 EFFECTIVE | 133 requirements |
| SDLC-QMS-RTM | v20.0 EFFECTIVE | 611 tests, qualified commit 7e708fc |
| Qualified Baseline | CLI-11.0 | qms-cli commit 7e708fc (main: c83dda0) |

### Controlled Document State

| Document | Version |
|----------|---------|
| SOP-001 | v21.0 EFFECTIVE |
| SOP-002 | v13.0 EFFECTIVE |
| SOP-003 | v3.0 EFFECTIVE |
| SOP-004 | v9.0 EFFECTIVE |
| SOP-005 | v5.0 EFFECTIVE |
| SOP-006 | v5.0 EFFECTIVE |
| SOP-007 | v2.0 EFFECTIVE |
| TEMPLATE-CR | v8.0 EFFECTIVE |
| TEMPLATE-VAR | v3.0 EFFECTIVE |
| TEMPLATE-ADD | v2.0 EFFECTIVE |
| TEMPLATE-VR | v2.0 EFFECTIVE |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| CR-091-VR-001 | IN_EXECUTION v1.0 | Inadequate — freehand, not interactive. To be superseded by CR-091-ADD-001-VR-001. |
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

### Next Session: CR-091-ADD-001 (Interaction System VR Remediation)

CR-091-VR-001 was authored as freehand markdown, bypassing the interaction system. Create an addendum (CR-091-ADD-001) to produce CR-091-ADD-001-VR-001 — a VR authored *through* the interaction engine via `qms interact` CLI, proving complete system functionality. The ADD should document the inadequacy of CR-091-VR-001 and establish CR-091-ADD-001-VR-001 as the true evidence.

**Prerequisite:** Restart MCP server to pick up the new `qms_interact` tool, or use CLI directly.

### Interaction System Phase 2+ (future)
- **Phase 3:** Expand to executable documents (TEMPLATE-CR, TEMPLATE-VAR, TEMPLATE-ADD) — likely hybrid interactive/freehand
- **Phase 4+:** Non-executable documents, intent decomposition layer

### Phase B: Git MCP Access Control (~1 session)
- Add identity resolution to `agent-hub/git_mcp/server.py`
- Allowlist: `["claude", "lead"]` — other agents blocked
- New requirement REQ-MCP-017, RS/RTM updates

### Phase D: GUI Enhancement (~2-3 sessions)
- D.1: MCP health monitoring
- D.2: QMS status panel
- D.3: Notification injection API
- D.4: Identity status visibility

### Phase E: Process Alignment (~1-2 sessions)
- SOP-007 and SOP-001 identity architecture updates
- Agent definition prohibitions

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
| Interactive document write protection (REQ-INT-023) | Medium | Session-2026-02-21-001 defect |
| Fix stale help text in `qms.py:154` ("QA/lead only" -> "administrators only") | Trivial | To-do 2026-01-17 |
| Remove stdio transport option from both MCP servers | Small | To-do 2026-02-16 |
| Stop tracking total counts of tests/REQs across documents | Small | To-do 2026-02-16 |

### Bundleable (natural CR groupings)

**Identity & Access Hardening** (~1 session) — proxy header validation (L7), Git MCP access control
**Agent Hub Robustness** (~1-2 sessions) — C3, H4, M6, M8, M9, M10
**GUI Polish** (~1-2 sessions) — H6, M3, M4, M5, M7, L3, L4, L5, L6
**Process Refinement** (~1-2 sessions) — branch protection/merge strategy in SOPs, commit column in EI table
**QMS Workflow** — proceduralize adding new documents, comments visibility restriction during active workflows

### Discussion / Design Needed

| Item | Context |
|------|---------|
| Automate RTM generation | RTM is large, repetitive, error-prone to maintain manually |
| Improve RTM readability | One test per line with row-spanning REQ IDs |
| Session heartbeat mechanism | Prevent post-compaction session discontinuities |
| Simplify SOPs to behavioral baselines | Review for tooling-dependent language |
| Production/test environment isolation | Programmatic separation between production and test environments |
| Subconscious agent | Design discussion complete (discussion-subconscious-agent.md); implementation design pending |

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value |
| Metadata injection into viewable rendition | No current pain point |

---

## 8. Gaps & Risks

**CR-091-VR-001 inadequacy.** Freehand VR bypassed the interaction system. Remediation via CR-091-ADD-001 is the immediate next step.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**Container security.** C3 (root user) remains the last critical code review finding.

**Hub/GUI test coverage.** Hub 42 tests, GUI 0%. QMS CLI well-tested at 611.
