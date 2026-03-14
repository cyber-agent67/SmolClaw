"""SaaS application registry API."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
except ImportError:
    raise ImportError("fastapi required")

router = APIRouter(prefix="/saas", tags=["saas"])


class SaaSAppCreate(BaseModel):
    saas_id: str
    display_name: str
    login_url: str = ""
    workspace_id: str = ""
    config: Dict[str, Any] = {}


class SaaSAppResponse(BaseModel):
    saas_id: str
    display_name: str
    login_url: str = ""
    workspace_id: str = ""
    status: str = "pending"  # pending, onboarded, error
    settings_count: int = 0
    config: Dict[str, Any] = {}


_saas_apps: Dict[str, Dict[str, Any]] = {}


@router.get("/", response_model=List[SaaSAppResponse])
async def list_saas_apps():
    """List all registered SaaS applications."""
    return list(_saas_apps.values())


@router.post("/", response_model=SaaSAppResponse, status_code=201)
async def register_saas_app(body: SaaSAppCreate):
    """Register a new SaaS application for monitoring."""
    if body.saas_id in _saas_apps:
        raise HTTPException(status_code=409, detail="SaaS app already registered")

    app = {
        "saas_id": body.saas_id,
        "display_name": body.display_name,
        "login_url": body.login_url,
        "workspace_id": body.workspace_id,
        "status": "pending",
        "settings_count": 0,
        "config": body.config,
    }
    _saas_apps[body.saas_id] = app
    return app


@router.get("/{saas_id}", response_model=SaaSAppResponse)
async def get_saas_app(saas_id: str):
    """Get SaaS app details."""
    if saas_id not in _saas_apps:
        raise HTTPException(status_code=404, detail="SaaS app not found")
    return _saas_apps[saas_id]


@router.delete("/{saas_id}", status_code=204)
async def delete_saas_app(saas_id: str):
    """Remove a SaaS application."""
    if saas_id not in _saas_apps:
        raise HTTPException(status_code=404, detail="SaaS app not found")
    del _saas_apps[saas_id]


@router.post("/{saas_id}/onboard", response_model=Dict[str, Any])
async def onboard_saas_app(saas_id: str):
    """Trigger onboarding for a SaaS application."""
    if saas_id not in _saas_apps:
        raise HTTPException(status_code=404, detail="SaaS app not found")
    # Would trigger actual onboarding pipeline
    _saas_apps[saas_id]["status"] = "onboarding"
    return {"message": f"Onboarding started for {saas_id}", "status": "onboarding"}
