"""Google Places helpers for inferring suggested locations."""

from __future__ import annotations

from typing import List

import httpx

from .config import settings

PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


def search_places(query: str, near: str, *, max_results: int = 2) -> list[dict[str, str]]:
    """Call the Places Text Search API and return simplified place info."""

    api_key = settings.google_maps_api_key
    if not api_key or not near:
        return []

    params = {
        "query": f"{query} near {near}",
        "key": api_key,
    }
    try:
        response = httpx.get(PLACES_SEARCH_URL, params=params, timeout=5)
    except httpx.HTTPError:
        return []

    if response.status_code != 200:
        return []

    payload = response.json()
    results: List[dict[str, str]] = []
    for item in payload.get("results", [])[:max_results]:
        results.append(
            {
                "name": item.get("name", query),
                "address": item.get("formatted_address"),
            }
        )
    return results


def estimate_travel_segments(home_address: str, task_address: str) -> tuple[int | None, int | None, str | None]:
    api_key = settings.google_maps_api_key
    if not api_key or not home_address or not task_address:
        return None, None, None

    params = {
        "origins": home_address,
        "destinations": task_address,
        "mode": "driving",
        "key": api_key,
    }
    try:
        response = httpx.get(DISTANCE_MATRIX_URL, params=params, timeout=5)
    except httpx.HTTPError:
        return None, None, None

    if response.status_code != 200:
        return None, None, None

    payload = response.json()
    rows = payload.get("rows") or []
    if not rows:
        return None, None, None
    elements = rows[0].get("elements") or []
    if not elements:
        return None, None, None
    first = elements[0]
    if first.get("status") != "OK":
            return None, None, None
    duration = first.get("duration", {}).get("value")
    if duration is None:
        return None, None, None
    text = first.get("duration", {}).get("text")
    # round trip = out + back (minutes)
    minutes = max(int(duration / 60), 1)
    summary = text or "Drive"
    return minutes, minutes, summary
