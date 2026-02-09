"""WebSocket endpoint for real-time terminal I/O and event broadcasting."""

import base64
import logging

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

from agent_hub.broadcaster import Broadcaster, ConnectionState
from agent_hub.hub import AgentHub

logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle a WebSocket connection for terminal I/O and events."""
    await websocket.accept()

    hub: AgentHub = websocket.app.state.hub
    broadcaster: Broadcaster = websocket.app.state.broadcaster
    conn = await broadcaster.connect(websocket)

    try:
        while True:
            msg = await websocket.receive_json()
            await _handle_message(hub, broadcaster, conn, msg)
    except WebSocketDisconnect:
        logger.debug("Client %s disconnected", conn.id)
    except Exception as e:
        logger.warning("WebSocket error for %s: %s", conn.id, e)
    finally:
        await broadcaster.disconnect(conn)


async def _handle_message(
    hub: AgentHub,
    broadcaster: Broadcaster,
    conn: ConnectionState,
    msg: dict,
) -> None:
    """Dispatch a client message to the appropriate handler."""
    msg_type = msg.get("type")

    if msg_type == "subscribe":
        await _handle_subscribe(hub, broadcaster, conn, msg)
    elif msg_type == "unsubscribe":
        await _handle_unsubscribe(broadcaster, conn, msg)
    elif msg_type == "input":
        await _handle_input(hub, conn, msg)
    elif msg_type == "resize":
        await _handle_resize(hub, conn, msg)
    else:
        await conn.websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {msg_type}",
        })


async def _handle_subscribe(
    hub: AgentHub,
    broadcaster: Broadcaster,
    conn: ConnectionState,
    msg: dict,
) -> None:
    """Subscribe to an agent's PTY output."""
    agent_id = msg.get("agent_id")
    if not agent_id:
        await conn.websocket.send_json({
            "type": "error",
            "message": "Missing agent_id",
        })
        return

    if hub.get_agent(agent_id) is None:
        await conn.websocket.send_json({
            "type": "error",
            "message": f"Agent not found: {agent_id}",
        })
        return

    broadcaster.subscribe(conn, agent_id)

    # Send scrollback buffer for late-joining clients
    buffer = hub.pty_manager.get_buffer(agent_id)
    buffer_b64 = base64.b64encode(buffer).decode("ascii") if buffer else ""

    await conn.websocket.send_json({
        "type": "subscribed",
        "agent_id": agent_id,
        "buffer": buffer_b64,
    })
    logger.debug("Client %s subscribed to %s", conn.id, agent_id)


async def _handle_unsubscribe(
    broadcaster: Broadcaster,
    conn: ConnectionState,
    msg: dict,
) -> None:
    """Unsubscribe from an agent's PTY output."""
    agent_id = msg.get("agent_id")
    if not agent_id:
        await conn.websocket.send_json({
            "type": "error",
            "message": "Missing agent_id",
        })
        return

    broadcaster.unsubscribe(conn, agent_id)
    await conn.websocket.send_json({
        "type": "unsubscribed",
        "agent_id": agent_id,
    })
    logger.debug("Client %s unsubscribed from %s", conn.id, agent_id)


async def _handle_input(
    hub: AgentHub,
    conn: ConnectionState,
    msg: dict,
) -> None:
    """Send keystrokes to an agent's terminal."""
    agent_id = msg.get("agent_id")
    data = msg.get("data")

    if not agent_id or data is None:
        await conn.websocket.send_json({
            "type": "error",
            "message": "Missing agent_id or data",
        })
        return

    if agent_id not in conn.subscriptions:
        await conn.websocket.send_json({
            "type": "error",
            "message": f"Not subscribed to agent: {agent_id}",
        })
        return

    try:
        await hub.pty_manager.write(agent_id, data.encode("utf-8"))
    except Exception as e:
        await conn.websocket.send_json({
            "type": "error",
            "message": f"Write failed: {e}",
        })


async def _handle_resize(
    hub: AgentHub,
    conn: ConnectionState,
    msg: dict,
) -> None:
    """Resize an agent's terminal."""
    agent_id = msg.get("agent_id")
    cols = msg.get("cols")
    rows = msg.get("rows")

    if not agent_id or cols is None or rows is None:
        await conn.websocket.send_json({
            "type": "error",
            "message": "Missing agent_id, cols, or rows",
        })
        return

    if agent_id not in conn.subscriptions:
        await conn.websocket.send_json({
            "type": "error",
            "message": f"Not subscribed to agent: {agent_id}",
        })
        return

    try:
        await hub.pty_manager.resize(agent_id, int(cols), int(rows))
    except Exception as e:
        await conn.websocket.send_json({
            "type": "error",
            "message": f"Resize failed: {e}",
        })
