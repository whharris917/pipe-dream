"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent_hub.api.routes import router
from agent_hub.api.websocket import ws_router
from agent_hub.broadcaster import Broadcaster
from agent_hub.hub import AgentHub


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop the Hub with the FastAPI app."""
    hub: AgentHub = app.state.hub
    broadcaster: Broadcaster = app.state.broadcaster
    hub.set_broadcaster(broadcaster)
    await hub.start()
    yield
    await hub.stop()


def create_app(hub: AgentHub) -> FastAPI:
    """Create the FastAPI app with the Hub wired in."""
    app = FastAPI(
        title="Agent Hub",
        description="Multi-agent container orchestration for Pipe Dream",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.hub = hub
    app.state.broadcaster = Broadcaster()
    app.include_router(router, prefix="/api")
    app.include_router(ws_router)

    return app
