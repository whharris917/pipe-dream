# Project State

*Last updated: Session-2026-02-17-001*

---

## 1. Where We Are Now

**CR-089 (VR Document Type) in execution — Phase 7 in progress.** Phases 1-6 complete: CLI code merged to main (424 tests), RS v15.0 and RTM v19.0 EFFECTIVE, submodule pointer updated. Phase 7 (controlled document updates) is in progress — TEMPLATE-VR created but not yet populated. Nine SOP/template updates remain (EI-10 through EI-17), plus the post-execution commit (EI-18).

The VR design from Session-2026-02-16-004 is now implemented in the CLI: VR is an executable child document of CR/VAR/ADD, born IN_EXECUTION at v1.0 (template is the pre-approval authority), following standard post-execution workflow.

**Known deficiency from CR-088:** Health check fix (GET→POST for /mcp) did not eliminate server log noise — POST with empty JSON produces 406 instead of 405. Needs a follow-up CR to switch to TCP connect.

Prior: 46 CRs CLOSED (CR-042 through CR-088). RS v15.0, RTM v19.0, CLI-10.0 at 424 tests. INV-011 CLOSED with all 3 CAPAs.

---

## 2. The Arc

**Foundation (Feb 1-5, CR-042 through CR-055).** Remote MCP transport, container infrastructure, streamable-HTTP, process improvements from INV-007 through INV-010.

**Multi-Agent Infrastructure (Feb 6-7, CR-056 through CR-063).** Unified launcher, Agent Hub, port-based discovery, agent permissions.

**Feature Build (Feb 8-9, CR-064 through CR-072).** PTY manager, WebSocket endpoint, Tauri GUI, demand-driven bootstrap.

**Identity and Security (Feb 9-10, CR-073 through CR-076).** Four-phase identity system, 396 tests, RS v12.0/RTM v14.0.

**Audit, Hardening, and Verification (Feb 14, CR-077 through CR-081).** Code review (27 findings, 4 fixed), Phase A integration testing (2 containerized agents, full QMS lifecycle), GUI terminal hardening.

**QMS Process Evolution (Feb 15-16, CR-082 through CR-088).** ADD document type. Merge gate. Integration verification mandate. Pre/post-execution commits. Rollback procedures. CLI quality and workflow enforcement. Agent Hub observability.

**Testing & Evidence Framework (Feb 16-17, CR-089 in progress).** VR document type — CLI support complete, controlled document updates in progress.

---

## 3. What's Built

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v15.0 EFFECTIVE | 111 requirements |
| SDLC-QMS-RTM | v19.0 EFFECTIVE | 424 tests, CI-verified |
| Qualified Baseline | CLI-10.0 | qms-cli commit c79e2df (main: 2c6b826) |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| **CR-089** | **IN_EXECUTION v1.1** | **VR document type — Phase 7 in progress (EI-10 through EI-18 pending)** |
| TEMPLATE-VR | DRAFT v0.1 | Created, checked out, needs content (EI-10) |
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

### Phase VR: CR-089 Remaining Work (~1 session)

**EI-10:** Populate TEMPLATE-VR controlled document (content from Session-2026-02-16-004 draft) → route to EFFECTIVE

**EI-11-14:** SOP updates:
- SOP-001: Add VR to definitions and naming conventions
- SOP-002: Simplify Section 6.8, add VR post-review gate
- SOP-004: VR scope, EI column, new Section 9C, post-review gate
- SOP-006: VR as third verification type

**EI-15-17:** Template updates:
- TEMPLATE-CR, TEMPLATE-VAR, TEMPLATE-ADD: Add VR column to EI tables

**EI-18:** Post-execution commit

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
- CR document path reference audit

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

| Item | Effort | Bundle |
|------|--------|--------|
| Correct SOP-001 Section 4.2 `fix` permission | Small | SOP Revision |
| Audit and fix CR document path references | Small | SOP Revision |

### Bundleable (natural CR groupings)

**SOP Revision** (~1 session) — fix permission, path references, simplification
**Identity & Access Hardening** (~1 session) — proxy header validation (L7), Git MCP access control
**Agent Hub Robustness** (~1-2 sessions) — C3, H4, M6, M8, M9, M10
**GUI Polish** (~1-2 sessions) — H6, M3, M4, M5, M7, L3, L4, L5, L6

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value |
| Metadata injection into viewable rendition | No current pain point |
| Stdio proxy for 100% MCP reliability | HTTP at 90% is workable |

---

## 8. Gaps & Risks

**CR-089 Phase 7 continuity.** TEMPLATE-VR checked out, CR-089 workspace has EI-01-09 recorded. Next session picks up at EI-10.

**Legacy QMS debt.** Eight open documents from early iterations. Bulk cleanup recommended.

**Container security.** C3 (root user) remains the last critical code review finding.

**Hub/GUI test coverage.** Hub 42 tests, GUI 0%. QMS CLI well-tested at 424.
