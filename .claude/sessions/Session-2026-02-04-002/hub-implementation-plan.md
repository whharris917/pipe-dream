# Agent Hub Implementation Plan

This document details the implementation of the Agent Hub—the programmatic coordinator for multi-agent container orchestration.

## Overview

The Hub is a Python service that:
- Manages Docker container lifecycle for QMS agents
- Multiplexes PTY connections between containers and clients
- Watches agent inboxes and enforces launch/shutdown policies
- Exposes REST and WebSocket APIs for clients (GUI, CLI)

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.11+ | Consistency with QMS CLI, async support |
| Async runtime | asyncio | Native Python, no external deps |
| HTTP/WebSocket | FastAPI + uvicorn | Modern, async-native, auto-docs |
| Docker | docker-py (aiodocker) | Official SDK, async variant available |
| File watching | watchfiles | Fast, cross-platform, async-compatible |
| PTY | pty + asyncio streams | Standard library for Unix PTY |
| CLI | click | Consistent with QMS CLI |

## Dependencies

```
# requirements.txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
websockets>=12.0
aiodocker>=0.21.0
watchfiles>=0.21.0
click>=8.1.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
```

## Directory Structure

```
agent-hub/
├── agent_hub/
│   ├── __init__.py
│   ├── __main__.py           # CLI entry point
│   ├── cli.py                # Click CLI commands
│   ├── hub.py                # Core Hub class
│   ├── models.py             # Pydantic models
│   ├── container.py          # Docker container management
│   ├── pty_manager.py        # PTY multiplexing
│   ├── inbox.py              # Inbox watcher
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py         # FastAPI app
│   │   ├── routes.py         # REST endpoints
│   │   └── websocket.py      # WebSocket handler
│   └── config.py             # Configuration
├── tests/
│   ├── __init__.py
│   ├── test_hub.py
│   ├── test_container.py
│   ├── test_inbox.py
│   └── conftest.py           # Fixtures
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Data Models

```python
# agent_hub/models.py

from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class AgentState(str, Enum):
    INACTIVE = "inactive"      # Container not running
    STARTING = "starting"      # Container starting up
    ACTIVE = "active"          # Container running, PTY attached
    STOPPING = "stopping"      # Container shutting down
    ERROR = "error"            # Container failed

class LaunchPolicy(str, Enum):
    MANUAL = "manual"          # Only launch on explicit request
    AUTO_ON_TASK = "auto"      # Launch when inbox has tasks
    ALWAYS_ON = "always"       # Launch with hub, never auto-stop

class ShutdownPolicy(str, Enum):
    MANUAL = "manual"          # Only stop on explicit request
    ON_INBOX_EMPTY = "empty"   # Stop when inbox is empty
    IDLE_TIMEOUT = "idle"      # Stop after idle timeout

class AgentPolicy(BaseModel):
    launch: LaunchPolicy = LaunchPolicy.MANUAL
    shutdown: ShutdownPolicy = ShutdownPolicy.MANUAL
    idle_timeout_minutes: int = 30

class Agent(BaseModel):
    id: str                              # e.g., "claude", "qa", "tu_ui"
    state: AgentState = AgentState.INACTIVE
    policy: AgentPolicy = AgentPolicy()
    container_id: str | None = None
    started_at: datetime | None = None
    last_activity: datetime | None = None
    inbox_count: int = 0

class AgentSummary(BaseModel):
    """Lightweight agent info for list endpoints."""
    id: str
    state: AgentState
    inbox_count: int
    policy: LaunchPolicy

class HubStatus(BaseModel):
    agents: list[AgentSummary]
    uptime_seconds: float
    mcp_servers: dict[str, bool]  # server name -> healthy
```

## Configuration

```python
# agent_hub/config.py

from pydantic_settings import BaseSettings
from pathlib import Path

class HubConfig(BaseSettings):
    # Paths
    project_root: Path = Path.cwd()
    users_dir: Path = Path(".claude/users")
    agents_dir: Path = Path(".claude/agents")

    # Network
    host: str = "127.0.0.1"
    port: int = 9000

    # Docker
    docker_image: str = "claude-agent"
    container_prefix: str = "agent-"

    # MCP servers (for health checks)
    qms_mcp_url: str = "http://localhost:8000/health"
    git_mcp_url: str = "http://localhost:8001/health"

    # Agent defaults
    default_launch_policy: LaunchPolicy = LaunchPolicy.MANUAL
    default_shutdown_policy: ShutdownPolicy = ShutdownPolicy.MANUAL
    default_idle_timeout: int = 30

    # Agents to manage
    agents: list[str] = [
        "claude", "qa", "tu_ui", "tu_scene",
        "tu_sketch", "tu_sim", "bu"
    ]

    # Special config for orchestrator
    orchestrator_agent: str = "claude"
    orchestrator_policy: LaunchPolicy = LaunchPolicy.ALWAYS_ON

    class Config:
        env_prefix = "HUB_"
        env_file = ".env"

    @property
    def inbox_paths(self) -> dict[str, Path]:
        """Return inbox path for each agent."""
        return {
            agent: self.project_root / self.users_dir / agent / "inbox"
            for agent in self.agents
        }
```

## Core Hub Class

```python
# agent_hub/hub.py

import asyncio
from datetime import datetime
from typing import Callable

from .models import Agent, AgentState, LaunchPolicy, ShutdownPolicy, AgentPolicy
from .config import HubConfig
from .container import ContainerManager
from .pty_manager import PtyManager
from .inbox import InboxWatcher

class AgentHub:
    def __init__(self, config: HubConfig):
        self.config = config
        self.agents: dict[str, Agent] = {}
        self.container_mgr = ContainerManager(config)
        self.pty_mgr = PtyManager()
        self.inbox_watcher = InboxWatcher(config, self._on_inbox_change)
        self._started_at: datetime | None = None
        self._subscribers: dict[str, list[Callable]] = {}  # agent_id -> callbacks

    async def start(self):
        """Start the hub and all always-on agents."""
        self._started_at = datetime.now()

        # Initialize agent records
        for agent_id in self.config.agents:
            policy = AgentPolicy(
                launch=self.config.orchestrator_policy
                    if agent_id == self.config.orchestrator_agent
                    else self.config.default_launch_policy,
                shutdown=self.config.default_shutdown_policy,
                idle_timeout_minutes=self.config.default_idle_timeout,
            )
            self.agents[agent_id] = Agent(id=agent_id, policy=policy)

        # Start inbox watcher
        await self.inbox_watcher.start()

        # Launch always-on agents
        for agent_id, agent in self.agents.items():
            if agent.policy.launch == LaunchPolicy.ALWAYS_ON:
                await self.start_agent(agent_id)

    async def stop(self):
        """Stop the hub and all running agents."""
        await self.inbox_watcher.stop()

        for agent_id, agent in self.agents.items():
            if agent.state == AgentState.ACTIVE:
                await self.stop_agent(agent_id)

    async def start_agent(self, agent_id: str) -> Agent:
        """Start an agent container."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_id}")

        if agent.state == AgentState.ACTIVE:
            return agent

        agent.state = AgentState.STARTING
        await self._broadcast_state_change(agent)

        try:
            # Start container
            container_id = await self.container_mgr.start(agent_id)
            agent.container_id = container_id

            # Attach PTY
            await self.pty_mgr.attach(
                agent_id,
                container_id,
                on_output=lambda data: self._on_pty_output(agent_id, data)
            )

            agent.state = AgentState.ACTIVE
            agent.started_at = datetime.now()
            agent.last_activity = datetime.now()

        except Exception as e:
            agent.state = AgentState.ERROR
            raise

        finally:
            await self._broadcast_state_change(agent)

        return agent

    async def stop_agent(self, agent_id: str) -> Agent:
        """Stop an agent container."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_id}")

        if agent.state != AgentState.ACTIVE:
            return agent

        agent.state = AgentState.STOPPING
        await self._broadcast_state_change(agent)

        try:
            # Detach PTY
            await self.pty_mgr.detach(agent_id)

            # Stop container
            if agent.container_id:
                await self.container_mgr.stop(agent.container_id)

            agent.state = AgentState.INACTIVE
            agent.container_id = None
            agent.started_at = None

        except Exception as e:
            agent.state = AgentState.ERROR
            raise

        finally:
            await self._broadcast_state_change(agent)

        return agent

    async def send_input(self, agent_id: str, data: bytes):
        """Send input to an agent's PTY."""
        agent = self.agents.get(agent_id)
        if not agent or agent.state != AgentState.ACTIVE:
            raise ValueError(f"Agent not active: {agent_id}")

        await self.pty_mgr.write(agent_id, data)
        agent.last_activity = datetime.now()

    async def resize_pty(self, agent_id: str, cols: int, rows: int):
        """Resize an agent's PTY."""
        await self.pty_mgr.resize(agent_id, cols, rows)

    def subscribe(self, agent_id: str, callback: Callable):
        """Subscribe to PTY output for an agent."""
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = []
        self._subscribers[agent_id].append(callback)

    def unsubscribe(self, agent_id: str, callback: Callable):
        """Unsubscribe from PTY output."""
        if agent_id in self._subscribers:
            self._subscribers[agent_id].remove(callback)

    async def _on_inbox_change(self, agent_id: str, task_count: int):
        """Handle inbox changes."""
        agent = self.agents.get(agent_id)
        if not agent:
            return

        agent.inbox_count = task_count

        # Auto-launch if needed
        if task_count > 0 and agent.state == AgentState.INACTIVE:
            if agent.policy.launch == LaunchPolicy.AUTO_ON_TASK:
                await self.start_agent(agent_id)

        # Auto-stop if needed
        elif task_count == 0 and agent.state == AgentState.ACTIVE:
            if agent.policy.shutdown == ShutdownPolicy.ON_INBOX_EMPTY:
                await self.stop_agent(agent_id)

        await self._broadcast_state_change(agent)

    def _on_pty_output(self, agent_id: str, data: bytes):
        """Handle PTY output from an agent."""
        agent = self.agents.get(agent_id)
        if agent:
            agent.last_activity = datetime.now()

        # Notify subscribers
        for callback in self._subscribers.get(agent_id, []):
            asyncio.create_task(callback(data))

    async def _broadcast_state_change(self, agent: Agent):
        """Broadcast agent state change to all subscribers."""
        # This will be called by the API layer to notify WebSocket clients
        pass  # Implemented in api/websocket.py
```

## Container Management

```python
# agent_hub/container.py

import aiodocker
from .config import HubConfig

class ContainerManager:
    def __init__(self, config: HubConfig):
        self.config = config
        self.docker: aiodocker.Docker | None = None

    async def connect(self):
        """Connect to Docker daemon."""
        self.docker = aiodocker.Docker()

    async def disconnect(self):
        """Disconnect from Docker daemon."""
        if self.docker:
            await self.docker.close()

    async def start(self, agent_id: str) -> str:
        """Start a container for an agent. Returns container ID."""
        if not self.docker:
            await self.connect()

        container_name = f"{self.config.container_prefix}{agent_id}"

        # Check if container already exists
        try:
            container = await self.docker.containers.get(container_name)
            info = await container.show()
            if info["State"]["Running"]:
                return container.id
            else:
                await container.start()
                return container.id
        except aiodocker.exceptions.DockerError:
            pass  # Container doesn't exist, create it

        # Build volume mounts
        project_root = str(self.config.project_root)
        workspace_path = f"{project_root}/.claude/users/{agent_id}/workspace"
        container_config_path = f"{project_root}/.claude/users/{agent_id}/container"
        sessions_path = f"{project_root}/.claude/sessions"

        # Determine CLAUDE.md mount
        if agent_id == self.config.orchestrator_agent:
            claude_md_mount = f"{project_root}/CLAUDE.md:/pipe-dream/CLAUDE.md:ro"
        else:
            agent_def = f"{project_root}/.claude/agents/{agent_id}.md"
            claude_md_mount = f"{agent_def}:/pipe-dream/CLAUDE.md:ro"

        config = {
            "Image": self.config.docker_image,
            "Hostname": agent_id,
            "WorkingDir": "/pipe-dream",
            "Env": [
                f"QMS_USER={agent_id}",
                "HOME=/",
                "CLAUDE_CONFIG_DIR=/claude-config",
                "MCP_TIMEOUT=60000",
            ],
            "HostConfig": {
                "Binds": [
                    f"{project_root}:/pipe-dream:ro",
                    f"{workspace_path}:/pipe-dream/.claude/users/{agent_id}/workspace:rw",
                    f"{sessions_path}:/pipe-dream/.claude/sessions:rw",
                    f"{container_config_path}:/claude-config:rw",
                    f"{project_root}/docker/.mcp.json:/pipe-dream/.mcp.json:ro",
                    f"{project_root}/docker/.claude-settings.json:/pipe-dream/.claude/settings.local.json:ro",
                    claude_md_mount,
                ],
                "ExtraHosts": ["host.docker.internal:host-gateway"],
            },
            "Tty": True,
            "OpenStdin": True,
            "AttachStdin": True,
            "AttachStdout": True,
            "AttachStderr": True,
        }

        container = await self.docker.containers.create(
            config=config,
            name=container_name,
        )
        await container.start()

        return container.id

    async def stop(self, container_id: str):
        """Stop a container."""
        if not self.docker:
            return

        try:
            container = await self.docker.containers.get(container_id)
            await container.stop()
        except aiodocker.exceptions.DockerError:
            pass  # Container already stopped or doesn't exist

    async def exec_claude(self, container_id: str) -> tuple:
        """
        Execute 'claude' command in container and return streams.
        Returns (stdin, stdout) streams for PTY attachment.
        """
        if not self.docker:
            await self.connect()

        container = await self.docker.containers.get(container_id)

        # Create exec instance
        exec_instance = await container.exec(
            cmd=["claude"],
            stdin=True,
            stdout=True,
            stderr=True,
            tty=True,
        )

        # Start exec and get streams
        stream = exec_instance.start(detach=False)

        return stream
```

## PTY Manager

```python
# agent_hub/pty_manager.py

import asyncio
from typing import Callable
from aiodocker import Docker

class PtySession:
    def __init__(self, agent_id: str, stream, on_output: Callable):
        self.agent_id = agent_id
        self.stream = stream
        self.on_output = on_output
        self._read_task: asyncio.Task | None = None

    async def start(self):
        """Start reading from PTY."""
        self._read_task = asyncio.create_task(self._read_loop())

    async def stop(self):
        """Stop reading from PTY."""
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

    async def write(self, data: bytes):
        """Write to PTY stdin."""
        await self.stream.write_in(data)

    async def resize(self, cols: int, rows: int):
        """Resize PTY."""
        # Note: aiodocker exec resize requires the exec ID
        # This may need adjustment based on actual API
        pass

    async def _read_loop(self):
        """Read output from PTY and dispatch to callback."""
        try:
            async for data in self.stream:
                if data:
                    self.on_output(data)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # Log error, notify of disconnect
            pass


class PtyManager:
    def __init__(self):
        self.sessions: dict[str, PtySession] = {}
        self.docker: Docker | None = None

    async def attach(
        self,
        agent_id: str,
        container_id: str,
        on_output: Callable[[bytes], None]
    ):
        """Attach to a container and start claude."""
        if not self.docker:
            self.docker = Docker()

        container = await self.docker.containers.get(container_id)

        # Execute claude command with TTY
        exec_instance = await container.exec(
            cmd=["claude"],
            stdin=True,
            stdout=True,
            stderr=True,
            tty=True,
        )

        stream = exec_instance.start(detach=False)

        session = PtySession(agent_id, stream, on_output)
        self.sessions[agent_id] = session
        await session.start()

    async def detach(self, agent_id: str):
        """Detach from a container's PTY."""
        session = self.sessions.pop(agent_id, None)
        if session:
            await session.stop()

    async def write(self, agent_id: str, data: bytes):
        """Write to an agent's PTY."""
        session = self.sessions.get(agent_id)
        if session:
            await session.write(data)

    async def resize(self, agent_id: str, cols: int, rows: int):
        """Resize an agent's PTY."""
        session = self.sessions.get(agent_id)
        if session:
            await session.resize(cols, rows)
```

## Inbox Watcher

```python
# agent_hub/inbox.py

import asyncio
from pathlib import Path
from typing import Callable
from watchfiles import awatch, Change

from .config import HubConfig

class InboxWatcher:
    def __init__(
        self,
        config: HubConfig,
        on_change: Callable[[str, int], asyncio.coroutine]
    ):
        self.config = config
        self.on_change = on_change
        self._watch_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    async def start(self):
        """Start watching all inbox directories."""
        # Ensure inbox directories exist
        for agent_id, inbox_path in self.config.inbox_paths.items():
            inbox_path.mkdir(parents=True, exist_ok=True)

        # Initial scan
        for agent_id, inbox_path in self.config.inbox_paths.items():
            count = self._count_tasks(inbox_path)
            await self.on_change(agent_id, count)

        # Start watch task
        self._watch_task = asyncio.create_task(self._watch_loop())

    async def stop(self):
        """Stop watching."""
        self._stop_event.set()
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass

    def _count_tasks(self, inbox_path: Path) -> int:
        """Count task files in an inbox."""
        if not inbox_path.exists():
            return 0
        return len(list(inbox_path.glob("*.md")))

    def _get_agent_from_path(self, path: Path) -> str | None:
        """Extract agent ID from a file path."""
        # Path format: .claude/users/{agent}/inbox/task.md
        parts = path.parts
        try:
            users_idx = parts.index("users")
            return parts[users_idx + 1]
        except (ValueError, IndexError):
            return None

    async def _watch_loop(self):
        """Watch for inbox changes."""
        watch_paths = [str(p) for p in self.config.inbox_paths.values()]

        try:
            async for changes in awatch(*watch_paths, stop_event=self._stop_event):
                # Group changes by agent
                affected_agents = set()
                for change_type, path in changes:
                    agent_id = self._get_agent_from_path(Path(path))
                    if agent_id:
                        affected_agents.add(agent_id)

                # Notify for each affected agent
                for agent_id in affected_agents:
                    inbox_path = self.config.inbox_paths.get(agent_id)
                    if inbox_path:
                        count = self._count_tasks(inbox_path)
                        await self.on_change(agent_id, count)

        except asyncio.CancelledError:
            raise
```

## API Server

```python
# agent_hub/api/server.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .websocket import websocket_endpoint
from ..hub import AgentHub
from ..config import HubConfig

def create_app(hub: AgentHub, config: HubConfig) -> FastAPI:
    app = FastAPI(
        title="Agent Hub",
        description="Multi-agent container orchestration",
        version="0.1.0",
    )

    # CORS for GUI
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store hub reference
    app.state.hub = hub
    app.state.config = config

    # REST routes
    app.include_router(router, prefix="/api")

    # WebSocket endpoint
    app.add_api_websocket_route("/ws", websocket_endpoint)

    return app
```

```python
# agent_hub/api/routes.py

from fastapi import APIRouter, HTTPException, Request
from ..models import Agent, AgentSummary, AgentPolicy, HubStatus

router = APIRouter()

@router.get("/agents", response_model=list[AgentSummary])
async def list_agents(request: Request):
    """List all agents and their states."""
    hub = request.app.state.hub
    return [
        AgentSummary(
            id=agent.id,
            state=agent.state,
            inbox_count=agent.inbox_count,
            policy=agent.policy.launch,
        )
        for agent in hub.agents.values()
    ]

@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, request: Request):
    """Get detailed agent info."""
    hub = request.app.state.hub
    agent = hub.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/agents/{agent_id}/start", response_model=Agent)
async def start_agent(agent_id: str, request: Request):
    """Start an agent container."""
    hub = request.app.state.hub
    try:
        return await hub.start_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_id}/stop", response_model=Agent)
async def stop_agent(agent_id: str, request: Request):
    """Stop an agent container."""
    hub = request.app.state.hub
    try:
        return await hub.stop_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/policy", response_model=AgentPolicy)
async def get_policy(agent_id: str, request: Request):
    """Get agent launch/shutdown policy."""
    hub = request.app.state.hub
    agent = hub.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.policy

@router.put("/agents/{agent_id}/policy", response_model=AgentPolicy)
async def set_policy(agent_id: str, policy: AgentPolicy, request: Request):
    """Set agent launch/shutdown policy."""
    hub = request.app.state.hub
    agent = hub.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.policy = policy
    return agent.policy

@router.get("/health")
async def health_check(request: Request):
    """Hub health check."""
    return {"status": "ok"}

@router.get("/status", response_model=HubStatus)
async def hub_status(request: Request):
    """Full hub status."""
    hub = request.app.state.hub
    from datetime import datetime

    uptime = (datetime.now() - hub._started_at).total_seconds() if hub._started_at else 0

    return HubStatus(
        agents=[
            AgentSummary(
                id=agent.id,
                state=agent.state,
                inbox_count=agent.inbox_count,
                policy=agent.policy.launch,
            )
            for agent in hub.agents.values()
        ],
        uptime_seconds=uptime,
        mcp_servers={
            "qms": True,  # TODO: actual health check
            "git": True,
        },
    )
```

```python
# agent_hub/api/websocket.py

import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from ..models import AgentState

class WebSocketClient:
    def __init__(self, websocket: WebSocket, hub):
        self.websocket = websocket
        self.hub = hub
        self.subscriptions: set[str] = set()

    async def handle(self):
        """Handle WebSocket connection."""
        await self.websocket.accept()

        try:
            while True:
                data = await self.websocket.receive_text()
                msg = json.loads(data)
                await self._handle_message(msg)
        except WebSocketDisconnect:
            self._cleanup()

    async def _handle_message(self, msg: dict):
        """Handle incoming WebSocket message."""
        msg_type = msg.get("type")

        if msg_type == "subscribe":
            agent_id = msg.get("agent_id")
            if agent_id and agent_id in self.hub.agents:
                self.subscriptions.add(agent_id)
                self.hub.subscribe(agent_id, self._on_pty_output)
                await self._send({"type": "subscribed", "agent_id": agent_id})

        elif msg_type == "unsubscribe":
            agent_id = msg.get("agent_id")
            if agent_id in self.subscriptions:
                self.subscriptions.discard(agent_id)
                self.hub.unsubscribe(agent_id, self._on_pty_output)
                await self._send({"type": "unsubscribed", "agent_id": agent_id})

        elif msg_type == "input":
            agent_id = msg.get("agent_id")
            data = msg.get("data", "")
            if agent_id in self.subscriptions:
                await self.hub.send_input(agent_id, data.encode())

        elif msg_type == "resize":
            agent_id = msg.get("agent_id")
            cols = msg.get("cols", 80)
            rows = msg.get("rows", 24)
            if agent_id in self.subscriptions:
                await self.hub.resize_pty(agent_id, cols, rows)

    async def _on_pty_output(self, data: bytes):
        """Callback for PTY output."""
        # Find which agent this is for
        # (In practice, we'd pass agent_id through the callback)
        await self._send({
            "type": "output",
            "data": data.decode("utf-8", errors="replace"),
        })

    async def _send(self, msg: dict):
        """Send message to client."""
        await self.websocket.send_text(json.dumps(msg))

    def _cleanup(self):
        """Clean up subscriptions on disconnect."""
        for agent_id in self.subscriptions:
            self.hub.unsubscribe(agent_id, self._on_pty_output)


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint handler."""
    hub = websocket.app.state.hub
    client = WebSocketClient(websocket, hub)
    await client.handle()
```

## CLI

```python
# agent_hub/cli.py

import asyncio
import click
import uvicorn

from .hub import AgentHub
from .config import HubConfig
from .api.server import create_app

@click.group()
def cli():
    """Agent Hub - Multi-agent container orchestration."""
    pass

@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind")
@click.option("--port", default=9000, help="Port to bind")
@click.option("--daemon", is_flag=True, help="Run in background")
def start(host: str, port: int, daemon: bool):
    """Start the hub."""
    config = HubConfig(host=host, port=port)
    hub = AgentHub(config)
    app = create_app(hub, config)

    async def run():
        await hub.start()
        config = uvicorn.Config(app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()

    if daemon:
        # TODO: Proper daemonization
        click.echo(f"Starting hub in background on {host}:{port}...")
    else:
        click.echo(f"Starting hub on {host}:{port}...")
        asyncio.run(run())

@cli.command()
def status():
    """Show hub and agent status."""
    import httpx

    try:
        response = httpx.get("http://localhost:9000/api/status")
        data = response.json()

        click.echo("AGENT       STATE      INBOX   POLICY")
        click.echo("-" * 45)
        for agent in data["agents"]:
            click.echo(
                f"{agent['id']:<12}{agent['state']:<11}"
                f"{agent['inbox_count']:<8}{agent['policy']}"
            )
    except httpx.ConnectError:
        click.echo("Hub is not running. Start with: agent-hub start")

@cli.command("start-agent")
@click.argument("agent_id")
def start_agent(agent_id: str):
    """Start an agent container."""
    import httpx

    try:
        response = httpx.post(f"http://localhost:9000/api/agents/{agent_id}/start")
        if response.status_code == 200:
            click.echo(f"Started {agent_id}")
        else:
            click.echo(f"Error: {response.json().get('detail')}")
    except httpx.ConnectError:
        click.echo("Hub is not running.")

@cli.command("stop-agent")
@click.argument("agent_id")
def stop_agent(agent_id: str):
    """Stop an agent container."""
    import httpx

    try:
        response = httpx.post(f"http://localhost:9000/api/agents/{agent_id}/stop")
        if response.status_code == 200:
            click.echo(f"Stopped {agent_id}")
        else:
            click.echo(f"Error: {response.json().get('detail')}")
    except httpx.ConnectError:
        click.echo("Hub is not running.")

@cli.command()
@click.argument("agent_id")
def attach(agent_id: str):
    """Attach terminal to an agent (like tmux attach)."""
    # TODO: Implement terminal attachment via WebSocket
    click.echo("Not yet implemented")

if __name__ == "__main__":
    cli()
```

```python
# agent_hub/__main__.py

from .cli import cli

if __name__ == "__main__":
    cli()
```

## Implementation Phases

### Phase 1: Core Structure
- [ ] Set up project structure with pyproject.toml
- [ ] Implement models.py with all data structures
- [ ] Implement config.py with environment loading
- [ ] Basic CLI skeleton

### Phase 2: Container Management
- [ ] Implement container.py with Docker integration
- [ ] Test starting/stopping containers manually
- [ ] Verify volume mounts work correctly
- [ ] Handle container naming and reuse

### Phase 3: PTY Management
- [ ] Implement pty_manager.py
- [ ] Test attaching to container and running claude
- [ ] Verify stdin/stdout streaming works
- [ ] Handle PTY resize

### Phase 4: Inbox Watching
- [ ] Implement inbox.py with watchfiles
- [ ] Test detecting inbox changes
- [ ] Verify initial scan on startup
- [ ] Test auto-launch policy

### Phase 5: API Server
- [ ] Implement REST endpoints
- [ ] Implement WebSocket handler
- [ ] Test from curl/wscat
- [ ] Add CORS for GUI

### Phase 6: Integration
- [ ] Wire all components together in hub.py
- [ ] End-to-end test: start hub, start agent, send input, receive output
- [ ] Test policy enforcement (auto-launch, auto-stop)
- [ ] Stress test with multiple agents

### Phase 7: CLI Polish
- [ ] Implement `attach` command for terminal access
- [ ] Add `--daemon` mode with proper process management
- [ ] Add logging configuration
- [ ] Write README

## Testing Strategy

```python
# tests/conftest.py

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from agent_hub.config import HubConfig
from agent_hub.hub import AgentHub

@pytest.fixture
def config(tmp_path):
    return HubConfig(
        project_root=tmp_path,
        agents=["test_agent"],
    )

@pytest.fixture
def mock_docker():
    return AsyncMock()

@pytest.fixture
async def hub(config, mock_docker, monkeypatch):
    monkeypatch.setattr("agent_hub.container.aiodocker.Docker", lambda: mock_docker)
    hub = AgentHub(config)
    await hub.start()
    yield hub
    await hub.stop()
```

## Open Questions Resolved

| Question | Decision |
|----------|----------|
| PTY attachment | Use aiodocker exec with TTY |
| Hub port | Default 9000, configurable via HUB_PORT |
| State persistence | Policies stored in memory; persist to file in future |
| Multiple GUIs | Supported - Hub broadcasts to all WebSocket clients |

## Next Steps

1. Create `agent-hub/` directory structure
2. Initialize with pyproject.toml
3. Implement Phase 1 (core structure)
4. Iterate through remaining phases
5. Create CR to formally adopt into QMS governance
