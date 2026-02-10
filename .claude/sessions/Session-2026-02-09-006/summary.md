# Session 2026-02-09-006 Summary

## Container-Based QMS Identity Authentication -- Design Exploration

### What Was Done

Explored the design space for replacing the QMS honor-system identity model with
transport-enforced authentication, now that agents run in isolated Docker
containers. This was a planning-only session -- no code changes or CR created.

Five distinct design concerns were identified and analyzed:
1. Identity enforcement (spoofing prevention)
2. Business continuity (graceful degradation when infrastructure is down)
3. Identity collision (duplicate instance prevention)
4. File modification privileges (least-privilege for host sub-agents)
5. Per-agent MCP server access control (Git MCP restricted to claude)

---

### The Problem

The QMS `user` parameter on all 20 MCP tools is a self-declared string. Any
caller (host or container) can claim any identity. SOP-007 prohibits
impersonation but there is no technical enforcement. A container running as `qa`
could pass `user="claude"` and vice versa.

### Key Technical Discovery

The MCP SDK (v1.26.0) preserves the full Starlette `Request` object through to
tool functions via `ctx.request_context.request`. For HTTP transport (containers),
this exposes headers. For stdio transport (host), this is `None`. This is the
natural discriminator between host and container origins.

---

### Design Concern 1: Identity Enforcement

#### Approaches Evaluated

| Approach | Verdict |
|----------|---------|
| **A: Header-based identity** | **Recommended.** Proxy injects `X-QMS-Identity` from `QMS_USER` env var. Server reads header. 3 files changed. |
| B: Per-agent endpoints | Rejected. FastMCP single-path limitation. High complexity. |
| C: Per-agent tokens | Deferred. Strongest security but over-engineered for single-host dev. Optional Phase 2. |
| D: Network-based identity | Rejected. All containers share Docker bridge gateway IP. Infeasible. |

#### Recommended Architecture

1. **Proxy side** (`mcp_proxy.py`): Reads `QMS_USER` from container environment
   (set immutably at creation by `ContainerManager`), injects `X-QMS-Identity`
   header on every HTTP request. `.mcp.json` stays identical for all containers.

2. **Server side** (`server.py`): New `resolve_identity(ctx)` function reads the
   header for HTTP requests, falls through to `user` parameter for stdio.
   Validates against known agents.

3. **Tools** (`tools.py`): All 20 tools gain `ctx: Context` parameter, call
   `resolve_identity()`. The `user` parameter is retained and used as the
   fallback identity for stdio transport.

4. **Host-side**: Stdio transport -> `user` parameter trusted (honor system).

---

### Design Concern 2: Business Continuity (Transport as Permission Toggle)

The system must not become fragile -- every component (MCP servers, Docker,
agent-hub) should not need to be running just to get work done. The solution:
the transport layer implicitly determines the permission mode. No explicit
global toggle is needed.

**Two implicit modes:**

| Mode | Transport | When | Identity Source |
|------|-----------|------|-----------------|
| **Enforced** | HTTP | Agent-hub up, containers running | `X-QMS-Identity` header (container-derived, `user` param ignored) |
| **Trusted** | Stdio | Host-only, agent-hub down | `user` parameter (honor system, Task-tool sub-agents pass their identity) |

This provides **business continuity**: when the container infrastructure is down,
the lead can run a host-only Claude Code session where sub-agents are spawned via
the Task tool with self-declared identities, falling back to the exact workflow
that exists today. When infrastructure is up, the same `resolve_identity()`
function automatically switches to enforced mode based on the transport.

**SOP implication:** SOPs should be agnostic to the permission mode. Language
like *"Agents shall use their assigned identity for all QMS operations. Identity
enforcement mechanisms are defined by the deployment configuration and are
outside the scope of this procedure."* The SOPs define the rules; the
infrastructure enforces them to whatever degree the deployment supports.

---

### Design Concern 3: Identity Collision (Duplicate Instance Prevention)

Distinct from identity *spoofing* -- this is identity *collision*. Scenario:
container infrastructure is up, QA is running in a container. Claude on the host
absentmindedly spawns a QA sub-agent via the Task tool. Both instances see the
same inbox task. One submits the review first; the other encounters an error and
goes on a troubleshooting spiral, potentially causing file conflicts.

**Core principle:** Exclusive lock on active QMS identities. When a container
holds an identity in enforced mode, no other instance of that identity should be
able to operate.

**Defense layers (complementary):**

| Layer | Mechanism | Catches |
|-------|-----------|---------|
| **1. MCP Server Identity Registry** | In-memory registry of enforced-active identities. HTTP request with `X-QMS-Identity: qa` registers `qa` as active. Stdio request with `user="qa"` checks registry and is rejected with clear error if active. TTL-based expiry for crash recovery. | Primary gate. Prevents duplicate instance from executing any QMS operation. |
| **2. Agent Hub container registry** | Hub knows which agents are running. Orchestrator checks hub status before spawning sub-agents for same role. | Soft enforcement. Catches the common case at the orchestrator level. |
| **3. QMS document-level locking** | Existing checkout system prevents two users with same identity from conflicting on same document. | Existing safety net for document-level conflicts. |
| **4. Inbox item claiming** | When agent begins processing an inbox item, mark as "claimed" in QMS metadata. Second instance sees "already in progress." | Prevents duplicate task processing specifically. |

**Key design detail for Layer 1:** The MCP server runs with `stateless_http=True`
(no server-side session tracking). The identity registry tracks *identity locks*,
not *sessions* -- a distinct concept that coexists with HTTP statelessness.

**Error message design:** When a trusted-mode request is rejected due to an active
enforced session, the error must be unambiguous and terminal:
*"IDENTITY LOCKED: 'qa' is active in enforced mode (container). Request rejected."*
This prevents the rejected sub-agent from interpreting the failure as a transient
error and attempting troubleshooting.

---

### Design Concern 4: File Modification Privileges (Host Sub-Agent Restrictions)

When sub-agents (qa, tu_ui, etc.) are spawned on the host via the Task tool,
they have full file system access -- Edit, Write, Bash, and all other tools.
In container mode this is constrained by read-only mounts, but on the host there
is no such isolation. Only `claude` (the orchestrator) should modify files on
the host. Sub-agents exist to fulfill QMS roles (review, approve), not to write
code or modify the file system.

**Guiding principle:** The system is in a vulnerable state when sub-agents operate
outside containers. Container mode is the standard; host-only mode is disaster
recovery. Even claude on the host presents residual risk (could write a script
to modify QMS files directly), but this must be pragmatically accepted for
business continuity.

**Enforcement by deployment mode:**

| Mode | File modification constraint | Enforcement type |
|------|----------------------------|------------------|
| **Container (standard)** | Only `claude`'s workspace writable | Technical (read-only mount) |
| **Host (disaster recovery)** | Only `claude` should modify files | Policy + platform mechanisms |

#### Potential Host-Side Enforcement Mechanisms

**1. `disallowedTools` in agent frontmatter (tested -- does NOT work)**

Claude Code documents `tools` and `disallowedTools` fields in `.claude/agents/`
frontmatter. We tested this empirically in this session:

- Added `disallowedTools: Edit, Write, NotebookEdit` to `.claude/agents/qa.md`
- Spawned a qa sub-agent via `Task(subagent_type="qa")`
- Asked it to write a test file
- **Result: the write succeeded.** `disallowedTools` has no effect on
  Task-spawned sub-agents.

`disallowedTools` applies only to agents running as the main thread via
`claude --agent qa`, not to sub-agents spawned dynamically mid-session.
**This mechanism is confirmed ineffective for our use case.**

**2. PreToolUse hooks (documented but limited)**

Claude Code supports hooks that fire before tool execution and can block via
exit code 2:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command", "command": "./scripts/block-non-claude.sh" }]
    }]
  }
}
```

**Limitation:** There is no documented mechanism for the hook to identify *which
agent* triggered the tool call. The hook fires at the session level. A hook that
blocks all Edit/Write calls would also block `claude` (the orchestrator). To be
useful, the hook would need a way to distinguish the orchestrator from sub-agents
-- which is not currently exposed in the hook context.

**3. Agent definition instructions (policy, honor system)**

The agent `.md` files already instruct sub-agents on their role. Adding explicit
prohibitions like "You must not use Edit, Write, or Bash to modify files" is
straightforward but is honor-system enforcement -- the same limitation as the
current `user` parameter.

**4. Container isolation (the real answer)**

The definitive solution. In containers, `/pipe-dream` is read-only. Sub-agents
physically cannot modify files outside their workspace. This is why the
trajectory is toward container mode as the standard deployment.

#### Assessment

For the host-only (disaster recovery) scenario, enforcement is layered:
- **Soft:** Agent definition instructions (immediate, honor-based)
- ~~**Medium:** `disallowedTools` frontmatter~~ **Confirmed ineffective** for
  Task-spawned sub-agents (tested 2026-02-09)
- **Medium:** PreToolUse hooks (works if agent identity can be inferred)
- **Hard:** Container isolation (the production answer)

The honest conclusion: host-mode sub-agent restrictions are inherently weaker
than container isolation. This is an accepted trade-off for business continuity.
The investment should go toward making container mode reliable and standard,
rather than trying to perfectly replicate container-level isolation on the host.

---

### Design Concern 5: Per-Agent MCP Server Access Control

Currently all containers share an identical `.mcp.json` that includes both the
QMS MCP server (port 8000) and the Git MCP server (port 8001). All agents can
call `git_exec()`. Only `claude` should have Git MCP access -- other agents have
no need to execute git commands.

**Two approaches:**

| Approach | How | Trade-off |
|----------|-----|-----------|
| **A: Server-side allowlist** | Git MCP server reads `X-QMS-Identity` header (already injected by proxy) and rejects non-`claude` identities | Simple, consistent with QMS identity pattern. Tool exists but is rejected. |
| **B: Per-agent `.mcp.json`** | `ContainerManager` generates per-agent config at container creation. Non-claude agents omit the git server entirely. | Stronger (tool is invisible, not just rejected). Breaks "identical config" simplicity. |

Option A is simpler and consistent with the identity enforcement pattern already
designed for the QMS MCP server. Option B is more secure (you can't call what
you can't see) but requires per-agent config generation in `ContainerManager`.

Both are straightforward to implement. Option B could be combined with Option A
for defense in depth.

---

### What This Solves (All Five Concerns Combined)

- Impersonation via MCP (identity derived from container, not parameter)
- Host privilege escalation when containers are running
- Separation of duties (QA reviews only from QA container in enforced mode)
- Business continuity (graceful fallback to honor system when infrastructure is down)
- Duplicate instance prevention (exclusive identity lock when container is active)
- Least-privilege for host sub-agents (policy + platform mechanisms, accepted
  residual risk)
- Git MCP access restricted to claude (server-side or config-based)

### What This Intentionally Doesn't Solve

- CLI bypass from host (human operator has ultimate authority by design)
- Per-agent cryptographic tokens (deferred to optional Phase 2)
- Perfect host-mode isolation (accepted trade-off; container mode is the answer)

---

## Phased Implementation Plan

Each phase is a separate CR, building up functionality incrementally.

### Phase 1: Transport-Based Identity Resolution (Foundation)

**CR scope:** Core identity enforcement + business continuity fallback.

**Files:**
- `agent-hub/docker/scripts/mcp_proxy.py` -- inject `X-QMS-Identity` from
  `QMS_USER` env var
- `qms-cli/qms_mcp/server.py` -- add `resolve_identity(ctx)` function
- `qms-cli/qms_mcp/tools.py` -- add `ctx: Context` to all 20 tools, call
  `resolve_identity()`

**Behavior:**
- HTTP transport: identity from `X-QMS-Identity` header (enforced mode)
- Stdio transport: identity from `user` parameter (trusted mode / fallback)
- `user` parameter retained in signatures, ignored for HTTP, respected for stdio
- Mismatch between `user` param and resolved identity logs a warning

**Testing:**
- Container: verify identity resolves from header, not parameter
- Host: verify `user` parameter still works (business continuity)
- Cross-identity: verify container agent cannot impersonate another identity

**Prerequisite:** Docker image rebuild (`docker-compose build --no-cache`)

---

### Phase 2: Identity Collision Prevention

**CR scope:** Exclusive identity locks to prevent duplicate instances.

**Files:**
- `qms-cli/qms_mcp/server.py` -- add in-memory identity registry with TTL

**Behavior:**
- When HTTP request arrives with `X-QMS-Identity: qa`, register `qa` as
  enforced-active (with timestamp)
- When stdio request arrives with `user="qa"`, check registry; reject if
  enforced-active
- TTL-based expiry (configurable, e.g. 5 minutes) for crash recovery
- Clear, terminal error message:
  *"IDENTITY LOCKED: 'qa' is active in enforced mode (container). Request rejected."*

**Testing:**
- Launch qa container, then spawn qa sub-agent on host via Task tool
- Verify sub-agent's QMS operations are rejected with lock message
- Kill container, wait for TTL, verify lock expires and sub-agent can operate

**Depends on:** Phase 1

---

### Phase 3: Git MCP Access Control

**CR scope:** Restrict Git MCP server to claude-only access.

**Approach decision:** Server-side allowlist (Option A) vs. per-agent config
(Option B) vs. both. To be decided at CR drafting time.

**Option A files:**
- Git MCP server code -- add `X-QMS-Identity` header check, allowlist `claude`

**Option B files:**
- `agent-hub/agent_hub/container.py` -- generate per-agent `.mcp.json` at
  container creation (claude gets QMS + Git; others get QMS only)
- `agent-hub/docker/.mcp.json` -- becomes a template or is replaced by
  per-agent generation

**Testing:**
- Launch qa container, attempt `git_exec()` -- verify rejected (Option A) or
  tool not visible (Option B)
- Launch claude container, attempt `git_exec()` -- verify succeeds

**Depends on:** Phase 1 (for header-based identity)

---

### Phase 4: SOP Updates (Process Alignment)

**CR scope:** Update SOPs to be identity-mode-agnostic.

**Documents:**
- SOP-007 (Agent Orchestration) -- replace identity-by-declaration language with
  mode-agnostic language: *"Agents shall use their assigned identity. Identity
  enforcement mechanisms are defined by deployment configuration."*
- SOP-001 (Document Control) -- update Section 4 (Users and Groups) if needed
  to reflect that identity verification is infrastructure-dependent
- CLAUDE.md -- update MCP operations section to document enforced vs. trusted
  mode, deprecate explicit `user` parameter guidance

**Testing:**
- QA review of updated SOPs for internal consistency
- Verify both deployment modes (container and host-only) work correctly under
  the updated procedural language

**Depends on:** Phase 1 (so SOPs describe something that exists)

---

### Phase 5: Agent Definition Hardening (Policy Layer)

**CR scope:** Strengthen agent definition files with explicit prohibitions for
the host-only (disaster recovery) scenario.

**Files:**
- `.claude/agents/qa.md` -- add explicit "do not modify files" instructions
- `.claude/agents/tu_*.md` -- same
- `.claude/agents/bu.md` -- same

**Note:** This is honor-system enforcement, acknowledged as the best available
for host-mode. `disallowedTools` frontmatter was tested and confirmed ineffective
for Task-spawned sub-agents (2026-02-09). If Claude Code adds support for
Task-level tool restrictions in the future, this phase can be revisited.

**Depends on:** Phase 4 (so agent definitions align with updated SOPs)

---

### Phase Summary

| Phase | CR Title (working) | Key Deliverable | Depends On |
|-------|-------------------|-----------------|------------|
| **1** | Transport-based identity resolution | `resolve_identity(ctx)` + proxy header injection | None |
| **2** | Identity collision prevention | In-memory identity registry with TTL | Phase 1 |
| **3** | Git MCP access control | Claude-only git access | Phase 1 |
| **4** | SOP identity-mode-agnostic updates | Updated SOP-001, SOP-007, CLAUDE.md | Phase 1 |
| **5** | Agent definition hardening | Explicit policy prohibitions in agent .md files | Phase 4 |

Phases 2, 3, 4, and 5 are independent of each other (all depend only on Phase 1)
and could be executed in any order or in parallel.

---

### Open Questions

1. Per-agent tokens as future enhancement beyond Phase 5?
2. Dual-transport server (stdio + HTTP simultaneously)?
3. TTL duration for identity lock expiry after container crash?
4. Should inbox item claiming (Concern 3, Layer 4) be part of Phase 2 or deferred?
5. Git MCP: Option A (server-side allowlist) vs Option B (per-agent config) vs both?
6. ~~Does `disallowedTools` frontmatter apply to Task-tool-spawned sub-agents?~~
   **Answered: No.** Tested 2026-02-09. Only applies to `claude --agent` main thread.
7. Can PreToolUse hooks identify which agent triggered a tool call?

### Artifacts

- Full plan: `.claude/plans/keen-giggling-giraffe.md` (covers Concern 1 only;
  Concerns 2-5 and phased implementation are documented in this summary)
