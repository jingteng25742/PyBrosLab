from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .location_inference import infer_locations, refresh_task_location_suggestions
from .locations import ensure_home_location, save_home_location
from .models import PlanBlock, Reminder, Task
from .places import estimate_travel_segments
from .planner import day_bounds, generate_plan, get_plan_for_date
from .schemas import (
    PlanRequest,
    PlanResponse,
    PlanBlockRead,
    ReminderRead,
    TaskCreate,
    TaskRead,
    TaskUpdate,
    LocationRead,
    LocationUpsert,
    ClientConfig,
    LocationInferenceRequest,
    LocationSuggestionPreview,
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


def populate_time_estimate(db: Session, tasks: list[Task]) -> None:
    if not tasks:
        return
    home = ensure_home_location(db)
    home_address = home.address or ""
    for task in tasks:
        task.time_estimate_minutes = None
        task.time_estimate_meta = None
        task.time_estimate_travel_to_minutes = None
        task.time_estimate_travel_back_minutes = None
        task.time_estimate_shopping_minutes = None
        if not home_address or not task.location:
            continue
        travel_to, travel_back, summary = estimate_travel_segments(home_address, task.location)
        if travel_to is None or travel_back is None:
            continue
        shopping_minutes = task.duration_minutes or settings.default_block_minutes
        total = travel_to + travel_back + shopping_minutes
        task.time_estimate_minutes = total
        task.time_estimate_meta = {
            "travel_to_minutes": travel_to,
            "travel_back_minutes": travel_back,
            "shopping_minutes": shopping_minutes,
            "summary": summary or "Drive",
        }
        task.time_estimate_travel_to_minutes = travel_to
        task.time_estimate_travel_back_minutes = travel_back
        task.time_estimate_shopping_minutes = shopping_minutes


@app.get("/", response_class=HTMLResponse)
def client_home() -> HTMLResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Sample client not found.")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.get("/health")
def healthcheck():
    return {"status": "ok", "timestamp": datetime.utcnow()}


@app.get("/client/config", response_model=ClientConfig)
def client_config() -> ClientConfig:
    return ClientConfig(google_maps_api_key=settings.google_maps_api_key)


@app.get("/locations/home", response_model=LocationRead)
def read_home_location(db: Session = Depends(get_db)):
    home = ensure_home_location(db)
    return LocationRead.from_orm(home)


@app.put("/locations/home", response_model=LocationRead)
def update_home_location(payload: LocationUpsert, db: Session = Depends(get_db)):
    home = save_home_location(db, **payload.dict())
    return LocationRead.from_orm(home)


@app.post("/tasks", response_model=TaskRead)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    refresh_task_location_suggestions(db, db_task)
    db.refresh(db_task)
    populate_time_estimate(db, [db_task])
    return db_task


@app.get("/tasks", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.priority.desc()).all()
    populate_time_estimate(db, tasks)
    return tasks


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
    if "title" in update_data:
        refresh_task_location_suggestions(db, task)
        db.refresh(task)
    populate_time_estimate(db, [task])
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    db.delete(task)
    db.commit()
    return Response(status_code=204)


@app.post("/tasks/infer-location", response_model=list[LocationSuggestionPreview])
def infer_task_location(payload: LocationInferenceRequest, db: Session = Depends(get_db)):
    suggestions = infer_locations(db, payload.title)
    return [
        LocationSuggestionPreview(label=item.get("name", payload.title), address=item.get("address"))
        for item in suggestions
    ]


@app.post("/plan/generate", response_model=PlanResponse)
def generate_daily_plan(payload: PlanRequest | None = None, db: Session = Depends(get_db)):
    payload = payload or PlanRequest()
    target_date = payload.date or date.today()
    blocks, reminders = generate_plan(db, target_date)
    home = ensure_home_location(db)
    return PlanResponse(
        date=target_date,
        blocks=[PlanBlockRead.from_orm(b) for b in blocks],
        reminders=[ReminderRead.from_orm(r) for r in reminders],
        home_location=LocationRead.from_orm(home) if home else None,
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
    home = ensure_home_location(db)
    return PlanResponse(
        date=target_date,
        blocks=[PlanBlockRead.from_orm(b) for b in blocks],
        reminders=[ReminderRead.from_orm(r) for r in reminders],
        home_location=LocationRead.from_orm(home) if home else None,
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
