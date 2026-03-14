"""Layered browser sub-agent modules.

Only Layer 1 (raw browser access) is in smolhand.
Other "layers" are now agent tools:
- Vision: smolclaw.agent.tools.vision
- Exploration: smolclaw.agent.tools.exploration
- Q-Learning: smolclaw.agent.tools.q_learning
"""

from smolclaw.tools.smolhand.services.layer1_browser import BrowserLayerService

__all__ = [
    "BrowserLayerService",
]
