from __future__ import annotations

from datetime import datetime, date as dt_date
from typing import Optional, Sequence

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = Field(ge=1, le=5, default=3)
    duration_minutes: int = Field(ge=15, le=240, default=60)
    location: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    duration_minutes: Optional[int] = Field(default=None, ge=15, le=240)
    location: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None


class TaskRead(TaskBase):
    id: int
    status: str

    class Config:
        from_attributes = True


class PlanBlockRead(BaseModel):
    id: int
    task_id: int
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None

    class Config:
        from_attributes = True


class ReminderRead(BaseModel):
    id: int
    task_id: int
    trigger_time: datetime
    reminder_type: str
    location_hint: Optional[str] = None

    class Config:
        from_attributes = True


class PlanResponse(BaseModel):
    date: dt_date
    blocks: Sequence[PlanBlockRead]
    reminders: Sequence[ReminderRead]


class PlanRequest(BaseModel):
    date: Optional[dt_date] = None
