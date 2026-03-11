"""Scan execution API — trigger and monitor SSPM scans."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException, BackgroundTasks
    from pydantic import BaseModel
except ImportError:
    raise ImportError("fastapi required")

router = APIRouter(prefix="/scans", tags=["scans"])


class ScanRequest(BaseModel):
    agent_id: str = ""
    saas_id: str
    workspace_id: str = ""
    stages: List[str] = ["login", "exploration", "navigation", "extraction"]
    target_url: str = ""
    context: Dict[str, Any] = {}


class ScanStatus(BaseModel):
    id: str
    saas_id: str
    status: str  # pending, running, succeeded, failed
    stages: Dict[str, Any] = {}
    total_settings: int = 0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: str = ""


_scans: Dict[str, Dict[str, Any]] = {}
_next_scan_id = 1


@router.post("/", response_model=ScanStatus, status_code=201)
async def trigger_scan(body: ScanRequest, background_tasks: BackgroundTasks):
    """Trigger a new SSPM scan."""
    global _next_scan_id
    scan_id = f"scan-{_next_scan_id}"
    _next_scan_id += 1

    scan = {
        "id": scan_id,
        "saas_id": body.saas_id,
        "status": "pending",
        "stages": {s: "pending" for s in body.stages},
        "total_settings": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "error": "",
    }
    _scans[scan_id] = scan

    # In production, this would launch the actual pipeline
    background_tasks.add_task(_execute_scan, scan_id, body)

    return scan


@router.get("/", response_model=List[ScanStatus])
async def list_scans(saas_id: str = "", limit: int = 20):
    """List scans, optionally filtered by SaaS app."""
    scans = list(_scans.values())
    if saas_id:
        scans = [s for s in scans if s["saas_id"] == saas_id]
    return scans[:limit]


@router.get("/{scan_id}", response_model=ScanStatus)
async def get_scan(scan_id: str):
    """Get scan status and results."""
    if scan_id not in _scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _scans[scan_id]


async def _execute_scan(scan_id: str, request: ScanRequest):
    """Background scan execution placeholder."""
    scan = _scans.get(scan_id)
    if not scan:
        return

    scan["status"] = "running"
    try:
        # Pipeline execution would go here
        # For now, mark stages as they would run
        for stage in request.stages:
            scan["stages"][stage] = "running"
            await asyncio.sleep(0.1)  # Placeholder
            scan["stages"][stage] = "succeeded"

        scan["status"] = "succeeded"
    except Exception as e:
        scan["status"] = "failed"
        scan["error"] = str(e)
    finally:
        scan["finished_at"] = datetime.now(timezone.utc).isoformat()
