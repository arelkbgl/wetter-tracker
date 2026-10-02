"""Unit-Tests für wetter/api.py – laufen komplett ohne Internet."""

import pytest
import requests

from wetter.api import fetch_weather, parse_response

# ---------------------------------------------------------------------------
# parse_response: Normalfall
# ---------------------------------------------------------------------------


def test_parse_response_creates_one_dict_per_day(sample_json):
    records = parse_response(sample_json)

    # Zwei Tage in der Antwort -> zwei Dictionaries in der Liste.
    assert len(records) == 2


def test_parse_response_maps_values_correctly(sample_json):
    records = parse_response(sample_json)

    # Der erste Tag muss genau die ersten Werte jeder Liste enthalten.
    assert records[0] == {
        "date": "2026-09-25",
        "temp_max": 20.0,
        "temp_min": 10.0,
        "precipitation": 0.0,
    }
    assert records[1]["precipitation"] == 3.2


# ---------------------------------------------------------------------------
# parse_response: Randfälle
# ---------------------------------------------------------------------------


def test_parse_response_with_no_days_returns_empty_list():
    empty_json = {
        "daily": {
            "time": [],
            "temperature_2m_max": [],
            "temperature_2m_min": [],
            "precipitation_sum": [],
        }
    }
    assert parse_response(empty_json) == []


def test_parse_response_keeps_none_values():
    # Die API liefert null (in Python: None), wenn ein Messwert fehlt.
    # Der Wert soll erhalten bleiben und nicht z. B. zu 0 werden.
    json_with_gap = {
        "daily": {
            "time": ["2026-09-25"],
            "temperature_2m_max": [None],
            "temperature_2m_min": [10.0],
            "precipitation_sum": [None],
        }
    }
    records = parse_response(json_with_gap)
    assert records[0]["temp_max"] is None
    assert records[0]["precipitation"] is None
    assert records[0]["temp_min"] == 10.0


def test_parse_response_without_daily_raises_key_error():
    # Ohne den Block "daily" kann parse_response nichts auswerten.
    # Ein klarer Fehler ist besser, als still eine falsche Liste zu liefern.
    with pytest.raises(KeyError):
        parse_response({})


# parametrize führt denselben Test mehrmals aus, einmal pro Wert in der Liste.
# So prüfen wir jedes Feld einzeln, ohne vier fast gleiche Tests zu schreiben.
@pytest.mark.parametrize(
    "missing_field",
    ["time", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
)
def test_parse_response_with_missing_field_raises_key_error(sample_json, missing_field):
    del sample_json["daily"][missing_field]

    with pytest.raises(KeyError):
        parse_response(sample_json)


def test_parse_response_with_unequal_list_lengths_raises_value_error(sample_json):
    # Issue #1: Fehlt in einer Liste ein Wert, dürfen die übrigen Daten
    # nicht still abgeschnitten werden. Wir erwarten einen klaren Fehler.
    sample_json["daily"]["temperature_2m_max"].pop()  # nur noch 1 statt 2 Werte

    with pytest.raises(ValueError):
        parse_response(sample_json)


# ---------------------------------------------------------------------------
# fetch_weather: HTTP-Aufruf gemockt
# ---------------------------------------------------------------------------


def test_fetch_weather_sends_correct_parameters(mock_api, sample_json):
    calls = mock_api(json_data=sample_json)

    fetch_weather(51.22, 6.78)

    # Genau ein HTTP-Aufruf mit den richtigen Parametern.
    assert len(calls) == 1
    params = calls[0]["params"]
    assert params["latitude"] == 51.22
    assert params["longitude"] == 6.78
    assert params["past_days"] == 7
    assert params["forecast_days"] == 0
    # Ein Timeout muss gesetzt sein, sonst könnte das Programm ewig hängen.
    assert calls[0]["timeout"] is not None


def test_fetch_weather_returns_parsed_records(mock_api, sample_json):
    mock_api(json_data=sample_json)

    records = fetch_weather(51.22, 6.78)

    # Ergebnis muss dasselbe sein, als hätten wir parse_response direkt aufgerufen.
    assert records == parse_response(sample_json)


@pytest.mark.parametrize("status_code", [400, 404, 500, 503])
def test_fetch_weather_raises_on_api_error(mock_api, status_code):
    # Die "API" antwortet mit einem Fehlercode statt mit Daten.
    mock_api(json_data={"error": True, "reason": "Fehler"}, status_code=status_code)

    # fetch_weather soll den Fehler weitergeben und nicht so tun, als ob alles ok wäre.
    with pytest.raises(requests.HTTPError):
        fetch_weather(51.22, 6.78)


def test_fetch_weather_raises_on_connection_error(monkeypatch):
    # Simuliert z. B. fehlendes Internet: requests.get wirft direkt einen Fehler.
    def failing_get(url, params, timeout):
        raise requests.ConnectionError("Keine Verbindung")

    monkeypatch.setattr(requests, "get", failing_get)

    with pytest.raises(requests.ConnectionError):
        fetch_weather(51.22, 6.78)
