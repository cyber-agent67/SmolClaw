"""Settings API — view and manage extracted security settings."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException, Query
    from pydantic import BaseModel
except ImportError:
    raise ImportError("fastapi required")

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingItem(BaseModel):
    label: str
    value: str
    element_type: str = "unknown"
    section: str = ""
    confidence: float = 1.0
    page_url: str = ""


class SettingsPage(BaseModel):
    saas_id: str
    url: str
    settings: List[SettingItem] = []
    extracted_at: Optional[str] = None


_settings_store: Dict[str, List[Dict[str, Any]]] = {}


@router.get("/{saas_id}", response_model=List[SettingItem])
async def get_settings(
    saas_id: str,
    section: str = Query("", description="Filter by section"),
):
    """Get extracted settings for a SaaS application."""
    settings = _settings_store.get(saas_id, [])
    if section:
        settings = [s for s in settings if section.lower() in s.get("section", "").lower()]
    return settings


@router.get("/{saas_id}/pages", response_model=List[SettingsPage])
async def get_settings_pages(saas_id: str):
    """Get settings grouped by page URL."""
    raw = _settings_store.get(saas_id, [])
    pages: Dict[str, SettingsPage] = {}
    for entry in raw:
        url = entry.get("page_url", "")
        if url not in pages:
            pages[url] = SettingsPage(saas_id=saas_id, url=url)
        pages[url].settings.append(SettingItem(**{k: entry[k] for k in SettingItem.model_fields if k in entry}))
    return list(pages.values())


@router.post("/{saas_id}/baseline", status_code=201)
async def create_baseline(saas_id: str):
    """Save current settings as baseline for drift detection."""
    settings = _settings_store.get(saas_id, [])
    if not settings:
        raise HTTPException(status_code=404, detail="No settings found for this SaaS app")
    # Would save to storage
    return {"message": f"Baseline created with {len(settings)} settings", "saas_id": saas_id}
