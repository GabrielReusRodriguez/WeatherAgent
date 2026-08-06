"""Tests for Open-Meteo weather service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from weather_agent.services import weather


def test_translate_wmo_code():
    assert weather.translate_wmo_code(0) == "clear sky"
    assert weather.translate_wmo_code(3) == "overcast"
    assert weather.translate_wmo_code(95) == "thunderstorm"
    assert weather.translate_wmo_code(None) is None
    assert "unknown" in weather.translate_wmo_code(999)


def test_current_sanitizes_and_maps_sky(open_meteo_current_payload):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = open_meteo_current_payload

    with patch("weather_agent.services.weather.requests.get", return_value=mock_resp) as get:
        result = weather.current(41.6, 2.28)

    assert result["timezone"] == "Europe/Madrid"
    assert result["current"]["sky_condition"] == "overcast"
    assert result["current"]["temperature_2m"] == "27.8 °C"
    # rain 0.0 is dropped
    assert "rain" not in result["current"]
    assert get.call_args.kwargs["params"]["timezone"] == "auto"


def test_daily_builds_records(open_meteo_daily_payload):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = open_meteo_daily_payload

    with patch("weather_agent.services.weather.requests.get", return_value=mock_resp):
        result = weather.daily(41.6, 2.28, "2026-08-08", "2026-08-08")

    assert len(result["daily"]) == 1
    day = result["daily"][0]
    assert day["time"] == "2026-08-08"
    assert day["sky_condition"] == "overcast"
    assert day["temperature_2m_max"] == "34.4 °C"


def test_hourly_builds_records():
    payload = {
        "latitude": 1.0,
        "longitude": 2.0,
        "elevation": 10.0,
        "timezone": "UTC",
        "hourly_units": {"temperature_2m": "°C", "weather_code": "wmo code"},
        "hourly": {
            "time": ["2026-08-08T00:00", "2026-08-08T01:00"],
            "temperature_2m": [20.0, 19.5],
            "weather_code": [0, 1],
        },
    }
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = payload

    with patch("weather_agent.services.weather.requests.get", return_value=mock_resp) as get:
        result = weather.hourly(1.0, 2.0, "2026-08-08", "2026-08-08")

    assert len(result["hourly"]) == 2
    assert result["hourly"][0]["sky_condition"] == "clear sky"
    assert get.call_args.kwargs["params"]["start_date"] == "2026-08-08"
