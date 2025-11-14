from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import PlanBlock, Reminder, Task
from .planner import day_bounds, generate_plan, get_plan_for_date
from .schemas import (
    PlanRequest,
    PlanResponse,
    PlanBlockRead,
    ReminderRead,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Day Planner MVP",
    version="0.1.0",
    description="Minimal FastAPI + SQLite backend for experimenting with planning flows.",
)

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def client_home() -> HTMLResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Sample client not found.")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.get("/health")
def healthcheck():
    return {"status": "ok", "timestamp": datetime.utcnow()}


@app.post("/tasks", response_model=TaskRead)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/tasks", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).order_by(Task.priority.desc()).all()


@app.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@app.post("/plan/generate", response_model=PlanResponse)
def generate_daily_plan(payload: PlanRequest | None = None, db: Session = Depends(get_db)):
    payload = payload or PlanRequest()
    target_date = payload.date or date.today()
    blocks, reminders = generate_plan(db, target_date)
    return PlanResponse(
        date=target_date,
        blocks=[PlanBlockRead.from_orm(b) for b in blocks],
        reminders=[ReminderRead.from_orm(r) for r in reminders],
    )


@app.get("/plan/{target_date}", response_model=PlanResponse)
def get_plan(target_date: date, db: Session = Depends(get_db)):
    blocks = get_plan_for_date(db, target_date)
    start, end = day_bounds(target_date)
    reminders = (
        db.query(Reminder)
        .filter(Reminder.trigger_time.between(start - timedelta(hours=2), end))
        .order_by(Reminder.trigger_time)
        .all()
    )
    if not blocks and not reminders:
        raise HTTPException(status_code=404, detail="Plan not found for that date.")
    return PlanResponse(
        date=target_date,
        blocks=[PlanBlockRead.from_orm(b) for b in blocks],
        reminders=[ReminderRead.from_orm(r) for r in reminders],
    )


@app.get("/reminders/today", response_model=list[ReminderRead])
def today_reminders(db: Session = Depends(get_db)):
    today = date.today()
    start, end = day_bounds(today)
    reminders = (
        db.query(Reminder)
        .filter(Reminder.trigger_time.between(start - timedelta(hours=2), end))
        .order_by(Reminder.trigger_time)
        .all()
    )
    return [ReminderRead.from_orm(r) for r in reminders]
