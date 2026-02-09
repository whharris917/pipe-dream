"""UAT for WebSocket endpoint — tests protocol layer without Docker containers.

Starts a Hub with a mock config (no real containers), connects via WebSocket,
and verifies the message protocol.
"""

import asyncio
import json
import base64

import httpx
import uvicorn
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from agent_hub.config import HubConfig
from agent_hub.hub import AgentHub
from agent_hub.api.server import create_app


def make_hub():
    """Create a Hub with minimal config (no real containers needed)."""
    config = HubConfig(
        agents=["test_agent_1", "test_agent_2"],
        host="127.0.0.1",
        port=0,  # not binding
    )
    return AgentHub(config)


def test_websocket_connect_disconnect():
    """T1: WebSocket handshake and clean disconnect."""
    hub = make_hub()
    app = create_app(hub)

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            # Connection established — broadcaster should have 1 connection
            assert app.state.broadcaster.connection_count == 1

        # After disconnect — broadcaster should have 0
        assert app.state.broadcaster.connection_count == 0


def test_subscribe_known_agent():
    """T2: Subscribe to a known agent returns subscribed + buffer."""
    hub = make_hub()
    app = create_app(hub)

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "subscribe", "agent_id": "test_agent_1"})
            resp = ws.receive_json()

            assert resp["type"] == "subscribed"
            assert resp["agent_id"] == "test_agent_1"
            assert "buffer" in resp
            # Buffer should be empty string (no PTY attached)
            assert resp["buffer"] == ""


def test_subscribe_unknown_agent():
    """T3: Subscribe to unknown agent returns error."""
    hub = make_hub()
    app = create_app(hub)

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "subscribe", "agent_id": "nonexistent"})
            resp = ws.receive_json()

            assert resp["type"] == "error"
            assert "not found" in resp["message"].lower()


def test_unsubscribe():
    """T4: Unsubscribe returns confirmation."""
    hub = make_hub()
    app = create_app(hub)

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            # Subscribe first
            ws.send_json({"type": "subscribe", "agent_id": "test_agent_1"})
            ws.receive_json()  # consume subscribed response

            # Unsubscribe
            ws.send_json({"type": "unsubscribe", "agent_id": "test_agent_1"})
            resp = ws.receive_json()

            assert resp["type"] == "unsubscribed"
            assert resp["agent_id"] == "test_agent_1"


def test_input_without_subscription():
    """T5: Input to unsubscribed agent returns error."""
    hub = make_hub()
    app = create_app(hub)

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({
                "type": "input",
                "agent_id": "test_agent_1",
                "data": "ls\r",
            })
            resp = ws.receive_json()

            assert resp["type"] == "error"
            assert "not subscribed" in resp["message"].lower()


def test_resize_without_subscription():
    """T6: Resize without subscription returns error."""
    hub = make_hub()
    app = create_app(hub)

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({
                "type": "resize",
                "agent_id": "test_agent_1",
                "cols": 120,
                "rows": 40,
            })
            resp = ws.receive_json()

            assert resp["type"] == "error"
            assert "not subscribed" in resp["message"].lower()


def test_unknown_message_type():
    """T7: Unknown message type returns error."""
    hub = make_hub()
    app = create_app(hub)

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "foobar"})
            resp = ws.receive_json()

            assert resp["type"] == "error"
            assert "unknown" in resp["message"].lower()


def test_missing_agent_id():
    """T8: Subscribe without agent_id returns error."""
    hub = make_hub()
    app = create_app(hub)

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "subscribe"})
            resp = ws.receive_json()

            assert resp["type"] == "error"
            assert "missing" in resp["message"].lower()


def test_broadcast_agent_state():
    """T9: Agent state change broadcasts to all connected clients."""
    hub = make_hub()
    app = create_app(hub)

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            # Trigger a state broadcast via the broadcaster directly
            broadcaster = app.state.broadcaster

            import asyncio
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                broadcaster.broadcast_agent_state(
                    "test_agent_1",
                    "running",
                    {"id": "test_agent_1", "state": "running"},
                )
            )
            loop.close()

            resp = ws.receive_json()
            assert resp["type"] == "agent_state_changed"
            assert resp["agent_id"] == "test_agent_1"
            assert resp["state"] == "running"


def test_broadcast_inbox_change():
    """T10: Inbox change broadcasts to all connected clients."""
    hub = make_hub()
    app = create_app(hub)

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            broadcaster = app.state.broadcaster

            import asyncio
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                broadcaster.broadcast_inbox_change("test_agent_1", 3)
            )
            loop.close()

            resp = ws.receive_json()
            assert resp["type"] == "inbox_changed"
            assert resp["agent_id"] == "test_agent_1"
            assert resp["count"] == 3


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
