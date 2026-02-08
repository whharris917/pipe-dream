"""Configuration for the Agent Hub."""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings

from agent_hub.models import LaunchPolicy, ShutdownPolicy


class HubConfig(BaseSettings):
    """Hub configuration, loadable from environment variables."""

    # Paths
    project_root: Path = Path.cwd()

    # Network
    host: str = "127.0.0.1"
    port: int = 9000

    # Docker
    docker_image: str = "docker-claude-agent"
    container_prefix: str = "agent-"

    # Agent roster
    agents: list[str] = [
        "claude", "qa", "tu_ui", "tu_scene",
        "tu_sketch", "tu_sim", "bu",
    ]

    # Default policies
    default_launch_policy: LaunchPolicy = LaunchPolicy.MANUAL
    default_shutdown_policy: ShutdownPolicy = ShutdownPolicy.MANUAL
    default_idle_timeout: int = 30

    # PTY Manager
    pty_buffer_size: int = 262144  # 256KB scrollback buffer per agent

    model_config = {"env_prefix": "HUB_"}

    @field_validator("project_root", mode="before")
    @classmethod
    def resolve_project_root(cls, v: str | Path) -> Path:
        return Path(v).resolve()

    @property
    def users_dir(self) -> Path:
        return self.project_root / ".claude" / "users"

    @property
    def agents_dir(self) -> Path:
        return self.project_root / ".claude" / "agents"

    def inbox_path(self, agent_id: str) -> Path:
        return self.users_dir / agent_id / "inbox"

    def workspace_path(self, agent_id: str) -> Path:
        return self.users_dir / agent_id / "workspace"

    def container_config_path(self, agent_id: str) -> Path:
        return self.users_dir / agent_id / "container"

    def agent_definition_path(self, agent_id: str) -> Path:
        return self.agents_dir / f"{agent_id}.md"
