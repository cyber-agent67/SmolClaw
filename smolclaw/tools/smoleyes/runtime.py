"""SmolEyes: Vision-based browser analysis tool.

SmolEyes provides vision model integration for browser analysis:
- Florence-2 for visual captioning and object detection
- Screenshot-based page understanding
- Visual element grounding
- OCR for text extraction from images

This tool connects directly to the smol agent as a vision interface.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Optional


def _encode_screenshot_base64(png_bytes: bytes) -> str:
    """Encode screenshot bytes to base64 string."""
    return base64.b64encode(png_bytes).decode("ascii")


def capture_screenshot_base64() -> str:
    """Capture current browser viewport as base64-encoded PNG.
    
    Returns:
        Base64-encoded PNG screenshot
    """
    from helium import get_driver
    
    driver = get_driver()
    png_bytes = driver.get_screenshot_as_png()
    return _encode_screenshot_base64(png_bytes)


def analyze_with_florence(
    image_base64: str,
    task: str = "Caption",
    prompt: str = "",
) -> Dict[str, Any]:
    """Analyze image using Florence-2 vision model.
    
    Args:
        image_base64: Base64-encoded image
        task: Florence-2 task type
            - "Caption": Basic image caption
            - "DetailedCaption": Detailed description
            - "ObjectDetection": Detect objects with bounding boxes
            - "OCR": Extract text from image
        prompt: Optional task-specific prompt
    
    Returns:
        Dictionary with analysis results
    """
    try:
        from agentic_navigator.interactions.florence.CaptionImage import CaptionImage
        from agentic_navigator.interactions.florence.DetectObjects import DetectObjects
        from agentic_navigator.interactions.florence.OCRImage import OCRImage
        
        # Decode image
        image_bytes = base64.b64decode(image_base64)
        
        if task == "ObjectDetection":
            result = DetectObjects.execute(image_bytes)
            return {
                "task": "object_detection",
                "objects": result.get("objects", []),
            }
        elif task == "OCR":
            result = OCRImage.execute(image_bytes)
            return {
                "task": "ocr",
                "text": result.get("text", ""),
            }
        else:  # Caption or DetailedCaption
            detailed = (task == "DetailedCaption")
            result = CaptionImage.execute(image_bytes, detailed=detailed)
            return {
                "task": "caption",
                "caption": result.get("caption", ""),
                "detailed": detailed,
            }
            
    except Exception as e:
        return {
            "error": str(e),
            "task": task,
        }


def describe_page_visual(
    prompt_hint: str = "",
    include_ocr: bool = False,
    include_objects: bool = False,
) -> Dict[str, Any]:
    """Describe current page using vision analysis.
    
    Args:
        prompt_hint: Optional hint to guide analysis
        include_ocr: Whether to include OCR text extraction
        include_objects: Whether to include object detection
    
    Returns:
        Dictionary with visual analysis results
    """
    screenshot_b64 = capture_screenshot_base64()
    
    results = {
        "screenshot_captured": True,
        "screenshot_size": len(screenshot_b64),
    }
    
    # Get caption
    caption_result = analyze_with_florence(
        screenshot_b64,
        task="DetailedCaption",
        prompt=prompt_hint,
    )
    results["caption"] = caption_result
    
    # Get OCR if requested
    if include_ocr:
        ocr_result = analyze_with_florence(screenshot_b64, task="OCR")
        results["ocr"] = ocr_result
    
    # Get objects if requested
    if include_objects:
        objects_result = analyze_with_florence(screenshot_b64, task="ObjectDetection")
        results["objects"] = objects_result
    
    return results


def find_visual_element(
    description: str,
    confidence_threshold: float = 0.5,
) -> Dict[str, Any]:
    """Find visual element on page by description.
    
    Args:
        description: Natural language description of element to find
            (e.g., "blue submit button", "search icon")
        confidence_threshold: Minimum confidence for matches
    
    Returns:
        Dictionary with found element info including bounding box
    """
    screenshot_b64 = capture_screenshot_base64()
    
    # Use Florence-2 object detection with prompt
    result = analyze_with_florence(
        screenshot_b64,
        task="ObjectDetection",
        prompt=description,
    )
    
    if "error" in result:
        return result
    
    # Filter by confidence
    objects = result.get("objects", [])
    filtered = [
        obj for obj in objects
        if obj.get("confidence", 0) >= confidence_threshold
    ]
    
    return {
        "found": len(filtered) > 0,
        "count": len(filtered),
        "elements": filtered,
        "description": description,
    }


def compare_pages(
    image1_base64: str,
    image2_base64: str,
    comparison_type: str = "difference",
) -> Dict[str, Any]:
    """Compare two page screenshots.
    
    Args:
        image1_base64: First screenshot (base64)
        image2_base64: Second screenshot (base64)
        comparison_type: Type of comparison
            - "difference": Find visual differences
            - "similarity": Compute similarity score
    
    Returns:
        Dictionary with comparison results
    """
    # This would require a vision model that can compare images
    # For now, return basic info
    return {
        "image1_size": len(image1_base64),
        "image2_size": len(image2_base64),
        "comparison_type": comparison_type,
        "note": "Full comparison requires multi-modal model support",
    }


def extract_text_from_region(
    x: int,
    y: int,
    width: int,
    height: int,
) -> Dict[str, Any]:
    """Extract text from specific region of current page.
    
    Args:
        x: X coordinate (top-left)
        y: Y coordinate (top-left)
        width: Region width
        height: Region height
    
    Returns:
        Dictionary with extracted text
    """
    from helium import get_driver
    
    driver = get_driver()
    
    # Capture full screenshot
    screenshot_b64 = capture_screenshot_base64()
    image_bytes = base64.b64decode(screenshot_b64)
    
    # For now, do OCR on full image
    # In future, could crop to region first
    result = analyze_with_florence(image_bytes, task="OCR")
    
    return {
        "region": {"x": x, "y": y, "width": width, "height": height},
        "ocr_result": result,
    }


__all__ = [
    "capture_screenshot_base64",
    "analyze_with_florence",
    "describe_page_visual",
    "find_visual_element",
    "compare_pages",
    "extract_text_from_region",
]
