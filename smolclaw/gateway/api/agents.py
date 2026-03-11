"""Agent management API — create, list, and manage scan agents."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
except ImportError:
    raise ImportError("fastapi and pydantic required for API: pip install fastapi pydantic")

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentCreate(BaseModel):
    name: str
    saas_id: str
    workspace_id: str = ""
    scan_frequency: str = "manual"  # manual, daily, weekly
    config: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    id: str
    name: str
    saas_id: str
    workspace_id: str
    status: str = "idle"
    scan_frequency: str = "manual"
    last_scan_at: Optional[str] = None
    config: Dict[str, Any] = {}


# In-memory store (replace with DB in production)
_agents: Dict[str, Dict[str, Any]] = {}
_next_id = 1


@router.get("/", response_model=List[AgentResponse])
async def list_agents():
    """List all registered agents."""
    return list(_agents.values())


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(body: AgentCreate):
    """Register a new scan agent."""
    global _next_id
    agent_id = f"agent-{_next_id}"
    _next_id += 1

    agent = {
        "id": agent_id,
        "name": body.name,
        "saas_id": body.saas_id,
        "workspace_id": body.workspace_id,
        "status": "idle",
        "scan_frequency": body.scan_frequency,
        "last_scan_at": None,
        "config": body.config,
    }
    _agents[agent_id] = agent
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent details."""
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agents[agent_id]


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str):
    """Delete an agent."""
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    del _agents[agent_id]
