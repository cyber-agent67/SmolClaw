"""Ground element interaction."""

from smolclaw.agent.entities.browser.ElementTarget import ElementTarget


class GroundElement:
    @staticmethod
    def execute(target_text: str) -> ElementTarget:
        target = ElementTarget()
        target.text = target_text
        target.found = False
        target.confidence = 0.0
        return target
