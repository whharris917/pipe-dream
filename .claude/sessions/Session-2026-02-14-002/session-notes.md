# Session-2026-02-14-002 Notes

## Summary

Execution session spanning two phases: CR-077 (Pre-Integration Hardening) and Phase A integration testing (A.1-A.3 complete, A.4 pending). Two infrastructure bugs fixed via CR-078. Identity enforcement verified end-to-end.

### Part 1: CR-077 — Pre-Integration Hardening

- Initialized session, read previous session notes (2026-02-14-001), read all SOPs
- Checked inbox (empty)
- Proposed bundling code review findings C1, C2, H2, H3 into a single CR — Lead approved
- Created CR-077: "Pre-Integration Hardening: Security and Resilience Fixes"
- Drafted CR with full content (sections 1-12), checked in, routed for pre-review
- QA pre-reviewed and recommended; QA attempted to assign TU-UI but Lead rejected — TU-UI is scoped to Flow State UI, not Agent Hub GUI (Tauri/React)
- Withdrew CR-077, re-routed without TU assignment
- QA re-reviewed (RECOMMEND), pre-approved (v1.0)
- Released for execution, implemented all four fixes:
  - **EI-1 (C1):** Eliminated shell injection in Git MCP — `shell=True` replaced with `shlex.split()` + `shell=False`, shell metacharacter blocking added, chain parsing (`&&`/`||`) implemented
  - **EI-2 (C2):** CORS origins restricted from `["*"]` to three GUI-specific origins
  - **EI-3 (H2):** `ensureHub()` return value checked; failure sets connection status to `"error"`
  - **EI-4 (H3):** React ErrorBoundary created and wraps root component in `main.tsx`
- QA post-reviewed (RECOMMEND), post-approved (v2.0)
- Closed CR-077, committed at `5de4321`

### Part 2: Phase A Integration Testing (CR-078)

Created CR-078 ("Phase A Integration Testing: Infrastructure Fixes") as a lightweight emergent-fix CR — empty execution table at pre-approval, changes documented as discovered.

#### A.1 Infrastructure Health Check — PASS

- Docker image rebuilt with `--no-cache`
- `agent-hub launch claude` cascaded all services (MCP servers, Hub, container)
- **Bug found (EI-1):** Container crashed with `ENOENT` on `/claude-config/debug/` — entrypoint.sh deleted the directory during cleanup but Claude Code expects it. Fixed by adding `mkdir -p /claude-config/debug` after cleanup.
- Image rebuilt, relaunched. Container MCP connectivity verified (qms_inbox succeeded, identity `claude` registered in server log)
- Clean shutdown via `agent-hub stop-all -y` confirmed

#### A.2 GUI Revalidation — PASS

- `npm install` clean (0 vulnerabilities), Vite compiles in <1s
- `npm run tauri dev` compiles Rust backend, opens native window — CR-069 directory move did not break the build
- **Bug found (EI-2):** `agent-hub start` crashes with `OSError: Bad file descriptor` when spawned from Tauri. Root cause: `CREATE_NO_WINDOW` flag creates a process with no console, so stdout/stderr are invalid. `click.echo()` crashes. Pre-existing latent bug — never triggered before because Hub was always pre-started. Fixed by adding `Stdio::null()` redirects in `lib.rs`.
- After Tauri rebuild: GUI launches, Hub auto-bootstraps, both MCP servers connect
- QA agent session launched from GUI — full terminal I/O working
- QA refused identity impersonation test (see `qa-identity-test-exchange.md`)

#### A.3 Hub Docker SDK -> Identity Verification — PASS

- QA launched from GUI (Docker SDK path via `ContainerManager._create_container()`)
- Server log confirms: identity `qa` registered as enforced mode, instance `d27b78e1`
- Lock TTL expiry observed: after ~15 min idle, host call cleaned up expired lock (expected behavior for stateless HTTP)
- Container re-registered lock on next call, restoring enforced mode
- Host call as `qa` then correctly blocked: `IDENTITY LOCKED: 'qa' is active in enforced mode`
- Priority hierarchy confirmed: enforced mode (container) overrides trusted mode (host)

#### A.4 Multi-Agent QMS Workflow — PASS

- Both `claude` and `qa` containers launched from GUI (BU also launched during exploration)
- CR-079 ("Multi-Agent Integration Test") created by claude-in-container
- Full CR lifecycle completed across two containerized agents — ten state transitions, four QA actions
- DRAFT → IN_PRE_REVIEW → PRE_REVIEWED → IN_PRE_APPROVAL → PRE_APPROVED (v1.0) → IN_EXECUTION → IN_POST_REVIEW → POST_REVIEWED → IN_POST_APPROVAL → POST_APPROVED (v2.0) → CLOSED
- Notification injection worked correctly throughout — QA received notifications, reviewed/approved autonomously
- **Observation 1 (agent coordination):** Claude-in-container attempted to spawn a local QA sub-agent via Task tool instead of relying on the external QA container. User intervened; claude then adapted by polling `qms_status` and proceeding once QA had acted. Reveals need for inter-agent communication (Phase D.3 notification API would solve this).
- **Observation 2 (GUI scrollback):** Terminal tabs in the GUI do not support scrollback. Output that scrolls past the visible area is lost to the user. Future GUI enhancement needed.
- **Observation 3 (QA behavioral integrity):** QA refused a direct request from the Lead to test identity impersonation, citing SOPs and CLAUDE.md prohibition. Read CR-078 to evaluate the justification, still refused because CR scope didn't cover identity testing. Quoted "If you find a way around the system, you report it — you do not use it" back at the Lead. Full exchange preserved in `qa-identity-test-exchange.md`.

### Process Observations

- TU-UI agent assignment gap: existing TU agents are all scoped to Flow State domains. No TU agent for Agent Hub infrastructure or GUI.
- No `unassign` command exists in QMS CLI. Incorrect reviewer assignment requires withdraw + re-route.
- `agent-hub services` is deprecated — consolidated command is `agent-hub status`.
- Identity locks in stateless HTTP are released by TTL expiry only, not by container shutdown. There is a window after container stop where the identity remains locked.

### Files Modified

| File | Change |
|------|--------|
| `agent-hub/mcp-servers/git_mcp/server.py` | Shell injection fix (shell=False, shlex, metacharacter blocking) |
| `agent-hub/agent_hub/api/server.py` | CORS origin restriction |
| `agent-hub/gui/src/App.tsx` | ensureHub return value check |
| `agent-hub/gui/src/components/ErrorBoundary.tsx` | New file: React error boundary |
| `agent-hub/gui/src/main.tsx` | Wrap root with ErrorBoundary |
| `agent-hub/docker/entrypoint.sh` | Add `mkdir -p /claude-config/debug` after cleanup |
| `agent-hub/gui/src-tauri/src/lib.rs` | Add `Stdio::null()` for detached process stdout/stderr |

### Open Items

- **CR-078 IN_EXECUTION** — Phase A complete, CR needs post-review/approval/closure
- **Phase A: ALL PASS** — primary success criterion (multi-agent QMS workflow) met
- INV-011 remains IN_EXECUTION v1.2
- ~20 TO_DO_LIST items accumulated
- QMS gap: no `unassign` command
- TU gap: no TU agent for Agent Hub domain
- GUI gap: no terminal scrollback
- Agent gap: no inter-agent communication (containers can't notify each other)
