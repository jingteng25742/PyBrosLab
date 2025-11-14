from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
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
    status: Mapped[str] = mapped_column(
        Enum("pending", "scheduled", "done", name="task_status"),
        default="pending",
    )

    plan_blocks: Mapped[list["PlanBlock"]] = relationship(back_populates="task")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="task")


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
