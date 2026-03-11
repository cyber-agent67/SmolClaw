"""Pipeline job entities with K8s-inspired spec/status pattern."""
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field


def generate_uid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class JobPhase(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageType(str, Enum):
    LOGIN = "login"
    EXPLORATION = "exploration"
    NAVIGATION = "navigation"
    EXTRACTION = "extraction"
    APP_INVENTORY = "app_inventory"


class StagePhase(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class JobSpec(BaseModel):
    saas_id: str
    workspace_id: str
    stages: list[StageType]
    headless: bool = True
    timeout_seconds: int = 1800
    context: dict = Field(default_factory=dict)


class StageStatus(BaseModel):
    phase: StagePhase = StagePhase.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    message: str | None = None
    result: dict | None = None

    def mark_running(self, message: str | None = None) -> None:
        self.phase = StagePhase.RUNNING
        self.started_at = utc_now()
        self.message = message

    def mark_succeeded(self, result: dict | None = None) -> None:
        self.phase = StagePhase.SUCCEEDED
        self.completed_at = utc_now()
        self.result = result

    def mark_failed(self, message: str, result: dict | None = None) -> None:
        self.phase = StagePhase.FAILED
        self.completed_at = utc_now()
        self.message = message
        self.result = result

    def mark_skipped(self, message: str | None = None) -> None:
        self.phase = StagePhase.SKIPPED
        self.message = message


class JobStatus(BaseModel):
    phase: JobPhase = JobPhase.PENDING
    current_stage: StageType | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    stages: dict[StageType, StageStatus] = Field(default_factory=dict)
    error: str | None = None
    replay_url: str | None = None

    def mark_running(self, stage: StageType) -> None:
        if self.phase == JobPhase.PENDING:
            self.phase = JobPhase.RUNNING
            self.started_at = utc_now()
        self.current_stage = stage

    def mark_succeeded(self) -> None:
        self.phase = JobPhase.SUCCEEDED
        self.completed_at = utc_now()
        self.current_stage = None

    def mark_failed(self, error: str) -> None:
        self.phase = JobPhase.FAILED
        self.completed_at = utc_now()
        self.error = error

    def mark_cancelled(self) -> None:
        self.phase = JobPhase.CANCELLED
        self.completed_at = utc_now()

    def get_stage_status(self, stage: StageType) -> StageStatus:
        if stage not in self.stages:
            self.stages[stage] = StageStatus()
        return self.stages[stage]

    @property
    def is_terminal(self) -> bool:
        return self.phase in (JobPhase.SUCCEEDED, JobPhase.FAILED, JobPhase.CANCELLED)


class PipelineJob(BaseModel):
    uid: str = Field(default_factory=generate_uid)
    created_at: datetime = Field(default_factory=utc_now)
    spec: JobSpec
    status: JobStatus = Field(default_factory=JobStatus)

    def initialize_stages(self) -> None:
        for stage in self.spec.stages:
            if stage not in self.status.stages:
                self.status.stages[stage] = StageStatus()

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal
