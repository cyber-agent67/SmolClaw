"""SmolEyes: Vision-based browser analysis for AI Agent.

SmolEyes provides vision model integration as a direct tool for the smol agent:
- Florence-2 for visual captioning and object detection
- Screenshot-based page understanding
- Visual element grounding
- OCR for text extraction from images

Usage:
    from smolclaw.smoleyes import SmolEyes
    
    eyes = SmolEyes()
    result = eyes.describe_page("What buttons are visible?")
    
Or use the tools directly:
    from smolclaw.tools.smoleyes.tools import analyze_visual_context
    result = analyze_visual_context("Describe this page")
"""

from smolclaw.tools.smoleyes.runtime import (
    analyze_with_florence,
    capture_screenshot_base64,
    compare_pages,
    describe_page_visual,
    extract_text_from_region,
    find_visual_element,
)
from smolclaw.tools.smoleyes.tools import (
    analyze_visual_context,
    detect_page_objects,
    describe_page_visual as describe_page_visual_tool,
    extract_text_from_screenshot,
    find_visual_element as find_visual_element_tool,
)


class SmolEyes:
    """Main SmolEyes vision interface.
    
    Provides high-level vision analysis methods for the AI Agent.
    
    Example:
        eyes = SmolEyes()
        
        # Describe page
        result = eyes.describe_page("What can I do here?")
        
        # Find element
        button = eyes.find("submit button")
        
        # Extract text
        text = eyes.read_text()
    """
    
    def __init__(self):
        """Initialize SmolEyes vision interface."""
        pass
    
    def describe_page(self, prompt_hint: str = "") -> dict:
        """Describe current page using vision analysis.
        
        Args:
            prompt_hint: Optional hint to guide analysis
        
        Returns:
            Dictionary with visual analysis results
        """
        return describe_page_visual(prompt_hint=prompt_hint)
    
    def find(self, description: str, confidence: float = 0.5) -> dict:
        """Find visual element by description.
        
        Args:
            description: Natural language description
            confidence: Confidence threshold
        
        Returns:
            Dictionary with found elements
        """
        return find_visual_element(description, confidence)
    
    def read_text(self) -> dict:
        """Extract all text from page using OCR.
        
        Returns:
            Dictionary with OCR results
        """
        from smolclaw.tools.smoleyes.runtime import describe_page_visual
        
        return describe_page_visual(prompt_hint="", include_ocr=True)
    
    def detect_objects(self) -> dict:
        """Detect all objects on page.
        
        Returns:
            Dictionary with detected objects
        """
        from smolclaw.tools.smoleyes.runtime import describe_page_visual
        
        return describe_page_visual(prompt_hint="", include_objects=True)
    
    def capture(self) -> str:
        """Capture screenshot as base64.
        
        Returns:
            Base64-encoded PNG screenshot
        """
        return capture_screenshot_base64()


__all__ = [
    # Main class
    "SmolEyes",
    # Runtime functions
    "capture_screenshot_base64",
    "analyze_with_florence",
    "describe_page_visual",
    "find_visual_element",
    "extract_text_from_region",
    "compare_pages",
    # Tools
    "analyze_visual_context",
    "find_visual_element_tool",
    "extract_text_from_screenshot",
    "detect_page_objects",
    "describe_page_visual_tool",
]
