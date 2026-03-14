"""Shared image analysis helpers for perception fallbacks."""

import base64
from io import BytesIO
from typing import Any, Dict, List, Optional

from PIL import Image, ImageStat, UnidentifiedImageError


def load_image_from_base64(image_base64: str) -> Optional[Image.Image]:
    """Decodes a base64 image payload into a Pillow image."""
    if not image_base64:
        return None

    try:
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes))
        image.load()
        return image
    except (ValueError, OSError, UnidentifiedImageError):
        return None


def summarize_image(image_base64: str) -> Dict[str, Any]:
    """Builds a lightweight descriptive summary without requiring a vision model."""
    image = load_image_from_base64(image_base64)
    if image is None:
        return {}

    rgb_image = image.convert("RGB")
    width, height = rgb_image.size
    orientation = "landscape" if width > height else "portrait" if height > width else "square"

    stat = ImageStat.Stat(rgb_image)
    channel_mean = [round(value, 1) for value in stat.mean[:3]]
    brightness = round(sum(channel_mean) / len(channel_mean), 1)
    color_spread = round(max(channel_mean) - min(channel_mean), 1)

    quadrants = [
        ("top_left", (0, 0, max(1, width // 2), max(1, height // 2))),
        ("top_right", (max(0, width // 2), 0, width, max(1, height // 2))),
        ("bottom_left", (0, max(0, height // 2), max(1, width // 2), height)),
        ("bottom_right", (max(0, width // 2), max(0, height // 2), width, height)),
    ]

    region_descriptions: List[Dict[str, Any]] = []
    for name, box in quadrants:
        region = rgb_image.crop(box)
        region_stat = ImageStat.Stat(region)
        region_brightness = round(sum(region_stat.mean[:3]) / 3, 1)
        region_descriptions.append(
            {
                "region": name,
                "brightness": region_brightness,
                "size": {"width": max(0, box[2] - box[0]), "height": max(0, box[3] - box[1])},
            }
        )

    brightest_region = max(region_descriptions, key=lambda item: item["brightness"])
    darkest_region = min(region_descriptions, key=lambda item: item["brightness"])

    caption = (
        f"{orientation.capitalize()} image {width}x{height} with average brightness {brightness}/255 "
        f"and RGB mean {channel_mean}."
    )
    detailed_caption = (
        f"Brightest region: {brightest_region['region']} ({brightest_region['brightness']}/255). "
        f"Darkest region: {darkest_region['region']} ({darkest_region['brightness']}/255). "
        f"Color spread across channels: {color_spread}."
    )

    return {
        "width": width,
        "height": height,
        "mode": image.mode,
        "orientation": orientation,
        "brightness": brightness,
        "channel_mean": channel_mean,
        "color_spread": color_spread,
        "caption": caption,
        "detailed_caption": detailed_caption,
        "region_descriptions": region_descriptions,
    }