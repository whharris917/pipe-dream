"""Cross-platform service lifecycle management for Agent Hub.

Provides functions for starting, stopping, and monitoring the background
services (MCP servers, Hub, Docker containers) that support the agent
orchestration infrastructure.

Translated from the battle-tested bash logic in launch.sh and pd-status.
CR-069: Agent Hub Consolidation.
CR-088: Granular Service Control and Observability.
"""

import os
import platform
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import click
import httpx

from agent_hub.config import HubConfig


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TMUX_SESSION_NAME = "agent"
"""Tmux session name used inside agent containers."""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ServiceInfo:
    """Definition of a background service."""
    label: str
    port: int
    health_path: str


@dataclass
class ServiceStatus:
    """Runtime status of a background service."""
    label: str
    port: int
    alive: bool
    pid: int | None = None
    extra: str = ""


SERVICE_REGISTRY: dict[str, ServiceInfo] = {
    "qms-mcp": ServiceInfo("QMS MCP", 8000, "/mcp"),
    "git-mcp": ServiceInfo("Git MCP", 8001, "/mcp"),
    "hub": ServiceInfo("Agent Hub", 9000, "/api/health"),
}

SERVICES = list(SERVICE_REGISTRY.values())

VALID_AGENTS = ["claude", "qa", "tu_ui", "tu_scene", "tu_sketch", "tu_sim", "bu"]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _is_windows() -> bool:
    return platform.system() == "Windows" or os.name == "nt"


def find_python(project_root: Path) -> Path:
    """Locate the Python interpreter in the project venv."""
    candidates = [
        project_root / ".venv" / "Scripts" / "python.exe",
        project_root / ".venv" / "bin" / "python",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"No Python venv found at {project_root / '.venv'}"
    )


def find_pid_on_port(port: int) -> int | None:
    """Find the PID of the process listening on a given port (cross-platform)."""
    try:
        if _is_windows():
            result = subprocess.run(
                [
                    "powershell.exe", "-NoProfile", "-Command",
                    f"$c = Get-NetTCPConnection -LocalPort {port} "
                    f"-State Listen -ErrorAction SilentlyContinue "
                    f"| Select-Object -First 1; "
                    f"if ($c) {{ $c.OwningProcess }}",
                ],
                capture_output=True, text=True, timeout=10,
            )
            pid_str = result.stdout.strip()
            return int(pid_str) if pid_str.isdigit() else None
        else:
            # Try lsof first, then ss
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().splitlines()[0])

            result = subprocess.run(
                ["ss", "-tlnp", f"sport = :{port}"],
                capture_output=True, text=True, timeout=5,
            )
            import re
            match = re.search(r"pid=(\d+)", result.stdout)
            return int(match.group(1)) if match else None
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return None


def _tcp_alive(port: int, timeout: float = 3) -> bool:
    """Check if a service is listening via TCP connect.

    Used for MCP endpoints where HTTP probes cause server log noise (406).
    """
    try:
        with socket.create_connection(("localhost", port), timeout=timeout):
            return True
    except (ConnectionRefusedError, TimeoutError, OSError):
        return False


def _health_request(port: int, health_path: str) -> httpx.Response:
    """Send an HTTP GET health check request.

    Used for endpoints with real HTTP health responses (e.g., /api/health).
    """
    url = f"http://localhost:{port}{health_path}"
    return httpx.get(url, timeout=3)


def is_port_alive(port: int, health_path: str) -> bool:
    """Check if a service is responding on the given port."""
    if health_path == "/mcp":
        return _tcp_alive(port)
    try:
        _health_request(port, health_path)
        return True  # Any HTTP response means the service is up
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
        return False


def health_code(port: int, health_path: str) -> int:
    """Get the HTTP status code from a health endpoint."""
    if health_path == "/mcp":
        return 200 if _tcp_alive(port) else 0
    try:
        response = _health_request(port, health_path)
        return response.status_code
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
        return 0


# ---------------------------------------------------------------------------
# Service start helpers
# ---------------------------------------------------------------------------

def _wait_for_service(port: int, health_path: str, timeout: int = 10) -> bool:
    """Poll until a service responds on the given port."""
    for _ in range(timeout):
        if is_port_alive(port, health_path):
            return True
        time.sleep(1)
    return False


def _start_qms_mcp(config: HubConfig) -> None:
    """Start the QMS MCP server if not already running."""
    if is_port_alive(config.qms_mcp_port, "/mcp"):
        click.echo(click.style("  + ", fg="green") + "QMS MCP server already running")
        return

    click.echo("  Starting QMS MCP server...")
    python_exe = str(find_python(config.project_root))
    log_dir = config.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    with open(log_dir / "qms-mcp-server.log", "w") as log_file:
        subprocess.Popen(
            [
                python_exe, "-m", "qms_mcp",
                "--transport", "streamable-http",
                "--host", "0.0.0.0",
                "--port", str(config.qms_mcp_port),
                "--project-root", str(config.project_root),
            ],
            cwd=str(config.project_root / "qms-cli"),
            stdout=log_file, stderr=log_file,
        )
    if _wait_for_service(config.qms_mcp_port, "/mcp"):
        click.echo(click.style("  + ", fg="green") + "QMS MCP server started")
    else:
        click.echo(click.style("  x ", fg="red") + "QMS MCP server failed to start")
        raise SystemExit(1)


def _start_git_mcp(config: HubConfig) -> None:
    """Start the Git MCP server if not already running."""
    if is_port_alive(config.git_mcp_port, "/mcp"):
        click.echo(click.style("  + ", fg="green") + "Git MCP server already running")
        return

    click.echo("  Starting Git MCP server...")
    python_exe = str(find_python(config.project_root))
    log_dir = config.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    with open(log_dir / "git-mcp-server.log", "w") as log_file:
        subprocess.Popen(
            [
                python_exe, "-m", "git_mcp",
                "--transport", "streamable-http",
                "--host", "0.0.0.0",
                "--port", str(config.git_mcp_port),
                "--project-root", str(config.project_root),
            ],
            cwd=str(config.mcp_servers_dir),
            stdout=log_file, stderr=log_file,
        )
    if _wait_for_service(config.git_mcp_port, "/mcp"):
        click.echo(click.style("  + ", fg="green") + "Git MCP server started")
    else:
        click.echo(click.style("  x ", fg="red") + "Git MCP server failed to start")
        raise SystemExit(1)


def _start_hub(config: HubConfig) -> None:
    """Start the Agent Hub if not already running."""
    if is_port_alive(config.port, "/api/health"):
        click.echo(click.style("  + ", fg="green") + "Agent Hub already running")
        return

    click.echo("  Starting Agent Hub...")
    python_exe = str(find_python(config.project_root))
    log_dir = config.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    with open(log_dir / "agent-hub.log", "w") as log_file:
        subprocess.Popen(
            [
                python_exe, "-m", "agent_hub.cli", "start",
                "--project-root", str(config.project_root),
            ],
            cwd=str(config.project_root),
            stdout=log_file, stderr=log_file,
        )
    if _wait_for_service(config.port, "/api/health"):
        click.echo(click.style("  + ", fg="green") + "Agent Hub started")
    else:
        click.echo(click.style("  x ", fg="red") + "Agent Hub failed to start")
        raise SystemExit(1)


def ensure_mcp_servers(config: HubConfig) -> None:
    """Start QMS and Git MCP servers if not already running."""
    _start_qms_mcp(config)
    _start_git_mcp(config)


def ensure_hub(config: HubConfig) -> None:
    """Start the Agent Hub if not already running."""
    _start_hub(config)


def start_service(name: str, config: HubConfig) -> None:
    """Start an individual service by registry name.

    Auto-starts dependencies: Hub requires both MCP servers.

    Args:
        name: Service registry key ("qms-mcp", "git-mcp", "hub")
        config: Hub configuration
    """
    if name not in SERVICE_REGISTRY:
        raise ValueError(
            f"Unknown service: {name}. Valid: {', '.join(SERVICE_REGISTRY)}"
        )

    if name == "qms-mcp":
        _start_qms_mcp(config)
    elif name == "git-mcp":
        _start_git_mcp(config)
    elif name == "hub":
        # Hub depends on both MCP servers
        _start_qms_mcp(config)
        _start_git_mcp(config)
        _start_hub(config)


def stop_service(name: str, config: HubConfig) -> None:
    """Stop an individual service by registry name.

    Args:
        name: Service registry key ("qms-mcp", "git-mcp", "hub")
        config: Hub configuration
    """
    if name not in SERVICE_REGISTRY:
        raise ValueError(
            f"Unknown service: {name}. Valid: {', '.join(SERVICE_REGISTRY)}"
        )

    svc = SERVICE_REGISTRY[name]
    if not is_port_alive(svc.port, svc.health_path):
        click.echo(f"  {svc.label} is not running.")
        return

    stop_service_on_port(svc.port, svc.label)


def ensure_docker_image(config: HubConfig) -> None:
    """Build Docker image if it doesn't exist."""
    result = subprocess.run(
        ["docker", "image", "inspect", f"{config.docker_image}:latest"],
        capture_output=True, timeout=10,
    )
    if result.returncode == 0:
        click.echo(click.style("  + ", fg="green") + "Docker image exists")
    else:
        click.echo("  Building Docker image...")
        env = os.environ.copy()
        if _is_windows():
            env["MSYS_NO_PATHCONV"] = "1"
        subprocess.run(
            ["docker-compose", "build", "claude-agent"],
            cwd=str(config.docker_dir),
            env=env,
            check=True,
        )
        click.echo(click.style("  + ", fg="green") + "Docker image built")


# ---------------------------------------------------------------------------
# Service stop helpers
# ---------------------------------------------------------------------------

def stop_service_on_port(port: int, label: str) -> bool:
    """Kill the process listening on a given port."""
    pid = find_pid_on_port(port)
    if pid is None:
        return False

    try:
        if _is_windows():
            subprocess.run(
                ["taskkill.exe", "/PID", str(pid), "/F"],
                capture_output=True, timeout=10,
            )
        else:
            os.kill(pid, 9)
        click.echo(click.style("  + ", fg="green") + f"Killed {label} (PID {pid} on :{port})")
        return True
    except (subprocess.TimeoutExpired, ProcessLookupError, PermissionError):
        click.echo(click.style("  ! ", fg="yellow") + f"Could not kill {label} (PID {pid})")
        return False


def get_services_status(config: HubConfig) -> list[ServiceStatus]:
    """Get the status of all background services."""
    results = []
    for svc in SERVICES:
        alive = is_port_alive(svc.port, svc.health_path)
        pid = find_pid_on_port(svc.port) if alive else None
        extra = ""

        # For Hub, get agent summary
        if svc.label == "Agent Hub" and alive:
            try:
                resp = httpx.get(
                    f"http://localhost:{svc.port}/api/status", timeout=3
                )
                if resp.status_code == 200:
                    data = resp.json()
                    agents = data.get("agents", [])
                    running = sum(1 for a in agents if a.get("state") == "running")
                    stale = sum(1 for a in agents if a.get("state") == "stale")
                    stopped = sum(1 for a in agents if a.get("state") == "stopped")
                    parts = []
                    if running > 0:
                        parts.append(f"{running} running")
                    if stale > 0:
                        parts.append(f"{stale} stale")
                    parts.append(f"{stopped} stopped")
                    extra = f"({', '.join(parts)})"
            except (httpx.ConnectError, httpx.TimeoutException):
                pass

        results.append(ServiceStatus(
            label=svc.label, port=svc.port,
            alive=alive, pid=pid, extra=extra,
        ))
    return results


def classify_container(
    name: str, valid_agents: list[str], prefix: str = "agent-"
) -> str:
    """Classify a container as 'managed' or 'manual'.

    Managed: matches {prefix}{known_agent_id} exactly (e.g., agent-claude).
    Manual: anything else matching the docker ps filter (e.g., docker-claude-agent-1).
    """
    for agent_id in valid_agents:
        if name == f"{prefix}{agent_id}":
            return "managed"
    return "manual"


def get_containers() -> list[tuple[str, str, str]]:
    """Get agent containers. Returns list of (name, state, status)."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=agent-",
             "--format", "{{.Names}}\t{{.State}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        containers = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("\t", 2)
            if len(parts) == 3:
                containers.append((parts[0], parts[1], parts[2]))
        return containers
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def stop_all_services(config: HubConfig, skip_confirm: bool = False) -> None:
    """Stop all services and remove containers."""
    statuses = get_services_status(config)
    containers = get_containers()

    running_services = [s for s in statuses if s.alive]
    has_work = bool(running_services) or bool(containers)

    if not has_work:
        click.echo("  Nothing to stop -- no services or containers found.")
        return

    # Show what will be stopped
    click.echo(click.style("  The following will be stopped:", fg="yellow"))
    click.echo()

    for s in running_services:
        pid_str = f"  (PID {s.pid})" if s.pid else ""
        click.echo(f"    {s.label:<12} :{s.port:<5}{pid_str}")

    if containers:
        click.echo()
        for name, state, status_str in containers:
            click.echo(f"    Container: {name}")

    click.echo()
    if not skip_confirm:
        if not click.confirm("  Proceed?", default=False):
            click.echo("  Cancelled.")
            return

    click.echo()

    # Kill services
    for s in running_services:
        stop_service_on_port(s.port, s.label)

    # Remove containers
    for name, _, _ in containers:
        try:
            subprocess.run(
                ["docker", "rm", "-f", name],
                capture_output=True, timeout=10,
            )
            click.echo(click.style("  + ", fg="green") + f"Removed container {name}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            click.echo(click.style("  ! ", fg="yellow") + f"Could not remove container {name}")

    click.echo()
    click.echo(click.style("  Done.", fg="green"))


# ---------------------------------------------------------------------------
# Terminal spawning
# ---------------------------------------------------------------------------

def launch_in_terminal(agent_id: str, config: HubConfig) -> None:
    """Spawn an agent session in a new OS terminal window."""
    if _is_windows():
        # Git Bash / MSYS / Cygwin on Windows
        subprocess.Popen(
            f'start "" mintty -t "Agent: {agent_id}" '
            f'-e bash -l -c "agent-hub launch {agent_id}; '
            f'read -p \'Press Enter to close...\'"',
            shell=True,
        )
    elif platform.system() == "Darwin":
        subprocess.Popen([
            "osascript", "-e",
            f'tell application "Terminal" to do script '
            f'"agent-hub launch {agent_id}"',
        ])
    else:
        # Linux: try terminal emulators in order
        terminals = [
            ("gnome-terminal", ["gnome-terminal", "--title", f"Agent: {agent_id}",
                                "--", "bash", "-c",
                                f"agent-hub launch {agent_id}; "
                                f"read -p 'Press Enter to close...'"]),
            ("xterm", ["xterm", "-title", f"Agent: {agent_id}", "-e",
                       "bash", "-c",
                       f"agent-hub launch {agent_id}; "
                       f"read -p 'Press Enter to close...'"]),
            ("konsole", ["konsole", "--new-tab", "-e",
                         "bash", "-c",
                         f"agent-hub launch {agent_id}; "
                         f"read -p 'Press Enter to close...'"]),
        ]
        import shutil
        for name, cmd in terminals:
            if shutil.which(name):
                subprocess.Popen(cmd)
                return
        raise RuntimeError("No supported terminal emulator found")
