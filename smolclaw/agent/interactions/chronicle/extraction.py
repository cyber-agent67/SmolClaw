"""Chronicle extraction interaction — extracts security settings from SaaS pages."""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


@dataclass
class ExtractedSettingItem:
    """A single extracted setting."""
    label: str
    value: str
    element_type: str = "unknown"
    selector: str = ""
    section: str = ""
    confidence: float = 1.0

    @property
    def setting_id(self) -> str:
        raw = f"{self.label}:{self.value}:{self.element_type}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]


@dataclass
class ExtractionPageResult:
    """Settings extracted from a single page."""
    url: str
    settings: List[ExtractedSettingItem] = field(default_factory=list)
    method: str = "dom"  # "dom" or "vision"
    error: str = ""


class _FormControlParser(HTMLParser):
    """Lightweight HTML parser to find form controls with labels and values."""

    def __init__(self):
        super().__init__()
        self.settings: List[Dict[str, str]] = []
        self._current_label = ""
        self._in_label = False
        self._label_for = ""

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)

        if tag == "label":
            self._in_label = True
            self._label_for = attr_dict.get("for", "")
            self._current_label = ""
            return

        if tag == "input":
            input_type = attr_dict.get("type", "text").lower()
            if input_type in ("hidden", "submit", "button"):
                return

            label = (
                self._current_label
                or attr_dict.get("aria-label", "")
                or attr_dict.get("placeholder", "")
                or attr_dict.get("name", "")
            )
            value = attr_dict.get("value", "")

            if input_type == "checkbox":
                value = "Enabled" if "checked" in attr_dict else "Disabled"
                element_type = "checkbox"
            elif input_type == "radio":
                value = attr_dict.get("value", "")
                element_type = "radio"
            else:
                element_type = "text_input"

            if label:
                selector = ""
                if attr_dict.get("id"):
                    selector = f"#{attr_dict['id']}"
                elif attr_dict.get("name"):
                    selector = f"input[name='{attr_dict['name']}']"

                self.settings.append({
                    "label": label.strip(),
                    "value": value,
                    "type": element_type,
                    "selector": selector,
                })

        elif tag == "select":
            label = (
                self._current_label
                or attr_dict.get("aria-label", "")
                or attr_dict.get("name", "")
            )
            if label:
                selector = ""
                if attr_dict.get("id"):
                    selector = f"#{attr_dict['id']}"
                self.settings.append({
                    "label": label.strip(),
                    "value": "",
                    "type": "dropdown",
                    "selector": selector,
                })

    def handle_data(self, data):
        if self._in_label:
            self._current_label += data

    def handle_endtag(self, tag):
        if tag == "label":
            self._in_label = False


def extract_settings_from_dom(html: str, context_hint: str = "") -> List[Dict[str, str]]:
    """Parse HTML to find form controls (toggles, checkboxes, dropdowns, etc.)."""
    parser = _FormControlParser()
    try:
        parser.feed(html)
    except Exception as e:
        logger.warning("DOM parsing error: %s", e)

    # Also check for toggle-like elements via regex patterns
    toggle_patterns = [
        r'role=["\']switch["\']',
        r'class=["\'][^"\']*toggle[^"\']*["\']',
        r'class=["\'][^"\']*switch[^"\']*["\']',
    ]
    for pattern in toggle_patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            # Try to find nearby label text
            start = max(0, match.start() - 200)
            context = html[start:match.start()]
            label_match = re.search(r'>([^<]{3,50})<', context)
            if label_match:
                label = label_match.group(1).strip()
                # Check aria-checked for value
                checked_match = re.search(
                    r'aria-checked=["\'](\w+)["\']',
                    html[match.start():match.start() + 100]
                )
                value = "Enabled" if checked_match and checked_match.group(1) == "true" else "Disabled"
                parser.settings.append({
                    "label": label,
                    "value": value,
                    "type": "toggle",
                    "selector": "",
                })

    return parser.settings


class ExtractSettings:
    """Extracts security settings from SaaS pages.

    Strategy: DOM-first extraction, falls back to vision AI only if DOM
    returns 0 settings.
    """

    def __init__(self, browser, vision_client=None):
        self.browser = browser
        self.vision_client = vision_client

    async def extract_from_current_page(
        self,
        context_hint: str = "",
        saas_name: str = "",
    ) -> ExtractionPageResult:
        """Extract settings from the currently loaded page."""
        url = await self.browser.get_current_url() or ""

        # Try DOM-first
        try:
            html = await self.browser.get_page_source()
            dom_settings = extract_settings_from_dom(html, context_hint)

            if dom_settings:
                items = [
                    ExtractedSettingItem(
                        label=s["label"],
                        value=s["value"],
                        element_type=s["type"],
                        selector=s.get("selector", ""),
                        confidence=0.9,
                    )
                    for s in dom_settings
                ]
                return ExtractionPageResult(url=url, settings=items, method="dom")
        except Exception as e:
            logger.warning("DOM extraction failed: %s", e)

        # Fall back to vision
        if self.vision_client:
            try:
                vision_settings = await self.browser.extract_settings_vision(
                    saas_name=saas_name or context_hint,
                )
                items = [
                    ExtractedSettingItem(
                        label=s.get("label", ""),
                        value=s.get("value", ""),
                        element_type=s.get("type", "unknown"),
                        confidence=s.get("confidence", 0.7),
                        section=s.get("section", ""),
                    )
                    for s in vision_settings
                ]
                return ExtractionPageResult(url=url, settings=items, method="vision")
            except Exception as e:
                logger.warning("Vision extraction failed: %s", e)
                return ExtractionPageResult(url=url, error=str(e))

        return ExtractionPageResult(url=url, settings=[], error="No settings found via DOM and no vision client available")

    async def extract_with_scroll(
        self,
        context_hint: str = "",
        saas_name: str = "",
        max_scrolls: int = 5,
    ) -> ExtractionPageResult:
        """Extract settings with incremental scrolling to capture below-fold content."""
        url = await self.browser.get_current_url() or ""
        all_settings: List[ExtractedSettingItem] = []
        seen_labels: set = set()

        for i in range(max_scrolls + 1):
            page_result = await self.extract_from_current_page(
                context_hint=context_hint,
                saas_name=saas_name,
            )

            for setting in page_result.settings:
                if setting.label not in seen_labels:
                    seen_labels.add(setting.label)
                    all_settings.append(setting)

            if i < max_scrolls:
                # Scroll down
                try:
                    await self.browser.click("window.scrollBy(0, window.innerHeight)")
                except Exception:
                    break

        return ExtractionPageResult(
            url=url,
            settings=all_settings,
            method="dom+scroll" if all_settings else "none",
        )
