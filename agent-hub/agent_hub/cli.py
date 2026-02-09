"""CLI for the Agent Hub."""

import asyncio
import logging
import sys

import click
import uvicorn

from agent_hub.config import HubConfig
from agent_hub.hub import AgentHub
from agent_hub.api.server import create_app


@click.group()
def cli():
    """Agent Hub - Multi-agent container orchestration for Pipe Dream."""
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind")
@click.option("--port", default=9000, type=int, help="Port to bind")
@click.option(
    "--project-root", default=None, type=click.Path(exists=True),
    help="Project root directory (default: cwd)",
)
@click.option("--log-level", default="info", help="Logging level")
def start(host: str, port: int, project_root: str | None, log_level: str):
    """Start the Hub as a foreground service."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    kwargs = {"host": host, "port": port}
    if project_root:
        kwargs["project_root"] = project_root

    config = HubConfig(**kwargs)
    hub = AgentHub(config)
    app = create_app(hub)

    click.echo(f"Starting Agent Hub on {host}:{port}")
    click.echo(f"Project root: {config.project_root}")
    click.echo(f"Agents: {', '.join(config.agents)}")
    click.echo()

    uvicorn.run(app, host=host, port=port, log_level=log_level)


@cli.command()
@click.option("--hub-url", default="http://localhost:9000", help="Hub URL")
def status(hub_url: str):
    """Show hub and agent status."""
    import httpx

    try:
        response = httpx.get(f"{hub_url}/api/status", timeout=5)
        response.raise_for_status()
        data = response.json()

        uptime = data["uptime_seconds"]
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)

        click.echo(f"Hub uptime: {hours}h {minutes}m")
        click.echo()
        click.echo(f"{'AGENT':<14} {'STATE':<12} {'INBOX':<8} {'POLICY'}")
        click.echo("-" * 50)
        for agent in data["agents"]:
            state_color = {
                "running": "green",
                "stopped": "white",
                "starting": "yellow",
                "stopping": "yellow",
                "stale": "yellow",
                "error": "red",
            }.get(agent["state"], "white")

            click.echo(
                f"{agent['id']:<14} "
                f"{click.style(agent['state'], fg=state_color):<21} "
                f"{agent['inbox_count']:<8} "
                f"{agent['launch_policy']}"
            )

    except httpx.ConnectError:
        click.echo("Hub is not running. Start with: agent-hub start")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@cli.command("start-agent")
@click.argument("agent_id")
@click.option("--hub-url", default="http://localhost:9000", help="Hub URL")
def start_agent(agent_id: str, hub_url: str):
    """Start an agent's container."""
    import httpx

    try:
        response = httpx.post(
            f"{hub_url}/api/agents/{agent_id}/start", timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            click.echo(f"Started {agent_id} (state: {data['state']})")
        else:
            detail = response.json().get("detail", "Unknown error")
            click.echo(f"Error: {detail}")
            sys.exit(1)
    except httpx.ConnectError:
        click.echo("Hub is not running.")
        sys.exit(1)


@cli.command("stop-agent")
@click.argument("agent_id")
@click.option("--hub-url", default="http://localhost:9000", help="Hub URL")
def stop_agent(agent_id: str, hub_url: str):
    """Stop an agent's container."""
    import httpx

    try:
        response = httpx.post(
            f"{hub_url}/api/agents/{agent_id}/stop", timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            click.echo(f"Stopped {agent_id} (state: {data['state']})")
        else:
            detail = response.json().get("detail", "Unknown error")
            click.echo(f"Error: {detail}")
            sys.exit(1)
    except httpx.ConnectError:
        click.echo("Hub is not running.")
        sys.exit(1)


@cli.command("set-policy")
@click.argument("agent_id")
@click.option(
    "--launch",
    type=click.Choice(["manual", "auto_on_task", "always_on"]),
    help="Launch policy",
)
@click.option(
    "--shutdown",
    type=click.Choice(["manual", "on_inbox_empty", "idle_timeout"]),
    help="Shutdown policy",
)
@click.option("--idle-timeout", type=int, help="Idle timeout in minutes")
@click.option("--hub-url", default="http://localhost:9000", help="Hub URL")
def set_policy(
    agent_id: str,
    launch: str | None,
    shutdown: str | None,
    idle_timeout: int | None,
    hub_url: str,
):
    """Set an agent's launch/shutdown policy."""
    import httpx

    try:
        # Get current policy
        response = httpx.get(
            f"{hub_url}/api/agents/{agent_id}/policy", timeout=5
        )
        if response.status_code != 200:
            click.echo(f"Error: {response.json().get('detail')}")
            sys.exit(1)

        policy = response.json()

        # Update fields
        if launch is not None:
            policy["launch"] = launch
        if shutdown is not None:
            policy["shutdown"] = shutdown
        if idle_timeout is not None:
            policy["idle_timeout_minutes"] = idle_timeout

        # Set updated policy
        response = httpx.put(
            f"{hub_url}/api/agents/{agent_id}/policy",
            json=policy,
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            click.echo(f"Policy for {agent_id}:")
            click.echo(f"  Launch:   {data['launch']}")
            click.echo(f"  Shutdown: {data['shutdown']}")
            click.echo(f"  Idle timeout: {data['idle_timeout_minutes']}m")
        else:
            click.echo(f"Error: {response.json().get('detail')}")
            sys.exit(1)

    except httpx.ConnectError:
        click.echo("Hub is not running.")
        sys.exit(1)


@cli.command("attach")
@click.argument("agent_id")
@click.option("--hub-url", default="http://localhost:9000", help="Hub URL")
def attach(agent_id: str, hub_url: str):
    """Attach to a running agent's terminal.

    Connects directly to the agent's tmux session inside its container.
    Detach with Ctrl-B D.

    If the agent is stale (container running but session dead), offers
    recovery options: restart session or teardown container.
    """
    import httpx
    import subprocess as sp

    try:
        response = httpx.get(
            f"{hub_url}/api/agents/{agent_id}", timeout=5
        )
        if response.status_code == 404:
            click.echo(f"Unknown agent: {agent_id}")
            sys.exit(1)
        response.raise_for_status()
        data = response.json()

        if data["state"] == "stale":
            click.echo(
                f"Agent '{agent_id}' is "
                + click.style("stale", fg="yellow")
                + " (container running, session dead)."
            )
            click.echo()
            click.echo("  [R] Restart session - launch Claude Code in existing container")
            click.echo("  [T] Teardown       - remove the container entirely")
            click.echo("  [C] Cancel")
            click.echo()
            choice = click.prompt("Choice", type=click.Choice(["R", "T", "C"], case_sensitive=False))

            if choice.upper() == "R":
                click.echo(f"Restarting session for {agent_id}...")
                try:
                    resp = httpx.post(
                        f"{hub_url}/api/agents/{agent_id}/restart-session",
                        timeout=120,
                    )
                    if resp.status_code != 200:
                        detail = resp.json().get("detail", "Unknown error")
                        click.echo(click.style(f"  Error: {detail}", fg="red"))
                        sys.exit(1)
                    click.echo(click.style("  Session restarted.", fg="green"))
                except httpx.ConnectError:
                    click.echo(click.style("  Hub not responding.", fg="red"))
                    sys.exit(1)
            elif choice.upper() == "T":
                click.echo(f"Tearing down {agent_id}...")
                try:
                    resp = httpx.post(
                        f"{hub_url}/api/agents/{agent_id}/stop",
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        click.echo(click.style("  Container removed.", fg="green"))
                    else:
                        detail = resp.json().get("detail", "Unknown error")
                        click.echo(click.style(f"  Error: {detail}", fg="red"))
                except httpx.ConnectError:
                    click.echo(click.style("  Hub not responding.", fg="red"))
                sys.exit(0)
            else:
                click.echo("Cancelled.")
                sys.exit(0)

        elif data["state"] != "running":
            click.echo(
                f"Agent {agent_id} is {data['state']}. "
                f"Must be running to attach."
            )
            sys.exit(1)

    except httpx.ConnectError:
        click.echo("Hub is not running. Start with: agent-hub start")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)

    container_name = f"agent-{agent_id}"
    click.echo(f"Attaching to {agent_id}... (detach with Ctrl-B D)")

    result = sp.run(
        ["docker", "exec", "-it", container_name,
         "tmux", "attach", "-t", "agent"]
    )

    if result.returncode != 0:
        click.echo(f"Attach exited with code {result.returncode}")


# ---------------------------------------------------------------------------
# New subcommands (CR-069: absorb launch.sh and pd-status)
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("agents", nargs=-1)
@click.option(
    "--project-root", default=None, type=click.Path(exists=True),
    help="Project root directory (default: auto-detect)",
)
def launch(agents: tuple[str, ...], project_root: str | None):
    """Launch agent session(s) with full orchestration.

    Starts MCP servers, builds Docker image, starts the Hub, then launches
    the specified agent(s). Replaces the old launch.sh script.

    \b
    Single agent:  agent-hub launch claude
    Multiple:      agent-hub launch qa tu_ui bu
    """
    from pathlib import Path
    from agent_hub.services import (
        VALID_AGENTS, ensure_mcp_servers, ensure_docker_image,
        ensure_hub, launch_in_terminal,
    )
    import httpx
    import subprocess as sp

    if not agents:
        click.echo("Usage: agent-hub launch <agent> [agent ...]")
        click.echo(f"Valid agents: {', '.join(VALID_AGENTS)}")
        sys.exit(1)

    # Validate agent names
    invalid = [a for a in agents if a not in VALID_AGENTS]
    if invalid:
        click.echo(f"Unknown agent(s): {', '.join(invalid)}")
        click.echo(f"Valid agents: {', '.join(VALID_AGENTS)}")
        sys.exit(1)

    kwargs = {}
    if project_root:
        kwargs["project_root"] = project_root
    config = HubConfig(**kwargs)

    click.echo()
    click.echo(click.style("=== Agent Hub Launch ===", bold=True))
    click.echo()

    # Phase 1: Ensure infrastructure
    click.echo(click.style("Infrastructure:", bold=True))
    try:
        ensure_mcp_servers(config)
        ensure_docker_image(config)
        ensure_hub(config)
    except SystemExit:
        click.echo()
        click.echo(click.style("Launch aborted due to infrastructure failure.", fg="red"))
        sys.exit(1)

    click.echo()

    hub_url = f"http://localhost:{config.port}"

    if len(agents) == 1:
        # Single agent: start via Hub API, then attach interactively
        agent_id = agents[0]
        click.echo(click.style(f"Starting {agent_id}...", bold=True))

        try:
            response = httpx.post(
                f"{hub_url}/api/agents/{agent_id}/start", timeout=120
            )
            if response.status_code == 200:
                click.echo(click.style("  \u2713 ", fg="green") + f"{agent_id} container started")
            else:
                detail = response.json().get("detail", "Unknown error")
                click.echo(click.style("  \u2717 ", fg="red") + f"Failed: {detail}")
                sys.exit(1)
        except httpx.ConnectError:
            click.echo(click.style("  \u2717 ", fg="red") + "Hub not responding")
            sys.exit(1)

        # Attach to tmux session interactively
        container_name = f"{config.container_prefix}{agent_id}"
        click.echo(f"Attaching to {agent_id}... (detach with Ctrl-B D)")
        click.echo()
        sp.run(
            ["docker", "exec", "-it", container_name,
             "tmux", "attach", "-t", "agent"]
        )
    else:
        # Multiple agents: start each via Hub API, spawn in new terminals
        click.echo(click.style(f"Starting {len(agents)} agents...", bold=True))

        for agent_id in agents:
            try:
                response = httpx.post(
                    f"{hub_url}/api/agents/{agent_id}/start", timeout=120
                )
                if response.status_code == 200:
                    click.echo(click.style("  \u2713 ", fg="green") + f"{agent_id} started")
                    launch_in_terminal(agent_id, config)
                else:
                    detail = response.json().get("detail", "Unknown error")
                    click.echo(click.style("  \u2717 ", fg="red") + f"{agent_id}: {detail}")
            except httpx.ConnectError:
                click.echo(click.style("  \u2717 ", fg="red") + "Hub not responding")
                sys.exit(1)

        click.echo()
        click.echo(click.style("All agents launched.", fg="green"))
        click.echo("Use 'agent-hub attach <agent>' to connect to an agent.")


@cli.command("services")
@click.option(
    "--project-root", default=None, type=click.Path(exists=True),
    help="Project root directory (default: auto-detect)",
)
def services_cmd(project_root: str | None):
    """Show status of all background services and containers.

    Replaces the old pd-status script.
    """
    from agent_hub.services import get_services_status, get_containers

    kwargs = {}
    if project_root:
        kwargs["project_root"] = project_root
    config = HubConfig(**kwargs)

    click.echo()
    click.echo(click.style("=== Services ===", bold=True))
    click.echo()

    statuses = get_services_status(config)

    click.echo(f"  {'SERVICE':<14} {'PORT':<8} {'STATE':<10} {'PID':<8} {'INFO'}")
    click.echo(f"  {'-' * 58}")

    for s in statuses:
        state_str = click.style("UP", fg="green") if s.alive else click.style("DOWN", fg="red")
        pid_str = str(s.pid) if s.pid else "-"
        click.echo(f"  {s.label:<14} :{s.port:<7} {state_str:<19} {pid_str:<8} {s.extra}")

    # Docker containers — enrich with Hub session health when available
    containers = get_containers()
    hub_agents = {}
    hub_available = False
    try:
        import httpx
        resp = httpx.get(f"http://localhost:{config.port}/api/agents", timeout=3)
        if resp.status_code == 200:
            hub_available = True
            for a in resp.json():
                hub_agents[f"{config.container_prefix}{a['id']}"] = a
    except Exception:
        pass

    click.echo()
    click.echo(click.style("=== Containers ===", bold=True))
    click.echo()

    if containers:
        click.echo(f"  {'NAME':<20} {'STATE':<12} {'STATUS'}")
        click.echo(f"  {'-' * 50}")
        for name, state, status_str in containers:
            hub_info = hub_agents.get(name)
            if hub_info and hub_info.get("state") == "stale":
                display_state = "stale"
                state_color = "yellow"
                status_str = "container running, session dead"
            elif state == "running" and not hub_available:
                display_state = state
                state_color = "green"
                status_str = "session state unknown (Hub down)"
            else:
                display_state = state
                state_color = "green" if state == "running" else "yellow"
            click.echo(
                f"  {name:<20} {click.style(display_state, fg=state_color):<21} {status_str}"
            )
    else:
        click.echo("  No agent containers found.")

    click.echo()


@cli.command("stop-all")
@click.option(
    "--project-root", default=None, type=click.Path(exists=True),
    help="Project root directory (default: auto-detect)",
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def stop_all_cmd(project_root: str | None, yes: bool):
    """Stop all services and remove containers.

    Replaces the old pd-status --stop-all command.
    """
    from agent_hub.services import stop_all_services

    kwargs = {}
    if project_root:
        kwargs["project_root"] = project_root
    config = HubConfig(**kwargs)

    click.echo()
    click.echo(click.style("=== Stop All ===", bold=True))
    click.echo()

    stop_all_services(config, skip_confirm=yes)


if __name__ == "__main__":
    cli()
