"""Login agent — high-level orchestration for SaaS authentication."""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

from .models import LoginErrorType, LoginRequest, LoginResult
from .totp import ChainedTOTPProvider

logger = logging.getLogger(__name__)


class LoginAgent:
    """Orchestrates SaaS login with credential resolution and TOTP handling.

    Steps:
    1. Resolve SaaS configuration
    2. Resolve credentials
    3. Navigate to login URL
    4. Build TOTP provider
    5. Execute login via LoginExecutor
    """

    def __init__(
        self,
        credential_provider=None,
        totp_provider: Optional[ChainedTOTPProvider] = None,
    ):
        self.credential_provider = credential_provider
        self.totp_provider = totp_provider

    async def login(self, browser, request: LoginRequest) -> LoginResult:
        """Execute a full login flow."""
        start = time.perf_counter()

        try:
            # Resolve credentials if not provided
            username = request.username
            password = request.password
            totp_seed = request.totp_seed

            if (not username or not password) and self.credential_provider:
                try:
                    creds = self.credential_provider.get_credentials(
                        saas_id=request.saas_id,
                        workspace_id=request.workspace_id,
                    )
                    username = username or creds.username
                    password = password or creds.password
                    totp_seed = totp_seed or creds.totp_seed
                except Exception as e:
                    elapsed = time.perf_counter() - start
                    return LoginResult(
                        success=False,
                        error=f"Credential resolution failed: {e}",
                        error_type=LoginErrorType.CREDENTIALS_NOT_FOUND,
                        duration_seconds=elapsed,
                    )

            # Build TOTP provider if needed
            totp = self.totp_provider
            if not totp and totp_seed:
                totp = ChainedTOTPProvider(totp_seed=totp_seed)

            # Handle Okta SSO TOTP
            if request.sso_enabled and request.idp_type and "okta" in request.idp_type.lower():
                okta_user = os.environ.get("OKTA_USERNAME", username)
                okta_pass = os.environ.get("OKTA_PASSWORD", password)
                okta_org = request.context.get("okta_org_url", "")
                if okta_org and not totp:
                    totp = ChainedTOTPProvider(
                        okta_org_url=okta_org,
                        okta_username=okta_user,
                        okta_password=okta_pass,
                    )

            # Import and use LoginExecutor from interactions
            from smolclaw.agent.interactions.chronicle.login import LoginExecutor, LoginRequest as ExecRequest

            executor = LoginExecutor(
                browser=browser,
                totp_provider=totp,
            )

            exec_request = ExecRequest(
                saas_id=request.saas_id,
                workspace_id=request.workspace_id,
                username=username,
                password=password,
                totp_seed=totp_seed,
                target_url=request.target_url,
                debug=request.debug,
            )

            exec_result = await executor.login(exec_request)

            elapsed = time.perf_counter() - start
            return LoginResult(
                success=exec_result.success,
                landed_url=exec_result.landed_url,
                error=exec_result.error,
                error_type=LoginErrorType(exec_result.error_type) if exec_result.error_type != "UNKNOWN" else LoginErrorType.UNKNOWN,
                duration_seconds=elapsed,
                screenshots=exec_result.screenshots,
            )

        except Exception as e:
            elapsed = time.perf_counter() - start
            error_type = self._classify_error(str(e))
            return LoginResult(
                success=False,
                error=str(e),
                error_type=error_type,
                duration_seconds=elapsed,
            )

    @staticmethod
    def _classify_error(error: str) -> LoginErrorType:
        error_lower = error.lower()
        if "mfa" in error_lower or "two-factor" in error_lower:
            return LoginErrorType.MFA_REQUIRED
        if "invalid" in error_lower and ("credential" in error_lower or "password" in error_lower):
            return LoginErrorType.INVALID_CREDENTIALS
        if "verification" in error_lower or "captcha" in error_lower:
            return LoginErrorType.VERIFICATION_REQUIRED
        if "blocked" in error_lower or "locked" in error_lower:
            return LoginErrorType.LOGIN_BLOCKED
        if "timeout" in error_lower:
            return LoginErrorType.TIMEOUT
        if "sso" in error_lower or "saml" in error_lower:
            return LoginErrorType.SSO_ERROR
        return LoginErrorType.UNKNOWN

    async def close(self) -> None:
        """Cleanup resources."""
        if self.credential_provider and hasattr(self.credential_provider, 'close'):
            self.credential_provider.close()
