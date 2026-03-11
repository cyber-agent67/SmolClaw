"""App inventory entities."""
from datetime import UTC, datetime
from pydantic import BaseModel, Field


class InstalledApp(BaseModel):
    app_name: str
    permissions: list[str] = Field(default_factory=list)
    app_id: str | None = None
    screenshot_path: str | None = None
    parent_app_name: str | None = None
    app_level: int | None = None
    scope_details: list[dict] | None = None


class AppInventoryResult(BaseModel):
    saas_id: str
    workspace_id: str
    apps: list[InstalledApp] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    success: bool
    error: str | None = None


class AppWithChanges(BaseModel):
    app_name: str
    app_id: str | None = None
    permissions: list[str]
    permission_count: int
    change_type: str | None = None
    added_permissions: list[str] = Field(default_factory=list)
    removed_permissions: list[str] = Field(default_factory=list)
    parent_app_name: str | None = None
    app_level: int = 0
    scope_details: list[dict] | None = None


class AppInventoryScanResult(BaseModel):
    apps: list[AppWithChanges]
    total_apps: int
    new_apps: int = 0
    removed_apps: list[str] = Field(default_factory=list)
    permission_changes: int = 0
    discovered_at: datetime
