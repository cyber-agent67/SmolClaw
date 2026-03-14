"""Memory store entities — Experience, ExperienceMemory, PromptCache."""

from typing import Dict, List


class Experience:
    def __init__(self):
        self.task: str = ""
        self.start_url: str = ""
        self.context: str = ""
        self.actions: List[Dict] = []
        self.success: bool = False
        self.final_url: str = ""
        self.result: str = ""
        self.timestamp: str = ""


def to_dict(experience: "Experience") -> Dict:
    """Serialize an Experience entity to a dictionary."""
    return {
        "task": experience.task,
        "start_url": experience.start_url,
        "context": experience.context,
        "actions": experience.actions,
        "success": experience.success,
        "final_url": experience.final_url,
        "result": experience.result,
        "timestamp": experience.timestamp,
    }


def from_dict(data: Dict) -> "Experience":
    """Deserialize a dictionary to an Experience entity."""
    exp = Experience()
    exp.task = data.get("task", "")
    exp.start_url = data.get("start_url", "")
    exp.context = data.get("context", "")
    exp.actions = data.get("actions", [])
    exp.success = data.get("success", False)
    exp.final_url = data.get("final_url", "")
    exp.result = data.get("result", "")
    exp.timestamp = data.get("timestamp", "")
    return exp


class ExperienceMemory:
    def __init__(self):
        self.memory_file: str = "navigation_missions.json"
        self.experiences: List[Experience] = []


class PromptCache:
    def __init__(self):
        self.cache_file: str = "keyword_cache.json"
        self.cache: Dict[str, str] = {}
