"""Core Hub class — orchestrates container, inbox, and policy components."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from agent_hub.config import HubConfig
from agent_hub.container import ContainerManager
from agent_hub.inbox import InboxWatcher
from agent_hub.models import Agent, AgentPolicy, AgentState, LaunchPolicy, ShutdownPolicy
from agent_hub.notifier import build_notification_text, inject_notification
from agent_hub.policy import evaluate_launch, evaluate_shutdown
from agent_hub.pty_manager import PTYManager

if TYPE_CHECKING:
    from agent_hub.broadcaster import Broadcaster

logger = logging.getLogger(__name__)


class AgentHub:
    """The Agent Hub — manages agent container lifecycle."""

    def __init__(self, config: HubConfig):
        self.config = config
        self.agents: dict[str, Agent] = {}
        self.container_mgr = ContainerManager(config)
        self.inbox_watcher = InboxWatcher(config, self._on_inbox_change)
        self.pty_manager = PTYManager(config, self.container_mgr.client)
        self._started_at: datetime | None = None
        self._idle_check_task: asyncio.Task | None = None
        self._container_sync_task: asyncio.Task | None = None
        self._hub_managed: set[str] = set()  # agents whose containers the Hub started
        self._pty_last_event: dict[str, datetime] = {}  # rate-limit activity tracking
        self._broadcaster: Broadcaster | None = None

    async def start(self) -> None:
        """Start the Hub and all always-on agents."""
        self._started_at = datetime.now()

        # Register PTY output callback for activity tracking
        self.pty_manager.register_callback(self._on_pty_output)

        # Initialize agent records
        for agent_id in self.config.agents:
            policy = AgentPolicy(
                launch=self.config.default_launch_policy,
                shutdown=self.config.default_shutdown_policy,
                idle_timeout_minutes=self.config.default_idle_timeout,
            )
            self.agents[agent_id] = Agent(id=agent_id, policy=policy)

        # Scan for already-running containers (includes PTY attach)
        await self._discover_running_containers()

        # Start inbox watcher
        await self.inbox_watcher.start()

        # Update initial inbox counts
        for agent_id in self.config.agents:
            count = self.inbox_watcher.get_inbox_count(agent_id)
            self.agents[agent_id].inbox_count = count

        # Launch always-on agents
        for agent_id, agent in self.agents.items():
            if agent.policy.launch == LaunchPolicy.ALWAYS_ON:
                if agent.state == AgentState.STOPPED:
                    await self.start_agent(agent_id)

        # Start periodic loops
        self._idle_check_task = asyncio.create_task(self._idle_check_loop())
        self._container_sync_task = asyncio.create_task(self._container_sync_loop())

        logger.info("Hub started with %d agents", len(self.agents))

    async def stop(self) -> None:
        """Stop the Hub and all running agents."""
        for task in (self._idle_check_task, self._container_sync_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        await self.inbox_watcher.stop()

        # Unregister broadcaster from PTY callbacks
        if self._broadcaster:
            self.pty_manager.unregister_callback(self._broadcaster.broadcast_pty_output)

        # Detach all PTY sessions
        await self.pty_manager.detach_all()

        # Stop only Hub-managed containers (not externally started ones)
        for agent_id, agent in self.agents.items():
            agent.pty_attached = False
            if agent.state == AgentState.RUNNING and agent_id in self._hub_managed:
                try:
                    await self.stop_agent(agent_id)
                except Exception as e:
                    logger.error("Error stopping agent %s: %s", agent_id, e)

        self.container_mgr.close()
        logger.info("Hub stopped")

    async def start_agent(self, agent_id: str) -> Agent:
        """Start an agent's container."""
        agent = self._get_agent(agent_id)

        if agent.state == AgentState.RUNNING:
            raise RuntimeError(
                f"Agent {agent_id} is already running. "
                f"Use 'agent-hub attach {agent_id}' to connect."
            )

        if agent.state not in (AgentState.STOPPED, AgentState.ERROR, AgentState.STALE):
            raise RuntimeError(
                f"Cannot start agent {agent_id}: state is {agent.state}"
            )

        agent.state = AgentState.STARTING
        logger.info("Starting agent %s", agent_id)

        try:
            container_id = await self.container_mgr.start(agent_id)
            agent.container_id = container_id
            agent.state = AgentState.RUNNING
            agent.session_alive = True
            agent.started_at = datetime.now()
            agent.last_activity = datetime.now()
            self._hub_managed.add(agent_id)
            logger.info("Agent %s is now RUNNING", agent_id)
        except Exception as e:
            agent.state = AgentState.ERROR
            logger.error("Failed to start agent %s: %s", agent_id, e)
            raise

        # Attach PTY (non-fatal — agent runs even if PTY fails)
        try:
            await self.pty_manager.attach(agent_id)
            agent.pty_attached = True
        except Exception as e:
            logger.warning("PTY attach failed for %s: %s", agent_id, e)

        await self._broadcast_state(agent_id, agent)
        return agent

    async def stop_agent(self, agent_id: str) -> Agent:
        """Stop an agent's container."""
        agent = self._get_agent(agent_id)

        if agent.state == AgentState.STOPPED:
            return agent

        if agent.state not in (AgentState.RUNNING, AgentState.STALE, AgentState.ERROR):
            raise RuntimeError(
                f"Cannot stop agent {agent_id}: state is {agent.state}"
            )

        agent.state = AgentState.STOPPING
        logger.info("Stopping agent %s", agent_id)

        # Detach PTY before stopping container
        await self.pty_manager.detach(agent_id)
        agent.pty_attached = False

        try:
            await self.container_mgr.stop(agent_id)
            agent.state = AgentState.STOPPED
            agent.container_id = None
            agent.started_at = None
            agent.session_alive = False
            logger.info("Agent %s is now STOPPED", agent_id)
        except Exception as e:
            agent.state = AgentState.ERROR
            logger.error("Failed to stop agent %s: %s", agent_id, e)
            raise

        await self._broadcast_state(agent_id, agent)
        return agent

    async def restart_agent_session(self, agent_id: str) -> Agent:
        """Restart the Claude Code session inside a stale container."""
        agent = self._get_agent(agent_id)

        if agent.state != AgentState.STALE:
            raise RuntimeError(
                f"Cannot restart session for {agent_id}: state is {agent.state} (expected stale)"
            )

        logger.info("Restarting session for stale agent %s", agent_id)

        try:
            await self.container_mgr.restart_session(agent_id)
            agent.state = AgentState.RUNNING
            agent.session_alive = True
            agent.last_activity = datetime.now()
            logger.info("Agent %s session restarted, now RUNNING", agent_id)
        except Exception as e:
            agent.state = AgentState.ERROR
            logger.error("Failed to restart session for %s: %s", agent_id, e)
            raise

        # Re-attach PTY
        try:
            if self.pty_manager.is_attached(agent_id):
                await self.pty_manager.detach(agent_id)
            await self.pty_manager.attach(agent_id)
            agent.pty_attached = True
        except Exception as e:
            logger.warning("PTY attach failed after session restart for %s: %s", agent_id, e)

        await self._broadcast_state(agent_id, agent)
        return agent

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get agent state (public, returns None if not found)."""
        return self.agents.get(agent_id)

    def set_agent_policy(self, agent_id: str, policy: AgentPolicy) -> Agent:
        """Update an agent's launch/shutdown policy."""
        agent = self._get_agent(agent_id)
        agent.policy = policy
        logger.info("Policy updated for %s: %s", agent_id, policy)
        return agent

    def set_broadcaster(self, broadcaster: Broadcaster) -> None:
        """Wire the broadcaster for WebSocket event fan-out."""
        self._broadcaster = broadcaster
        self.pty_manager.register_callback(broadcaster.broadcast_pty_output)

    @property
    def uptime_seconds(self) -> float:
        if self._started_at is None:
            return 0.0
        return (datetime.now() - self._started_at).total_seconds()

    # -- Internal methods --

    async def _broadcast_state(self, agent_id: str, agent: Agent) -> None:
        """Broadcast agent state change to WebSocket clients."""
        if self._broadcaster:
            await self._broadcaster.broadcast_agent_state(
                agent_id, agent.state.value, agent.model_dump(mode="json"),
            )

    def _get_agent(self, agent_id: str) -> Agent:
        """Get agent state (internal, raises if not found)."""
        agent = self.agents.get(agent_id)
        if agent is None:
            raise ValueError(f"Unknown agent: {agent_id}")
        return agent

    async def _on_pty_output(self, agent_id: str, data: bytes) -> None:
        """Handle PTY output — update agent activity timestamp.

        Uses rate-based filtering to ignore periodic terminal noise (e.g.,
        tmux status bar refreshes every ~60s). Only counts as real activity
        when output events arrive in rapid succession (within 10 seconds),
        which is characteristic of actual Claude Code work.
        """
        agent = self.agents.get(agent_id)
        if agent is None:
            return
        now = datetime.now()
        prev = self._pty_last_event.get(agent_id)
        self._pty_last_event[agent_id] = now
        # Require two output events within 10s to count as activity.
        # tmux status bar fires once every ~60s — won't trigger this.
        # Real Claude Code output fires many events per second — triggers immediately.
        if prev is not None and (now - prev).total_seconds() < 10:
            agent.last_activity = now

    async def _discover_running_containers(self) -> None:
        """Check for containers already running from a previous Hub session."""
        for agent_id in self.config.agents:
            container_id = await self.container_mgr.get_container_id(agent_id)
            if container_id is not None:
                agent = self.agents[agent_id]
                agent.container_id = container_id
                agent.started_at = datetime.now()

                # Check if the session is actually alive
                session_alive = await self.container_mgr.is_session_alive(agent_id)
                agent.session_alive = session_alive

                if session_alive:
                    agent.state = AgentState.RUNNING
                    agent.last_activity = datetime.now()
                    logger.info("Discovered running container for %s (session alive)", agent_id)

                    # Attempt PTY attach (non-fatal)
                    try:
                        await self.pty_manager.attach(agent_id)
                        agent.pty_attached = True
                    except Exception as e:
                        logger.warning(
                            "PTY attach failed for discovered container %s: %s",
                            agent_id, e,
                        )
                else:
                    agent.state = AgentState.STALE
                    logger.warning(
                        "Discovered stale container for %s (container running, session dead)",
                        agent_id,
                    )

    async def _on_inbox_change(
        self, agent_id: str, inbox_count: int, new_filename: str | None
    ) -> None:
        """Handle inbox change from the watcher."""
        agent = self.agents.get(agent_id)
        if agent is None:
            return

        agent.inbox_count = inbox_count
        logger.info(
            "Inbox change for %s: %d items (new: %s)",
            agent_id, inbox_count, new_filename,
        )

        # Broadcast inbox change to WebSocket clients
        if self._broadcaster:
            await self._broadcaster.broadcast_inbox_change(agent_id, inbox_count)

        # Evaluate launch policy
        decision = evaluate_launch(agent, inbox_count)
        if decision.action == "start":
            logger.info("Auto-launching %s: %s", agent_id, decision.reason)
            try:
                await self.start_agent(agent_id)
            except Exception as e:
                logger.error("Auto-launch failed for %s: %s", agent_id, e)

        # Inject notification if agent is running and a new file arrived
        if (
            new_filename is not None
            and agent.state == AgentState.RUNNING
        ):
            container_name = self.container_mgr.container_name(agent_id)
            text = build_notification_text(agent_id, new_filename)
            await inject_notification(container_name, text)

        # Evaluate shutdown policy
        decision = evaluate_shutdown(agent, inbox_count)
        if decision.action == "stop":
            logger.info("Auto-stopping %s: %s", agent_id, decision.reason)
            try:
                await self.stop_agent(agent_id)
            except Exception as e:
                logger.error("Auto-stop failed for %s: %s", agent_id, e)

    async def _idle_check_loop(self) -> None:
        """Periodically check for idle agents that should be stopped.

        Only evaluates IDLE_TIMEOUT policy here. ON_INBOX_EMPTY is
        evaluated in _on_inbox_change when the inbox count actually drops.
        """
        while True:
            await asyncio.sleep(60)  # Check every minute
            for agent_id, agent in self.agents.items():
                if agent.state != AgentState.RUNNING:
                    continue
                if agent.policy.shutdown != ShutdownPolicy.IDLE_TIMEOUT:
                    continue
                decision = evaluate_shutdown(
                    agent, agent.inbox_count
                )
                if decision.action == "stop":
                    logger.info(
                        "Idle shutdown for %s: %s", agent_id, decision.reason
                    )
                    try:
                        await self.stop_agent(agent_id)
                    except Exception as e:
                        logger.error(
                            "Idle shutdown failed for %s: %s", agent_id, e
                        )

    async def _container_sync_loop(self) -> None:
        """Periodically reconcile Hub state with Docker reality.

        Containers may be started or stopped externally (e.g., by launch.sh).
        This loop ensures the Hub's view stays consistent with what Docker
        reports, enabling correct notification injection and policy evaluation.

        Also checks session health: if a container is running but the tmux
        session has died, the agent transitions to STALE.
        """
        while True:
            await asyncio.sleep(10)
            for agent_id, agent in self.agents.items():
                try:
                    running = await self.container_mgr.is_running(agent_id)
                except Exception:
                    continue

                if running and agent.state == AgentState.STOPPED:
                    # New container discovered — check session health
                    session_alive = await self.container_mgr.is_session_alive(agent_id)
                    agent.container_id = await self.container_mgr.get_container_id(agent_id)
                    agent.started_at = datetime.now()
                    agent.session_alive = session_alive

                    if session_alive:
                        agent.state = AgentState.RUNNING
                        agent.last_activity = datetime.now()
                        logger.info(
                            "Sync: discovered running container for %s", agent_id
                        )
                        if not self.pty_manager.is_attached(agent_id):
                            try:
                                await self.pty_manager.attach(agent_id)
                                agent.pty_attached = True
                            except Exception as e:
                                logger.warning(
                                    "Sync: PTY attach failed for %s: %s",
                                    agent_id, e,
                                )
                    else:
                        agent.state = AgentState.STALE
                        logger.warning(
                            "Sync: discovered stale container for %s", agent_id
                        )
                    await self._broadcast_state(agent_id, agent)

                elif running and agent.state == AgentState.RUNNING:
                    # Check if session has died inside a running container
                    session_alive = await self.container_mgr.is_session_alive(agent_id)
                    agent.session_alive = session_alive
                    if not session_alive:
                        # Detach PTY — session is gone
                        if self.pty_manager.is_attached(agent_id):
                            await self.pty_manager.detach(agent_id)
                        agent.state = AgentState.STALE
                        agent.pty_attached = False
                        logger.warning(
                            "Sync: agent %s session died, transitioning to STALE",
                            agent_id,
                        )
                        await self._broadcast_state(agent_id, agent)

                elif not running and agent.state in (AgentState.RUNNING, AgentState.STALE):
                    # Container stopped (externally or after teardown)
                    if self.pty_manager.is_attached(agent_id):
                        await self.pty_manager.detach(agent_id)
                    agent.state = AgentState.STOPPED
                    agent.container_id = None
                    agent.started_at = None
                    agent.pty_attached = False
                    agent.session_alive = False
                    logger.info(
                        "Sync: container stopped externally for %s", agent_id
                    )
                    await self._broadcast_state(agent_id, agent)
