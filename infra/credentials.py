"""Credential resolution — chained provider pattern for SaaS credentials."""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CredentialNotFoundError(Exception):
    """Raised when credentials cannot be resolved for a SaaS application."""
    pass


@dataclass
class ResolvedCredentials:
    """Resolved credentials for a SaaS application."""
    saas_id: str
    username: str
    password: str
    totp_seed: str = ""
    workspace_id: str = ""


class EnvCredentialProvider:
    """Reads credentials from environment variables.

    Tries formats:
    1. SMOLCLAW_{SAAS_ID}_{WORKSPACE_ID}_USERNAME (full)
    2. {SAAS_ID}_USERNAME (simple)
    """

    def get_credentials(
        self, saas_id: str, workspace_id: str = "", vault_ref: Any = None
    ) -> ResolvedCredentials:
        normalized_saas = self._normalize(saas_id)
        normalized_ws = self._normalize(workspace_id) if workspace_id else ""

        # Try full format
        if normalized_ws:
            prefix = f"SMOLCLAW_{normalized_saas}_{normalized_ws}"
            username = os.environ.get(f"{prefix}_USERNAME")
            password = os.environ.get(f"{prefix}_PASSWORD")
            if username and password:
                totp = os.environ.get(f"{prefix}_TOTP_SEED", "")
                logger.debug("credentials_loaded", saas_id=saas_id, format="full")
                return ResolvedCredentials(
                    saas_id=saas_id,
                    username=username,
                    password=password,
                    totp_seed=totp,
                    workspace_id=workspace_id,
                )

        # Try simple format
        prefix = normalized_saas
        username = os.environ.get(f"{prefix}_USERNAME")
        password = os.environ.get(f"{prefix}_PASSWORD")
        if username and password:
            totp = os.environ.get(f"{prefix}_TOTP_SEED", "")
            logger.debug("credentials_loaded", saas_id=saas_id, format="simple")
            return ResolvedCredentials(
                saas_id=saas_id,
                username=username,
                password=password,
                totp_seed=totp,
                workspace_id=workspace_id,
            )

        raise CredentialNotFoundError(
            f"No env credentials found for {saas_id} (tried SMOLCLAW_{normalized_saas}_* and {prefix}_*)"
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9]", "_", value).upper()


class HomeCredentialProvider:
    """Reads credentials from ~/.smolclaw/credentials.json."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or (Path.home() / ".smolclaw" / "credentials.json")
        self._cache: Optional[Dict[str, Any]] = None

    def get_credentials(
        self, saas_id: str, workspace_id: str = "", vault_ref: Any = None
    ) -> ResolvedCredentials:
        data = self._load()
        key = saas_id.lower()

        if key not in data:
            raise CredentialNotFoundError(
                f"No credentials found for '{saas_id}' in {self.path}"
            )

        entry = data[key]
        return ResolvedCredentials(
            saas_id=saas_id,
            username=entry.get("username", ""),
            password=entry.get("password", ""),
            totp_seed=entry.get("totp_seed", ""),
            workspace_id=workspace_id,
        )

    def _load(self) -> Dict[str, Any]:
        if self._cache is not None:
            return self._cache
        if not self.path.exists():
            logger.debug("credentials_file_not_found", path=str(self.path))
            self._cache = {}
            return self._cache
        try:
            self._cache = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("credentials_parse_error", path=str(self.path), error=str(e))
            self._cache = {}
        return self._cache


class ChainedCredentialProvider:
    """Chains credential providers with priority fallback.

    Order: home (~/.smolclaw/credentials.json) → environment variables.
    """

    def __init__(
        self,
        env_provider: Optional[EnvCredentialProvider] = None,
        home_provider: Optional[HomeCredentialProvider] = None,
    ):
        self.home_provider = home_provider or HomeCredentialProvider()
        self.env_provider = env_provider or EnvCredentialProvider()

    def get_credentials(
        self, saas_id: str, workspace_id: str = "", vault_ref: Any = None
    ) -> ResolvedCredentials:
        # Try home dir first
        try:
            creds = self.home_provider.get_credentials(saas_id, workspace_id, vault_ref)
            logger.info("credentials_from_home_dir", saas_id=saas_id)
            return creds
        except CredentialNotFoundError:
            pass
        except Exception as e:
            logger.warning("home_credentials_error", saas_id=saas_id, error=str(e))

        # Fall back to env
        try:
            creds = self.env_provider.get_credentials(saas_id, workspace_id, vault_ref)
            logger.info("credentials_from_env", saas_id=saas_id)
            return creds
        except CredentialNotFoundError:
            raise

    def close(self) -> None:
        """Cleanup resources."""
        pass
