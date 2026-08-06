"""Tests for Nominatim geocoding."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from weather_agent.services import geocode


def test_resolve_location_success(nominatim_hit):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = nominatim_hit

    with patch("weather_agent.services.geocode.requests.get", return_value=mock_resp) as get:
        result = geocode.resolve_location("Granollers")

    assert result["lat"] == 41.6079555
    assert result["lon"] == 2.2876008
    assert "Granollers" in result["display_name"]
    get.assert_called_once()
    kwargs = get.call_args.kwargs
    assert kwargs["params"]["q"] == "Granollers"
    assert kwargs["params"]["format"] == "json"
    assert "User-Agent" in kwargs["headers"]


def test_resolve_location_empty_place():
    with pytest.raises(ValueError, match="empty"):
        geocode.resolve_location("   ")


def test_resolve_location_not_found():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = []

    with patch("weather_agent.services.geocode.requests.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="No coordinates"):
            geocode.resolve_location("CiudadInventadaXYZ")


def test_resolve_location_http_error():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("503")

    with patch("weather_agent.services.geocode.requests.get", return_value=mock_resp):
        with pytest.raises(requests.HTTPError):
            geocode.resolve_location("Madrid")
