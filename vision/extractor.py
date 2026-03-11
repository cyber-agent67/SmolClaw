"""Extraction worker — batch processes screenshots for settings extraction."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import VisionClient

logger = logging.getLogger(__name__)


@dataclass
class PageExtraction:
    """Extraction result for a single page."""
    url: str
    settings: List[Dict[str, Any]] = field(default_factory=list)
    screenshot_path: str = ""
    method: str = "vision"
    error: str = ""

    @property
    def count(self) -> int:
        return len(self.settings)


@dataclass
class BatchExtractionResult:
    """Result of batch extraction across multiple pages."""
    pages: List[PageExtraction] = field(default_factory=list)
    success: bool = True
    errors: List[str] = field(default_factory=list)

    @property
    def total_settings(self) -> int:
        return sum(p.count for p in self.pages)

    @property
    def total_pages(self) -> int:
        return len(self.pages)


class ExtractionWorker:
    """Processes screenshots in batch for settings extraction.

    Reads screenshot files from a run directory, processes each through
    VisionClient, and aggregates results.
    """

    def __init__(self, vision_client: VisionClient):
        self.vision_client = vision_client

    def extract_from_screenshot(
        self,
        screenshot_path: str,
        page_url: str = "",
        context_hint: str = "",
        expected_labels: Optional[List[str]] = None,
    ) -> PageExtraction:
        """Process a single screenshot."""
        try:
            settings = self.vision_client.extract_settings(
                screenshot_path=screenshot_path,
                page_url=page_url,
                context_hint=context_hint,
                expected_labels=expected_labels,
            )
            return PageExtraction(
                url=page_url,
                settings=settings,
                screenshot_path=screenshot_path,
                method="vision",
            )
        except Exception as e:
            logger.error("Extraction failed for %s: %s", screenshot_path, e)
            return PageExtraction(
                url=page_url,
                screenshot_path=screenshot_path,
                error=str(e),
            )

    def extract_from_directory(
        self,
        run_dir: str,
        context_hint: str = "",
    ) -> BatchExtractionResult:
        """Process all screenshots in a run directory."""
        result = BatchExtractionResult()
        run_path = Path(run_dir)

        if not run_path.exists():
            result.success = False
            result.errors.append(f"Directory not found: {run_dir}")
            return result

        # Load navigation context if available
        nav_context = self._load_navigation_context(run_path)

        # Find screenshots
        screenshots = self._find_screenshots(run_path, nav_context)

        if not screenshots:
            result.success = False
            result.errors.append("No screenshots found in run directory")
            return result

        for screenshot_info in screenshots:
            page_url = screenshot_info.get("url", "")
            path = screenshot_info.get("path", "")

            page_result = self.extract_from_screenshot(
                screenshot_path=path,
                page_url=page_url,
                context_hint=context_hint,
            )
            result.pages.append(page_result)

            if page_result.error:
                result.errors.append(page_result.error)

        return result

    @staticmethod
    def _load_navigation_context(run_path: Path) -> Dict[str, Any]:
        """Load navigation map and result JSON if available."""
        context: Dict[str, Any] = {}

        for name in ["navigation_map.json", "navigation_result.json"]:
            path = run_path / name
            if path.exists():
                try:
                    context[name.replace(".json", "")] = json.loads(
                        path.read_text(encoding="utf-8")
                    )
                except Exception:
                    pass
        return context

    @staticmethod
    def _find_screenshots(
        run_path: Path, nav_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Discover screenshot files."""
        screenshots = []

        # Check navigation result for screenshot paths
        nav_result = nav_context.get("navigation_result", {})
        if isinstance(nav_result, dict):
            for step in nav_result.get("step_results", []):
                if isinstance(step, dict) and step.get("screenshot_path"):
                    ss_path = run_path / step["screenshot_path"]
                    if ss_path.exists():
                        screenshots.append({
                            "path": str(ss_path),
                            "url": step.get("url", ""),
                        })

        # Check for final_screenshot.png
        final = run_path / "final_screenshot.png"
        if final.exists():
            screenshots.append({"path": str(final), "url": ""})

        # Check screenshots/ subdirectory
        ss_dir = run_path / "screenshots"
        if ss_dir.exists():
            for png in sorted(ss_dir.glob("*.png")):
                if str(png) not in [s["path"] for s in screenshots]:
                    screenshots.append({"path": str(png), "url": ""})

        # Fallback: any PNG in run directory
        if not screenshots:
            for png in sorted(run_path.glob("*.png")):
                screenshots.append({"path": str(png), "url": ""})

        return screenshots
