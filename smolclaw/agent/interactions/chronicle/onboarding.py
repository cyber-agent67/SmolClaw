"""Chronicle onboarding interaction — registers a new SaaS app for monitoring."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OnboardingResult:
    """Result of onboarding a SaaS application."""
    saas_id: str
    success: bool = False
    login_verified: bool = False
    settings_pages_found: int = 0
    baseline_settings_count: int = 0
    navigation_paths: List[Dict[str, Any]] = field(default_factory=list)
    error: str = ""


class OnboardSaaSApp:
    """Onboards a new SaaS application for security monitoring.

    Steps:
    1. Verify login works
    2. Explore to find settings pages
    3. Extract initial baseline settings
    4. Store navigation paths for future scans
    """

    def __init__(
        self,
        browser,
        login_executor=None,
        explorer=None,
        extractor=None,
    ):
        self.browser = browser
        self.login_executor = login_executor
        self.explorer = explorer
        self.extractor = extractor

    async def onboard(
        self,
        saas_id: str,
        workspace_id: str = "",
        login_request=None,
        exploration_targets: Optional[List[str]] = None,
        keyword_weights: Optional[Dict[str, float]] = None,
    ) -> OnboardingResult:
        """Onboard a SaaS application."""
        result = OnboardingResult(saas_id=saas_id)

        # Step 1: Verify login
        if self.login_executor and login_request:
            try:
                login_result = await self.login_executor.login(login_request)
                result.login_verified = login_result.success
                if not login_result.success:
                    result.error = f"Login failed: {login_result.error}"
                    return result
            except Exception as e:
                result.error = f"Login error: {e}"
                return result

        # Step 2: Explore for settings pages
        targets = exploration_targets or [
            "security settings",
            "authentication settings",
            "admin settings",
        ]

        all_paths = []
        if self.explorer:
            for target in targets:
                try:
                    exploration = await self.explorer.explore(
                        target=target,
                        keyword_weights=keyword_weights,
                    )
                    for path in exploration.paths:
                        path_data = {
                            "target": target,
                            "steps": [
                                {"url": s.url, "title": s.title, "score": s.score}
                                for s in path
                            ],
                        }
                        all_paths.append(path_data)
                except Exception as e:
                    logger.warning("Exploration for '%s' failed: %s", target, e)

        result.navigation_paths = all_paths
        result.settings_pages_found = len(all_paths)

        # Step 3: Extract baseline settings from discovered pages
        if self.extractor and all_paths:
            total_settings = 0
            for path_data in all_paths:
                steps = path_data.get("steps", [])
                if steps:
                    last_step = steps[-1]
                    url = last_step.get("url", "")
                    if url:
                        try:
                            await self.browser.goto(url)
                            page_result = await self.extractor.extract_from_current_page(
                                context_hint=saas_id,
                                saas_name=saas_id,
                            )
                            total_settings += len(page_result.settings)
                        except Exception as e:
                            logger.warning("Baseline extraction from %s failed: %s", url, e)

            result.baseline_settings_count = total_settings

        result.success = result.login_verified or not login_request
        return result
