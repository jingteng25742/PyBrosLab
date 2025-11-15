"""Helpers for working with persistent locations (home base, etc.)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from .config import settings
from .models import Location


def get_home_location(db: Session) -> Location | None:
    return db.query(Location).filter(Location.is_home.is_(True)).first()


def ensure_home_location(db: Session) -> Location:
    home = get_home_location(db)
    if home:
        return home

    home = Location(
        name=settings.home_location_name,
        address=settings.home_location_address,
        is_home=True,
    )
    db.add(home)
    db.commit()
    db.refresh(home)
    return home


def save_home_location(
    db: Session,
    *,
    name: str,
    address: str | None = None,
) -> Location:
    home = get_home_location(db)
    if not home:
        home = Location(is_home=True)
        db.add(home)

    home.name = name
    home.address = address
    db.commit()
    db.refresh(home)
    return home
