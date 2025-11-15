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
    location_suggestions: Sequence["TaskLocationSuggestionRead"] = ()
    time_estimate_minutes: Optional[int] = None
    time_estimate_meta: Optional[dict] = None
    time_estimate_travel_to_minutes: Optional[int] = None
    time_estimate_travel_back_minutes: Optional[int] = None
    time_estimate_shopping_minutes: Optional[int] = None

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


class TaskLocationSuggestionRead(BaseModel):
    id: int
    label: str
    address: Optional[str] = None
    source: str

    class Config:
        from_attributes = True


class LocationSuggestionPreview(BaseModel):
    label: str
    address: Optional[str] = None


class LocationInferenceRequest(BaseModel):
    title: str


class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None


class LocationRead(LocationBase):
    id: int
    is_home: bool

    class Config:
        from_attributes = True


class LocationUpsert(LocationBase):
    pass


class PlanResponse(BaseModel):
    date: dt_date
    blocks: Sequence[PlanBlockRead]
    reminders: Sequence[ReminderRead]
    home_location: Optional[LocationRead] = None


class PlanRequest(BaseModel):
    date: Optional[dt_date] = None


class ClientConfig(BaseModel):
    google_maps_api_key: Optional[str] = None
