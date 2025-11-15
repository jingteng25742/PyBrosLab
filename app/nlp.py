"""spaCy pipeline loading helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def get_nlp() -> Any | None:
    """Load the transformer-based English pipeline if available."""

    try:
        import spacy  # noqa: WPS433 - imported lazily to keep dependency optional
    except ModuleNotFoundError:
        return None

    try:
        return spacy.load("en_core_web_trf")
    except OSError:
        return None
