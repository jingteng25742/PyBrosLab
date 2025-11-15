from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import OperationalError

from .config import settings


class Base(DeclarativeBase):
    """Base model for SQLAlchemy."""


settings.data_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _ensure_task_columns() -> None:
    statements = [
        "ALTER TABLE tasks ADD COLUMN time_estimate_minutes INTEGER",
        "ALTER TABLE tasks ADD COLUMN time_estimate_meta JSON",
        "ALTER TABLE tasks ADD COLUMN time_estimate_travel_to_minutes INTEGER",
        "ALTER TABLE tasks ADD COLUMN time_estimate_travel_back_minutes INTEGER",
        "ALTER TABLE tasks ADD COLUMN time_estimate_shopping_minutes INTEGER",
    ]
    with engine.begin() as connection:
        for stmt in statements:
            try:
                connection.execute(text(stmt))
            except OperationalError as exc:
                if "duplicate column" in str(exc).lower():
                    continue
                if "no such table" in str(exc).lower():
                    break
                raise


_ensure_task_columns()


def get_db():
    """FastAPI dependency that provides a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
