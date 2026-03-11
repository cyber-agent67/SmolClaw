"""Optional async database support using SQLAlchemy."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# SQLAlchemy is optional — only needed if using persistent database
try:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


class Database:
    """Async database connection manager.

    Only functional if sqlalchemy[asyncio] is installed.
    SmolClaw works without a database — this is for Chronicle SSPM features
    that need persistent storage of scan results.
    """

    def __init__(self, url: str = ""):
        self._url = url
        self._engine: Optional[object] = None
        self._session_factory: Optional[object] = None

    async def connect(self, url: str = "") -> None:
        """Initialize database connection."""
        if not HAS_SQLALCHEMY:
            logger.warning("SQLAlchemy not installed — database features disabled")
            return

        db_url = url or self._url
        if not db_url:
            logger.warning("No database URL configured")
            return

        self._engine = create_async_engine(db_url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("database_connected", url=db_url.split("@")[-1])

    def get_session_factory(self):
        """Return the async session factory."""
        return self._session_factory

    async def close(self) -> None:
        """Close database connection."""
        if self._engine and HAS_SQLALCHEMY:
            await self._engine.dispose()
            logger.info("database_disconnected")
