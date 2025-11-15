"""Infer potential task locations based on task titles."""

from __future__ import annotations

from sqlalchemy.orm import Session

from .locations import ensure_home_location
from .models import Task, TaskLocationSuggestion
from .nlp import get_nlp
from .places import search_places

STORE_LABELS = {"ORG", "FAC", "GPE", "LOC", "PRODUCT"}
FALLBACK_SEPARATORS = [" at ", " @ ", " from ", " to "]


def _extract_queries(title: str) -> list[str]:
    title = title or ""
    nlp = get_nlp()
    matches: list[str] = []
    seen: set[str] = set()
    if nlp and title:
        doc = nlp(title)
        for ent in doc.ents:
            if ent.label_ in STORE_LABELS:
                text = ent.text.strip()
                if text and text not in seen:
                    matches.append(text)
                    seen.add(text)

    if not matches:
        lowered = title.lower()
        for sep in FALLBACK_SEPARATORS:
            idx = lowered.find(sep)
            if idx != -1:
                start = idx + len(sep)
                part = title[start:]
                hint = part.split(" and ")[0].split(",")[0].strip()
                hint = hint.rstrip(".!?")
                if hint and hint not in seen:
                    matches.append(hint)
                    seen.add(hint)
    return matches


def infer_locations(db: Session, title: str) -> list[dict[str, str | None]]:
    """Infer potential location dicts for a given title without mutating state."""

    queries = _extract_queries(title or "")
    if not queries:
        return []

    home = ensure_home_location(db)
    if not home.address:
        return []

    suggestions: list[dict[str, str | None]] = []
    for query in queries:
        places = search_places(query, home.address)
        for place in places:
            suggestions.append(
                {
                    "name": place.get("name", query),
                    "address": place.get("address"),
                }
            )
    return suggestions


def refresh_task_location_suggestions(db: Session, task: Task) -> None:
    """Rebuild location suggestions for a task based on its title."""

    for suggestion in list(task.location_suggestions):
        db.delete(suggestion)
    db.commit()

    suggestions = infer_locations(db, task.title or "")
    for place in suggestions:
        suggestion = TaskLocationSuggestion(
            task_id=task.id,
            label=place.get("name") or "",
            address=place.get("address"),
        )
        db.add(suggestion)
    db.commit()
    db.refresh(task)
