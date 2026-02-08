"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent_hub.api.routes import router
from agent_hub.hub import AgentHub


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop the Hub with the FastAPI app."""
    hub: AgentHub = app.state.hub
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
    app.include_router(router, prefix="/api")

    return app
