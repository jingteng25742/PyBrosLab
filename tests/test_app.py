from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_create_and_list_tasks_sorted_by_priority(client: TestClient):
    low_priority = {
        "title": "Read docs",
        "description": "Go through FastAPI tutorial",
        "priority": 2,
        "duration_minutes": 45,
    }
    high_priority = {
        "title": "Ship feature",
        "description": "Finish reminder workflow",
        "priority": 5,
        "duration_minutes": 60,
    }

    assert client.post("/tasks", json=low_priority).status_code == 200
    assert client.post("/tasks", json=high_priority).status_code == 200

    tasks = client.get("/tasks").json()
    assert [task["priority"] for task in tasks] == [5, 2]


def test_update_task_allows_partial_edits(client: TestClient):
    new_task = {
        "title": "Initial title",
        "priority": 3,
        "duration_minutes": 30,
    }
    created = client.post("/tasks", json=new_task).json()

    updated = client.patch(
        f"/tasks/{created['id']}",
        json={"title": "Updated title", "duration_minutes": 90},
    )

    assert updated.status_code == 200
    response_body = updated.json()
    assert response_body["title"] == "Updated title"
    assert response_body["duration_minutes"] == 90


def test_generate_plan_creates_blocks_and_reminders(client: TestClient):
    payloads = [
        {
            "title": "Morning focus block",
            "priority": 5,
            "duration_minutes": 60,
            "due_date": "2030-01-01T09:00:00",
        },
        {
            "title": "Workout",
            "priority": 3,
            "duration_minutes": 45,
            "location": "Gym",
            "due_date": "2030-01-01T17:00:00",
        },
    ]
    for payload in payloads:
        assert client.post("/tasks", json=payload).status_code == 200

    response = client.post("/plan/generate", json={"date": date.today().isoformat()})
    assert response.status_code == 200
    data = response.json()

    assert len(data["blocks"]) == len(payloads)
    assert len(data["reminders"]) == len(payloads)

    tasks_after_plan = client.get("/tasks").json()
    assert {task["status"] for task in tasks_after_plan} == {"scheduled"}
