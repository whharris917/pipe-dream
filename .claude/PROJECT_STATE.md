# Project State

*Last updated: Session-2026-02-14-003*

---

## 1. Where We Are Now

The multi-agent orchestration platform is built and validated. Over 44 sessions and 38 Change Records (CR-042 through CR-079), the project evolved from a single Claude instance running locally into a containerized, identity-enforced, GUI-controlled multi-agent ecosystem. Phase A integration testing — the primary success criterion — passed on February 14: two containerized agents (claude and qa) autonomously completed a full QMS document lifecycle (DRAFT through CLOSED) with ten state transitions, four QA actions, and identity enforcement throughout.

The platform layer is operational: Docker containers with read-only QMS mounts, MCP connectivity (QMS and Git servers), the Agent Hub (lifecycle management, PTY multiplexing, WebSocket streaming), a Tauri desktop GUI with xterm.js terminals, and a four-phase identity system (transport resolution, collision prevention, single-authority MCP, hardened validation) backed by 396 unit tests and 7/7 identity UAT. A comprehensive code review of ~3,600 lines across 40 files produced 27 findings; the four most critical (shell injection, CORS, error boundary, Hub failure propagation) were fixed in CR-077 before integration testing.

What remains is hardening, closing loose ends, and enhancing the GUI. Phases B through E cover Git MCP access control, INV-011 closure, GUI feature completion, and SOP alignment. Estimated 4-6 sessions.

---

## 2. The Arc

**Foundation (Feb 1-5, CR-042 through CR-055).** The vision began with remote MCP transport for containerized agents. SSE proved buggy in Docker; streamable-HTTP replaced it. Container infrastructure was built and qualified: read-only QMS mounts, workspace airlocks, Claude Code auth persistence, Git authentication via GitHub CLI + PAT. A cascade of debugging revealed that MCP HTTP connections in Docker achieve ~90% reliability (unfixable from the server side). The period also produced significant process improvements — TEMPLATE-CR patterns, SOP-006 CR closure prerequisites, SDLC prerequisite gates — each emerging from investigations of real failures (INV-007 through INV-010).

**Multi-Agent Infrastructure (Feb 6-7, CR-056 through CR-063).** CR-056 closed the container foundation with a unified launcher. The Ouroboros Reactor vision was articulated: Pipe Dream as an exogenic evolution platform where agents evolve their environment (rules, knowledge, tools) rather than their weights. The Agent Hub was born — a Python service replacing shell scripts with proper lifecycle management, inbox monitoring, and a policy engine. Supporting infrastructure followed: port-based process discovery, container readiness checks, agent permissions.

**Feature Build (Feb 8-9, CR-064 through CR-072).** Rapid feature development delivered the PTY manager (terminal I/O multiplexing with rate-based idle detection), the WebSocket endpoint (real-time broadcasting), and the Tauri GUI scaffold (React + xterm.js). Everything consolidated under `agent-hub/`. Session health detection, status command unification, and demand-driven bootstrap (GUI auto-starts Hub, Hub auto-starts MCP servers) completed the operational stack. Nine CRs closed in four days.

**Identity and Security (Feb 9-10, CR-073 through CR-076).** A five-phase identity plan was designed and executed in four sessions. Phase 1: proxy-injected `X-QMS-Identity` headers with enforced/trusted modes. Phase 2: in-memory identity registry with TTL and collision detection. Phase 2.5 (emerged from UAT): single-authority MCP eliminating the dual-process registry vulnerability. Phase 3: hardened validation removing all defaults and fallbacks. UAT: 7/7 PASS including cross-transport collision detection and duplicate container blocking. The SDLC grew from RS v8.0/RTM v10.0 to RS v12.0/RTM v14.0 (396 tests).

**Audit, Hardening, and Verification (Feb 14, CR-077 through CR-079).** A deep code review produced 27 findings across three severity tiers. CR-077 bundled the four most urgent fixes (shell injection, CORS restriction, error boundary, Hub failure propagation). Phase A integration testing then validated the full stack in four sub-phases: infrastructure health, GUI revalidation, identity verification, and the crown jewel — a multi-agent QMS workflow where containerized claude and qa completed CR-079 autonomously. Two bugs emerged and were fixed via CR-078 (missing debug directory, bad file descriptor from Tauri process spawn). QA behavioral integrity was confirmed when the qa agent refused the Lead's direct instruction to test identity impersonation, citing CLAUDE.md's prohibition and proposing a proper test protocol instead.

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
| | CR-072 | Demand-Driven Bootstrap | GUI→Hub→MCP auto-start chain |
| **Identity** | CR-073 | Transport-Based Identity Resolution | Proxy-injected headers, enforced/trusted modes |
| | CR-074 | Identity Collision Prevention | In-memory registry, TTL, UUID instance tracking |
| | CR-075 | Single-Authority MCP + HTTP Hardening | Eliminated dual-process vulnerability |
| | CR-076 | Hardened Identity Management | Removed defaults, explicit validation, mismatch errors |
| **Verification** | CR-077 | Pre-Integration Hardening | Shell injection fix, CORS, ErrorBoundary, Hub failure |
| | CR-078 | Phase A Integration Fixes | Debug dir ENOENT, Tauri bad file descriptor |
| | CR-079 | Multi-Agent Integration Test | Full QMS lifecycle across 2 containerized agents |

*CR-057 predates the orchestration era. All 37 CRs above are CLOSED.*

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v12.0 EFFECTIVE | 98 requirements |
| SDLC-QMS-RTM | v14.0 EFFECTIVE | 396 tests, CI-verified |
| Qualified Baseline | CLI-6.0 | qms-cli commit 94345fa |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| **INV-011** | IN_EXECUTION v1.2 | CR-075 incomplete execution (`.mcp.json` transport omission). CAPA-001 PASS, CAPA-002 PASS. CAPA-003 (ADD document type) to be deferred via Type 2 VAR. **Closing this is Phase C.** |
| CR-001 | IN_EXECUTION v1.0 | Legacy workflow test from early QMS iterations. Candidate for cancellation. |
| CR-020 | DRAFT v0.1 | Test document. Candidate for cancellation. |
| INV-002 | IN_EXECUTION v1.0 | SOP-005 missing revision summary. Legacy — from before process stabilization. |
| INV-003 | PRE_REVIEWED v0.1 | CR-012 workflow deficiencies. Legacy — predates current workflow maturity. |
| INV-004 | IN_EXECUTION v1.0 | CR-019 template loading. Legacy — template system has since been rebuilt. |
| INV-005 | IN_EXECUTION v1.0 | Locked section edit during execution. Legacy — editing model redesigned. |
| INV-006 | IN_EXECUTION v1.0 | Incorrect code modification target. Legacy — predates submodule separation. |
| CR-036-VAR-002 | IN_EXECUTION v1.0 | Documentation drift and qualification gap. Legacy — from pre-SDLC era. |
| CR-036-VAR-004 | IN_EXECUTION v1.0 | Partial test coverage pattern analysis. Legacy — test coverage now at 396. |

Legacy documents (all except INV-011) are from early QMS iterations before process stabilization. A bulk cleanup — cancel with rationale or close with retrospective — would reduce cognitive overhead. Consider bundling as a single housekeeping CR.

---

## 5. Forward Plan (Phases B-E)

### Phase B: Git MCP Access Control (~1 session)
- Add identity resolution to `agent-hub/git_mcp/server.py`
- Allowlist: `["claude", "lead"]` — other agents blocked from git operations
- New requirement REQ-MCP-017, RS/RTM updates
- Can parallel with Phase C

### Phase C: Close INV-011 (~1 session)
- Create Type 2 VAR on CAPA-003 (ADD document type deferred — QMS usage patterns not yet stable)
- Route INV-011 through post-review → post-approval → CLOSED
- Can parallel with Phase B

### Phase D: GUI Enhancement (~2-3 sessions)
- **D.1:** MCP health monitoring (replace placeholder panel)
- **D.2:** QMS status panel (replace placeholder panel)
- **D.3:** Notification injection API (`POST /api/agents/{id}/notify`) for inter-agent communication
- **D.4:** Identity status visibility in sidebar
- **D.+:** Terminal scrollback support (discovered gap during Phase A.4)

### Phase E: Process Alignment (~1-2 sessions)
- Update SOP-007 and SOP-001 to reflect identity architecture
- Update agent definitions with "do not modify files" prohibitions
- Consider formalizing UAT as a stage gate for code CRs
- Audit and fix CR document path references in SOPs/templates

---

## 6. Code Review Status

Comprehensive audit performed Session-2026-02-14-001: ~3,600 lines across 40 files (Hub backend, GUI frontend, infrastructure). 27 findings total.

### Fixed (CR-077)

| ID | Severity | Finding | Fix |
|----|----------|---------|-----|
| C1 | CRITICAL | Git MCP shell injection (`shell=True`) | `shlex.split()` + `shell=False`, metacharacter blocking |
| C2 | CRITICAL | CORS wildcard (`allow_origins=["*"]`) | Restricted to three GUI-specific origins |
| H2 | HIGH | `ensureHub()` failure not propagated to WebSocket | Return value checked, connection status set to "error" |
| H3 | HIGH | No React ErrorBoundary | Created ErrorBoundary wrapping root component |

### Open — Critical (1)

| ID | Finding | File | Bundle |
|----|---------|------|--------|
| C3 | Container runs as root (no `USER` directive) | `agent-hub/docker/Dockerfile` | Agent Hub Robustness |

### Open — High (3)

| ID | Finding | File | Bundle |
|----|---------|------|--------|
| H1 | File handle leaks in service startup (3 `open()` never closed) | `services.py:160,183,212` | Agent Hub Robustness |
| H4 | No Hub shutdown on GUI exit (orphaned processes) | `lib.rs` | Agent Hub Robustness |
| H6 | Agent action errors only logged to console (no user feedback) | `AgentItem.tsx` | GUI Polish |

### Open — Medium (8 actionable + 2 downgraded)

| ID | Finding | Bundle |
|----|---------|--------|
| M3 | ResizeObserver not debounced (floods WebSocket) | GUI Polish |
| M4 | Context menu viewport bounds not checked | GUI Polish |
| M5 | Tauri CSP uses `unsafe-inline` for styles | GUI Polish |
| M6 | WebSocket resize validation weak | Agent Hub Robustness |
| M7 | No API retry logic in GUI | GUI Polish |
| M8 | No graceful degradation for missing Docker | Agent Hub Robustness |
| M9 | No container resource limits | Agent Hub Robustness |
| M10 | Entrypoint jq failure prints false success | Agent Hub Robustness |
| ~~M1~~ | ~~Inbox watcher deduplication~~ | *Downgraded to NOTE — count always correct* |
| ~~M2~~ | ~~`_pty_last_event` never cleaned~~ | *Downgraded to NOTE — bounded to 7 entries* |

### Open — Low/Note (9)

| ID | Finding | Bundle |
|----|---------|--------|
| L1 | Hardcoded tmux session name "agent" in 4+ locations | Agent Hub Robustness |
| L2 | Hub logging inconsistencies | Agent Hub Observability |
| L3 | `useHubConnection()` hook unused (dead code) | GUI Polish |
| L4 | Hub URL hardcoded (`localhost:9000`) | GUI Polish |
| L5 | No GUI test files | GUI Polish |
| L6 | No lint/format config for GUI | GUI Polish |
| L7 | Proxy header validation missing | Identity Hardening |
| L8 | Identity lock TTL (5 min) may be too long for dev | Identity Hardening |
| L9 | Entrypoint jq failure not handled | Agent Hub Robustness |

---

## 7. Backlog

### Ready (no blockers)

| Item | Effort | Bundle |
|------|--------|--------|
| Fix unit test assertion in `test_qms_auth.py` for improved error message | Trivial | QMS CLI Cleanup |
| Add ASSIGN to REQ-AUDIT-002 required event types in RS | Small | RS/RTM Update |
| Correct SOP-001 Section 4.2 `fix` permission (shows QA, should be Initiators) | Small | SOP Revision |
| Remove in-memory fallback for inbox prompts in qms-cli | Small | QMS CLI Cleanup |
| Audit and fix CR document path references (agents use wrong paths) | Small | SOP Revision |

### Bundleable (natural CR groupings)

**QMS CLI Cleanup** (~1 session)
- Fix `test_qms_auth.py` assertion
- Remove in-memory prompt fallback (legacy from CR-027)
- Derive TRANSITIONS from WORKFLOW_TRANSITIONS (single source of truth)
- Investigate checkout-from-review not cancelling workflow (INV-009 observation)

**SOP Revision** (~1 session)
- SOP-001 Section 4.2 `fix` permission correction
- SOP-005 qualification process explanation expansion
- Audit CR document path references in SOPs/templates
- Consider simplifying SOPs to behavioral baselines (large scope — may need its own phase)

**Identity & Access Hardening** (~1 session, overlaps Phase B)
- Surface identity mismatch warning to callers (not just server log) — INV-011 observation P1-T3
- Investigate whether `resolve_identity()` defensive fallback is still needed
- Prevent multiple instances of same QMS user running simultaneously
- Proxy header validation (L7)
- Identity lock TTL tuning (L8)
- Git MCP access control (Phase B)

**Agent Hub Robustness** (~1-2 sessions)
- C3: Add non-root user to Dockerfile
- H1: Close file handles in `services.py`
- H4: Hub shutdown on GUI exit
- M6, M8, M9, M10, L1, L9: Various hardening
- Docker graceful degradation for missing Docker
- Container resource limits
- Entrypoint jq error handling

**Agent Hub Observability** (~1 session)
- Unify logging across MCP chain (L2)
- Fix health check protocol mismatch (`GET` vs `POST`)
- Make identity management logging verbose
- Consider unified log format

**GUI Polish** (~1-2 sessions, overlaps Phase D)
- H6: Error toasts for failed agent actions
- M3: ResizeObserver debounce
- M4: Context menu viewport bounds
- M5: Tauri CSP hardening
- M7: API retry logic
- L3: Remove dead `useHubConnection()` hook
- L4: Configurable Hub URL
- L5, L6: Test infrastructure, lint config
- Terminal scrollback support (CR-080, in execution)
- Initial tmux terminal dimensions: `tmux new-session` in container.py:279 has no `-x`/`-y` flags, defaults to 80x24. Agent TUI tables render for wrong width until GUI resize arrives. Fix: pass initial dimensions or send resize on PTY attach.

### Blocked

| Item | Blocker |
|------|---------|
| Formalize UAT as stage gate for code CRs | Needs process maturity — wait until Phase E |
| Comments visibility restriction during active workflows | Was REQ-QRY-007, removed from RS. Needs design decision. |
| Prerequisite: commit/push pipe-dream as first EI of a CR | Needs SOP-002/004 revision — bundle with SOP revision phase |

### Deferred

| Item | Rationale |
|------|-----------|
| CAPA-003: ADD document type | QMS usage patterns not yet stable enough. Deferred via Type 2 VAR on INV-011 (Phase C). |
| Remove EFFECTIVE status / rename to APPROVED | Touches every SOP, all CLI code, all metadata. High disruption, low value now. |
| Metadata injection into viewable rendition | Nice-to-have. No current pain point. |
| "Pass with exception" test outcome type | No test execution exercising this gap. Revisit when test procedures formalized. |
| Production/test environment isolation review | Structurally addressed by submodule separation (CR-030). Residual risk low. |
| Proceduralize how to add new documents to QMS | Works well enough in practice. Formalize when pain emerges. |
| Owner-initiated withdrawal (`qms withdraw`) | Workaround exists (QA reject + checkout). Low frequency need. |
| Hide `.claude/agents/` from container mounts | Prevents sub-agent spawning conflicts. Quick win but not urgent. |
| Add `agent-hub services` deprecation notice | Cosmetic. Low priority. |
| No TU agent for Agent Hub domain | Gap identified in Phase A. Not blocking anything yet. |
| Stdio proxy for 100% MCP reliability | HTTP at 90% is workable. Revisit if reliability becomes a friction point. |

---

## 8. Gaps & Risks

**Legacy QMS debt.** Nine open documents from early iterations accumulate cognitive overhead. A cleanup pass (bulk cancel with rationale) would clear the backlog. Low effort, high clarity return.

**Container security posture.** C3 (root user) is the last critical code review finding. Combined with the resolved shell injection (C1), the container attack surface is narrowing but not fully hardened.

**Hub/GUI test coverage.** Hub backend ~5% (10 tests), GUI 0%. QMS CLI is well-tested (396 tests). The GUI polish bundle should include test infrastructure (L5, L6).

**No inter-agent communication.** Containers can't notify each other directly. Phase D.3 (notification API) addresses this, but until then, agents can only coordinate through QMS document routing and inbox polling.

**Identity lock TTL.** Container shutdown doesn't release identity locks — they expire by TTL only (5 min). Creates a window of inaccessibility after container stop. Workable but could cause friction during rapid iteration.

**No `unassign` CLI command.** Incorrect reviewer assignment requires withdraw + re-route. Minor friction, low priority.

**MCP reliability.** HTTP transport achieves ~90% connection success. The stdio proxy (deferred) would reach ~100%. Current reliability is workable but occasionally requires manual reconnect.
