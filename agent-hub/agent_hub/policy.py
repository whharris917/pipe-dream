"""Policy engine — evaluates launch and shutdown rules.

Policies determine when agents should be automatically started or stopped.
The Hub calls into this module when state changes occur (inbox change,
idle tick) and acts on the decisions returned.
"""

import logging
from datetime import datetime

from agent_hub.models import Agent, AgentState, LaunchPolicy, ShutdownPolicy

logger = logging.getLogger(__name__)


class PolicyDecision:
    """Result of a policy evaluation."""

    def __init__(self, action: str | None, reason: str = ""):
        self.action = action  # "start", "stop", or None
        self.reason = reason

    def __repr__(self) -> str:
        return f"PolicyDecision(action={self.action!r}, reason={self.reason!r})"


def evaluate_launch(agent: Agent, inbox_count: int) -> PolicyDecision:
    """Evaluate whether an agent should be launched.

    Called when:
    - Inbox count changes (new task arrives)
    - Hub starts (for ALWAYS_ON agents)
    """
    if agent.state != AgentState.STOPPED:
        return PolicyDecision(None, "agent not stopped")

    if agent.policy.launch == LaunchPolicy.ALWAYS_ON:
        return PolicyDecision("start", "always-on policy")

    if agent.policy.launch == LaunchPolicy.AUTO_ON_TASK and inbox_count > 0:
        return PolicyDecision("start", f"auto-on-task: {inbox_count} items in inbox")

    return PolicyDecision(None, "no launch policy triggered")


def evaluate_shutdown(agent: Agent, inbox_count: int) -> PolicyDecision:
    """Evaluate whether an agent should be stopped.

    Called when:
    - Inbox count changes (task removed)
    - Idle timeout tick fires
    """
    if agent.state != AgentState.RUNNING:
        return PolicyDecision(None, "agent not running")

    # Never auto-stop always-on agents
    if agent.policy.launch == LaunchPolicy.ALWAYS_ON:
        return PolicyDecision(None, "always-on: never auto-stop")

    if agent.policy.shutdown == ShutdownPolicy.ON_INBOX_EMPTY and inbox_count == 0:
        return PolicyDecision("stop", "inbox empty")

    if agent.policy.shutdown == ShutdownPolicy.IDLE_TIMEOUT:
        if agent.last_activity is not None:
            idle_minutes = (
                datetime.now() - agent.last_activity
            ).total_seconds() / 60
            if idle_minutes >= agent.policy.idle_timeout_minutes:
                return PolicyDecision(
                    "stop",
                    f"idle for {idle_minutes:.0f}m (limit: {agent.policy.idle_timeout_minutes}m)",
                )

    return PolicyDecision(None, "no shutdown policy triggered")
