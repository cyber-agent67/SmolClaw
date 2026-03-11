"""Settings extraction entities."""
import hashlib
from datetime import UTC, datetime
from enum import Enum
from pydantic import BaseModel, Field, computed_field


class ElementType(str, Enum):
    TOGGLE = "toggle"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    RADIO = "radio"
    TEXT = "text"
    SELECT = "select"
    BUTTON = "button"
    LINK = "link"
    UNKNOWN = "unknown"


class ExtractedSetting(BaseModel):
    label: str
    raw_value: str
    raw_label_extracted: str | None = None
    raw_value_extracted: str | None = None
    element_type: ElementType
    confidence: float = Field(ge=0.0, le=1.0)
    possible_values: list[str] | None = None
    page_url: str
    screenshot_path: str
    description: str | None = None
    section: str | None = None
    recommended_value: str | None = None
    has_drift: bool | None = None
    frameworks: list[str] | None = None
    risk_level: str | None = None
    previous_scan_value: str | None = None
    has_historical_drift: bool | None = None
    schema_key: str | None = None
    schema_match_status: str | None = None
    schema_priority: str | None = None
    api_available: bool | None = None

    @computed_field
    @property
    def setting_id(self) -> str:
        section = self.section or ""
        content = f"{self.page_url}:{section}:{self.label}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class ExtractedSettingsPage(BaseModel):
    page_url: str
    screenshot_path: str
    sitemap_id: str | None = None
    saas_name: str
    settings: list[ExtractedSetting] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    page_title: str | None = None
    error: str | None = None

    @computed_field
    @property
    def settings_count(self) -> int:
        return len(self.settings)


class ExtractionResult(BaseModel):
    run_id: str
    saas_id: str
    workspace_id: str | None = None
    pages: list[ExtractedSettingsPage] = Field(default_factory=list)
    scan_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    success: bool = True
    error: str | None = None

    @computed_field
    @property
    def total_settings(self) -> int:
        return sum(page.settings_count for page in self.pages)

    @computed_field
    @property
    def total_pages(self) -> int:
        return len(self.pages)

    @computed_field
    @property
    def avg_confidence(self) -> float:
        all_confidences = [s.confidence for p in self.pages for s in p.settings]
        if not all_confidences:
            return 0.0
        return sum(all_confidences) / len(all_confidences)
