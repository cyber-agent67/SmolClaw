"""TOTP code generation providers — chained with fallback."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


class TOTPProvider(Protocol):
    """Protocol for TOTP code providers."""
    async def get_totp_code(self) -> Optional[str]:
        ...


class PyOTPProvider:
    """Generates TOTP codes using pyotp library from a Base32 seed."""

    def __init__(self, seed: str):
        self.seed = seed

    async def get_totp_code(self) -> Optional[str]:
        if not self.seed:
            return None
        try:
            import pyotp
            totp = pyotp.TOTP(self.seed)
            return totp.now()
        except ImportError:
            logger.warning("pyotp not installed — cannot generate TOTP codes")
            return None
        except Exception as e:
            logger.error("TOTP generation failed: %s", e)
            return None


class BitwardenTOTPProvider:
    """Gets TOTP codes from Bitwarden CLI."""

    def __init__(self, item_id: str):
        self.item_id = item_id

    async def get_totp_code(self) -> Optional[str]:
        if not self.item_id:
            return None

        session = os.environ.get("BW_SESSION", "")
        if not session:
            logger.warning("BW_SESSION not set — cannot use Bitwarden TOTP")
            return None

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["bw", "get", "totp", self.item_id, "--session", session],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                code = result.stdout.strip()
                if code and code.isdigit() and len(code) == 6:
                    return code
            logger.warning("Bitwarden TOTP failed: %s", result.stderr)
        except FileNotFoundError:
            logger.warning("bw CLI not found on PATH")
        except Exception as e:
            logger.error("Bitwarden TOTP error: %s", e)
        return None


class OktaVerifyTOTPProvider:
    """Programmatic Okta Verify TOTP enrollment and code generation.

    Enrolls as a TOTP factor via Okta API, caches the shared secret,
    and generates codes using pyotp.
    """

    def __init__(
        self,
        okta_org_url: str,
        username: str,
        password: str,
        cache_key: str = "",
    ):
        self.okta_org_url = okta_org_url.rstrip("/")
        self.username = username
        self.password = password
        self.cache_key = cache_key or f"{username}@{okta_org_url.split('//')[- 1]}"
        self._secret: Optional[str] = None

    async def get_totp_code(self) -> Optional[str]:
        # Check cache first
        secret = self._load_cached_secret()
        if not secret:
            secret = await self._enroll_totp()
            if secret:
                self._save_cached_secret(secret)

        if not secret:
            return None

        self._secret = secret
        try:
            import pyotp
            return pyotp.TOTP(secret).now()
        except ImportError:
            logger.warning("pyotp not installed")
            return None

    def _load_cached_secret(self) -> Optional[str]:
        cache_dir = Path.home() / ".smolclaw" / "okta_verify"
        cache_file = cache_dir / f"{self.cache_key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                return data.get("shared_secret")
            except Exception:
                pass
        return None

    def _save_cached_secret(self, secret: str) -> None:
        cache_dir = Path.home() / ".smolclaw" / "okta_verify"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{self.cache_key}.json"
        cache_file.write_text(
            json.dumps({"shared_secret": secret}), encoding="utf-8"
        )
        cache_file.chmod(0o600)

    async def _enroll_totp(self) -> Optional[str]:
        """Enroll as TOTP factor via Okta Authentication API."""
        try:
            import aiohttp
        except ImportError:
            logger.warning("aiohttp required for Okta TOTP enrollment")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Authenticate
                auth_url = f"{self.okta_org_url}/api/v1/authn"
                async with session.post(auth_url, json={
                    "username": self.username,
                    "password": self.password,
                }) as resp:
                    if resp.status != 200:
                        logger.error("Okta auth failed: %d", resp.status)
                        return None
                    auth_data = await resp.json()

                status = auth_data.get("status")
                state_token = auth_data.get("stateToken")

                if status == "MFA_ENROLL" and state_token:
                    # Enroll TOTP factor
                    enroll_url = f"{self.okta_org_url}/api/v1/authn/factors"
                    async with session.post(enroll_url, json={
                        "stateToken": state_token,
                        "factorType": "token:software:totp",
                        "provider": "GOOGLE",
                    }) as resp:
                        if resp.status != 200:
                            logger.error("TOTP enrollment failed: %d", resp.status)
                            return None
                        enroll_data = await resp.json()

                    # Extract shared secret
                    embedded = enroll_data.get("_embedded", {})
                    activation = embedded.get("activation", {})
                    shared_secret = activation.get("sharedSecret")

                    if shared_secret:
                        # Activate by submitting a code
                        try:
                            import pyotp
                            code = pyotp.TOTP(shared_secret).now()
                            factor_id = enroll_data.get("id")
                            activate_url = f"{self.okta_org_url}/api/v1/authn/factors/{factor_id}/lifecycle/activate"
                            async with session.post(activate_url, json={
                                "stateToken": state_token,
                                "passCode": code,
                            }) as resp:
                                if resp.status == 200:
                                    return shared_secret
                        except ImportError:
                            return shared_secret  # Can't activate without pyotp but have the secret

                elif status == "SUCCESS":
                    logger.info("Already authenticated — TOTP may already be enrolled")

                elif status == "MFA_REQUIRED":
                    logger.info("MFA already required — existing TOTP factor detected")

        except Exception as e:
            logger.error("Okta TOTP enrollment error: %s", e)

        return None


class InteractiveTOTPProvider:
    """Prompts user for TOTP code via stdin."""

    async def get_totp_code(self) -> Optional[str]:
        try:
            code = await asyncio.to_thread(
                input, "Enter TOTP/MFA code: "
            )
            code = code.strip()
            if code and code.isdigit() and len(code) == 6:
                return code
            logger.warning("Invalid TOTP code format")
        except Exception:
            pass
        return None


class ChainedTOTPProvider:
    """Chains TOTP providers with priority fallback.

    Order: Bitwarden CLI → Okta Verify API → PyOTP seed → Interactive
    """

    def __init__(
        self,
        bitwarden_item_id: str = "",
        totp_seed: str = "",
        okta_org_url: str = "",
        okta_username: str = "",
        okta_password: str = "",
        interactive: bool = True,
    ):
        self.providers: list = []

        if bitwarden_item_id:
            self.providers.append(BitwardenTOTPProvider(bitwarden_item_id))

        if okta_org_url and okta_username and okta_password:
            self.providers.append(OktaVerifyTOTPProvider(
                okta_org_url=okta_org_url,
                username=okta_username,
                password=okta_password,
            ))

        if totp_seed:
            self.providers.append(PyOTPProvider(totp_seed))

        if interactive:
            self.providers.append(InteractiveTOTPProvider())

    async def get_totp_code(self) -> Optional[str]:
        for provider in self.providers:
            try:
                code = await provider.get_totp_code()
                if code:
                    logger.info("TOTP code from %s", type(provider).__name__)
                    return code
            except Exception as e:
                logger.debug("TOTP provider %s failed: %s", type(provider).__name__, e)

        logger.warning("All TOTP providers exhausted")
        return None
