"""Tests for WeatherAgent tools and registration."""

from __future__ import annotations

import datetime
import json
from unittest.mock import patch

from gaia.agents.base.tools import _TOOL_REGISTRY

from weather_agent import build_registration
from weather_agent.agent import WeatherAgent, WeatherAgentConfig


def test_build_registration():
    reg = build_registration()
    assert reg.id == "weather_agent"
    assert reg.tools_count == 6


def test_system_prompt_requires_period_in_weather_data():
    agent = WeatherAgent(WeatherAgentConfig(silent_mode=True))
    prompt = agent._get_system_prompt()
    assert "period" in prompt
    assert "draft_weather_report" in prompt
    assert "Never repeat a tool call" in prompt


def test_registered_tools():
    WeatherAgent(WeatherAgentConfig(silent_mode=True))
    expected = {
        "date_from_today",
        "resolve_place",
        "get_current_weather",
        "get_hourly_forecast",
        "get_daily_forecast",
        "draft_weather_report",
    }
    assert expected.issubset(set(_TOOL_REGISTRY.keys()))


def test_date_from_today_tool():
    WeatherAgent(WeatherAgentConfig(silent_mode=True))
    tool_fn = _TOOL_REGISTRY["date_from_today"]["function"]
    result = tool_fn(days_offset=2)
    expected = datetime.date.today() + datetime.timedelta(days=2)
    assert result["date"] == expected.strftime("%Y-%m-%d")
    assert result["weekday"] == expected.strftime("%A")


def test_draft_weather_report_tool_calls_mistral():
    WeatherAgent(WeatherAgentConfig(silent_mode=True))
    tool_fn = _TOOL_REGISTRY["draft_weather_report"]["function"]
    payload = {
        "place": "Granollers",
        "period": {"date": "2026-08-08", "weekday": "Saturday"},
        "forecast": {"daily": []},
    }

    with patch(
        "weather_agent.services.mistral_report.draft_report",
        return_value="Informe sábado",
    ) as draft:
        out = tool_fn(
            weather_data=json.dumps(payload),
            objective_prompt="Pronóstico para pasado mañana en Granollers",
            language="Spanish",
        )

    assert out == {"report": "Informe sábado"}
    draft.assert_called_once()
    kwargs = draft.call_args.kwargs
    assert kwargs["language"] == "Spanish"
    assert kwargs["weather_data"]["period"]["weekday"] == "Saturday"
    assert "pasado mañana" in kwargs["objective_prompt"]
