"""Geocoding via OpenStreetMap Nominatim."""

from __future__ import annotations

from typing import Any

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "GabAgentsv2-WeatherAgent/0.1 (weather forecast agent)"


def resolve_location(place: str) -> dict[str, Any]:
    """Resolve a place name to coordinates.

    Args:
        place: Free-text location (e.g. "Madrid", "Paris, France").

    Returns:
        Dict with lat, lon and display_name.

    Raises:
        ValueError: If the place cannot be found.
        requests.HTTPError: On HTTP failures.
    """
    query = (place or "").strip()
    if not query:
        raise ValueError("Place name is empty")

    params = {
        "q": query,
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError(f"No coordinates found for '{query}'")

    hit = data[0]
    return {
        "lat": float(hit["lat"]),
        "lon": float(hit["lon"]),
        "display_name": hit.get("display_name", query),
    }
