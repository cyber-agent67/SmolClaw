"""SmolEyes vision tools for AI Agent.

This module provides @tool decorated functions that expose vision
capabilities to the AI Agent.
"""

import json
from typing import Optional

from smolagents import tool


@tool
def describe_page_visual(prompt_hint: str = "") -> str:
    """Describe current page using vision analysis (Florence-2).
    
    This tool captures a screenshot and uses Florence-2 to generate:
    - Detailed visual caption
    - Optional OCR text extraction
    - Optional object detection
    
    Args:
        prompt_hint: Optional hint to guide the visual analysis
            (e.g., "Describe the navigation menu", "What buttons are visible?")
    
    Returns:
        JSON string with visual analysis including:
        - caption: Detailed visual description
        - ocr: Extracted text (if requested)
        - objects: Detected objects (if requested)
    
    Example:
        describe_page_visual("Describe the main content area")
        describe_page_visual("What form fields are visible?")
    """
    from smolclaw.tools.smoleyes.runtime import describe_page_visual as vision_describe
    
    result = vision_describe(prompt_hint=prompt_hint, include_ocr=False, include_objects=False)
    return json.dumps(result, indent=2)


@tool
def find_visual_element(description: str, confidence_threshold: float = 0.5) -> str:
    """Find visual element on page by natural language description.
    
    This tool uses Florence-2 object detection to find elements like:
    - "blue submit button"
    - "search icon"
    - "navigation menu"
    - "logo in top left"
    
    Args:
        description: Natural language description of element to find
        confidence_threshold: Minimum confidence for matches (0.0-1.0)
    
    Returns:
        JSON string with found elements including:
        - found: Whether element was found
        - count: Number of matches
        - elements: List of elements with bounding boxes and confidence
    
    Example:
        find_visual_element("red delete button")
        find_visual_element("search icon", confidence_threshold=0.7)
    """
    from smolclaw.tools.smoleyes.runtime import find_visual_element as vision_find
    
    result = vision_find(description, confidence_threshold)
    return json.dumps(result, indent=2)


@tool
def extract_text_from_screenshot() -> str:
    """Extract all text visible on current page using OCR.
    
    This tool uses Florence-2 OCR to extract text from:
    - Images with text
    - Buttons with icons
    - Custom fonts
    - Canvas elements
    
    Returns:
        JSON string with OCR results including:
        - text: All extracted text
        - confidence: OCR confidence score
    
    Example:
        extract_text_from_screenshot()
    """
    from smolclaw.tools.smoleyes.runtime import describe_page_visual as vision_describe
    
    result = vision_describe(prompt_hint="", include_ocr=True, include_objects=False)
    
    # Return just OCR results
    ocr_result = result.get("ocr", {})
    return json.dumps({
        "text": ocr_result.get("text", ""),
        "task": "ocr",
    }, indent=2)


@tool
def detect_page_objects() -> str:
    """Detect all objects on current page.
    
    This tool uses Florence-2 to detect and localize:
    - Buttons
    - Images
    - Text blocks
    - Forms
    - Navigation elements
    
    Returns:
        JSON string with detected objects including:
        - count: Number of objects detected
        - objects: List with labels, bounding boxes, confidence
    
    Example:
        detect_page_objects()
    """
    from smolclaw.tools.smoleyes.runtime import describe_page_visual as vision_describe
    
    result = vision_describe(prompt_hint="", include_ocr=False, include_objects=True)
    
    # Return just object detection results
    objects_result = result.get("objects", {})
    return json.dumps(objects_result, indent=2)


@tool
def analyze_visual_context(prompt_hint: str = "") -> str:
    """Analyze current page visual context with detailed caption.
    
    This is the main vision tool for general page understanding.
    It provides a detailed visual description guided by the prompt.
    
    Args:
        prompt_hint: Optional hint to focus the analysis
            (e.g., "Focus on the header area", "Describe available actions")
    
    Returns:
        JSON string with visual analysis including:
        - caption: Detailed visual description
        - url: Current page URL
        - title: Current page title
    
    Example:
        analyze_visual_context("What can I do on this page?")
        analyze_visual_context("Describe the layout")
    """
    from smolclaw.tools.smoleyes.runtime import describe_page_visual as vision_describe
    
    result = vision_describe(prompt_hint=prompt_hint, include_ocr=False, include_objects=False)
    
    # Add page info
    from helium import get_driver
    driver = get_driver()
    result["url"] = driver.current_url
    result["title"] = driver.title
    
    return json.dumps(result, indent=2)


__all__ = [
    "describe_page_visual",
    "find_visual_element",
    "extract_text_from_screenshot",
    "detect_page_objects",
    "analyze_visual_context",
]
