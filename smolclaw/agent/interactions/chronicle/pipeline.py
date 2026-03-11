"""Chronicle pipeline interaction — orchestrates full SSPM scan."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    LOGIN = "login"
    EXPLORATION = "exploration"
    NAVIGATION = "navigation"
    EXTRACTION = "extraction"


class PipelinePhase(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StageResult:
    """Result of a single pipeline stage."""
    stage: PipelineStage
    phase: PipelinePhase = PipelinePhase.PENDING
    started_at: float = 0.0
    finished_at: float = 0.0
    output: Dict[str, Any] = field(default_factory=dict)
    error: str = ""

    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return 0.0


@dataclass
class PipelineResult:
    """Result of a full pipeline run."""
    phase: PipelinePhase = PipelinePhase.PENDING
    stages: Dict[str, StageResult] = field(default_factory=dict)
    total_settings: int = 0
    total_pages: int = 0

    @property
    def duration_seconds(self) -> float:
        return sum(s.duration_seconds for s in self.stages.values())


class RunPipeline:
    """Orchestrates the full SSPM scan pipeline.

    Stages:
    1. LOGIN -- Authenticate to the SaaS application
    2. EXPLORATION -- Discover navigation paths to settings pages
    3. NAVIGATION -- Follow paths to each settings page
    4. EXTRACTION -- Extract security settings from each page
    """

    def __init__(self, browser, login_executor=None, explorer=None, extractor=None):
        self.browser = browser
        self.login_executor = login_executor
        self.explorer = explorer
        self.extractor = extractor

    async def run(
        self,
        saas_id: str,
        workspace_id: str,
        stages: Optional[List[PipelineStage]] = None,
        login_request=None,
        exploration_target: str = "security settings",
        keyword_weights: Optional[Dict[str, float]] = None,
        navigation_urls: Optional[List[str]] = None,
        context_hint: str = "",
    ) -> PipelineResult:
        """Execute the pipeline stages in order."""
        if stages is None:
            stages = list(PipelineStage)

        result = PipelineResult(phase=PipelinePhase.RUNNING)

        for stage in stages:
            stage_result = StageResult(stage=stage)
            stage_result.phase = PipelinePhase.RUNNING
            stage_result.started_at = time.perf_counter()
            result.stages[stage.value] = stage_result

            try:
                if stage == PipelineStage.LOGIN:
                    await self._run_login(stage_result, login_request)
                elif stage == PipelineStage.EXPLORATION:
                    await self._run_exploration(
                        stage_result, exploration_target, keyword_weights
                    )
                elif stage == PipelineStage.NAVIGATION:
                    await self._run_navigation(
                        stage_result, navigation_urls, result
                    )
                elif stage == PipelineStage.EXTRACTION:
                    await self._run_extraction(
                        stage_result, saas_id, context_hint, result
                    )

                stage_result.phase = PipelinePhase.SUCCEEDED
            except Exception as e:
                stage_result.phase = PipelinePhase.FAILED
                stage_result.error = str(e)
                logger.error("Stage %s failed: %s", stage.value, e)
                result.phase = PipelinePhase.FAILED
                break
            finally:
                stage_result.finished_at = time.perf_counter()

        if result.phase == PipelinePhase.RUNNING:
            result.phase = PipelinePhase.SUCCEEDED

        return result

    async def _run_login(self, stage_result: StageResult, login_request) -> None:
        if not self.login_executor or not login_request:
            logger.info("Skipping login stage (no executor or request)")
            return

        login_result = await self.login_executor.login(login_request)
        stage_result.output = {
            "success": login_result.success,
            "landed_url": login_result.landed_url,
            "duration": login_result.duration_seconds,
        }
        if not login_result.success:
            raise RuntimeError(f"Login failed: {login_result.error}")

    async def _run_exploration(
        self,
        stage_result: StageResult,
        target: str,
        keyword_weights: Optional[Dict[str, float]],
    ) -> None:
        if not self.explorer:
            logger.info("Skipping exploration stage (no explorer)")
            return

        exploration = await self.explorer.explore(
            target=target,
            keyword_weights=keyword_weights,
        )
        stage_result.output = {
            "paths_found": len(exploration.paths),
            "best_path": [
                {"url": s.url, "title": s.title, "score": s.score}
                for s in exploration.best_path
            ],
            "total_links_scored": exploration.total_links_scored,
        }

    async def _run_navigation(
        self,
        stage_result: StageResult,
        navigation_urls: Optional[List[str]],
        pipeline_result: PipelineResult,
    ) -> None:
        urls = navigation_urls or []

        # If no explicit URLs, use exploration results
        if not urls:
            exploration_output = pipeline_result.stages.get("exploration", StageResult(stage=PipelineStage.EXPLORATION))
            best_path = exploration_output.output.get("best_path", [])
            urls = [step["url"] for step in best_path if step.get("url")]

        navigated = []
        for url in urls:
            try:
                await self.browser.goto(url)
                current = await self.browser.get_current_url() or ""
                navigated.append({"target": url, "landed": current, "success": True})
            except Exception as e:
                navigated.append({"target": url, "landed": "", "success": False, "error": str(e)})

        stage_result.output = {"navigated_pages": navigated, "count": len(navigated)}
        pipeline_result.total_pages = len(navigated)

    async def _run_extraction(
        self,
        stage_result: StageResult,
        saas_id: str,
        context_hint: str,
        pipeline_result: PipelineResult,
    ) -> None:
        if not self.extractor:
            logger.info("Skipping extraction stage (no extractor)")
            return

        # Get URLs to extract from (current page or navigated pages)
        nav_output = pipeline_result.stages.get("navigation", StageResult(stage=PipelineStage.NAVIGATION))
        pages = nav_output.output.get("navigated_pages", [])

        all_settings = []
        for page_info in pages:
            if not page_info.get("success"):
                continue
            url = page_info.get("landed", page_info.get("target", ""))
            if url:
                await self.browser.goto(url)
                page_result = await self.extractor.extract_from_current_page(
                    context_hint=context_hint or saas_id,
                    saas_name=saas_id,
                )
                all_settings.extend(page_result.settings)

        # If no navigation happened, extract from current page
        if not pages:
            page_result = await self.extractor.extract_from_current_page(
                context_hint=context_hint or saas_id,
                saas_name=saas_id,
            )
            all_settings = page_result.settings

        stage_result.output = {
            "total_settings": len(all_settings),
            "settings": [
                {"label": s.label, "value": s.value, "type": s.element_type}
                for s in all_settings
            ],
        }
        pipeline_result.total_settings = len(all_settings)
