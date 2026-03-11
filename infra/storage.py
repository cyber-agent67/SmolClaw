"""Local file storage for screenshots, results, and navigation data."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LocalStorage:
    """File-based storage for scan artifacts.

    Directory structure:
    ~/.smolclaw/storage/
    ├── {saas_id}/
    │   ├── screenshots/
    │   ├── results/
    │   ├── navigation/
    │   └── baselines/
    """

    def __init__(self, root: Optional[Path] = None):
        self.root = root or (Path.home() / ".smolclaw" / "storage")
        self.root.mkdir(parents=True, exist_ok=True)

    def _saas_dir(self, saas_id: str, subdir: str = "") -> Path:
        path = self.root / saas_id.lower()
        if subdir:
            path = path / subdir
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_screenshot(
        self, saas_id: str, data: bytes, name: str = ""
    ) -> Path:
        """Save a screenshot and return the file path."""
        directory = self._saas_dir(saas_id, "screenshots")
        if not name:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            name = f"screenshot_{ts}.png"
        path = directory / name
        path.write_bytes(data)
        logger.debug("screenshot_saved", path=str(path))
        return path

    def save_result(
        self, saas_id: str, data: Dict[str, Any], name: str = ""
    ) -> Path:
        """Save an extraction or scan result as JSON."""
        directory = self._saas_dir(saas_id, "results")
        if not name:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            name = f"result_{ts}.json"
        path = directory / name
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.debug("result_saved", path=str(path))
        return path

    def save_navigation_map(
        self, saas_id: str, nav_data: Dict[str, Any], name: str = ""
    ) -> Path:
        """Save a navigation map."""
        directory = self._saas_dir(saas_id, "navigation")
        if not name:
            name = "navigation_map.json"
        path = directory / name
        path.write_text(json.dumps(nav_data, indent=2, default=str), encoding="utf-8")
        return path

    def save_baseline(
        self, saas_id: str, settings: list, name: str = ""
    ) -> Path:
        """Save baseline settings for drift detection."""
        directory = self._saas_dir(saas_id, "baselines")
        if not name:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            name = f"baseline_{ts}.json"
        path = directory / name
        path.write_text(
            json.dumps(settings, indent=2, default=str), encoding="utf-8"
        )
        return path

    def load_baseline(self, saas_id: str, name: str = "") -> list:
        """Load the most recent baseline or a specific one."""
        directory = self._saas_dir(saas_id, "baselines")
        if name:
            path = directory / name
        else:
            # Find most recent baseline
            baselines = sorted(directory.glob("baseline_*.json"), reverse=True)
            if not baselines:
                return []
            path = baselines[0]

        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def list_results(self, saas_id: str) -> list:
        """List all stored results for a SaaS app."""
        directory = self._saas_dir(saas_id, "results")
        return sorted(
            [f.name for f in directory.glob("*.json")],
            reverse=True,
        )
