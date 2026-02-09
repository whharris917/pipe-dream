# Agent Hub UAT — Primary Surface Commands

**Prerequisite:** `pip install -e agent-hub/` completed, Docker running.

---

### Test 1: `services` (cold start)

```bash
agent-hub services
```

**Expected:** All three services show DOWN, no containers listed. This command should work with nothing running.

- [ ] QMS MCP: DOWN
- [ ] Git MCP: DOWN
- [ ] Agent Hub: DOWN
- [ ] "No agent containers found."

---

### Test 2: `launch` (single agent)

```bash
agent-hub launch claude
```

**Expected:** Infrastructure starts in order, then attaches to claude's tmux session interactively.

- [ ] QMS MCP starts (or shows "already running")
- [ ] Git MCP starts (or shows "already running")
- [ ] Docker image exists (or builds)
- [ ] Agent Hub starts (or shows "already running")
- [ ] Claude container starts
- [ ] You are attached to a tmux session with Claude Code running
- [ ] Detach with Ctrl-B D (returns to your shell)

---

### Test 3: `services` (after launch)

```bash
agent-hub services
```

**Expected:** All three services show UP with PIDs. One container listed.

- [ ] QMS MCP: UP
- [ ] Git MCP: UP
- [ ] Agent Hub: UP
- [ ] Container `agent-claude` shown as running

---

### Test 4: `attach` (reconnect)

```bash
agent-hub attach claude
```

**Expected:** Reattaches to the same tmux session from Test 2.

- [ ] You see the Claude Code session (same state as when you detached)
- [ ] Detach with Ctrl-B D

---

### Test 5: `stop-all` (teardown)

```bash
agent-hub stop-all
```

**Expected:** Lists what will be stopped, prompts for confirmation, then tears everything down.

- [ ] Shows services and containers that will be stopped
- [ ] Prompts "Proceed?"
- [ ] After confirming: kills services, removes container
- [ ] "Done."

---

### Test 6: `services` (verify clean)

```bash
agent-hub services
```

**Expected:** Back to the cold-start state from Test 1.

- [ ] All services DOWN
- [ ] No containers

---

### Test 7: `stop-all -y` (idempotent, no prompt)

```bash
agent-hub stop-all -y
```

**Expected:** Nothing to stop, no prompt.

- [ ] "Nothing to stop" message
