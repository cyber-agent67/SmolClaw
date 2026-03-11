"""Browser configuration."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class BrowserConfig:
    """Configuration for browser instances."""

    env: Literal["LOCAL", "BROWSERBASE"] = "LOCAL"
    headless: bool = False
    bot_evasion: bool = False
    window_width: int = 1280
    window_height: int = 1100
    scale_factor: float = 1.0
    navigation_timeout_ms: int = 30000
    dom_settle_timeout_ms: int = 3000
    # Cloud browser settings
    browserbase_api_key: str | None = None
    browserbase_project_id: str | None = None
    cdp_url: str | None = None
    use_proxies: bool = False
    proxy_country: str | None = None

    # Anti-detection
    BOT_EVASION_ARGS: list[str] = field(default_factory=lambda: [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--disable-background-timer-throttling",
        "--disable-popup-blocking",
    ])
