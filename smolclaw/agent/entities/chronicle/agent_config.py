"""Agent configuration entities."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class ConnectionStatus(str, Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    NEEDS_REVERIFICATION = "needs_reverification"


class ScanFrequency(str, Enum):
    MANUAL = "manual"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Agent(BaseModel):
    uid: str
    tenant_id: str
    workspace_id: str
    saas_id: str
    saas_name: str
    vault_uid: str | None = None
    vault_name: str | None = None
    vault_secret_id: str | None = None
    bw_item: str | None = None
    mfa_enabled: bool = False
    frequency: ScanFrequency
    status: AgentStatus
    last_scan_uid: str | None = None
    last_scan_at: datetime | None = None
    next_scan_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    browserbase_context_id: str | None = None
    connection_status: ConnectionStatus = ConnectionStatus.PENDING
    last_successful_login: datetime | None = None
    connection_error: str | None = None
