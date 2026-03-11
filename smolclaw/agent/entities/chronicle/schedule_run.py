"""Schedule run entities."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ScheduleRunStatus(str, Enum):
    SCHEDULED = "scheduled"
    EXECUTED = "executed"
    SKIPPED = "skipped"
    FAILED = "failed"


class ScheduleRun(BaseModel):
    id: int
    agent_uid: str
    scheduled_at: datetime
    executed_at: datetime | None = None
    scan_uid: str | None = None
    status: ScheduleRunStatus
    skip_reason: str | None = None
    error: str | None = None
    created_at: datetime


class CreateScheduleRunRequest(BaseModel):
    agent_uid: str
    scheduled_at: datetime
    status: ScheduleRunStatus = ScheduleRunStatus.SCHEDULED
