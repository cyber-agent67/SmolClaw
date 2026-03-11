"""Settings value normalization for consistency across extractions."""
from __future__ import annotations

import re
from typing import Any, Dict, List


# Canonical value mappings
TOGGLE_TRUE = {"enabled", "on", "true", "yes", "active", "checked"}
TOGGLE_FALSE = {"disabled", "off", "false", "no", "inactive", "unchecked"}


def normalize_toggle_value(value: str) -> str:
    """Normalize toggle/boolean values to Enabled/Disabled."""
    v = value.strip().lower()
    if v in TOGGLE_TRUE:
        return "Enabled"
    if v in TOGGLE_FALSE:
        return "Disabled"
    return value


def normalize_label(label: str) -> str:
    """Clean up setting label text."""
    # Remove extra whitespace
    label = re.sub(r"\s+", " ", label).strip()
    # Remove trailing colons
    label = label.rstrip(":")
    return label


def normalize_setting(setting: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a single setting's label and value."""
    result = dict(setting)
    result["label"] = normalize_label(result.get("label", ""))

    element_type = result.get("type", "").lower()
    if element_type in ("toggle", "checkbox", "switch"):
        result["value"] = normalize_toggle_value(result.get("value", ""))

    return result


def normalize_settings(settings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize a list of settings."""
    return [normalize_setting(s) for s in settings]


def deduplicate_settings(settings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate settings by label."""
    seen = set()
    result = []
    for s in settings:
        key = s.get("label", "").lower().strip()
        if key and key not in seen:
            seen.add(key)
            result.append(s)
    return result


def normalize_settings_pipeline(settings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Full normalization pipeline: normalize → deduplicate."""
    return deduplicate_settings(normalize_settings(settings))
