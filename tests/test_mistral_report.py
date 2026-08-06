"""Tests for Mistral report drafting."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from weather_agent.services import mistral_report


def test_draft_report_requires_api_key(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(ValueError, match="MISTRAL_API_KEY"):
        mistral_report.draft_report({"a": 1}, "objetivo")


def test_draft_report_success(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_MODEL", "mistral-small-latest")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Informe de prueba para sábado"}}]
    }

    weather_data = {
        "place": "Granollers",
        "period": {"date": "2026-08-08", "weekday": "Saturday"},
        "forecast": {"daily": []},
    }

    with patch(
        "weather_agent.services.mistral_report.requests.post", return_value=mock_resp
    ) as post:
        text = mistral_report.draft_report(
            weather_data=weather_data,
            objective_prompt="Pronóstico para pasado mañana en Granollers",
            language="Spanish",
        )

    assert text == "Informe de prueba para sábado"
    post.assert_called_once()
    kwargs = post.call_args.kwargs
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    body = kwargs["json"]
    assert body["model"] == "mistral-small-latest"
    assert body["messages"][0]["role"] == "system"
    assert "period" in mistral_report.REPORT_SYSTEM_PROMPT
    user_msg = body["messages"][1]["content"]
    assert "pasado mañana" in user_msg
    assert "2026-08-08" in user_msg
    assert json.loads(
        user_msg.split("Meteorological data (JSON):\n", 1)[1]
    )["period"]["weekday"] == "Saturday"


def test_draft_report_accepts_json_string(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "ok"}}]
    }

    with patch(
        "weather_agent.services.mistral_report.requests.post", return_value=mock_resp
    ):
        text = mistral_report.draft_report(
            weather_data='{"place":"X"}',
            objective_prompt="obj",
        )
    assert text == "ok"


def test_draft_report_empty_content(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": "  "}}]}

    with patch(
        "weather_agent.services.mistral_report.requests.post", return_value=mock_resp
    ):
        with pytest.raises(ValueError, match="empty"):
            mistral_report.draft_report({"a": 1}, "obj")


def test_draft_report_http_error(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("401")

    with patch(
        "weather_agent.services.mistral_report.requests.post", return_value=mock_resp
    ):
        with pytest.raises(requests.HTTPError):
            mistral_report.draft_report({"a": 1}, "obj")
