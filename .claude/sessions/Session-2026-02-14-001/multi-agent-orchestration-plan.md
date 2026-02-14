# Refined Project Plan: Multi-Agent Orchestration

*Session-2026-02-14-001 — Successor to Session-2026-02-06-004*

---

## Context

This plan charts the path from the current state to the stated goal: **multi-agent container-based QMS workflows with identity enforcement, MCP-based command execution, all controllable from a central GUI.**

The original plan (written earlier this session) incorrectly characterized several components as "never tested." A thorough deep-dive into all session notes, CR execution evidence, and UAT records reveals that substantially more integration testing was performed than initially credited. This refined plan corrects the record and focuses effort on the genuine remaining gaps.

---

## Part 1: What Has Actually Been Tested (Evidence-Based)

### Hub CLI — UAT 7/7 PASS (Session 2026-02-09-001)

| Test | Command | Result |
|------|---------|--------|
| T1 | `agent-hub services` (cold) | PASS — all DOWN |
| T2 | `agent-hub launch claude` | PASS — full infrastructure startup |
| T3 | `agent-hub services` (warm) | PASS — all UP |
| T4 | `agent-hub attach claude` | PASS — reconnect works |
| T5 | `agent-hub stop-all` | PASS — clean teardown |
| T6 | `agent-hub services` (post-teardown) | PASS — all DOWN |
| T7 | `agent-hub stop-all -y` (idempotent) | PASS — "nothing to stop" |

**Gap found:** Orphaned containers when user exits Claude Code instead of detaching tmux. Addressed by CR-070 (session health detection, stale state).

### WebSocket Protocol — 10/10 PASS (Session 2026-02-08-003)

`agent-hub/tests/test_websocket_uat.py`: connect, subscribe, unsubscribe, input, resize, error handling, broadcast agent_state, broadcast inbox_change — all via FastAPI TestClient.

### GUI — All Checks PASS (Session 2026-02-08-004)

CR-068 UAT confirmed: connection status display, agent list rendering, terminal I/O, tab management, terminal resize. This was the initial GUI scaffold test.

**Caveat:** This test was performed BEFORE:
- CR-069 (file consolidation: `agent-gui/` -> `agent-hub/gui/`)
- CR-070 through CR-076 (session health, services consolidation, identity management)
- The GUI has not been tested since the file move or identity system deployment.

### Identity Management — UAT 7/7 PASS (Session 2026-02-10-004)

| Test | Scenario | Result |
|------|----------|--------|
| P1-T1 | Host trusted mode via HTTP | PASS |
| P1-T2 | Container enforced mode | PASS |
| P1-T4 | HTTP without header (explicit trusted) | PASS |
| P2-T1 | Container locks identity | PASS |
| P2-T2 | Cross-transport collision detection | PASS |
| P2-T3 | Duplicate container blocked | PASS |
| P2-T4 | Different identities coexist | PASS |

**Observation logged (P1-T3):** Silent identity override when container passes wrong `user` param. CR-076 later hardened this to raise ValueError on mismatch.

### Unit Test Suite — 396 Tests, All CI-Verified

| CR | Tests | CI Run |
|----|-------|--------|
| CR-073 | 378 | 21878115349 |
| CR-074 | 392 | 21881322045 |
| CR-075 | 393 | 21886071685 |
| CR-076 | 396 | 21891224329 |

---

## Part 2: What Is Genuinely Untested (The Real Gaps)

### Gap 1: GUI Post-Consolidation (Medium Risk)

The GUI was tested at `agent-gui/` on Feb 8. It was moved to `agent-hub/gui/` on Feb 9 (CR-069). It has **not been run since the move**. Possible issues:
- Import paths may have changed
- Tauri config may reference old paths
- npm dependencies may need refresh after weeks dormant
- Rust toolchain may need updating (Tauri v2 dependency)

**Risk level:** Medium. The code was moved, not rewritten. But build toolchain rot is common.

### Gap 2: GUI + Identity Integration (Low Risk)

The GUI was tested before identity management existed. The identity system operates at the MCP server layer (HTTP headers), not at the GUI/Hub layer. The GUI communicates with the Hub via REST/WebSocket, not directly with MCP. Therefore identity enforcement should be transparent to the GUI.

**Risk level:** Low. Identity enforcement is below the GUI's abstraction layer.

### Gap 3: Hub Docker SDK -> Identity Headers (Medium Risk)

Identity UAT used containers started via `docker-compose` and `agent-hub launch`. The Hub's `ContainerManager._create_container()` (container.py line 205) sets `QMS_USER` in the container environment. The proxy reads `QMS_USER` and injects `X-QMS-Identity`. This chain was tested individually but not specifically validated when Hub starts containers programmatically via Docker SDK.

**Risk level:** Medium. The Hub sets the same env var that docker-compose does, but the Docker SDK path hasn't been explicitly verified.

### Gap 4: Multi-Agent QMS Workflow (High Risk — Never Attempted)

No session has ever run multiple agents simultaneously performing a real QMS cycle (create CR -> route -> review -> approve -> close). This is the ultimate integration test and the project's success criterion.

**Risk level:** High. This exercises everything simultaneously: Hub, containers, identity, MCP, QMS CLI, inbox monitoring, notifications.

### Gap 5: GUI Placeholder Components (Known — Requires New Code)

- `McpHealth.tsx` — placeholder, no Hub endpoint
- `QmsStatus.tsx` — placeholder, no Hub endpoint
- No `POST /api/agents/{id}/notify` endpoint

### Gap 6: Git MCP Identity (Known — Requires New Code)

`agent-hub/mcp-servers/git_mcp/server.py` has no identity resolution. Any container can execute git commands.

### Gap 7: INV-011 CAPA-003 (Known — Requires QMS Process)

CAPA-003 (ADD document type) is deferred. Type 2 VAR recommended to allow INV-011 closure.

---

## Part 3: The Forward Plan

### Phase A: Regression Verification & Integration Testing (Priority 1)

**Goal:** Confirm nothing regressed, then validate the genuine gaps.

**A.1. Infrastructure Health Check (~15 min)**

Quick smoke test of already-validated paths. Not a full re-test — just confirming things still work after weeks dormant.

1. Verify Docker image exists (rebuild with `--no-cache` if stale)
2. Start MCP servers: `start-mcp-server.sh --background` and `start-git-mcp.sh`
3. `agent-hub services` — confirm services come up
4. `agent-hub launch claude` — confirm container starts, Claude Code ready
5. Verify MCP connectivity from container (quick `qms_inbox` call)
6. `agent-hub stop-all -y` — clean shutdown

**If anything fails:** Fix inline. These are regression bugs, not new features.

**A.2. GUI Revalidation (~30 min)**

The GUI hasn't been run since Feb 8, before the CR-069 file move. This is a targeted revalidation, not a from-scratch test.

1. `cd agent-hub/gui && npm install` (refresh dependencies)
2. `npm run tauri dev` — does it build and launch?
3. Verify Hub auto-bootstrap (ensureHub.ts -> spawn_hub Tauri command)
4. Verify agent list loads in sidebar
5. Start an agent from the sidebar -> terminal tab opens
6. Type in terminal -> verify input reaches agent
7. Stop agent -> verify state updates in sidebar

**If GUI doesn't build:** This becomes the first fix priority. Check Tauri config paths, Rust toolchain, npm dependencies.

**A.3. Hub Docker SDK -> Identity Verification (~15 min)**

Targeted test of the one identity path not yet verified.

1. Start Hub and MCP servers
2. `agent-hub launch qa` (Hub starts container via Docker SDK)
3. From QA container terminal: `qms_inbox(user="qa")` — verify X-QMS-Identity header arrives at MCP server
4. From host: `qms_inbox(user="qa")` — verify identity collision detected (lock held by container)
5. Stop QA container — verify lock expires

**A.4. Multi-Agent QMS Workflow (~60 min)**

The integration test that has never been attempted. This is the project's success criterion.

1. Start Hub with MCP servers running
2. Launch `claude` and `qa` containers (via Hub CLI or GUI)
3. From claude's terminal:
   - Create a test CR: `qms_create("CR", "Integration Test CR")`
   - Draft content, checkin, route for review
4. Verify QA's inbox badge updates (in GUI sidebar or via `qms_inbox`)
5. From QA's terminal:
   - Review the CR: `qms_review("CR-XXX", "recommend", comment="LGTM")`
6. From claude's terminal:
   - Route for approval
7. From QA's terminal:
   - Approve: `qms_approve("CR-XXX")`
8. From claude's terminal:
   - Release, execute, route post-review
9. QA post-reviews and post-approves
10. Claude closes the CR

**If this works:** The project's primary success criterion is met.
**If this fails:** Document what broke. Each failure narrows the integration gap.

### Phase B: Git MCP Access Control (Priority 2)

**Goal:** Restrict `git_exec` to claude-only. Closes Phase 3 of the identity plan.

**Approach:** The Git MCP server runs on HTTP (:8001). The container proxy already injects `X-QMS-Identity` headers to both :8000 (QMS) and :8001 (Git). Add identity resolution to `git_mcp/server.py`.

**Implementation (single CR):**

1. **Modify `agent-hub/mcp-servers/git_mcp/server.py`:**
   - Read `X-QMS-Identity` header from HTTP request context
   - Check against allowlist (initially: `["claude", "lead"]`)
   - Reject with clear error message if identity not in allowlist
   - Trusted mode (no header) allowed — host access unaffected

2. **Update SDLC-QMS-RS** — add REQ-MCP-017: Git MCP access control
3. **Update SDLC-QMS-RTM** — add test coverage
4. **Add tests** — identity allowlist, rejection, trusted-mode passthrough

**Key file:** `agent-hub/mcp-servers/git_mcp/server.py` (243 lines, currently no identity logic)

### Phase C: Close INV-011 (Priority 2, parallel with B)

**Goal:** Resolve INV-011 so it can proceed through post-review to CLOSED.

**Current state:** IN_EXECUTION v1.2. CAPA-001 PASS, CAPA-002 PASS, CAPA-003 DEFERRED.

**Recommendation:** Type 2 VAR on CAPA-003 (ADD document type).

**Rationale:**
- CAPA-003 is **preventive**, not corrective
- Corrective actions (CAPA-001, CAPA-002) are already PASS
- ADD document type is a QMS infrastructure improvement, not a fix for the deviation
- Already tracked in TO_DO_LIST as future enhancement
- Type 2 VAR allows INV-011 closure without CAPA-003 completion (per SOP-004 Section 9A.2)

**Steps:**
1. Checkout INV-011, document CAPA-003 as Fail with VAR attachment
2. Create `INV-011-VAR-001` (Type 2) documenting deferral rationale
3. Route VAR for pre-review/pre-approval (Type 2: pre-approval sufficient)
4. Route INV-011 for post-review
5. QA post-reviews and post-approves
6. Close INV-011

### Phase D: GUI Enhancement — Operational Awareness (Priority 3)

**Goal:** Replace placeholder sidebar components with live operational data.

**D.1. MCP Health Monitoring**

| Layer | Change |
|-------|--------|
| Hub | Add `GET /api/mcp/health` endpoint. Hub pings :8000/mcp and :8001/mcp periodically. |
| Hub | Broadcast `mcp_health_changed` events via existing WebSocket broadcaster. |
| GUI | Implement `McpHealth.tsx` — green/red dots for QMS MCP and Git MCP. |

**Key files:**
- `agent-hub/agent_hub/api/routes.py` — new endpoint
- `agent-hub/agent_hub/hub.py` — periodic health check task
- `agent-hub/gui/src/components/Sidebar/McpHealth.tsx` — replace placeholder
- `agent-hub/gui/src/hooks/useAgentStore.ts` — add MCP health state

**D.2. QMS Status Panel**

| Layer | Change |
|-------|--------|
| Hub | Add `GET /api/qms/status` endpoint. Hub queries QMS MCP for active docs. |
| GUI | Implement `QmsStatus.tsx` — list active documents with status and owner. |

**Key files:**
- `agent-hub/agent_hub/api/routes.py` — new endpoint
- `agent-hub/gui/src/components/Sidebar/QmsStatus.tsx` — replace placeholder

**D.3. Notification Injection API**

| Layer | Change |
|-------|--------|
| Hub | Add `POST /api/agents/{id}/notify` endpoint using existing `notifier.py`. |
| GUI | Optional: "Send Message" context menu option in AgentItem.tsx. |

**Key files:**
- `agent-hub/agent_hub/api/routes.py` — new endpoint (trivial: calls existing `inject_notification()`)
- `agent-hub/agent_hub/notifier.py` — already exists, no changes needed

**D.4. Identity Status Visibility**

- Show enforced/trusted mode indicator per agent in sidebar
- Surface identity mismatch warnings from MCP server to GUI
- Requires Hub to poll or receive identity events from MCP server

### Phase E: Process Alignment (Priority 4)

**E.1. SOP Updates**
- SOP-007: Replace identity-by-declaration with mode-agnostic language
- SOP-001: Update Section 4 for infrastructure-dependent identity verification
- CLAUDE.md: Document enforced vs. trusted mode

**E.2. Agent Definition Hardening**
- Add "do not modify files" prohibitions to qa.md, tu_*.md, bu.md
- Honor-system enforcement; container isolation is the real control

**E.3. TO_DO_LIST Items**
- Formalize UAT as stage gate for code CRs
- Surface identity mismatch warnings to callers
- Investigate `resolve_identity()` defensive fallback necessity

---

## Part 4: Dependencies and Execution Order

```
Phase A: Regression + Integration (MUST BE FIRST)
    A.1 Infrastructure Health Check     (~15 min)
    A.2 GUI Revalidation                (~30 min)
    A.3 Hub->Identity Verification      (~15 min)
    A.4 Multi-Agent QMS Workflow         (~60 min)
    |
    +---> Phase B: Git Access Control     } Can run in parallel
    |                                     }
    +---> Phase C: Close INV-011          }
    |
    +---> Phase D: GUI Enhancement
              |
              +---> Phase E: Process Alignment (can overlap with D)
```

**Estimated effort:**
- Phase A: 1-2 sessions (mostly human-driven testing)
- Phase B: 1 session (code + CR + qualification)
- Phase C: 1 session (QMS workflow)
- Phase D: 2-3 sessions (4 sub-phases, each a CR)
- Phase E: 1-2 sessions (SOP updates through QMS)
- **Total: 5-8 sessions** (reduced from original 6-9 estimate by eliminating redundant testing)

---

## Part 5: Success Criteria

The project reaches "done" when:

1. **Multi-agent QMS workflow completes** (Phase A.4): Create CR -> review -> approve -> execute -> close, with multiple agents, all visible in one interface.

2. **GUI is the primary control interface** (Phase D): Agent list, terminal tabs, MCP health, QMS status, inbox badges — all live, all in one window.

3. **Identity enforcement is end-to-end** (Phase A.3 + B): Container MCP calls resolve identity from headers. Git MCP restricted to claude. Collisions detected.

4. **INV-011 is CLOSED** (Phase C): Corrective actions verified, CAPA-003 resolved via Type 2 VAR.

5. **SOPs reflect reality** (Phase E): SOP-007 and SOP-001 describe the identity architecture accurately.

---

## Part 6: Key Files

| File | Relevance |
|------|-----------|
| `agent-hub/agent_hub/container.py:205` | Sets `QMS_USER` env. Hub->Identity integration point. |
| `agent-hub/agent_hub/api/routes.py` | Hub REST API. Phase D adds MCP health, QMS status, notify endpoints. |
| `agent-hub/agent_hub/hub.py` | Core Hub. Phase D adds MCP health check task. |
| `agent-hub/agent_hub/notifier.py` | Existing `inject_notification()`. Phase D.3 wraps as API endpoint. |
| `agent-hub/mcp-servers/git_mcp/server.py` | Phase B adds identity + allowlist. |
| `agent-hub/gui/src/components/Sidebar/McpHealth.tsx` | Placeholder -> Phase D.1. |
| `agent-hub/gui/src/components/Sidebar/QmsStatus.tsx` | Placeholder -> Phase D.2. |
| `agent-hub/gui/src/hooks/useHubConnection.ts` | WebSocket singleton. Phase D adds new event types. |
| `agent-hub/gui/src/hooks/useAgentStore.ts` | Zustand store. Phase D adds MCP health state. |
| `agent-hub/gui/src/ensureHub.ts` | Hub auto-bootstrap. Phase A.2 validates. |
| `qms-cli/qms_mcp/server.py` | `resolve_identity()` at line 143. Identity foundation. |
| `agent-hub/docker/scripts/mcp_proxy.py` | Stdio proxy. Injects X-QMS-Identity headers. |
| `agent-hub/tests/test_websocket_uat.py` | 10 existing protocol tests. |
| `QMS/SOP/SOP-007.md` | Phase E updates. |
| `QMS/SOP/SOP-001.md` | Phase E updates. |
| `QMS/INV/INV-011/INV-011.md` | Phase C resolves. |

---

## Part 7: Prior UAT Evidence Registry

For traceability, here is the complete record of prior integration testing:

| Date | Session | Scope | Result | Evidence |
|------|---------|-------|--------|----------|
| Feb 8 | 2026-02-08-003 | WebSocket protocol (10 tests) | 10/10 PASS | `test_websocket_uat.py` |
| Feb 8 | 2026-02-08-004 | GUI scaffold (connection, agents, terminal, tabs, resize) | All PASS | CR-068 summary |
| Feb 9 | 2026-02-09-001 | Hub CLI (launch, services, attach, stop-all) | 7/7 PASS | `hub-uat.md` |
| Feb 10 | 2026-02-10-004 | Identity (transport, collision, coexistence) | 7/7 PASS | CR-075 UAT summary |
| Feb 10 | 2026-02-10-004 | MCP single-authority + CAPA-001/002 | PASS | INV-011 execution |
