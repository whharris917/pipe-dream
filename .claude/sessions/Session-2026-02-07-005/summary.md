# Session 2026-02-07-005 Summary

## Completed

### CR-063 CLOSED: Remove PID files — port-based process discovery
- Updated CR-063 scope to include deleting legacy `.mcp-server.pid` and `.mcp-server.log`
- Full QMS lifecycle: draft (from session 004) → pre-review → pre-approval → execution → post-review (1 round of updates for stale `revision_summary`) → post-approval → closed
- **`pd-status` changes:**
  - Replaced `pid_alive()` with `find_pid_on_port()` — uses PowerShell `Get-NetTCPConnection` on Windows, `lsof`/`ss` on Linux/Mac
  - Simplified service definitions from 4-field (`label:port:pidfile:healthpath`) to 3-field (`label:port:healthpath`)
  - `show_status()` now shows RUNNING with actual PID or STOPPED — no stale-PID warnings, no Warnings section
  - `stop_all()` kills services by port-based PID discovery instead of reading PID files
  - Fixed pre-existing bug in `port_alive()`: `curl -w "%{http_code}" ... || echo "000"` concatenated curl's own `000` with the fallback producing `000000`, which made dead ports appear alive. Same fix applied to `health_code()`
- **`launch.sh` changes:**
  - Removed 3 `echo $! > ...pid` lines from `ensure_mcp_servers()` and `ensure_hub()`
  - Post-session messages now say `./pd-status --stop-all` instead of `kill $(cat ...pid)`
- **Cleanup:**
  - Deleted 5 files: `.mcp-server.pid`, `.mcp-server.log`, `.qms-mcp-server.pid`, `.git-mcp-server.pid`, `.agent-hub.pid`
  - Updated `.gitignore`: removed PID file entries, retained log file entries, added `.agent-hub.log` and `.agent-hub-test.log`

## Observations
- MCP servers (:8000, :8001) were actually dead — the old `pd-status` had been showing them as RUNNING due to the `port_alive()` bug
- Only Agent Hub (:9000, PID 15148) was genuinely running
- The `docker-claude-agent-1` container (from session 004 Hub experiment) is still EXITED — not cleaned up

## Agent IDs for Resume
- QA agent: `a27577d` (used for CR-063 pre-review, pre-approval, post-review x2, post-approval — 5 interactions)
