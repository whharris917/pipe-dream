# UAT: CR-066 PTY Manager Stress Test

## Prerequisites

```bash
# Ensure Hub is installed
cd agent-hub && pip install -e .

# Start MCP servers on host
cd docker/scripts && ./start-mcp-server.sh --background
cd docker/scripts && ./start-git-mcp.sh --background

# Ensure Docker image is built
cd docker && docker-compose build
```

---

## Test 1: Basic PTY Attachment

**Purpose:** Verify PTY attaches when Hub starts an agent.

```bash
# Terminal 1: Start Hub with debug logging
agent-hub start --log-level debug
```

```bash
# Terminal 2:
agent-hub start-agent qa
```

**Verify:**
- Hub logs show `PTY attached for qa`
- Hub logs show `claude started in tmux session for agent-qa`
- The PTY attach log appears AFTER the `Claude Code ready` log

```bash
# Terminal 2: Check API
curl -s http://localhost:9000/api/agents/qa | python -m json.tool
```

**Verify:**
- `"state": "running"`
- `"pty_attached": true`

---

## Test 2: Activity Tracking (Live Signal)

**Purpose:** Verify `last_activity` updates from terminal output, not just startup.

```bash
# Terminal 2: Record initial timestamp
curl -s http://localhost:9000/api/agents/qa | python -m json.tool | grep last_activity
```

Wait 30 seconds. The agent should be generating output (initializing, reading SOPs, etc.).

```bash
# Terminal 2: Check again
curl -s http://localhost:9000/api/agents/qa | python -m json.tool | grep last_activity
```

**Verify:**
- `last_activity` timestamp has advanced since the first check
- The timestamp is NOT stuck at the `started_at` value

---

## Test 3: Idle Detection Goes Quiet

**Purpose:** Verify `last_activity` stops advancing when the agent is idle at a prompt.

Wait for the agent to finish its startup sequence and sit at a prompt (2-3 minutes).

```bash
# Terminal 2: Take two readings 30 seconds apart
curl -s http://localhost:9000/api/agents/qa | python -m json.tool | grep last_activity
sleep 30
curl -s http://localhost:9000/api/agents/qa | python -m json.tool | grep last_activity
```

**Verify:**
- `last_activity` is the same (or nearly the same) in both readings
- The agent is genuinely idle -- no output being generated

---

## Test 4: Idle Timeout Policy Fires

**Purpose:** Verify the idle_timeout shutdown policy actually stops an idle agent.

```bash
# Terminal 2: Set a 2-minute idle timeout on QA
curl -s -X PUT http://localhost:9000/api/agents/qa/policy \
  -H "Content-Type: application/json" \
  -d '{"launch": "manual", "shutdown": "idle_timeout", "idle_timeout_minutes": 2}'
```

Wait for the agent to go idle and then wait 2+ minutes.

**Verify (Hub logs):**
- `Idle shutdown for qa: ...` appears
- `Stopping agent qa` follows
- `PTY detached for qa`
- `Agent qa is now STOPPED`

```bash
# Terminal 2: Confirm
curl -s http://localhost:9000/api/agents/qa | python -m json.tool
```

**Verify:**
- `"state": "stopped"`
- `"pty_attached": false`

```bash
# Reset policy for subsequent tests
curl -s -X PUT http://localhost:9000/api/agents/qa/policy \
  -H "Content-Type: application/json" \
  -d '{"launch": "manual", "shutdown": "manual", "idle_timeout_minutes": 30}'
```

---

## Test 5: CLI Attach

**Purpose:** Verify `agent-hub attach` gives a live interactive terminal.

```bash
# Terminal 2: Start qa again
agent-hub start-agent qa
```

Wait for it to reach RUNNING.

```bash
# Terminal 2: Attach
agent-hub attach qa
```

**Verify:**
- You see `Attaching to qa... (detach with Ctrl-B D)`
- Claude Code's terminal output appears (prompt, conversation history)
- You can type and the agent receives input
- Ctrl-B D detaches cleanly and returns you to your shell

**Negative test:**

```bash
# Terminal 2: Try to attach to a stopped agent
agent-hub stop-agent qa
agent-hub attach qa
```

**Verify:**
- Message: `Agent qa is stopped. Must be running to attach.`
- No crash, clean exit

---

## Test 6: Discovery of Pre-Existing Container

**Purpose:** Verify the Hub attaches PTY to containers it didn't start.

```bash
# Terminal 1: Stop the Hub (Ctrl-C)
```

```bash
# Terminal 2: Start a container manually via launch.sh or docker
docker run -d --name agent-qa \
  -e SETUP_ONLY=1 -e HOME=/ -e QMS_USER=qa \
  -e CLAUDE_CONFIG_DIR=/claude-config -e MCP_TIMEOUT=60000 \
  --add-host host.docker.internal:host-gateway \
  -v "$(pwd):/pipe-dream:ro" \
  -v "$(pwd)/.claude/users/qa/workspace:/pipe-dream/.claude/users/qa/workspace:rw" \
  -v "$(pwd)/.claude/sessions:/pipe-dream/.claude/sessions:rw" \
  -v "$(pwd)/docker/.mcp.json:/pipe-dream/.mcp.json:ro" \
  -v "$(pwd)/.claude/users/qa/container:/claude-config:rw" \
  docker-claude-agent

# Wait for setup, then start claude in tmux
sleep 10
docker exec -d agent-qa tmux new-session -d -s agent "claude"
```

```bash
# Terminal 1: Start the Hub again
agent-hub start --log-level debug
```

**Verify (Hub logs):**
- `Discovered running container for qa`
- `PTY attached for qa`

```bash
# Terminal 2:
curl -s http://localhost:9000/api/agents/qa | python -m json.tool
```

**Verify:**
- `"state": "running"`
- `"pty_attached": true`
- `last_activity` is advancing (agent is generating output)

---

## Test 7: External Stop (Container Sync)

**Purpose:** Verify the sync loop detects an externally stopped container and detaches PTY.

```bash
# Terminal 2: Kill the container directly (not through Hub)
docker stop agent-qa && docker rm agent-qa
```

Wait 10-15 seconds for the sync loop (runs every 10s).

**Verify (Hub logs):**
- `PTY read loop stopped for qa` (socket closed when container died)
- `Sync: container stopped externally for qa`

```bash
# Terminal 2:
curl -s http://localhost:9000/api/agents/qa | python -m json.tool
```

**Verify:**
- `"state": "stopped"`
- `"pty_attached": false`

---

## Test 8: Multiple Agents Simultaneously

**Purpose:** Verify independent PTY sessions for concurrent agents.

```bash
# Terminal 2: Start two agents
agent-hub start-agent qa
agent-hub start-agent tu_ui
```

Wait for both to reach RUNNING.

```bash
# Terminal 2: Verify both have PTY
curl -s http://localhost:9000/api/agents | python -m json.tool
```

**Verify:**
- Both `qa` and `tu_ui` show `"state": "running"`
- Hub logs show separate `PTY attached for qa` and `PTY attached for tu_ui`

```bash
# Terminal 2: Check activity independently
curl -s http://localhost:9000/api/agents/qa | python -m json.tool | grep last_activity
curl -s http://localhost:9000/api/agents/tu_ui | python -m json.tool | grep last_activity
```

**Verify:**
- Timestamps are independent (not identical)

```bash
# Clean up
agent-hub stop-agent qa
agent-hub stop-agent tu_ui
```

**Verify (Hub logs):**
- `PTY detached for qa` and `PTY detached for tu_ui` appear separately
- No errors, no cross-contamination

---

## Test 9: Rapid Start/Stop Cycle

**Purpose:** Verify no resource leaks or race conditions on quick lifecycle churn.

```bash
# Terminal 2: Rapid cycle (3 times)
for i in 1 2 3; do
  echo "--- Cycle $i ---"
  agent-hub start-agent qa
  sleep 5
  agent-hub stop-agent qa
  sleep 2
done
```

**Verify (Hub logs):**
- Each cycle shows: `PTY attached for qa` ... `PTY detached for qa`
- No orphaned read loops (`PTY read loop stopped` appears for each cycle)
- No `PTY already attached` warnings (clean detach before re-attach)
- No Python tracebacks or unhandled exceptions

```bash
# Final state
curl -s http://localhost:9000/api/agents/qa | python -m json.tool
```

**Verify:**
- `"state": "stopped"`
- `"pty_attached": false`

---

## Test 10: Hub Shutdown with Running Agents

**Purpose:** Verify clean shutdown detaches all PTY sessions.

```bash
# Terminal 2:
agent-hub start-agent qa
```

Wait for RUNNING.

```bash
# Terminal 1: Stop Hub with Ctrl-C
```

**Verify (Hub logs):**
- `PTY detached for qa` (from `detach_all`)
- No tracebacks during shutdown
- Hub exits cleanly

---

## Summary Scorecard

| # | Test | Result | Notes |
|---|------|--------|-------|
| 1 | Basic PTY attachment | | |
| 2 | Activity tracking (live signal) | | |
| 3 | Idle detection goes quiet | | |
| 4 | Idle timeout policy fires | | |
| 5 | CLI attach (+ negative test) | | |
| 6 | Discovery of pre-existing container | | |
| 7 | External stop (container sync) | | |
| 8 | Multiple agents simultaneously | | |
| 9 | Rapid start/stop cycle | | |
| 10 | Hub shutdown with running agents | | |

Tests 1-5 verify the primary functionality surface. Tests 6-10 stress the edges -- lifecycle events the Hub doesn't control, concurrency, rapid churn, and graceful shutdown.
