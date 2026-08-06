"""Draft weather report text via Mistral Chat Completions API."""

from __future__ import annotations

import json
import os
from typing import Any

import requests

MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = "mistral-small-latest"

REPORT_SYSTEM_PROMPT = """
You are a meteorologist that writes clear text weather forecast reports.

Write the report in the language indicated by the user message.
If no language is specified, write in Spanish.

Use ONLY the meteorological JSON provided. Never invent values.
Omit any variable that is missing, empty, or zero.

DATES AND WEEKDAYS (source of truth):
- The JSON includes "period" with "date" (YYYY-MM-DD) and "weekday" from a
  calendar tool. Treat period as the only truth for which day it is.
- When naming the weekday in the report language, translate period.weekday
  (e.g. Saturday → sábado). Never invent a different weekday.
- Ignore any weekday or absolute date mentioned in the Objective if it
  conflicts with period; prefer period.
- Use "place" from the JSON for the location name when present.
- Weather variables are under "forecast" (or at the top level if forecast is absent).

REPORT STRUCTURE (in this order, only when data is available):
1. Sky / weather condition for the location (mention place + date/weekday from period)
2. Temperature
3. Apparent temperature (feels like)
4. Humidity
5. Rain / precipitation
6. Snow
7. Atmospheric pressure
8. Cloud cover
9. Wind
10. Sunrise
11. Sunset
12. Short health and leisure recommendations based on the data

FORMAT:
- Express sky condition and key variables with a short icon/emoji plus descriptive text when helpful.
- Keep the report readable as plain text; do not dump raw JSON.
""".strip()


def draft_report(
    weather_data: Any,
    objective_prompt: str,
    language: str = "Spanish",
) -> str:
    """Call Mistral to draft a weather report from meteorological data.

    Args:
        weather_data: Dict or JSON string with weather variables.
        objective_prompt: Goal for the report (place, period, tone, etc.).
        language: Language for the report text.

    Returns:
        Report text from Mistral.

    Raises:
        ValueError: If MISTRAL_API_KEY is missing or the response has no content.
        requests.HTTPError: On HTTP failures from the Mistral API.
    """
    api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY is not set. Export it before drafting reports."
        )

    model = os.getenv("MISTRAL_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    if isinstance(weather_data, str):
        payload_data = weather_data
    else:
        payload_data = json.dumps(weather_data, ensure_ascii=False)

    user_content = (
        f"Language: {language}\n\n"
        f"Objective:\n{objective_prompt}\n\n"
        f"Meteorological data (JSON):\n{payload_data}"
    )

    response = requests.post(
        MISTRAL_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
        },
        timeout=60,
    )
    response.raise_for_status()
    body = response.json()

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected Mistral response shape: {body!r}") from exc

    if not content or not str(content).strip():
        raise ValueError("Mistral returned an empty report")

    return str(content).strip()
