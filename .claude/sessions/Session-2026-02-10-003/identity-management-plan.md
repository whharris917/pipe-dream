# Identity Management Initiative -- Refreshed Plan

## Origin
Designed in Session 2026-02-09-006 as a 5-phase plan to replace the QMS
honor-system identity model with transport-enforced authentication.

## Current Status (as of Session 2026-02-10-003)

| Phase | Title | CR | Status |
|-------|-------|----|--------|
| **1** | Transport-based identity resolution | CR-073 | CLOSED (v2.0). UAT: 4/4 pass (1 vulnerability noted). |
| **2** | Identity collision prevention | CR-074 | CLOSED (v2.0). UAT: 6/7 pass (1 not testable). |
| **2.5** | Single-authority MCP + HTTP hardening | -- | NEW. Addresses issues found during UAT. |
| **3** | Git MCP access control | -- | Pending. |
| **4** | SOP updates (process alignment) | -- | Pending. |
| **5** | Agent definition hardening | -- | Pending. |

---

## Phase 1: Transport-Based Identity Resolution -- COMPLETE

**CR-073 (CLOSED v2.0)**

Implemented `resolve_identity(ctx)` in the MCP server. HTTP transport reads
`X-QMS-Identity` header (enforced mode). Stdio transport uses `user` parameter
(trusted mode). All 20 MCP tools updated with `ctx: Context` parameter.

**Key files:**
- `qms-cli/qms_mcp/server.py` -- `resolve_identity()` function
- `qms-cli/qms_mcp/tools.py` -- `ctx: Context` on all tools
- `agent-hub/docker/scripts/mcp_proxy.py` -- header injection from `QMS_USER`

**UAT results:** 4/4 pass. P1-T4 (missing header fallback) passes per plan but
identified as a vulnerability -- see Phase 2.5.

**SDLC:** REQ-MCP-015, 9 qualification tests, SDLC-QMS-RS v9.0, SDLC-QMS-RTM v11.0.

---

## Phase 2: Identity Collision Prevention -- COMPLETE

**CR-074 (CLOSED v2.0)**

Added in-memory identity registry with TTL-based expiry. HTTP callers register
their identity (with instance UUID). Duplicate containers and cross-transport
collisions are detected and rejected with clear error messages.

**Key files:**
- `qms-cli/qms_mcp/server.py` -- `IdentityLock`, `_identity_registry`, collision logic
- `agent-hub/docker/scripts/mcp_proxy.py` -- `X-QMS-Instance` UUID header

**UAT results:** 6/7 pass. P2-T2 (container blocks host stdio) is not testable
due to the dual-process registry problem -- see Phase 2.5.

**SDLC:** REQ-MCP-016, 14 qualification tests, SDLC-QMS-RS v10.0, SDLC-QMS-RTM v12.0.

---

## Phase 2.5: Single-Authority MCP + HTTP Hardening -- NEW

**Addresses two issues discovered during Phase 1 & 2 UAT.**

### Issue 1: Dual-Process Registry Problem

**Problem:** Claude Code spawns a separate stdio MCP server subprocess for the host
session. The HTTP MCP server (port 8000) is an independent process. Each has its own
`_identity_registry`. A container registering `qa` in the HTTP server is invisible to
the stdio server, making cross-transport collision detection (P2-T2) impossible.

**Root cause:** The Phase 2 design assumed all MCP traffic flows through a single
server process. This assumption was incorrect.

**Fix: Single-authority MCP.** Route all traffic -- host and container -- through
the HTTP server on port 8000. The host MCP config changes from stdio transport to
HTTP transport, pointing to `http://localhost:8000/mcp`. One process, one registry.

**Implementation:**
- Change `.mcp.json` (host) to use HTTP transport instead of stdio for the QMS server
- The MCP proxy (`mcp_proxy.py`) already handles HTTP -- the host just needs to use it
  directly, or Claude Code's native HTTP MCP client connects to the server
- Host requests will NOT have `X-QMS-Identity` header (no proxy in the path)
- Server distinguishes host from container by header presence (see Issue 2 fix)

**Trade-off:** The HTTP server must be running for the host to do QMS operations.
This weakens the business continuity story. Mitigation: starting the server is a
single command (`start-mcp-server.sh --background`), and could be automated.

**Impact on existing tests:**
- P2-T2 becomes testable and should pass (single registry sees both transports)
- P1-T1 behavior changes: host calls go through HTTP, not stdio

### Issue 2: HTTP Header Fallback Vulnerability

**Problem:** HTTP requests without `X-QMS-Identity` header silently fall back to the
`user` parameter (P1-T4). Any HTTP caller can bypass identity enforcement by omitting
the header. This was designed for "business continuity" but in HTTP context it's a
bypass.

**Fix:** Split behavior based on header presence:
- `X-QMS-Identity` header present -> enforced mode (use header, ignore `user` param)
- `X-QMS-Identity` header absent -> trusted mode (use `user` param, no identity lock)

The distinction is no longer transport-based (HTTP vs stdio) but header-based. This
works because:
- Container proxy always injects the header -> enforced mode
- Host HTTP client never injects the header -> trusted mode
- The server doesn't need to know the transport, just whether the header is present

**Behavior matrix after fix:**

| Caller | Header Present? | Identity Source | Mode | Registry Lock? |
|--------|----------------|-----------------|------|---------------|
| Container | Yes | `X-QMS-Identity` header | Enforced | Yes (register + heartbeat) |
| Host | No | `user` parameter | Trusted | No (but checked against locks) |

**Key insight:** This preserves the original design intent (container = enforced,
host = trusted) without relying on transport type, which is no longer a reliable
discriminator after the single-authority change.

### CR Scope (Phase 2.5)

**Files to modify:**
- `qms-cli/qms_mcp/server.py` -- update `resolve_identity()` to use header-presence
  instead of transport as the mode discriminator. Remove the "HTTP request without
  X-QMS-Identity header" warning-and-fallthrough path.
- `.mcp.json` (host project root) -- change QMS MCP config from stdio to HTTP transport
- Potentially `start-mcp-server.sh` -- consider always starting in background as part
  of `agent-hub launch` or as a separate startup step

**Files NOT modified:**
- `mcp_proxy.py` -- no changes needed, already injects headers correctly
- `tools.py` -- no changes needed, `resolve_identity()` interface unchanged

**Testing:**
- Re-run P1-T4: verify headerless HTTP request is rejected (not silently degraded)
- Re-run P2-T2: verify container identity lock blocks host `user` param for same identity
- Verify host operations still work (trusted mode via `user` param, no header)
- Regression: all existing P1 and P2 tests still pass

**Depends on:** Phase 1, Phase 2 (both complete)

---

## Phase 3: Git MCP Access Control -- PENDING

**CR scope:** Restrict Git MCP server to claude-only access.

**Approach decision:** Server-side allowlist (Option A) vs. per-agent config
(Option B) vs. both. To be decided at CR drafting time.

**Option A files:**
- Git MCP server code -- add `X-QMS-Identity` header check, allowlist `claude`

**Option B files:**
- `agent-hub/agent_hub/container.py` -- generate per-agent `.mcp.json` at container
  creation (claude gets QMS + Git; others get QMS only)
- `agent-hub/docker/.mcp.json` -- becomes a template or is replaced by per-agent
  generation

**Testing:**
- Launch qa container, attempt `git_exec()` -- verify rejected (Option A) or tool
  not visible (Option B)
- Launch claude container, attempt `git_exec()` -- verify succeeds

**Depends on:** Phase 1 (for header-based identity). Independent of Phases 2/2.5.

---

## Phase 4: SOP Updates (Process Alignment) -- PENDING

**CR scope:** Update SOPs to be identity-mode-agnostic.

**Documents:**
- SOP-007 (Agent Orchestration) -- replace identity-by-declaration language with
  mode-agnostic language: "Agents shall use their assigned identity. Identity
  enforcement mechanisms are defined by deployment configuration."
- SOP-001 (Document Control) -- update Section 4 (Users and Groups) if needed to
  reflect that identity verification is infrastructure-dependent
- CLAUDE.md -- update MCP operations section to document enforced vs. trusted mode,
  deprecate explicit `user` parameter guidance

**Testing:**
- QA review of updated SOPs for internal consistency
- Verify both deployment modes work correctly under updated procedural language

**Depends on:** Phase 1 (so SOPs describe something that exists). Should also
incorporate Phase 2.5 changes if completed first.

---

## Phase 5: Agent Definition Hardening (Policy Layer) -- PENDING

**CR scope:** Strengthen agent definition files with explicit prohibitions for the
host-only (disaster recovery) scenario.

**Files:**
- `.claude/agents/qa.md` -- add explicit "do not modify files" instructions
- `.claude/agents/tu_*.md` -- same
- `.claude/agents/bu.md` -- same

**Note:** This is honor-system enforcement, acknowledged as the best available for
host-mode. `disallowedTools` frontmatter was tested and confirmed ineffective for
Task-spawned sub-agents (2026-02-09). If Claude Code adds support for Task-level
tool restrictions in the future, this phase can be revisited.

**Depends on:** Phase 4 (so agent definitions align with updated SOPs)

---

## Phase Summary

| Phase | CR Title (working) | Key Deliverable | Status | Depends On |
|-------|-------------------|-----------------|--------|------------|
| **1** | Transport-based identity resolution | `resolve_identity(ctx)` + proxy header injection | COMPLETE (CR-073) | None |
| **2** | Identity collision prevention | In-memory identity registry with TTL | COMPLETE (CR-074) | Phase 1 |
| **2.5** | Single-authority MCP + HTTP hardening | All traffic through one server; header-based mode | NEW | Phases 1, 2 |
| **3** | Git MCP access control | Claude-only git access | Pending | Phase 1 |
| **4** | SOP identity-mode-agnostic updates | Updated SOP-001, SOP-007, CLAUDE.md | Pending | Phase 1 (+2.5) |
| **5** | Agent definition hardening | Explicit policy prohibitions in agent .md files | Pending | Phase 4 |

Phases 2.5, 3, 4, and 5 can be executed in any order (all depend only on Phase 1,
which is complete). Phase 2.5 is recommended next as it closes the vulnerability
and enables P2-T2 testing.

---

## Open Questions (Updated)

1. ~~Per-agent tokens as future enhancement beyond Phase 5?~~ Deferred.
2. ~~Dual-transport server (stdio + HTTP simultaneously)?~~ Resolved: single HTTP
   server for all traffic (Phase 2.5).
3. ~~TTL duration for identity lock expiry after container crash?~~ Resolved: 5 minutes,
   confirmed adequate during UAT.
4. ~~Should inbox item claiming be part of Phase 2 or deferred?~~ Deferred beyond Phase 5.
5. Git MCP: Option A (server-side allowlist) vs Option B (per-agent config) vs both?
6. ~~Does `disallowedTools` frontmatter apply to Task-tool-spawned sub-agents?~~
   Answered: No. Tested 2026-02-09.
7. Can PreToolUse hooks identify which agent triggered a tool call?
8. **NEW:** Should `start-mcp-server.sh --background` be automated as part of
   `agent-hub launch`? This would mitigate the business continuity trade-off.
9. **NEW:** After Phase 2.5, should the mismatch warning fire for ALL tools
   (not just those with `user` param)? Currently tools without `user` param
   silently pass "claude" as default, masking mismatches.
