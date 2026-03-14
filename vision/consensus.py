"""Multi-pass consensus for deterministic extraction results."""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .client import VisionClient
from .normalization import normalize_settings_pipeline

logger = logging.getLogger(__name__)


@dataclass
class ConsensusConfig:
    """Configuration for consensus extraction."""
    num_passes: int = 3
    agreement_threshold: float = 0.66  # fraction of passes that must agree
    min_confidence: float = 0.3


def run_consensus_extraction(
    vision_client: VisionClient,
    screenshot_path: str = "",
    screenshot_bytes: Optional[bytes] = None,
    page_url: str = "",
    context_hint: str = "",
    config: Optional[ConsensusConfig] = None,
) -> List[Dict[str, Any]]:
    """Run multiple extraction passes and return settings with consensus agreement.

    Each setting must appear in at least `agreement_threshold` fraction of passes
    to be included in the final result. Values use majority voting.
    """
    cfg = config or ConsensusConfig()
    all_passes: List[List[Dict[str, Any]]] = []

    for pass_num in range(cfg.num_passes):
        try:
            settings = vision_client.extract_settings(
                screenshot_path=screenshot_path,
                screenshot_bytes=screenshot_bytes,
                page_url=page_url,
                context_hint=context_hint,
            )
            normalized = normalize_settings_pipeline(settings)
            all_passes.append(normalized)
        except Exception as e:
            logger.warning("Consensus pass %d failed: %s", pass_num + 1, e)

    if not all_passes:
        return []

    # Count label occurrences across passes
    label_counts: Counter = Counter()
    label_values: Dict[str, Counter] = {}
    label_types: Dict[str, Counter] = {}
    label_sections: Dict[str, Counter] = {}

    for pass_settings in all_passes:
        for setting in pass_settings:
            label = setting.get("label", "").lower().strip()
            if not label:
                continue
            label_counts[label] += 1

            if label not in label_values:
                label_values[label] = Counter()
                label_types[label] = Counter()
                label_sections[label] = Counter()

            label_values[label][setting.get("value", "")] += 1
            label_types[label][setting.get("type", "unknown")] += 1
            label_sections[label][setting.get("section", "")] += 1

    # Filter by agreement threshold
    min_appearances = max(1, int(len(all_passes) * cfg.agreement_threshold))
    consensus_settings = []

    for label, count in label_counts.items():
        if count < min_appearances:
            continue

        # Use majority vote for value, type, section
        best_value = label_values[label].most_common(1)[0][0]
        best_type = label_types[label].most_common(1)[0][0]
        best_section = label_sections[label].most_common(1)[0][0]

        # Confidence = fraction of passes that found this setting
        confidence = count / len(all_passes)
        if confidence < cfg.min_confidence:
            continue

        # Find original label casing from the first pass that had it
        original_label = label
        for pass_settings in all_passes:
            for s in pass_settings:
                if s.get("label", "").lower().strip() == label:
                    original_label = s["label"]
                    break
            if original_label != label:
                break

        consensus_settings.append({
            "label": original_label,
            "value": best_value,
            "type": best_type,
            "section": best_section,
            "confidence": round(confidence, 2),
        })

    return consensus_settings
