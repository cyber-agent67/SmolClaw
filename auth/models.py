"""Auth data models for login requests and results."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class LoginErrorType(str, Enum):
    """Classification of login errors."""
    MFA_REQUIRED = "MFA_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    LOGIN_BLOCKED = "LOGIN_BLOCKED"
    SAAS_CONFIG_NOT_FOUND = "SAAS_CONFIG_NOT_FOUND"
    CREDENTIALS_NOT_FOUND = "CREDENTIALS_NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    SSO_ERROR = "SSO_ERROR"
    UNKNOWN = "UNKNOWN"


@dataclass
class LoginRequest:
    """Request to authenticate to a SaaS application."""
    saas_id: str
    workspace_id: str = ""
    username: str = ""
    password: str = ""
    totp_seed: str = ""
    target_url: str = ""
    idp_name: str = ""
    idp_type: str = ""
    sso_enabled: bool = False
    debug: bool = False
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoginResult:
    """Result of a login attempt."""
    success: bool
    landed_url: str = ""
    error: str = ""
    error_type: LoginErrorType = LoginErrorType.UNKNOWN
    duration_seconds: float = 0.0
    screenshots: List[bytes] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
