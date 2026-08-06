"""WeatherAgent — GAIA agent that writes text weather forecast reports."""

from __future__ import annotations

import datetime
import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from gaia.agents.base.agent import Agent
from gaia.agents.base.console import AgentConsole
from gaia.agents.base.tools import _TOOL_REGISTRY, tool

from weather_agent.services import geocode, mistral_report, weather


@dataclass
class WeatherAgentConfig:
    base_url: Optional[str] = "http://ai.core.lan:8080/api/v1"
    model_id: Optional[str] = "Gemma-4-E4B-it-GGUF"
    max_steps: int = 10
    streaming: bool = False
    debug: bool = False
    show_stats: bool = False
    silent_mode: bool = False
    output_dir: Optional[str] = None


class WeatherAgent(Agent):
    """GAIA agent that produces weather forecast text reports."""

    AGENT_ID = "weather_agent"
    AGENT_NAME = "weather_agent"
    AGENT_DESCRIPTION = (
        "Generates text weather forecast reports for a place and time, "
        "in the language requested by the user"
    )
    CONVERSATION_STARTERS = [
        "What is the weather tomorrow in Valencia?",
        "Weather in Berlin this weekend in English",
        "¿Qué tiempo hace ahora en Madrid?",
    ]

    def __init__(self, config: Optional[WeatherAgentConfig] = None):
        config = config or WeatherAgentConfig()
        super().__init__(
            base_url=config.base_url
            or os.getenv("LEMONADE_BASE_URL", "http://ai.core.lan:8080/api/v1"),
            model_id=config.model_id or "Gemma-4-E4B-it-GGUF",
            max_steps=config.max_steps,
            streaming=config.streaming,
            debug=config.debug,
            show_stats=config.show_stats,
            silent_mode=config.silent_mode,
            output_dir=config.output_dir,
        )

    def _get_system_prompt(self) -> str:
        return """
You are a weather data orchestrator. Collect data with tools, then call
draft_weather_report (Mistral). Never write the report yourself.

WORKFLOW (follow in order; do each step at most once for the same args):
1) date_from_today — map relative days ("hoy"=0, "mañana"=1, "pasado mañana"=2).
   Save date+weekday. Do NOT call date_from_today again with the same days_offset.
2) resolve_place — get lat/lon/display_name.
3) get_current_weather and/or get_daily_forecast / get_hourly_forecast using
   those coordinates and dates.
4) draft_weather_report once, then answer with ONLY its "report" field.

LANGUAGE: pass the user's language to draft_weather_report; default Spanish.

DATA RULES:
- Never invent dates, weekdays, coordinates, or weather values.
- Prefer daily forecast for a day; hourly only if the user asks hour by hour.

draft_weather_report arguments:
- weather_data: JSON string exactly like
  {"place":"<display_name>","period":{"date":"<from date_from_today>",
  "weekday":"<from date_from_today>"},"forecast":<weather tool result>}
  For a multi-day range, period is a list of {date, weekday}.
- objective_prompt: short user intent without weekdays or YYYY-MM-DD dates
  (e.g. "Pronóstico para pasado mañana en Granollers").
- language: report language

After draft_weather_report returns, your final answer MUST be exactly report.
Never repeat a tool call that already succeeded with the same arguments.
""".strip()

    def _create_console(self):
        return AgentConsole()

    def _register_tools(self):
        _TOOL_REGISTRY.clear()

        @tool
        def date_from_today(days_offset: int) -> dict[str, str]:
            """Compute a calendar date relative to today.

            Call once per days_offset. After you get the result, proceed to
            resolve_place / weather tools — do not call this again with the
            same days_offset.

            Args:
                days_offset: Days to add to today. 0 = today, positive = future,
                    negative = past.

            Returns:
                Dict with date (YYYY-MM-DD) and weekday (English ISO name).
                Copy these fields into weather_data.period for draft_weather_report.
            """
            target = datetime.date.today() + datetime.timedelta(days=int(days_offset))
            return {
                "date": target.strftime("%Y-%m-%d"),
                "weekday": target.strftime("%A"),
            }

        @tool
        def resolve_place(place: str) -> dict[str, Any]:
            """Geocode a place name to latitude and longitude.

            Use this before any weather tool. Accept city, region, or
            "City, Country" strings.

            Args:
                place: Location text, e.g. "Valencia", "Berlin, Germany".

            Returns:
                Dict with lat, lon and display_name.
            """
            return geocode.resolve_location(place)

        @tool
        def get_current_weather(lat: float, lon: float) -> dict[str, Any]:
            """Fetch current weather conditions for coordinates.

            Args:
                lat: Latitude from resolve_place.
                lon: Longitude from resolve_place.

            Returns:
                Sanitized current weather dict (sky_condition, temperature, etc.).
            """
            return weather.current(float(lat), float(lon))

        @tool
        def get_hourly_forecast(
            lat: float, lon: float, start_date: str, end_date: str
        ) -> dict[str, Any]:
            """Fetch hourly forecast between two dates (inclusive).

            Args:
                lat: Latitude from resolve_place.
                lon: Longitude from resolve_place.
                start_date: Start date YYYY-MM-DD (from date_from_today).
                end_date: End date YYYY-MM-DD (from date_from_today).

            Returns:
                Hourly weather records for the range.
            """
            return weather.hourly(float(lat), float(lon), start_date, end_date)

        @tool
        def get_daily_forecast(
            lat: float, lon: float, start_date: str, end_date: str
        ) -> dict[str, Any]:
            """Fetch daily forecast between two dates (inclusive).

            Args:
                lat: Latitude from resolve_place.
                lon: Longitude from resolve_place.
                start_date: Start date YYYY-MM-DD (from date_from_today).
                end_date: End date YYYY-MM-DD (from date_from_today).

            Returns:
                Daily weather records including sunrise/sunset when available.
            """
            return weather.daily(float(lat), float(lon), start_date, end_date)

        @tool
        def draft_weather_report(
            weather_data: str,
            objective_prompt: str,
            language: str = "Spanish",
        ) -> dict[str, str]:
            """Draft the final weather report text via Mistral.

            Call this AFTER date_from_today + weather tools. Dates and weekdays
            must come from date_from_today inside weather_data.period.
            Return the "report" field EXACTLY as the final user answer.

            Args:
                weather_data: JSON string shaped as
                    {"place": "...", "period": {"date": "YYYY-MM-DD",
                    "weekday": "...from date_from_today..."}, "forecast": {...}}.
                    For ranges, period may be a list of {date, weekday}.
                objective_prompt: User request in natural language (place,
                    relative period, tone). Do NOT include weekdays or absolute
                    calendar dates; those are only in weather_data.period.
                language: Language for the report. Default Spanish.

            Returns:
                Dict with key "report" containing the finished text.
            """
            try:
                parsed: Any = json.loads(weather_data)
            except (TypeError, json.JSONDecodeError):
                parsed = weather_data

            report = mistral_report.draft_report(
                weather_data=parsed,
                objective_prompt=objective_prompt,
                language=language or "Spanish",
            )
            return {"report": report}
