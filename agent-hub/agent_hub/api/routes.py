"""REST API endpoints for the Agent Hub."""

from fastapi import APIRouter, HTTPException, Request

from agent_hub.models import Agent, AgentPolicy, AgentSummary, HubStatus

router = APIRouter()


def _get_hub(request: Request):
    return request.app.state.hub


@router.get("/health")
async def health_check():
    """Hub health check."""
    return {"status": "ok"}


@router.get("/status", response_model=HubStatus)
async def hub_status(request: Request):
    """Full hub status — all agents + uptime."""
    hub = _get_hub(request)
    return HubStatus(
        agents=[
            AgentSummary(
                id=agent.id,
                state=agent.state,
                inbox_count=agent.inbox_count,
                launch_policy=agent.policy.launch,
            )
            for agent in hub.agents.values()
        ],
        uptime_seconds=hub.uptime_seconds,
    )


@router.get("/agents", response_model=list[AgentSummary])
async def list_agents(request: Request):
    """List all agents with state and inbox count."""
    hub = _get_hub(request)
    return [
        AgentSummary(
            id=agent.id,
            state=agent.state,
            inbox_count=agent.inbox_count,
            launch_policy=agent.policy.launch,
        )
        for agent in hub.agents.values()
    ]


@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, request: Request):
    """Get detailed agent info."""
    hub = _get_hub(request)
    agent = hub.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return agent


@router.post("/agents/{agent_id}/start", response_model=Agent)
async def start_agent(agent_id: str, request: Request):
    """Start an agent's container."""
    hub = _get_hub(request)
    try:
        return await hub.start_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/stop", response_model=Agent)
async def stop_agent(agent_id: str, request: Request):
    """Stop an agent's container."""
    hub = _get_hub(request)
    try:
        return await hub.stop_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/restart-session", response_model=Agent)
async def restart_session(agent_id: str, request: Request):
    """Restart the Claude Code session in a stale container."""
    hub = _get_hub(request)
    try:
        return await hub.restart_agent_session(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/policy", response_model=AgentPolicy)
async def get_policy(agent_id: str, request: Request):
    """Get an agent's launch/shutdown policy."""
    hub = _get_hub(request)
    agent = hub.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return agent.policy


@router.put("/agents/{agent_id}/policy", response_model=AgentPolicy)
async def set_policy(agent_id: str, policy: AgentPolicy, request: Request):
    """Set an agent's launch/shutdown policy."""
    hub = _get_hub(request)
    try:
        agent = hub.set_agent_policy(agent_id, policy)
        return agent.policy
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
