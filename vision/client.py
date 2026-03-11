"""Vision client for AI-powered page analysis via LiteLLM."""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Rate limit constants
RATE_LIMIT_INITIAL_DELAY = 1.0
RATE_LIMIT_MAX_DELAY = 60.0
RATE_LIMIT_MAX_RETRIES = 3
JSON_PARSE_MAX_RETRIES = 2

EXTRACTION_SYSTEM_PROMPT = """You are a settings extraction expert. Analyze the screenshot of a web application settings page and extract ALL visible settings.

For each setting found, provide:
- label: The setting name/label as shown on screen
- value: The current value (for toggles use "Enabled"/"Disabled", for checkboxes use "Checked"/"Unchecked")
- type: One of: toggle, checkbox, dropdown, radio, text_input, select, button, link, unknown
- section: The section/group header this setting belongs to (if visible)
- confidence: Your confidence in the extraction (0.0-1.0, based on visual clarity)

Rules:
- Extract EVERY visible setting, not just security-related ones
- For compound settings with sub-options, format as "Parent Setting - Sub Option"
- Do NOT include: navigation items, page headers, action buttons, status displays
- For toggles/switches, check their visual state (green/blue = Enabled, gray = Disabled)

Return ONLY a JSON array of objects with the fields above. No explanation text."""


SETTINGS_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "label": {"type": "string"},
            "value": {"type": "string"},
            "type": {"type": "string"},
            "section": {"type": "string"},
            "confidence": {"type": "number"},
        },
        "required": ["label", "value", "type"],
    },
}


def _detect_provider(model_name: str) -> str:
    """Detect LLM provider from model name."""
    model_lower = model_name.lower()
    if "gemini" in model_lower:
        return "gemini"
    if "claude" in model_lower or "anthropic" in model_lower:
        return "anthropic"
    if "gpt" in model_lower or "openai" in model_lower:
        return "openai"
    return "unknown"


def _get_api_key(provider: str) -> str:
    """Get API key for the detected provider."""
    key_map = {
        "gemini": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    env_var = key_map.get(provider, "")
    return os.environ.get(env_var, "")


def _format_for_litellm(model_name: str, provider: str) -> str:
    """Format model name for LiteLLM."""
    if provider == "gemini" and not model_name.startswith("gemini/"):
        return f"gemini/{model_name}"
    if provider == "anthropic" and not model_name.startswith("anthropic/"):
        return f"anthropic/{model_name}"
    return model_name


def _load_image_base64(path: str) -> str:
    """Encode an image file to base64."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_mime_type(path: str) -> str:
    """Get MIME type from file extension."""
    ext = Path(path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def _extract_json_from_response(text: str) -> str:
    """Extract JSON from LLM response that may contain markdown fences."""
    # Try raw parse first
    text = text.strip()
    if text.startswith("[") or text.startswith("{"):
        return text

    # Try to extract from markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return text


class VisionClient:
    """Model-agnostic vision client for page analysis and settings extraction.

    Supports Gemini, OpenAI, and Anthropic via LiteLLM.
    """

    def __init__(self, model_name: str = ""):
        self.model_name = model_name or os.environ.get("EXTRACTION_MODEL", "")
        if not self.model_name:
            raise ValueError(
                "No model specified. Set EXTRACTION_MODEL env var or pass model_name."
            )

        self.provider = _detect_provider(self.model_name)
        self.litellm_model = _format_for_litellm(self.model_name, self.provider)
        self.api_key = _get_api_key(self.provider)
        self.last_usage: Dict[str, int] = {}

    def extract_settings(
        self,
        screenshot_path: str = "",
        screenshot_bytes: Optional[bytes] = None,
        page_url: str = "",
        context_hint: str = "",
        expected_labels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Extract settings from a screenshot (sync wrapper)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
        except RuntimeError:
            pass

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self._extract_async(
                    screenshot_path=screenshot_path,
                    screenshot_bytes=screenshot_bytes,
                    page_url=page_url,
                    context_hint=context_hint,
                    expected_labels=expected_labels,
                )
            )
        finally:
            loop.close()

    async def _extract_async(
        self,
        screenshot_path: str = "",
        screenshot_bytes: Optional[bytes] = None,
        page_url: str = "",
        context_hint: str = "",
        expected_labels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Async extraction implementation."""
        try:
            import litellm
        except ImportError:
            raise ImportError("litellm is required for vision extraction: pip install litellm")

        # Encode image
        if screenshot_bytes:
            img_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            mime = "image/png"
        elif screenshot_path:
            img_b64 = _load_image_base64(screenshot_path)
            mime = _get_mime_type(screenshot_path)
        else:
            raise ValueError("Either screenshot_path or screenshot_bytes required")

        # Build prompt
        user_prompt = self._build_user_prompt(page_url, context_hint, expected_labels)

        # Build messages
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{img_b64}",
                        },
                    },
                ],
            },
        ]

        # Call LLM with retries
        response_text = await self._call_with_retries(litellm, messages)

        # Parse response
        return self._parse_response(response_text)

    async def _call_with_retries(self, litellm, messages: list) -> str:
        """Call LLM with rate limit and truncation retries."""
        delay = RATE_LIMIT_INITIAL_DELAY
        max_tokens = 4096

        for attempt in range(RATE_LIMIT_MAX_RETRIES + 1):
            try:
                kwargs = {
                    "model": self.litellm_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.1,
                }
                if self.api_key:
                    kwargs["api_key"] = self.api_key

                response = await litellm.acompletion(**kwargs)

                content = response.choices[0].message.content or ""

                # Track usage
                if hasattr(response, "usage") and response.usage:
                    self.last_usage = {
                        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                    }

                # Check for truncation
                finish_reason = getattr(response.choices[0], "finish_reason", "")
                if finish_reason == "length" and max_tokens < 32768:
                    max_tokens *= 2
                    logger.warning("Response truncated, retrying with max_tokens=%d", max_tokens)
                    continue

                return content

            except Exception as e:
                if self._is_rate_limit(e) and attempt < RATE_LIMIT_MAX_RETRIES:
                    logger.warning("Rate limited, retrying in %.1fs", delay)
                    import asyncio
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, RATE_LIMIT_MAX_DELAY)
                    continue
                raise

        return ""

    def _build_user_prompt(
        self,
        page_url: str,
        context_hint: str,
        expected_labels: Optional[List[str]],
    ) -> str:
        parts = ["Extract all settings from this screenshot."]
        if page_url:
            parts.append(f"Page URL: {page_url}")
        if context_hint:
            parts.append(f"Context: {context_hint}")
        if expected_labels:
            parts.append(f"Expected settings to look for: {', '.join(expected_labels)}")
        return "\n".join(parts)

    def _parse_response(self, text: str) -> List[Dict[str, Any]]:
        """Parse LLM response into settings list."""
        json_str = _extract_json_from_response(text)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Failed to parse vision response as JSON")
            return []

        if isinstance(data, list):
            return [self._clean_setting(item) for item in data if isinstance(item, dict)]
        if isinstance(data, dict) and "settings" in data:
            return [self._clean_setting(item) for item in data["settings"] if isinstance(item, dict)]
        return []

    @staticmethod
    def _clean_setting(item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single setting item."""
        confidence = item.get("confidence", 0.8)
        if isinstance(confidence, (int, float)):
            confidence = max(0.0, min(1.0, float(confidence)))
        else:
            confidence = 0.8

        return {
            "label": str(item.get("label", "")).strip(),
            "value": str(item.get("value", "")).strip(),
            "type": str(item.get("type", "unknown")).strip().lower(),
            "section": str(item.get("section", "")).strip(),
            "confidence": confidence,
        }

    @staticmethod
    def _is_rate_limit(error: Exception) -> bool:
        error_str = str(error).lower()
        return "429" in error_str or "rate limit" in error_str or "quota" in error_str

    async def analyze_page(
        self,
        screenshot_bytes: bytes,
        question: str = "Describe what you see on this page.",
    ) -> str:
        """General-purpose page analysis (not settings extraction)."""
        try:
            import litellm
        except ImportError:
            raise ImportError("litellm required")

        img_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                    },
                ],
            },
        ]

        kwargs = {
            "model": self.litellm_model,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.2,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key

        response = await litellm.acompletion(**kwargs)
        return response.choices[0].message.content or ""
