"""Data models for the Agent Hub."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class AgentState(str, Enum):
    """Container lifecycle states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STALE = "stale"
    STOPPING = "stopping"
    ERROR = "error"


class LaunchPolicy(str, Enum):
    """When to start an agent's container."""

    MANUAL = "manual"
    AUTO_ON_TASK = "auto_on_task"
    ALWAYS_ON = "always_on"


class ShutdownPolicy(str, Enum):
    """When to stop an agent's container."""

    MANUAL = "manual"
    ON_INBOX_EMPTY = "on_inbox_empty"
    IDLE_TIMEOUT = "idle_timeout"


class AgentPolicy(BaseModel):
    """Launch and shutdown policy for an agent."""

    launch: LaunchPolicy = LaunchPolicy.MANUAL
    shutdown: ShutdownPolicy = ShutdownPolicy.MANUAL
    idle_timeout_minutes: int = 30


class Agent(BaseModel):
    """Full agent state."""

    id: str
    state: AgentState = AgentState.STOPPED
    policy: AgentPolicy = AgentPolicy()
    container_id: str | None = None
    started_at: datetime | None = None
    last_activity: datetime | None = None
    inbox_count: int = 0
    pty_attached: bool = False
    session_alive: bool = False


class AgentSummary(BaseModel):
    """Lightweight agent info for list endpoints."""

    id: str
    state: AgentState
    inbox_count: int
    launch_policy: LaunchPolicy


class HubStatus(BaseModel):
    """Overall hub status."""

    agents: list[AgentSummary]
    uptime_seconds: float
