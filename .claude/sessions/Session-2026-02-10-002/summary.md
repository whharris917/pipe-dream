# Session 2026-02-10-002 Summary

## Objective
Implement Phase 2 of the identity management plan: Identity Collision Prevention (CR-074).

## Completed
- **CR-074 CLOSED**: Identity collision prevention (Phase 2)
  - Added in-memory identity registry with TTL-based expiry to MCP server
  - Scenario A: HTTP-enforced identity blocks stdio requests for same identity
  - Scenario B: Duplicate containers detected via X-QMS-Instance header (UUID per proxy lifecycle)
  - 14 new qualification tests for REQ-MCP-016
  - 392/392 tests passing, CI verified (run 21881322045)
  - PR #10 merged to qms-cli main

## SDLC Documents Updated
- SDLC-QMS-RS v10.0 (EFFECTIVE) - Added REQ-MCP-016
- SDLC-QMS-RTM v12.0 (EFFECTIVE) - Full traceability, qualified baseline at commit 78ec519

## Key Files Modified
- `qms-cli/qms_mcp/server.py` - IdentityCollisionError, IdentityLock, registry, collision logic
- `agent-hub/docker/scripts/mcp_proxy.py` - UUID instance injection, X-QMS-Instance header
- `qms-cli/tests/qualification/test_mcp.py` - 14 tests + autouse cleanup fixture

## 5-Phase Plan Progress
- Phase 1: COMPLETE (CR-073, Session 2026-02-10-001)
- Phase 2: COMPLETE (CR-074, this session)
- Phase 3: Container identity wiring (pending)
- Phase 4: Agent-hub launch integration (pending)
- Phase 5: User acceptance testing (pending)

## Next Steps: User Acceptance / Integration Testing (Phases 1 & 2)

The next session should perform UAT and integration testing to validate that both
CR-073 (transport-based identity resolution) and CR-074 (identity collision prevention)
work correctly in a live environment. This covers Phases 1 and 2 end-to-end.

### Prerequisites
1. Rebuild the Docker image to pick up the updated `mcp_proxy.py` (X-QMS-Instance header):
   ```bash
   cd agent-hub/docker && docker-compose build --no-cache
   ```
2. Ensure the QMS MCP server on the host is running the latest `qms-cli` (submodule at fc26476):
   ```bash
   cd agent-hub/docker/scripts && ./start-mcp-server.sh
   ```

### Phase 1 Tests (CR-073: Transport-Based Identity Resolution)

| Test | Description | How to Verify |
|------|-------------|---------------|
| P1-T1 | Host stdio uses `user` parameter | On host, call a QMS MCP tool with `user="tu_ui"`. Verify audit trail shows `tu_ui` as performer. |
| P1-T2 | Container HTTP uses X-QMS-Identity header | Launch a container with `QMS_USER=qa`. Call a QMS MCP tool (e.g., `qms_inbox`). Verify the server log shows `Identity: qa (from QMS_USER)` and the tool operates as `qa`. |
| P1-T3 | Container identity overrides `user` param | From inside the container, call a tool with `user="claude"`. Verify the server log warns about mismatch and the enforced identity (from header) is used, not the parameter. |
| P1-T4 | Missing header falls back to param | Make an HTTP request without X-QMS-Identity header. Verify warning is logged and `user` param is used as fallback. |

### Phase 2 Tests (CR-074: Identity Collision Prevention)

| Test | Description | How to Verify |
|------|-------------|---------------|
| P2-T1 | Container locks identity | Launch container with `QMS_USER=qa`. Make a QMS call. Verify server log shows `Identity 'qa' registered (instance XXXXXXXX)`. |
| P2-T2 | Scenario A: Container blocks host | With `qa` container running (identity registered), call a QMS tool on the host stdio with `user="qa"`. Verify `IdentityCollisionError` with "IDENTITY LOCKED" message. |
| P2-T3 | Scenario B: Duplicate container rejected | With `qa` container running, attempt to start a second container with `QMS_USER=qa`. Verify the second container's MCP calls are rejected with "IDENTITY LOCKED" and "duplicate container" message. |
| P2-T4 | Different identities coexist | With `qa` container running, launch a `tu_ui` container. Verify both can operate simultaneously without collision. |
| P2-T5 | TTL expiry recovery | Stop the `qa` container. Wait 5+ minutes (or temporarily reduce TTL for testing). Verify host stdio can then use `user="qa"` successfully. |
| P2-T6 | Same container heartbeat | From a running container, make multiple sequential MCP calls. Verify each refreshes the heartbeat (server log shows same instance ID) without collision. |
| P2-T7 | X-QMS-Instance header present | Check container proxy stderr for `Instance: XXXXXXXX` log line on startup, confirming UUID generation. |

### Acceptance Criteria
- All P1 and P2 tests pass
- No regressions in normal QMS operations (inbox, status, create, checkout, checkin)
- Error messages for collision scenarios are clear and actionable
- Server logs provide sufficient diagnostic information for troubleshooting
