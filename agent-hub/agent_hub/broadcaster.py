"""WebSocket connection fan-out coordinator.

Manages the set of active WebSocket connections and provides methods
for broadcasting PTY output, agent state changes, and inbox events
to connected clients.
"""

import asyncio
import base64
import logging
import uuid

from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class ConnectionState:
    """Per-WebSocket-connection state."""

    __slots__ = ("websocket", "subscriptions", "id")

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket
        self.subscriptions: set[str] = set()
        self.id: str = uuid.uuid4().hex[:8]

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConnectionState):
            return NotImplemented
        return self.id == other.id


class Broadcaster:
    """Manages WebSocket connections and event fan-out."""

    def __init__(self) -> None:
        self._connections: set[ConnectionState] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> ConnectionState:
        """Register a new WebSocket connection."""
        conn = ConnectionState(websocket)
        async with self._lock:
            self._connections.add(conn)
        logger.info("WebSocket connected: %s (%d total)", conn.id, len(self._connections))
        return conn

    async def disconnect(self, conn: ConnectionState) -> None:
        """Remove a WebSocket connection and clear its subscriptions."""
        conn.subscriptions.clear()
        async with self._lock:
            self._connections.discard(conn)
        logger.info("WebSocket disconnected: %s (%d remaining)", conn.id, len(self._connections))

    def subscribe(self, conn: ConnectionState, agent_id: str) -> None:
        """Add an agent subscription for a connection."""
        conn.subscriptions.add(agent_id)

    def unsubscribe(self, conn: ConnectionState, agent_id: str) -> None:
        """Remove an agent subscription for a connection."""
        conn.subscriptions.discard(agent_id)

    async def broadcast_pty_output(self, agent_id: str, data: bytes) -> None:
        """Send PTY output to connections subscribed to this agent.

        This method matches the PTYOutputCallback signature so it can be
        registered directly with PTYManager.register_callback().
        """
        msg = {
            "type": "output",
            "agent_id": agent_id,
            "data": base64.b64encode(data).decode("ascii"),
        }
        await self._send_to_subscribers(agent_id, msg)

    async def broadcast_agent_state(
        self, agent_id: str, state: str, agent_dict: dict
    ) -> None:
        """Send agent state-change event to ALL connected clients."""
        msg = {
            "type": "agent_state_changed",
            "agent_id": agent_id,
            "state": state,
            "agent": agent_dict,
        }
        await self._send_to_all(msg)

    async def broadcast_inbox_change(self, agent_id: str, count: int) -> None:
        """Send inbox count change to ALL connected clients."""
        msg = {
            "type": "inbox_changed",
            "agent_id": agent_id,
            "count": count,
        }
        await self._send_to_all(msg)

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    async def _send_to_subscribers(self, agent_id: str, msg: dict) -> None:
        """Send a message to connections subscribed to an agent."""
        async with self._lock:
            snapshot = set(self._connections)

        stale: list[ConnectionState] = []
        for conn in snapshot:
            if agent_id not in conn.subscriptions:
                continue
            if not await self._safe_send(conn, msg):
                stale.append(conn)

        if stale:
            await self._cleanup_stale(stale)

    async def _send_to_all(self, msg: dict) -> None:
        """Send a message to all connected clients."""
        async with self._lock:
            snapshot = set(self._connections)

        stale: list[ConnectionState] = []
        for conn in snapshot:
            if not await self._safe_send(conn, msg):
                stale.append(conn)

        if stale:
            await self._cleanup_stale(stale)

    async def _safe_send(self, conn: ConnectionState, msg: dict) -> bool:
        """Send JSON to a connection, returning False if the connection is dead."""
        try:
            if conn.websocket.client_state == WebSocketState.CONNECTED:
                await conn.websocket.send_json(msg)
                return True
            return False
        except Exception:
            logger.debug("Send failed for connection %s", conn.id)
            return False

    async def _cleanup_stale(self, stale: list[ConnectionState]) -> None:
        """Remove stale connections."""
        async with self._lock:
            for conn in stale:
                conn.subscriptions.clear()
                self._connections.discard(conn)
        if stale:
            logger.info("Cleaned up %d stale connection(s)", len(stale))
