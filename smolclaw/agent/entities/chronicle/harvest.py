"""Harvest entities for interactive settings extraction."""
from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field
from .settings import ExtractedSetting


class InteractionType(str, Enum):
    EXPAND_SECTION = "expand_section"
    OPEN_MODAL = "open_modal"
    SWITCH_TAB = "switch_tab"
    CLICK_EDIT = "click_edit"


class HarvestAction(BaseModel):
    interaction_type: InteractionType
    trigger_description: str
    screenshot_before: str = ""
    screenshot_after: str
    settings_extracted: list[ExtractedSetting] = Field(default_factory=list)
    reversal_action: str | None = None
    success: bool
    error: str | None = None


class SettingsNode(BaseModel):
    label: str
    node_type: Literal["section", "setting", "group"]
    setting: ExtractedSetting | None = None
    children: list[SettingsNode] = Field(default_factory=list)
    source: str = "visible"
    screenshot_path: str | None = None


class HarvestResult(BaseModel):
    page_url: str
    settings_tree: list[SettingsNode] = Field(default_factory=list)
    flat_settings: list[ExtractedSetting] = Field(default_factory=list)
    actions_performed: list[HarvestAction] = Field(default_factory=list)
    screenshot_filenames: list[str] = Field(default_factory=list)
    total_settings: int = 0
    total_interactions: int = 0
    success: bool = True
    error: str | None = None
