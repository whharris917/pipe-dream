# MCP Connection Timeline Analysis

## Searching for "MCP servers were successfully connected"

From the conversation summary, the user reported at one point:
> "Both Claude Code sessions successfully launched. I had to authenticate in both, as expected. In both, the qms and git mcp servers were successfully connected immediately."

This was BEFORE I made the change to remove `claude mcp add` commands.

## The Breaking Change

I made this change (incorrectly):
```bash
# REMOVED THIS (bad):
docker exec "$CONTAINER" claude mcp add --transport http --scope user \
    --header "X-API-Key: qms-internal" \
    --header "Authorization: Bearer internal-trusted" \
    qms "http://host.docker.internal:8000/mcp"

# REPLACED WITH (insufficient):
# "MCP servers are configured via project-level .mcp.json"
# Just verified files exist, didn't run claude mcp add
```

The rationale was that `.mcp.json` (mounted at `/pipe-dream/.mcp.json`) should provide the config. But this was wrong - Claude Code needs the `claude mcp add` registration.

## After Restoring `claude mcp add`

Direct launch works:
```
/mcp
Project MCPs (/pipe-dream/.mcp.json)
❯ git · ✔ connected
  qms · ✔ connected
```

But multi-agent launch shows "failed and not authenticated".

## Key Question

What's different between:
1. Running `./claude-session.sh` in the current terminal
2. Running `./claude-session.sh` in a mintty subshell launched by multi-agent-session.sh

Possibilities:
- Environment variables (PATH, HOME, etc.)
- Credential files not accessible
- Path resolution differs (cygpath behavior)
- Docker context differs
- Race condition with multiple containers

## Test to Run Later

Run these in BOTH scenarios and compare:
```bash
echo "PATH=$PATH"
echo "HOME=$HOME"
echo "SCRIPT_DIR=$SCRIPT_DIR"
cygpath -w "$SCRIPT_DIR"
docker info | head -5
```
