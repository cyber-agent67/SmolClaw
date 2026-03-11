"""Vault entities for credential storage."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class VaultType(str, Enum):
    BITWARDEN = "bitwarden"


class VaultStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class Vault(BaseModel):
    uid: str
    name: str
    vault_type: VaultType
    status: VaultStatus = VaultStatus.DISCONNECTED
    description: str | None = None
    credential_count: int = 0
    last_sync_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class VaultCredentialRef(BaseModel):
    vault_uid: str
    secret_id: str


class VaultCredential(BaseModel):
    username: str
    password: str
    totp_seed: str | None = None
    metadata: dict | None = None


class VaultTestResult(BaseModel):
    success: bool
    message: str
    credential_count: int | None = None
