"""Chronicle drift detection interaction — compares settings against baseline."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DriftItem:
    """A single setting that has drifted from baseline."""
    setting_label: str
    baseline_value: str
    current_value: str
    drift_type: str  # "changed", "added", "removed"
    severity: str = "medium"  # "low", "medium", "high", "critical"


@dataclass
class DriftResult:
    """Result of a drift detection scan."""
    saas_id: str
    total_settings_checked: int = 0
    drifts: List[DriftItem] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return len(self.drifts) > 0

    @property
    def critical_count(self) -> int:
        return sum(1 for d in self.drifts if d.severity == "critical")


class DetectDrift:
    """Detects configuration drift by comparing current settings to a baseline."""

    def __init__(self, browser, extractor):
        self.browser = browser
        self.extractor = extractor

    async def detect(
        self,
        saas_id: str,
        baseline_settings: List[Dict[str, str]],
        page_url: str = "",
        context_hint: str = "",
    ) -> DriftResult:
        """Compare current page settings against baseline."""
        if page_url:
            await self.browser.goto(page_url)

        # Extract current settings
        page_result = await self.extractor.extract_from_current_page(
            context_hint=context_hint or saas_id,
            saas_name=saas_id,
        )

        result = DriftResult(saas_id=saas_id)

        # Build lookup from baseline
        baseline_map = {s["label"].lower().strip(): s for s in baseline_settings}
        current_map = {s.label.lower().strip(): s for s in page_result.settings}

        result.total_settings_checked = len(set(baseline_map.keys()) | set(current_map.keys()))

        # Check for changed and removed settings
        for label_key, baseline in baseline_map.items():
            if label_key in current_map:
                current = current_map[label_key]
                if current.value != baseline.get("value", ""):
                    severity = self._assess_severity(
                        baseline.get("value", ""),
                        current.value,
                        baseline.get("type", ""),
                    )
                    result.drifts.append(DriftItem(
                        setting_label=baseline.get("label", label_key),
                        baseline_value=baseline.get("value", ""),
                        current_value=current.value,
                        drift_type="changed",
                        severity=severity,
                    ))
            else:
                result.drifts.append(DriftItem(
                    setting_label=baseline.get("label", label_key),
                    baseline_value=baseline.get("value", ""),
                    current_value="",
                    drift_type="removed",
                    severity="high",
                ))

        # Check for added settings
        for label_key, current in current_map.items():
            if label_key not in baseline_map:
                result.drifts.append(DriftItem(
                    setting_label=current.label,
                    baseline_value="",
                    current_value=current.value,
                    drift_type="added",
                    severity="low",
                ))

        return result

    @staticmethod
    def _assess_severity(baseline_value: str, current_value: str, setting_type: str) -> str:
        """Assess drift severity based on the nature of the change."""
        b = baseline_value.lower().strip()
        c = current_value.lower().strip()

        # Security-relevant toggles being disabled is critical
        if b in ("enabled", "on", "true") and c in ("disabled", "off", "false"):
            return "critical"
        if b in ("disabled", "off", "false") and c in ("enabled", "on", "true"):
            return "low"  # Enabling is usually good

        # MFA/2FA changes are critical
        security_keywords = ["mfa", "2fa", "two-factor", "authentication", "password", "encryption"]
        if any(kw in (baseline_value + current_value).lower() for kw in security_keywords):
            return "high"

        return "medium"
