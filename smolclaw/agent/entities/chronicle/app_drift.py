"""App drift entities."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

DriftType = Literal[
    "new_app", "removed_app", "permissions_added",
    "permissions_removed", "child_apps_added", "child_apps_removed",
]
DriftStatus = Literal["open", "acknowledged", "resolved", "suppressed"]


class NewAppChangeDetails(BaseModel):
    permissions: list[str]
    permission_count: int


class RemovedAppChangeDetails(BaseModel):
    last_known_permissions: list[str]


class PermissionsAddedChangeDetails(BaseModel):
    added: list[str]


class PermissionsRemovedChangeDetails(BaseModel):
    removed: list[str]


class ChildAppsAddedChangeDetails(BaseModel):
    added_apps: list[str]


class ChildAppsRemovedChangeDetails(BaseModel):
    removed_apps: list[str]


class AppDrift(BaseModel):
    drift_id: str
    tenant_id: str
    saas_id: str
    workspace_id: str
    agent_uid: str
    app_name: str
    app_id: str | None = None
    parent_app_name: str | None = None
    app_level: int = 0
    drift_type: DriftType
    change_details: dict
    detected_at: datetime
    detected_in_scan_uid: str
    last_observed_at: datetime
    last_observed_in_scan_uid: str
    status: DriftStatus
    resolved_at: datetime | None = None
    resolved_in_scan_uid: str | None = None
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    screenshot_path: str | None = None
    created_at: datetime
    updated_at: datetime
