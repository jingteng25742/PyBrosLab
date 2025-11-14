from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Sequence

from sqlalchemy import delete, extract, select
from sqlalchemy.orm import Session

from .config import settings
from .models import PlanBlock, Reminder, Task


def day_bounds(target_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(
        target_date,
        time(hour=settings.planner_start_hour),
    )
    end = datetime.combine(
        target_date,
        time(hour=settings.planner_end_hour),
    )
    return start, end


def get_plan_for_date(db: Session, target_date: date) -> Sequence[PlanBlock]:
    stmt = (
        select(PlanBlock)
        .where(extract("year", PlanBlock.start_time) == target_date.year)
        .where(extract("month", PlanBlock.start_time) == target_date.month)
        .where(extract("day", PlanBlock.start_time) == target_date.day)
        .order_by(PlanBlock.start_time)
    )
    return db.execute(stmt).scalars().all()


def generate_plan(db: Session, target_date: date) -> tuple[list[PlanBlock], list[Reminder]]:
    start, end = day_bounds(target_date)

    # wipe existing plan blocks/reminders for the date
    db.execute(
        delete(PlanBlock).where(
            PlanBlock.start_time.between(start, end),
        )
    )
    db.execute(
        delete(Reminder).where(
            Reminder.trigger_time.between(start - timedelta(hours=2), end),
        )
    )

    tasks = (
        db.query(Task)
        .filter(Task.status.in_(["pending", "scheduled"]))
        .order_by(Task.priority.desc(), Task.due_date)
        .all()
    )

    cursor = start
    plan_blocks: list[PlanBlock] = []
    reminders: list[Reminder] = []

    for task in tasks:
        duration = timedelta(minutes=task.duration_minutes)
        block_end = cursor + duration
        if block_end > end:
            break

        block = PlanBlock(
            task_id=task.id,
            start_time=cursor,
            end_time=block_end,
            location=task.location,
        )
        db.add(block)
        plan_blocks.append(block)

        reminder = Reminder(
            task_id=task.id,
            trigger_time=cursor - timedelta(minutes=10),
            reminder_type="location" if task.location else "time",
            location_hint=task.location,
        )
        db.add(reminder)
        reminders.append(reminder)

        task.status = "scheduled"
        cursor = block_end

    db.commit()

    for block in plan_blocks:
        db.refresh(block)
    for reminder in reminders:
        db.refresh(reminder)

    return plan_blocks, reminders
