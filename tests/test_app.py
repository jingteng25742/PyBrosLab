from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
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


def test_create_task_endpoint_matches_ui_payload(client: TestClient):
    payload = {
        "title": "Pickup groceries",
        "description": "Trader Joe's haul",
        "priority": 4,
        "duration_minutes": 45,
        "location": "Trader Joe's",
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == payload["title"]
    assert body["location"] == payload["location"]
    assert "time_estimate_minutes" in body


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
    resp = client.put(
        "/locations/home",
        json={
            "name": "Studio",
            "address": "123 Home St",
        },
    )
    assert resp.status_code == 200
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
    assert data["home_location"]["name"] == "Studio"

    tasks_after_plan = client.get("/tasks").json()
    assert {task["status"] for task in tasks_after_plan} == {"scheduled"}


def test_home_location_defaults_and_updates(client: TestClient):
    # Default home should be provisioned automatically
    default_home = client.get("/locations/home").json()
    assert default_home["is_home"] is True
    assert default_home["name"]

    update_payload = {
        "name": "Townhouse",
        "address": "456 Main St",
    }
    updated = client.put("/locations/home", json=update_payload)
    assert updated.status_code == 200
    body = updated.json()
    assert body["name"] == "Townhouse"
    assert body["address"] == "456 Main St"


def test_delete_task_removes_record(client: TestClient):
    created = client.post(
        "/tasks",
        json={"title": "One-off errand", "priority": 1, "duration_minutes": 15},
    ).json()
    task_id = created["id"]

    delete_response = client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 204

    list_response = client.get("/tasks").json()
    ids = [task["id"] for task in list_response]
    assert task_id not in ids


def test_infer_location_endpoint_uses_title_keywords(client: TestClient, monkeypatch):
    client.put(
        "/locations/home",
        json={"name": "HQ", "address": "100 Main St"},
    )

    def fake_search(query, near, *, max_results=2):
        return [{"name": query, "address": "456 Elm"}]

    monkeypatch.setattr("app.location_inference.search_places", fake_search)

    response = client.post(
        "/tasks/infer-location",
        json={"title": "Pick up lumber at Home Depot"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["label"] == "Home Depot"


def test_task_api_fields_match_db_and_ui_expectations(client: TestClient):
    client.put(
        "/locations/home",
        json={"name": "HQ", "address": "100 Main St"},
    )
    client.post(
        "/tasks",
        json={
            "title": "Run to Target",
            "description": "Need detergent",
            "priority": 3,
            "duration_minutes": 30,
            "location": "Target",
        },
    )

    record = client.get("/tasks").json()[0]
    api_fields = set(record.keys())
    ui_fields = {
        "id",
        "title",
        "priority",
        "location",
        "status",
        "due_date",
        "time_estimate_minutes",
        "time_estimate_travel_to_minutes",
        "time_estimate_travel_back_minutes",
        "time_estimate_shopping_minutes",
        "location_suggestions",
    }
    assert ui_fields.issubset(api_fields)

    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("tasks")}
    db_fields = {
        "time_estimate_minutes",
        "time_estimate_meta",
        "time_estimate_travel_to_minutes",
        "time_estimate_travel_back_minutes",
        "time_estimate_shopping_minutes",
    }
    assert db_fields.issubset(columns)
