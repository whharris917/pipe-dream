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


if __name__ == "__main__":
    cli()
