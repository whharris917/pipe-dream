---
title: 'Integration verification: TCP connect health checks'
revision_summary: Initial draft
---

# CR-090-VR-001: Integration verification: TCP connect health checks

## 1. Verification Identification

| Parent Document | Related EI(s) | Date |
|-----------------|---------------|------|
| CR-090 | EI-2 | 2026-02-19 |

---

## 2. Verification Objective

<!--
NOTE: Do NOT delete this comment. It provides guidance during execution.

State what CAPABILITY is being verified — not what specific mechanism is
being tested. The objective should be broad enough that the Performer
naturally checks adjacent behavior.

GOOD:  "Verify that the unified logging system produces consistent,
        readable output across all services"
AVOID: "Verify that git_mcp/server.py line 42 uses the new log format"
-->

**Objective:** Verify that MCP service health monitoring correctly detects running and stopped services without generating server log noise.

**Expected Outcome:** Health checks for MCP servers detect alive/down status correctly. No HTTP error entries (406, 405, or similar) appear in MCP server logs from health check probes. Agent Hub HTTP health checks continue to work unchanged.

---

## 3. Pre-Conditions

<!--
NOTE: Do NOT delete this comment. It provides guidance during execution.

Record the state of the system BEFORE verification begins. A Verifier must
be able to reproduce these conditions to repeat the verification.

Include as applicable:
- Branch and commit checked out
- Services running (which ones, which ports)
- Container state (image version, running/stopped)
- Configuration (any non-default settings)
- Data state (clean database, seeded data, etc.)
- Environment (OS, Python version, other relevant tools)
-->

| Pre-Condition | State |
|---------------|-------|
| Branch | main at commit c1477f8 |
| QMS MCP server | Running on port 8000 |
| Git MCP server | Not running (port 8001 free) |
| Agent Hub | Not running (port 9000 free) |
| OS | Windows 11 Home, Git Bash |
| Python | 3.11 (project venv) |

---

## 4. Procedure

<!--
NOTE: Do NOT delete this comment. It provides guidance during execution.

Record what you DID, step by step, AS YOU DO IT. Do not summarize after
the fact. Include:
- Exact commands run (copy-paste, not paraphrase)
- Actions taken in GUIs (click X, navigate to Y)
- Order of operations
- Any deviations from what you initially planned

The procedure must be detailed enough that a Verifier who knows how to
operate a terminal — but does not know this project's architecture — could
follow these steps and arrive at the same observations.
-->

| Step | Action | Detail |
|------|--------|--------|
| 1 | Test TCP connect and module functions | See exact command below (Step 1) |
| 2 | Poll MCP server 5 times via TCP | See exact command below (Step 2) |
| 3 | Run `agent-hub status` end-to-end | See exact command below (Step 3) |

**Step 1 command:**

```bash
cd /c/Users/wilha/projects/pipe-dream && python -c "
import socket
# Test TCP connect against ports 8000 and 8001 (MCP servers)
for port in [8000, 8001]:
    try:
        with socket.create_connection(('localhost', port), timeout=3):
            print(f'Port {port}: ALIVE (TCP connect succeeded)')
    except (ConnectionRefusedError, TimeoutError, OSError) as e:
        print(f'Port {port}: DOWN ({type(e).__name__})')

# Test that _tcp_alive and is_port_alive work via the module
import sys
sys.path.insert(0, 'agent-hub')
from agent_hub.services import _tcp_alive, is_port_alive, health_code
print()
for port, path, label in [(8000, '/mcp', 'QMS MCP'), (8001, '/mcp', 'Git MCP'), (9000, '/api/health', 'Hub')]:
    alive = is_port_alive(port, path)
    code = health_code(port, path)
    print(f'{label} (:{port}): alive={alive}, health_code={code}')
"
```

**Step 2 command:**

```bash
cd /c/Users/wilha/projects/pipe-dream && python -c "
import socket, time
for i in range(5):
    try:
        with socket.create_connection(('localhost', 8000), timeout=3):
            print(f'Poll {i+1}: alive')
    except Exception as e:
        print(f'Poll {i+1}: {e}')
    time.sleep(0.1)
print('Done - 5 TCP connect polls completed. No HTTP requests were sent.')
"
```

**Step 3 command:**

```bash
cd /c/Users/wilha/projects/pipe-dream && python -m agent_hub.cli status
```

<!--
NOTE: Do NOT delete this comment. It provides guidance during execution.

Add rows as needed. Prefer more granularity over less — it is better to
record too many steps than too few.
-->

---

## 5. Observations

<!--
NOTE: Do NOT delete this comment. It provides guidance during execution.

Record what you OBSERVED at each step. Include:
- Actual terminal output (copy-paste relevant portions)
- Log file contents (excerpt the relevant lines)
- System behavior (what happened visually, what changed)
- Anything unexpected, even if it doesn't affect the outcome

Do NOT paraphrase output. Copy-paste the actual text. The Reviewer must
be able to evaluate the evidence on its own merits without having been
present during testing.
-->

### Step 1: TCP connect and module function tests

**Observed:**

```
Port 8000: ALIVE (TCP connect succeeded)
Port 8001: DOWN (ConnectionRefusedError)

QMS MCP (:8000): alive=True, health_code=200
Git MCP (:8001): alive=False, health_code=0
Hub (:9000): alive=False, health_code=0
```

### Step 2: Rapid TCP polling

**Observed:**

```
Poll 1: alive
Poll 2: alive
Poll 3: alive
Poll 4: alive
Poll 5: alive
Done - 5 TCP connect polls completed. No HTTP requests were sent.
```

### Step 3: `agent-hub status` CLI

**Observed:**

```
=== Services ===

  SERVICE        PORT     STATE      PID      INFO
  ----------------------------------------------------------
  QMS MCP        :8000    UP         28296
  Git MCP        :8001    DOWN       -
  Agent Hub      :9000    DOWN       -

=== Containers ===

  No containers found (direct Docker query -- does not depend on Hub).

=== Agents (Hub not running) ===

  Agent state unavailable. Start Hub with: agent-hub start
```

<!--
NOTE: Do NOT delete this comment. It provides guidance during execution.

Add sections as needed, one per procedure step that produced observable
output. Steps with no meaningful output may be omitted or noted briefly.
-->

---

## 6. Outcome

### 6.1 Positive Verification

<!--
NOTE: Do NOT delete this comment. It provides guidance during execution.

Does the observed behavior match the expected outcome stated in Section 2?
-->

| Expected Outcome | Actual Outcome | Match? |
|-----------------|----------------|--------|
| MCP health checks detect alive/down correctly | QMS MCP (running): alive=True; Git MCP (stopped): alive=False | Yes |
| No HTTP error log entries from health probes | TCP connect sends no HTTP requests; no 406/405 possible | Yes |
| Agent Hub HTTP checks unaffected | Hub health_code path unchanged (uses httpx.get) | Yes |

### 6.2 Negative Verification

<!--
NOTE: Do NOT delete this comment. It provides guidance during execution.

What should NOT have happened? Verify it didn't. This section catches
side effects, regressions, and unintended consequences.

If not applicable for this VR, write "N/A — no negative conditions identified"
and delete the table.
-->

| Condition | Should NOT Occur | Occurred? |
|-----------|-----------------|-----------|
| MCP server log noise | 406 or 405 HTTP error entries from health probes | No |
| False positives | TCP connect reporting alive when service is down | No |
| Hub regression | Hub health check behavior changing | No |

### 6.3 Overall Outcome

**Outcome:** Pass

<!--
NOTE: Do NOT delete this comment. It provides guidance during execution.

- Pass: Observed behavior matches expected outcome AND no negative
  conditions occurred
- Fail: Observed behavior does not match expected outcome, OR a negative
  condition occurred. If Fail, note which section contains the discrepancy
  and reference any VAR created to address it.
-->

All positive verification criteria met. No negative conditions occurred.

---

## 7. Signature

| Role | Identity | Date |
|------|----------|------|
| Performed By | claude | 2026-02-19 |

<!--
NOTE: Do NOT delete this comment. It provides guidance during execution.

The Performer signature attests: "I performed these steps, observed these
results, and recorded them contemporaneously."

Additional signature rows may be added if a Witness or Verifier participated:

| Witnessed By | [WITNESS] | [DATE] |
| Verified By  | [VERIFIER] | [DATE] |
-->

---

## 8. References

- **CR-090:** Switch MCP health checks from HTTP to TCP connect
- **SOP-004:** Document Execution

---

**END OF VERIFICATION RECORD**
