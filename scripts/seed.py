#!/usr/bin/env python3
"""Seed the SQLite database with sample tasks for quick demos."""

from datetime import datetime, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal, Base, engine  # noqa:E402
from app.models import Task  # noqa:E402

SAMPLE_TASKS = [
    {
        "title": "Review project backlog",
        "description": "Sort tasks into priority buckets.",
        "priority": 5,
        "duration_minutes": 60,
        "location": "Home Office",
    },
    {
        "title": "Groceries pickup",
        "description": "Trader Joe's order curbside",
        "priority": 3,
        "duration_minutes": 45,
        "location": "Trader Joe's - Elm St.",
    },
    {
        "title": "Gym session",
        "description": "Leg day + stretch",
        "priority": 2,
        "duration_minutes": 90,
        "location": "Anytime Fitness",
    },
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Task).count() > 0:
            print("Tasks already present, skipping seed.")
            return

        due_base = datetime.utcnow()
        for idx, payload in enumerate(SAMPLE_TASKS):
            task = Task(
                **payload,
                due_date=due_base + timedelta(hours=idx * 2 + 2),
            )
            db.add(task)
        db.commit()
        print("Seeded sample tasks.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
