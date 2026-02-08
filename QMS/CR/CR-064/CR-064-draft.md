---
title: Agent container readiness check via tmux capture-pane
revision_summary: Initial draft
---

# CR-064: Agent container readiness check via tmux capture-pane

## 1. Purpose

Fix a timing bug where the Agent Hub injects task notifications into agent containers before Claude Code has finished initializing, causing the notification text to appear on screen but never be submitted.

---

## 2. Scope

### 2.1 Context

Discovered during exploratory testing in Session 2026-02-08-001. When the Hub auto-starts a QA container via `auto_on_task` policy and immediately injects a notification, the text arrives before Claude Code's input prompt is ready. The Enter keystroke is lost, leaving the notification text visible but unsubmitted.

- **Parent Document:** None (exploratory testing finding)

### 2.2 Changes Summary

Add a readiness check to the Agent Hub's container startup that polls `tmux capture-pane` output until Claude Code's input prompt (`❯`) is detected, ensuring notifications are only injected after the agent is ready to accept input.

### 2.3 Files Affected

- `agent-hub/agent_hub/container.py` — Add `wait_for_ready()` method using `tmux capture-pane`
- `agent-hub/agent_hub/hub.py` — Ensure notification injection occurs only after readiness confirmed

---

## 3. Current State

The Hub's `ContainerManager.start()` method calls `_exec_claude()` which fires `tmux new-session -d -s agent "claude"` and returns immediately (fire-and-forget). The `start_agent()` method in `hub.py` sets `agent.state = RUNNING` as soon as `start()` returns. The `_on_inbox_change` callback then immediately calls `inject_notification()`, which uses `tmux send-keys` to inject text and Enter into the session.

There is no check that Claude Code has finished initializing. The Enter keystroke arrives before Claude Code is listening for input, so it is lost. The notification text persists on screen (buffered by tmux) but is never submitted.

---

## 4. Proposed State

After `_exec_claude()`, a new `_wait_for_ready()` method polls `tmux capture-pane -t agent -p` via `docker exec` until the Claude Code prompt character (`❯`) appears in the output. If the prompt is detected, `start()` returns normally and the agent becomes RUNNING. If the timeout expires without detecting the prompt, the method logs a warning and raises `RuntimeError`. The existing error handler in `start_agent()` sets the agent to ERROR state but does not stop or remove the container — it remains alive for the Lead to attach and investigate. This ensures that when `agent.state` becomes `RUNNING`, Claude Code is genuinely ready to accept input, and notification injection will succeed.

---

## 5. Change Description

### 5.1 Readiness Check (`container.py`)

Add a `_wait_for_ready()` method to `ContainerManager`:

```python
async def _wait_for_ready(self, name: str, timeout: float = 60.0) -> None:
    """Wait for Claude Code to be ready for input.

    Polls tmux capture-pane output until the prompt character (❯)
    is detected, indicating Claude Code has finished initializing
    and is ready to accept user input.
    """
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "exec", name,
                "tmux", "capture-pane", "-t", "agent", "-p",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if "❯" in stdout.decode("utf-8", errors="replace"):
                logger.info("Claude Code ready in %s", name)
                return
        except (asyncio.TimeoutError, Exception):
            pass
        await asyncio.sleep(2.0)

    logger.warning(
        "Claude Code readiness not confirmed in %s after %.0fs — "
        "container left running for inspection",
        name, timeout,
    )
    raise RuntimeError(
        f"Claude Code in {name} did not become ready within {timeout:.0f}s"
    )
```

Call sequence in `start()`:
1. `_create_container()` — create and start the Docker container
2. `_wait_for_setup()` — wait for entrypoint to complete (existing)
3. `_exec_claude()` — launch Claude Code in tmux (existing)
4. `_wait_for_ready()` — **new** — wait for Claude Code's input prompt

### 5.2 Hub Integration (`hub.py`)

No changes needed to `hub.py`. The fix is entirely in `container.py` — `start()` already blocks until it returns, and the notification injection in `_on_inbox_change` only runs after `start_agent()` completes. By making `start()` wait for readiness, the existing flow is fixed without restructuring.

---

## 6. Justification

- **Problem:** Hub-launched agents miss their first task notification because the Enter keystroke is lost during Claude Code's initialization window. The agent sits idle with unsubmitted text until a human attaches and manually submits it.
- **Impact of not fixing:** Hub-managed agents cannot reliably process tasks autonomously, defeating the purpose of the `auto_on_task` launch policy.
- **Root cause:** No readiness check between launching Claude Code and injecting notifications. The container being "running" is not the same as Claude Code being "ready."

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `agent-hub/agent_hub/container.py` | Modify | Add `_wait_for_ready()` method, call it from `start()` |
| `agent-hub/agent_hub/hub.py` | No change | Existing flow is correct once `start()` blocks on readiness |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| None | — | No controlled documents affected |

### 7.3 Other Impacts

The `start()` method will take longer to return (up to 60s in worst case, typically 10-20s based on observed Claude Code startup times). This is acceptable because:
- Container startup is already an async operation
- The Hub's event loop remains responsive during the polling
- The notification would fail anyway without this wait

If readiness times out, the container is intentionally left running (not stopped or removed) so the Lead can attach with `docker exec -it agent-{id} tmux attach -t agent` to inspect the actual state of Claude Code.

---

## 8. Testing Summary

- Start QA container via Hub, inject a notification, verify the text is submitted (Enter key lands successfully)
- Verify `tmux capture-pane` reliably detects the `❯` prompt during startup
- Verify timeout behavior: if Claude Code fails to become ready, the method logs a warning, raises an error, and the container is left running for inspection (agent state becomes ERROR)

---

## 9. Implementation Plan

### 9.1 Implementation

1. Add `_wait_for_ready()` method to `ContainerManager` in `container.py`
2. Insert call to `_wait_for_ready()` in `start()` after `_exec_claude()`

### 9.2 Integration Test

1. Create a test CR and route for review (to populate QA inbox)
2. Verify Hub auto-starts QA container and notification is successfully submitted
3. Verify QA processes the review task end-to-end

---

## 10. Execution

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Add `_wait_for_ready()` to `container.py` and call from `start()` | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Integration test: verify notification injection succeeds after auto-start | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Add rows as needed. When adding rows, fill columns 3-5 during execution.
-->

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during execution.
Add rows as needed.

This section is the appropriate place to attach VARs that do not apply
to any individual execution item, but apply to the CR as a whole.
-->

---

## 11. Execution Summary

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Complete this section after all EIs are executed.
Summarize the overall outcome and any deviations from the plan.
-->

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **Session 2026-02-08-001:** Exploratory testing that discovered the timing bug

---

**END OF DOCUMENT**
