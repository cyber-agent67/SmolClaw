"""Navigation, exploration, and step-execution entities for Chronicle integration."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Literal, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .harvest import HarvestResult


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ActionType(str, Enum):
    GOTO = "goto"
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    SCREENSHOT = "screenshot"


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

class VerificationResult(BaseModel):
    success: bool
    confidence: float = Field(ge=0, le=1)
    method: Literal["quick", "vision"]
    details: str | None = None


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

class FallbackContext(BaseModel):
    action_type: ActionType
    original_instruction: str
    target_description: str | None = None
    expected_outcome: str | None = None
    current_url: str
    value_to_enter: str | None = None
    target_url: str | None = None


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

class NavStep(BaseModel):
    action: ActionType
    instruction: str
    selector: str | None = None
    alt_selectors: list[str] = []
    fallback_instruction: str | None = None
    url: str | None = None
    value: str | None = None
    wait_after_ms: int = 500
    timestamp: datetime
    success: bool = True
    error: str | None = None
    target_element_description: str | None = None
    expected_outcome: str | None = None
    expected_url_pattern: str | None = None
    expected_page_indicators: list[str] = []


# ---------------------------------------------------------------------------
# Navigation map
# ---------------------------------------------------------------------------

class NavigationMap(BaseModel):
    saas_id: str
    workspace_id: str
    start_url: str
    steps: list[NavStep] = []
    created_at: datetime

    def add_step(self, step: NavStep) -> None:
        self.steps.append(step)


# ---------------------------------------------------------------------------
# Exploration result
# ---------------------------------------------------------------------------

class ExplorationResult(BaseModel):
    success: bool
    navigation_map: NavigationMap
    screenshot_path: str | None = None
    screenshot_paths: list[str] = []
    step_urls: list[str] = []
    final_url: str
    error: str | None = None
    draft_uid: str | None = None


# ---------------------------------------------------------------------------
# Step execution result
# ---------------------------------------------------------------------------

class StepExecutionResult(BaseModel):
    step_index: int
    action: ActionType
    success: bool
    used_fallback: bool = False
    selector_used: str | None = None
    error: str | None = None
    duration_ms: int = 0
    verification_performed: bool = False
    verification_result: VerificationResult | None = None


# ---------------------------------------------------------------------------
# Screenshot capture
# ---------------------------------------------------------------------------

class ScreenshotCapture(BaseModel):
    filename: str
    scroll_area: str = "main"
    scroll_position: int = 0
    captured_at: datetime


# ---------------------------------------------------------------------------
# Navigation result
# ---------------------------------------------------------------------------

class NavigationResult(BaseModel):
    run_id: str
    map_path: str
    saas_id: str
    workspace_id: str
    success: bool
    total_steps: int
    steps_succeeded: int
    fallback_used_count: int = 0
    login_required: bool = False
    step_results: list[StepExecutionResult] = []
    screenshots: list[ScreenshotCapture] = []
    screenshot_dir: str | None = None
    final_url: str
    page_title: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int = 0
    error: str | None = None
    harvest_result: HarvestResult | None = None
