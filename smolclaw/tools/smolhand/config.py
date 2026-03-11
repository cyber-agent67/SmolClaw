"""Configuration for browser subagents Layer 1 (raw browser access).

This module provides configuration for basic browser automation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Layer1Config:
    """Configuration for Layer 1 (raw browser access).

    Attributes:
        timeout_ms: Timeout for browser operations in milliseconds
        max_links: Maximum number of links to extract from a page
        dom_settle_timeout_ms: Timeout for DOM to settle before extraction
    """
    timeout_ms: int = 30000
    max_links: int = 500
    dom_settle_timeout_ms: int = 3000

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Layer1Config":
        """Create config from dictionary."""
        return cls(
            timeout_ms=data.get("timeout_ms", 30000),
            max_links=data.get("max_links", 500),
            dom_settle_timeout_ms=data.get("dom_settle_timeout_ms", 3000),
        )


@dataclass
class BrowserConfig:
    """Master configuration for browser subagents (Layer 1 only).

    Attributes:
        layer1: Layer 1 configuration
    """
    layer1: Layer1Config = None  # type: ignore

    def __post_init__(self) -> None:
        if self.layer1 is None:
            self.layer1 = Layer1Config()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrowserConfig":
        """Create config from dictionary."""
        return cls(
            layer1=Layer1Config.from_dict(data.get("layer1", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "layer1": {
                "timeout_ms": self.layer1.timeout_ms,
                "max_links": self.layer1.max_links,
                "dom_settle_timeout_ms": self.layer1.dom_settle_timeout_ms,
            },
        }


# Global configuration instance
_config: Optional[BrowserConfig] = None


def get_config() -> BrowserConfig:
    """Get or create the global configuration."""
    global _config
    if _config is None:
        _config = BrowserConfig()
    return _config


def set_config(config: BrowserConfig) -> None:
    """Set the global configuration."""
    global _config
    _config = config


__all__ = [
    "Layer1Config",
    "BrowserConfig",
    "get_config",
    "set_config",
]
