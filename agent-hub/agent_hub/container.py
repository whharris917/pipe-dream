"""Docker container lifecycle management.

Replicates launch.sh's container creation logic using the Docker SDK.
Uses the SETUP_ONLY two-phase startup pattern:
  1. docker run -d with SETUP_ONLY=1 (entrypoint does setup, then sleeps)
  2. docker exec to start claude inside tmux
"""

import asyncio
import logging
import os
import platform
from pathlib import Path

import docker
from docker.errors import NotFound, APIError

from agent_hub.config import HubConfig

logger = logging.getLogger(__name__)


class ContainerManager:
    """Manages Docker container lifecycle for agents."""

    def __init__(self, config: HubConfig):
        self.config = config
        self._client: docker.DockerClient | None = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def container_name(self, agent_id: str) -> str:
        return f"{self.config.container_prefix}{agent_id}"

    async def start(self, agent_id: str) -> str:
        """Start a container for an agent. Returns container ID.

        Uses the SETUP_ONLY pattern:
        1. Run container detached with SETUP_ONLY=1
        2. Wait for entrypoint setup to complete
        3. Exec claude inside tmux
        """
        name = self.container_name(agent_id)

        # Remove any existing container with this name
        await self._remove_if_exists(name)

        # Ensure required directories exist
        self._ensure_agent_dirs(agent_id)

        # Build and run the container
        container = await asyncio.to_thread(
            self._create_container, agent_id, name
        )

        # Wait for entrypoint setup
        await self._wait_for_setup(name)

        # Start claude inside tmux
        await self._exec_claude(name)

        # Wait for Claude Code to be ready for input
        await self._wait_for_ready(name)

        logger.info("Container %s started for agent %s", name, agent_id)
        return container.id

    async def stop(self, agent_id: str) -> None:
        """Stop and remove an agent's container."""
        name = self.container_name(agent_id)
        await self._remove_if_exists(name, stop_first=True)
        logger.info("Container %s stopped for agent %s", name, agent_id)

    async def is_running(self, agent_id: str) -> bool:
        """Check if an agent's container is running."""
        name = self.container_name(agent_id)
        try:
            container = await asyncio.to_thread(self.client.containers.get, name)
            return container.status == "running"
        except NotFound:
            return False

    async def get_container_id(self, agent_id: str) -> str | None:
        """Get the container ID if the agent's container is running."""
        name = self.container_name(agent_id)
        try:
            container = await asyncio.to_thread(self.client.containers.get, name)
            if container.status == "running":
                return container.id
        except NotFound:
            pass
        return None

    async def _remove_if_exists(self, name: str, stop_first: bool = False) -> None:
        """Remove a container if it exists."""
        try:
            container = await asyncio.to_thread(self.client.containers.get, name)
            if stop_first and container.status == "running":
                await asyncio.to_thread(container.stop, timeout=10)
            await asyncio.to_thread(container.remove, force=True)
        except NotFound:
            pass

    def _ensure_agent_dirs(self, agent_id: str) -> None:
        """Ensure required agent directories exist on host."""
        self.config.container_config_path(agent_id).mkdir(parents=True, exist_ok=True)
        self.config.workspace_path(agent_id).mkdir(parents=True, exist_ok=True)

    def _resolve_host_path(self, path: Path) -> str:
        """Resolve a path suitable for Docker volume mounts.

        On Windows with Git Bash, paths need to be converted to
        Windows-style for the Docker daemon.
        """
        resolved = str(path.resolve())
        # On Windows, Docker Desktop expects Windows paths
        if platform.system() == "Windows":
            return resolved
        return resolved

    def _create_container(self, agent_id: str, name: str) -> docker.models.containers.Container:
        """Create and start a container (blocking, run in thread)."""
        project = self._resolve_host_path(self.config.project_root)
        workspace = self._resolve_host_path(
            self.config.workspace_path(agent_id)
        )
        sessions = self._resolve_host_path(
            self.config.project_root / ".claude" / "sessions"
        )
        container_config = self._resolve_host_path(
            self.config.container_config_path(agent_id)
        )
        mcp_json = self._resolve_host_path(
            self.config.project_root / "docker" / ".mcp.json"
        )
        settings_json = self._resolve_host_path(
            self.config.project_root / "docker" / ".claude-settings.json"
        )

        # Volume mounts
        volumes = {
            project: {"bind": "/pipe-dream", "mode": "ro"},
            workspace: {
                "bind": f"/pipe-dream/.claude/users/{agent_id}/workspace",
                "mode": "rw",
            },
            sessions: {"bind": "/pipe-dream/.claude/sessions", "mode": "rw"},
            mcp_json: {"bind": "/pipe-dream/.mcp.json", "mode": "ro"},
            settings_json: {
                "bind": "/pipe-dream/.claude/settings.local.json",
                "mode": "ro",
            },
            container_config: {"bind": "/claude-config", "mode": "rw"},
        }

        # For non-claude agents, mount their definition as CLAUDE.md
        if agent_id != "claude":
            agent_def = self._resolve_host_path(
                self.config.agent_definition_path(agent_id)
            )
            volumes[agent_def] = {
                "bind": "/pipe-dream/CLAUDE.md",
                "mode": "ro",
            }

        # Environment
        environment = {
            "HOME": "/",
            "CLAUDE_CONFIG_DIR": "/claude-config",
            "MCP_TIMEOUT": "60000",
            "QMS_USER": agent_id,
            "SETUP_ONLY": "1",
        }

        # Add GH_TOKEN if available
        gh_token = os.environ.get("GH_TOKEN")
        if not gh_token:
            env_file = self.config.project_root / "docker" / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("GH_TOKEN="):
                        gh_token = line.split("=", 1)[1].strip()
                        break
        if gh_token:
            environment["GH_TOKEN"] = gh_token

        container = self.client.containers.run(
            image=self.config.docker_image,
            name=name,
            hostname=agent_id,
            working_dir="/pipe-dream",
            detach=True,
            stdin_open=True,
            tty=True,
            volumes=volumes,
            environment=environment,
            extra_hosts={"host.docker.internal": "host-gateway"},
        )

        return container

    async def _wait_for_setup(self, name: str, timeout: float = 15.0) -> None:
        """Wait for the entrypoint's setup phase to complete."""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            try:
                container = await asyncio.to_thread(
                    self.client.containers.get, name
                )
                if container.status != "running":
                    raise RuntimeError(
                        f"Container {name} exited during setup"
                    )
                logs = await asyncio.to_thread(
                    container.logs, tail=20
                )
                if b"Setup complete. Waiting for docker exec" in logs:
                    return
            except NotFound:
                raise RuntimeError(f"Container {name} disappeared during setup")
            await asyncio.sleep(1.0)

        # If container is still running, proceed anyway (same as launch.sh)
        try:
            container = await asyncio.to_thread(self.client.containers.get, name)
            if container.status == "running":
                logger.warning(
                    "Container %s: setup message not seen, proceeding anyway", name
                )
                return
        except NotFound:
            pass

        raise RuntimeError(f"Container {name} failed to start within {timeout}s")

    async def _exec_claude(self, name: str) -> None:
        """Start claude inside tmux in the container.

        This is a fire-and-forget exec — claude runs interactively
        inside tmux and we don't capture its output here.
        """
        container = await asyncio.to_thread(self.client.containers.get, name)
        await asyncio.to_thread(
            container.exec_run,
            cmd=["tmux", "new-session", "-d", "-s", "agent", "claude"],
            detach=True,
            tty=True,
        )
        logger.info("claude started in tmux session for %s", name)

    async def _wait_for_ready(self, name: str, timeout: float = 60.0) -> None:
        """Wait for Claude Code to be ready for input.

        Polls tmux capture-pane output until the prompt character
        (U+276F) is detected, indicating Claude Code has finished
        initializing and is ready to accept user input.
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
                if "\u276f" in stdout.decode("utf-8", errors="replace"):
                    logger.info("Claude Code ready in %s", name)
                    return
            except (asyncio.TimeoutError, Exception):
                pass
            await asyncio.sleep(2.0)

        logger.warning(
            "Claude Code readiness not confirmed in %s after %.0fs -- "
            "container left running for inspection",
            name, timeout,
        )
        raise RuntimeError(
            f"Claude Code in {name} did not become ready within {timeout:.0f}s"
        )

    def close(self) -> None:
        """Close the Docker client."""
        if self._client is not None:
            self._client.close()
            self._client = None
