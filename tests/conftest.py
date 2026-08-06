"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def nominatim_hit():
    return [
        {
            "lat": "41.6079555",
            "lon": "2.2876008",
            "display_name": "Granollers, Catalunya, España",
        }
    ]


@pytest.fixture
def open_meteo_current_payload():
    return {
        "latitude": 41.625,
        "longitude": 2.3125,
        "elevation": 153.0,
        "timezone": "Europe/Madrid",
        "current_units": {
            "time": "iso8601",
            "temperature_2m": "°C",
            "weather_code": "wmo code",
            "rain": "mm",
        },
        "current": {
            "time": "2026-08-06T12:00",
            "interval": 900,
            "temperature_2m": 27.8,
            "weather_code": 3,
            "rain": 0.0,
        },
    }


@pytest.fixture
def open_meteo_daily_payload():
    return {
        "latitude": 41.625,
        "longitude": 2.3125,
        "elevation": 153.0,
        "timezone": "Europe/Madrid",
        "daily_units": {
            "time": "iso8601",
            "weather_code": "wmo code",
            "temperature_2m_max": "°C",
            "temperature_2m_min": "°C",
        },
        "daily": {
            "time": ["2026-08-08"],
            "weather_code": [3],
            "temperature_2m_max": [34.4],
            "temperature_2m_min": [22.3],
        },
    }
