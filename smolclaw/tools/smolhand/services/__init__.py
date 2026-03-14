"""Browser Layer 1 service exports for raw browser access.

This package provides service facade for Layer 1 only:
- BrowserLayerService: Raw browser access (page state, hyperlinks, DOM)

Note: All intelligence is now in AI Agent tools:
- Vision (Florence-2): agentic_navigator/tools/vision/
- Exploration (A*): agentic_navigator/tools/exploration/
- Q-Learning: agentic_navigator/tools/q_learning/
"""

from smolclaw.tools.smolhand.services.layer1_browser import BrowserLayerService

__all__ = [
    "BrowserLayerService",
]
