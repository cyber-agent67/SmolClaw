"""Chronicle login interaction — executes SaaS login flows."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class LoginRequest:
    """Request to login to a SaaS application."""
    saas_id: str
    workspace_id: str
    username: str = ""
    password: str = ""
    totp_seed: str = ""
    target_url: str = ""
    debug: bool = False


@dataclass
class LoginResult:
    """Result of a login attempt."""
    success: bool
    landed_url: str = ""
    error: str = ""
    error_type: str = "UNKNOWN"
    duration_seconds: float = 0.0
    screenshots: list = field(default_factory=list)


class LoginExecutor:
    """Executes login flow using BrowserWrapper.

    Steps:
    1. Navigate to login URL
    2. Fill username field
    3. Fill password field (secure)
    4. Handle MFA/TOTP if needed
    5. Verify login success
    """

    def __init__(self, browser, totp_provider=None, saas_config=None):
        self.browser = browser
        self.totp_provider = totp_provider
        self.saas_config = saas_config

    async def login(self, request: LoginRequest) -> LoginResult:
        """Execute the full login flow."""
        start = time.perf_counter()
        screenshots = []

        try:
            # Step 1: Navigate to login URL
            target_url = request.target_url
            if not target_url and self.saas_config:
                target_url = self.saas_config.login_url_template.format(
                    workspace_id=request.workspace_id
                ) if hasattr(self.saas_config, 'login_url_template') else ""

            if target_url:
                current = await self.browser.get_current_url()
                if not current or target_url not in (current or ""):
                    await self.browser.goto(target_url)
                    await asyncio.sleep(2)

            # Step 2: Handle pre-login actions (e.g., "Sign in with password" button)
            if self.saas_config and hasattr(self.saas_config, 'pre_login_action') and self.saas_config.pre_login_action:
                try:
                    await self.browser.click(
                        selector=None,
                        fallback_instruction=self.saas_config.pre_login_action
                    )
                    await asyncio.sleep(1)
                except Exception:
                    logger.debug("Pre-login action skipped or not found")

            # Step 3: Fill username
            if request.username:
                username_selectors = self._get_username_selectors()
                filled = False
                for sel in username_selectors:
                    try:
                        await self.browser.type_text(sel, request.username)
                        filled = True
                        break
                    except Exception:
                        continue
                if not filled:
                    logger.warning("Could not fill username with known selectors")

            # Step 4: Fill password (secure)
            if request.password:
                password_selectors = self._get_password_selectors()
                filled = False
                for sel in password_selectors:
                    try:
                        await self.browser.secure_fill("password", request.password)
                        filled = True
                        break
                    except Exception:
                        continue
                if not filled:
                    logger.warning("Could not fill password with known selectors")

            # Step 5: Submit login form
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Sign in')",
                "button:contains('Log in')",
            ]
            for sel in submit_selectors:
                try:
                    await self.browser.click(sel)
                    break
                except Exception:
                    continue

            await asyncio.sleep(3)

            # Step 6: Handle MFA/TOTP if needed
            if self.totp_provider and request.totp_seed:
                try:
                    code = await self.totp_provider.get_totp_code()
                    if code:
                        totp_selectors = [
                            "input[name='totp']",
                            "input[name='code']",
                            "input[name='verification_code']",
                            "input[type='tel']",
                        ]
                        for sel in totp_selectors:
                            try:
                                await self.browser.secure_fill("TOTP code", code)
                                break
                            except Exception:
                                continue
                        await asyncio.sleep(2)
                except Exception as e:
                    logger.warning("TOTP handling failed: %s", e)

            # Step 7: Verify login
            if request.debug:
                screenshot = await self.browser.screenshot()
                if screenshot:
                    screenshots.append(screenshot)

            landed_url = await self.browser.get_current_url() or ""
            success = self._is_login_successful(landed_url, request)

            elapsed = time.perf_counter() - start
            return LoginResult(
                success=success,
                landed_url=landed_url,
                duration_seconds=elapsed,
                screenshots=screenshots,
            )

        except Exception as e:
            elapsed = time.perf_counter() - start
            error_type = self._classify_error(str(e))
            return LoginResult(
                success=False,
                error=str(e),
                error_type=error_type,
                duration_seconds=elapsed,
                screenshots=screenshots,
            )

    def _get_username_selectors(self) -> list:
        if self.saas_config and hasattr(self.saas_config, 'login_selectors'):
            s = self.saas_config.login_selectors
            if hasattr(s, 'username_selector') and s.username_selector:
                return [s.username_selector]
        return [
            "input[name='username']",
            "input[name='email']",
            "input[type='email']",
            "input[id='username']",
            "#okta-signin-username",
        ]

    def _get_password_selectors(self) -> list:
        if self.saas_config and hasattr(self.saas_config, 'login_selectors'):
            s = self.saas_config.login_selectors
            if hasattr(s, 'password_selector') and s.password_selector:
                return [s.password_selector]
        return [
            "input[name='password']",
            "input[type='password']",
            "input[id='password']",
            "#okta-signin-password",
        ]

    def _is_login_successful(self, landed_url: str, request: LoginRequest) -> bool:
        login_indicators = ["/login", "/signin", "/sign-in", "/auth", "accounts.google.com"]
        for indicator in login_indicators:
            if indicator in landed_url.lower():
                return False
        if self.saas_config and hasattr(self.saas_config, 'login_success_url_patterns'):
            for pattern in self.saas_config.login_success_url_patterns:
                if pattern in landed_url:
                    return True
        return True

    @staticmethod
    def _classify_error(error: str) -> str:
        error_lower = error.lower()
        if "mfa" in error_lower or "two-factor" in error_lower or "2fa" in error_lower:
            return "MFA_REQUIRED"
        if "invalid" in error_lower and ("credential" in error_lower or "password" in error_lower):
            return "INVALID_CREDENTIALS"
        if "verification" in error_lower or "captcha" in error_lower:
            return "VERIFICATION_REQUIRED"
        if "blocked" in error_lower or "locked" in error_lower:
            return "LOGIN_BLOCKED"
        if "timeout" in error_lower:
            return "TIMEOUT"
        return "UNKNOWN"
