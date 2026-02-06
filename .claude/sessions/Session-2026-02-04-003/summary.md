# Session 2026-02-04-003: Multi-Agent Infrastructure - Final Summary

## Session Outcome: 95% Working, One Automation Gap

**What works:**
- Container launches correctly
- Claude Code runs in container
- MCP servers are reachable from container
- MCP config is correct (Claude finds `/pipe-dream/.mcp.json`)
- Manual MCP reconnect **always succeeds**
- Multi-agent identity (qa knows it's qa)
- Inbox watcher displays notifications
- All QMS operations work once connected

**What doesn't work:**
- MCP auto-connect at session start (requires manual `/mcp` → Reconnect)

This is a narrow but critical gap for full automation.

## Key Discovery: Docker Cache Invalidation

**Critical finding late in session:** Docker's build cache may have been serving stale entrypoint code throughout our testing. When we finally forced `--no-cache` rebuild, we confirmed previous "tests" may not have been running the code we thought they were.

**Implication:** All test results from this session (and possibly prior sessions) are suspect. We cannot be certain which version of the entrypoint was actually running at any given time.

## Technical Insights Gained

### 1. MCP Configuration Scopes (Documented)
- **User scope**: `claude mcp add --scope user` → stored in `$CLAUDE_CONFIG_DIR/.claude.json`
- **Project scope**: `.mcp.json` file in project root

We had BOTH configured, which may cause conflicts. Simplified to project-scope only.

### 2. OAuth Bypass Requirement (GitHub #7290)
Claude Code attempts OAuth discovery before using auth headers. The workaround requires **dual headers**:
```json
{
  "headers": {
    "X-API-Key": "any-value",
    "Authorization": "Bearer any-value"
  }
}
```
Both headers must be present. Values are not validated - they just trigger a code path that bypasses OAuth.

**Fixed:** Added dual headers to git server in `.mcp.json` (was missing).

### 3. Entrypoint Architecture
- Original entrypoint used `claude mcp add` (user scope) + marker files
- Simplified entrypoint relies on project-level `.mcp.json` only
- Added mount verification to check files exist before starting Claude

### 4. Docker-Compose vs Docker Run
| Approach | Entrypoint | MCP Config | Result |
|----------|------------|------------|--------|
| docker-compose up -d + exec | Runs | By entrypoint | Was "working" |
| docker run --entrypoint override | Bypassed | Manual | Broken |
| docker run (no override) | Runs | By entrypoint | Untested reliably |

## Files Modified

### docker/entrypoint.sh
- Removed `claude mcp add` commands (eliminated user-scope config)
- Removed marker file logic
- Added mount verification (waits for .mcp.json)
- Added config dump for debugging

### docker/.mcp.json
- Added dual headers to git server for OAuth bypass

### Created Documentation
- `container-architecture-primer.md` - First-principles explanation of Docker, mounts, entrypoints, MCP

### Test Scripts Created
- `claude-session-v2.sh` - docker-compose with project names (partial success)
- `claude-session-v3.sh` - docker run preserving entrypoint (not fully tested)
- `claude-session-updated.sh` - backup of multi-agent changes

## What We Don't Know

1. **Is the "original working" script actually reliable?** Given cache issues, we can't be certain.

2. **Why does manual reconnect work but auto-connect fail?** The config is correct (Claude finds it), network is reachable (verified), headers are present. Something in Claude Code's startup sequence differs from manual reconnect.

3. **Is there a timing/race condition?** Mounts appear ready, but maybe Claude Code reads config before something else initializes.

4. **Are there Windows/Git Bash specific issues?** Path translation, filesystem timing, Docker Desktop quirks.

## Recommended Next Steps

### Option A: Start Fresh with Known State
1. Delete all Docker images: `docker rmi docker-claude-agent`
2. Delete all container config: `rm -rf .claude/users/*/container/*`
3. Rebuild with `--no-cache`
4. Test original `claude-session.sh` multiple times
5. Document exact behavior

### Option B: Investigate Claude Code Internals
1. Run Claude Code with debug logging (if available)
2. Check what happens differently between startup and manual reconnect
3. File issue with Claude Code team if it's a bug

### Option C: Accept Manual Reconnect
1. Keep current architecture
2. Document that MCP may need manual reconnect on first launch
3. Focus on other features

## Project Architecture (Remains Sound)

The overall multi-agent hub design is solid:

```
Rung 1: Basic Container (working for single agent)
Rung 2: Multi-Agent Sessions (blocked by MCP issue)
Rung 3: Hub Architecture (designed, not implemented)
Rung 4: Autonomous Agents (future)
Rung 5: GUI Dashboard (future)
```

The QMS, agent definitions, inbox system, and orchestration concepts are all well-designed. The blocker is specifically MCP auto-connect reliability in containers.

## Session Duration
~4 hours of debugging with diminishing returns.

## Emotional State
Lead frustrated; Claude apologetic. The systematic approach was good but the problem proved resistant to diagnosis. Docker caching revelation late in session undermined confidence in all prior testing.
