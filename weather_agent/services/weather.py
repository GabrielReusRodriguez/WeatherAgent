"""Weather forecasts via Open-Meteo."""

from __future__ import annotations

from typing import Any

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes → neutral English labels for the LLM to translate.
WMO_CODES: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow fall",
    73: "moderate snow fall",
    75: "heavy snow fall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}

CURRENT_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "is_day",
    "precipitation",
    "rain",
    "showers",
    "snowfall",
    "weather_code",
    "cloud_cover",
    "pressure_msl",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
]

HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "rain",
    "snowfall",
    "weather_code",
    "cloud_cover",
    "pressure_msl",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
]

DAILY_VARS = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "apparent_temperature_mean",
    "sunrise",
    "sunset",
    "daylight_duration",
    "sunshine_duration",
    "uv_index_max",
    "rain_sum",
    "showers_sum",
    "snowfall_sum",
    "precipitation_sum",
    "precipitation_hours",
    "precipitation_probability_max",
    "precipitation_probability_mean",
    "wind_speed_10m_max",
    "wind_speed_10m_mean",
    "wind_direction_10m_dominant",
    "cloud_cover_mean",
    "cloud_cover_max",
    "cloud_cover_min",
    "relative_humidity_2m_mean",
    "relative_humidity_2m_max",
    "relative_humidity_2m_min",
    "surface_pressure_mean",
    "surface_pressure_max",
    "surface_pressure_min",
]


def translate_wmo_code(code: int | None) -> str | None:
    """Translate a WMO weather_code to a neutral English label."""
    if code is None:
        return None
    try:
        return WMO_CODES.get(int(code), f"unknown ({code})")
    except (TypeError, ValueError):
        return None


def _is_empty(value: Any) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, (int, float)) and value == 0:
        return True
    return False


def _attach_units(block: dict[str, Any], units: dict[str, Any] | None) -> dict[str, Any]:
    """Merge numeric values with unit suffixes; drop empty/zero fields; map weather_code."""
    if not block:
        return {}
    units = units or {}
    out: dict[str, Any] = {}
    for key, value in block.items():
        if key in {"time", "interval", "is_day"}:
            out[key] = value
            continue
        if key == "weather_code":
            label = translate_wmo_code(value if not isinstance(value, list) else None)
            if isinstance(value, list):
                out["sky_condition"] = [translate_wmo_code(c) for c in value]
            elif label:
                out["sky_condition"] = label
            continue
        if _is_empty(value):
            continue
        unit = units.get(key, "")
        if unit and not isinstance(value, list):
            out[key] = f"{value} {unit}".strip()
        else:
            out[key] = value
    return out


def _sanitize_series(payload: dict[str, Any], key: str) -> dict[str, Any]:
    """Turn an Open-Meteo hourly/daily block into a list of per-time records."""
    series = payload.get(key) or {}
    units = payload.get(f"{key}_units") or {}
    times = series.get("time") or []
    records: list[dict[str, Any]] = []
    for i, t in enumerate(times):
        row: dict[str, Any] = {"time": t}
        for field, values in series.items():
            if field == "time" or not isinstance(values, list):
                continue
            if i >= len(values):
                continue
            row[field] = values[i]
        records.append(_attach_units(row, units))
    return {
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "elevation": payload.get("elevation"),
        "timezone": payload.get("timezone"),
        key: records,
    }


def _get(params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(OPEN_METEO_URL, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def current(lat: float, lon: float) -> dict[str, Any]:
    """Current weather conditions for coordinates."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": CURRENT_VARS,
        "timezone": "auto",
    }
    payload = _get(params)
    current_block = _attach_units(payload.get("current") or {}, payload.get("current_units"))
    return {
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "elevation": payload.get("elevation"),
        "timezone": payload.get("timezone"),
        "current": current_block,
    }


def hourly(lat: float, lon: float, start_date: str, end_date: str) -> dict[str, Any]:
    """Hourly forecast between start_date and end_date (YYYY-MM-DD)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": HOURLY_VARS,
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    }
    return _sanitize_series(_get(params), "hourly")


def daily(lat: float, lon: float, start_date: str, end_date: str) -> dict[str, Any]:
    """Daily forecast between start_date and end_date (YYYY-MM-DD)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": DAILY_VARS,
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    }
    return _sanitize_series(_get(params), "daily")
