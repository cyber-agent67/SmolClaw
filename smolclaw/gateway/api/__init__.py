"""Chronicle SSPM REST API routers."""

from smolclaw.gateway.api.agents import router as agents_router
from smolclaw.gateway.api.saas import router as saas_router
from smolclaw.gateway.api.scans import router as scans_router
from smolclaw.gateway.api.settings import router as settings_router

__all__ = [
    "agents_router",
    "saas_router",
    "scans_router",
    "settings_router",
]
