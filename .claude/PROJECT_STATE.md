# Project State

*Last updated: Session-2026-02-16-003*

---

## 1. Where We Are Now

CR-088 closed: Agent Hub Granular Service Control and Observability. Added `start-svc`/`stop-svc` CLI commands, unified log format across all services, tool invocation logging, and resolved 4 code review findings (H1 file handle leaks, L1 tmux constant, L8 TTL reduction, L9 entrypoint fix). RS v14.0, RTM v18.0, CLI at 416 tests.

**Known deficiency from CR-088:** The health check fix (GET→POST for /mcp) did not eliminate server log noise — POST with empty JSON produces 406 instead of 405. Needs a follow-up CR to switch to TCP connect. Root cause: integration verification was structural, not behavioral. The containerization infrastructure that enables real behavioral testing was not in use during execution.

Prior: CR-087 consolidated state machine, CR-086 fixed pre/post-execution commits as bookend EIs, CR-085 added pre-execution commit requirement, CR-084 codified integration verification, CR-083 codified the merge gate, CR-082 added the ADD document type (CLI-7.0), INV-011 CLOSED with all 3 CAPAs.

The platform layer remains operational: Docker containers, MCP connectivity, Agent Hub, Tauri GUI, and identity enforcement. Phases B and D cover Git MCP access control and GUI feature completion.

---

## 2. The Arc

**Foundation (Feb 1-5, CR-042 through CR-055).** Remote MCP transport, container infrastructure, streamable-HTTP, process improvements from INV-007 through INV-010.

**Multi-Agent Infrastructure (Feb 6-7, CR-056 through CR-063).** Unified launcher, Agent Hub, port-based discovery, agent permissions.

**Feature Build (Feb 8-9, CR-064 through CR-072).** PTY manager, WebSocket endpoint, Tauri GUI, demand-driven bootstrap.

**Identity and Security (Feb 9-10, CR-073 through CR-076).** Four-phase identity system, 396 tests, RS v12.0/RTM v14.0.

**Audit, Hardening, and Verification (Feb 14, CR-077 through CR-081).** Code review (27 findings, 4 fixed), Phase A integration testing (2 containerized agents, full QMS lifecycle), GUI terminal hardening (scrollback, control mode, dimensions).

**QMS Process Evolution (Feb 15-16, CR-082 through CR-087).** ADD document type (CAPA-003). Merge gate and qualified commit convention. Integration verification mandate. Pre/post-execution commit as bookend EIs. Rollback procedures for code CRs. CLI quality and workflow enforcement.

---

## 3. What's Built

### The CR Chain (Multi-Agent Orchestration Era)

| Phase | CR | Title | Outcome |
|-------|----|-------|---------|
| **Foundation** | CR-042 | Remote Transport Support | SSE transport for containerized MCP access |
| | CR-043 | Container Infrastructure | Dockerfile, docker-compose, read-only QMS mount |
| | CR-044 | TEMPLATE-CR Best Practices | CODE CR PATTERNS, standardized 7-phase implementation |
| | CR-045 | Requalify SSE Transport | Integration tests, CLI-5.0 baseline |
| | CR-046 | Containerization Operational Verification | End-to-end container validation |
| | CR-047 | Streamable-HTTP Transport | Replaced buggy SSE, CLI-6.0 baseline |
| | CR-048 | Workflow Improvements | Status-aware checkout, withdraw command, archive-on-commit |
| | CR-049 | Add qms_withdraw Tool | Combined requalification with CR-065 |
| | CR-050 | INV-009 Corrective Actions | Fixed test assertion, CI on all branches |
| | CR-051 | SDLC Prerequisite Gate CAPAs | RS/RTM must be EFFECTIVE before CR closure |
| | CR-052 | Streamline Container Session Startup | Zero-friction auth persistence, MCP auto-connect |
| | CR-053 | Container Git Authentication | GitHub CLI + PAT, entrypoint auto-config |
| | CR-054 | Git MCP Server | `git_exec` tool with submodule/destructive blocking |
| | CR-055 | Git MCP Launch Integration | Unified startup with both MCP servers |
| **Multi-Agent** | CR-056 | Multi-Agent Container Infrastructure | Unified launcher, variance closure (3 VARs) |
| | CR-058 | Inbox Watcher Notification Injection | tmux push notifications, Claude Code pending queue |
| | CR-059 | Container Agent Permissions | 51 allow rules, state persistence across restarts |
| | CR-060 | Agent Hub Genesis | Python service: lifecycle, inbox, policy, API, CLI |
| | CR-061 | Hub Integration and Cleanup | Absorbed launch.sh, deleted obsolete scripts |
| | CR-062 | pd-status Utility | Unified process status overview |
| | CR-063 | PID-less Process Discovery | Port-based detection replacing PID files |
| **Hub Features** | CR-064 | Container Readiness Check | tmux capture-pane polling before notification |
| | CR-065 | Fix qms_review Mapping | MCP tool argument mapping bug, equivalence tests |
| | CR-066 | PTY Manager | Terminal I/O multiplexing, rate-based idle filter |
| | CR-067 | WebSocket Endpoint | Real-time broadcasting, PTY streaming, event fan-out |
| | CR-068 | GUI Scaffold | Tauri + React + xterm.js desktop application |
| | CR-069 | Hub Consolidation | All tools under `agent-hub/`, CLI commands |
| | CR-070 | Session Health Detection | STALE state, tmux health check, recovery menu |
| | CR-071 | Status Command Consolidation | Unified display, duplicate launch prevention |
| | CR-072 | Demand-Driven Bootstrap | GUI auto-starts Hub, Hub auto-starts MCP |
| **Identity** | CR-073 | Transport-Based Identity Resolution | Proxy-injected headers, enforced/trusted modes |
| | CR-074 | Identity Collision Prevention | In-memory registry, TTL, UUID instance tracking |
| | CR-075 | Single-Authority MCP + HTTP Hardening | Eliminated dual-process vulnerability |
| | CR-076 | Hardened Identity Management | Removed defaults, explicit validation, mismatch errors |
| **Verification** | CR-077 | Pre-Integration Hardening | Shell injection fix, CORS, ErrorBoundary, Hub failure |
| | CR-078 | Phase A Integration Fixes | Debug dir ENOENT, Tauri bad file descriptor |
| | CR-079 | Multi-Agent Integration Test | Full QMS lifecycle across 2 containerized agents |
| **GUI Hardening** | CR-080 | Terminal Scrollback Support | ESC sequence stripping for xterm.js scrollback |
| | CR-081 | Terminal Dimensions + Control Mode | Default 120x30, tmux -CC for raw PTY bytes |
| **QMS Process** | CR-082 | ADD (Addendum) Document Type | Post-closure correction mechanism, CLI-7.0 |
| | CR-083 | Merge Gate and Qualified Commit Convention | SOP-005/006/TEMPLATE-CR updated, merge type codified |
| | CR-084 | Integration Verification Mandate | SOP-002/004, TEMPLATE-CR/VAR updated, new Phase 5 |
| | CR-085 | Pre-Execution Repository Commit | SOP-002/004, TEMPLATE-CR updated, commit before release |
| | CR-086 | State Preservation, Rollback, CR-085 Fix | Pre/post commits as EIs, SOP-005 rollback, language fix |
| | CR-087 | QMS CLI Quality, State Machine, Workflow Enforcement | Consolidated state machine, auto-withdraw/auto-checkin, 416 tests |
| | CR-088 | Agent Hub Granular Service Control and Observability | start-svc/stop-svc, unified logging, tool logging, H1/L1/L8/L9 |

*CR-057 predates the orchestration era. All 46 CRs above are CLOSED.*

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v14.0 EFFECTIVE | 109 requirements |
| SDLC-QMS-RTM | v18.0 EFFECTIVE | 416 tests, CI-verified |
| Qualified Baseline | CLI-9.0 | qms-cli commit fe1a681 (main: 208da7f) |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| CR-001 | IN_EXECUTION v1.0 | Legacy workflow test. Candidate for cancellation. |
| CR-020 | DRAFT v0.1 | Test document. Candidate for cancellation. |
| INV-002 | IN_EXECUTION v1.0 | Legacy — SOP-005 missing revision summary. |
| INV-003 | PRE_REVIEWED v0.1 | Legacy — CR-012 workflow deficiencies. |
| INV-004 | IN_EXECUTION v1.0 | Legacy — CR-019 template loading. |
| INV-005 | IN_EXECUTION v1.0 | Legacy — locked section edit during execution. |
| INV-006 | IN_EXECUTION v1.0 | Legacy — incorrect code modification target. |
| CR-036-VAR-002 | IN_EXECUTION v1.0 | Legacy — documentation drift. |
| CR-036-VAR-004 | IN_EXECUTION v1.0 | Legacy — partial test coverage analysis. |

All remaining open documents are legacy from early QMS iterations. A bulk cleanup would reduce cognitive overhead.

---

## 5. Forward Plan (Phases B-E)

### Phase B: Git MCP Access Control (~1 session)
- Add identity resolution to `agent-hub/git_mcp/server.py`
- Allowlist: `["claude", "lead"]` — other agents blocked from git operations
- New requirement REQ-MCP-017, RS/RTM updates

### ~~Phase C: Close INV-011~~ DONE
- INV-011 CLOSED v2.0. All 3 CAPAs pass.

### Phase D: GUI Enhancement (~2-3 sessions)
- **D.1:** MCP health monitoring (replace placeholder panel)
- **D.2:** QMS status panel (replace placeholder panel)
- **D.3:** Notification injection API for inter-agent communication
- **D.4:** Identity status visibility in sidebar

### Phase E: Process Alignment (~1-2 sessions)
- Update SOP-007 and SOP-001 to reflect identity architecture
- Update agent definitions with "do not modify files" prohibitions
- Audit and fix CR document path references in SOPs/templates

---

## 6. Code Review Status

Comprehensive audit performed Session-2026-02-14-001. 27 findings, 4 fixed (CR-077), 4 fixed (CR-088).

### Open — Critical (1)

| ID | Finding | Bundle |
|----|---------|--------|
| C3 | Container runs as root | Agent Hub Robustness |

### Open — High (2)

| ID | Finding | Bundle |
|----|---------|--------|
| H4 | No Hub shutdown on GUI exit | Agent Hub Robustness |
| H6 | Agent action errors not surfaced to user | GUI Polish |

### Resolved by CR-088

H1 (file handle leaks), L1 (tmux constant), L8 (TTL reduction), L9 (entrypoint false success).

### Open — Medium/Low/Note (13)

See Session-2026-02-14 notes for full details. Grouped into Agent Hub Robustness, GUI Polish, and Identity Hardening bundles.

---

## 7. Backlog

### Ready (no blockers)

| Item | Effort | Bundle |
|------|--------|--------|
| Correct SOP-001 Section 4.2 `fix` permission | Small | SOP Revision |
| Audit and fix CR document path references | Small | SOP Revision |

### Bundleable (natural CR groupings)

**SOP Revision** (~1 session)
- SOP-001 Section 4.2 `fix` permission correction
- Audit CR document path references in SOPs/templates
- Consider simplifying SOPs to behavioral baselines

**Identity & Access Hardening** (~1 session, overlaps Phase B)
- Proxy header validation (L7)
- Git MCP access control (Phase B)

**Agent Hub Robustness** (~1-2 sessions)
- C3: Non-root user in Dockerfile
- H4, M6, M8, M9, M10

**GUI Polish** (~1-2 sessions, overlaps Phase D)
- H6, M3, M4, M5, M7, L3, L4, L5, L6

### Blocked

| Item | Blocker |
|------|---------|
| Comments visibility restriction during active workflows | Needs design decision |

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value |
| Metadata injection into viewable rendition | No current pain point |
| "Pass with exception" test outcome type | No test execution exercising this gap |
| Production/test environment isolation review | Addressed by submodule separation |
| Proceduralize how to add new documents to QMS | Works well enough |
| Stdio proxy for 100% MCP reliability | HTTP at 90% is workable |

---

## 8. Gaps & Risks

**Legacy QMS debt.** Eight open documents from early iterations. Bulk cleanup recommended.

**Container security.** C3 (root user) remains the last critical code review finding.

**Hub/GUI test coverage.** Hub 42 tests, GUI 0%. QMS CLI well-tested at 416.

**No inter-agent communication.** Phase D.3 addresses this.
