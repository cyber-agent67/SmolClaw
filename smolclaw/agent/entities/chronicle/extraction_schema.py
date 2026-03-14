"""Baseline extraction schema entities."""
from typing import Literal
from pydantic import BaseModel, Field


def _label_similarity(a: str, b: str) -> float:
    """Simple label similarity using token overlap."""
    tokens_a = set(a.strip().lower().split())
    tokens_b = set(b.strip().lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


class BaselineSetting(BaseModel):
    label: str
    key: str
    priority: Literal["High", "Medium", "Low"]
    allowed_values: list[str]
    description: str
    section: str = ""
    api_available: bool = False


class ExtractionSchema(BaseModel):
    saas_id: str
    settings: list[BaselineSetting] = Field(default_factory=list)

    @property
    def labels(self) -> list[str]:
        return [s.label for s in self.settings]

    @property
    def keys(self) -> list[str]:
        return [s.key for s in self.settings]

    def find_by_label(self, label: str, threshold: float = 0.80) -> BaselineSetting | None:
        label_lower = label.strip().lower()
        for setting in self.settings:
            if setting.label.strip().lower() == label_lower:
                return setting
        best_match: BaselineSetting | None = None
        best_score = 0.0
        for setting in self.settings:
            score = _label_similarity(label, setting.label)
            if score > best_score:
                best_score = score
                best_match = setting
        if best_match is not None and best_score >= threshold:
            return best_match
        return None

    def find_by_key(self, key: str) -> BaselineSetting | None:
        for setting in self.settings:
            if setting.key == key:
                return setting
        return None
