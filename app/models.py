from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text())
    priority: Mapped[int] = mapped_column(Integer, default=3)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    location: Mapped[str | None] = mapped_column(String(120), default=None)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    time_estimate_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    time_estimate_meta: Mapped[dict | None] = mapped_column(JSON)
    time_estimate_travel_to_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    time_estimate_travel_back_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    time_estimate_shopping_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    status: Mapped[str] = mapped_column(
        Enum("pending", "scheduled", "done", name="task_status"),
        default="pending",
    )

    plan_blocks: Mapped[list["PlanBlock"]] = relationship(back_populates="task")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="task")
    location_suggestions: Mapped[list["TaskLocationSuggestion"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )


class PlanBlock(Base):
    __tablename__ = "plan_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    location: Mapped[str | None] = mapped_column(String(120))

    task: Mapped["Task"] = relationship(back_populates="plan_blocks")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    trigger_time: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    reminder_type: Mapped[str] = mapped_column(
        Enum("time", "location", "manual", name="reminder_type"),
        default="time",
    )
    location_hint: Mapped[str | None] = mapped_column(String(120))

    task: Mapped["Task"] = relationship(back_populates="reminders")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str | None] = mapped_column(String(255))
    is_home: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class TaskLocationSuggestion(Base):
    __tablename__ = "task_location_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(180))
    address: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(50), default="places")

    task: Mapped["Task"] = relationship(back_populates="location_suggestions")
