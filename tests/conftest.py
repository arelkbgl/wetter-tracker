"""Gemeinsame Fixtures für alle Tests.

pytest lädt diese Datei automatisch. Fixtures, die hier definiert sind,
kann jeder Test einfach als Parameter anfordern, ohne sie zu importieren.
"""

import pytest
import requests

from wetter import api


@pytest.fixture
def sample_json():
    """Beispielantwort im gleichen Aufbau wie die echte Open-Meteo-API.

    Zwei Tage mit ausgedachten Werten, die sich leicht nachrechnen lassen:
    Tagesmitten 15.0 und 25.0 -> Durchschnitt 20.0.
    """
    return {
        "daily": {
            "time": ["2026-09-25", "2026-09-26"],
            "temperature_2m_max": [20.0, 30.0],
            "temperature_2m_min": [10.0, 20.0],
            "precipitation_sum": [0.0, 3.2],
        }
    }


class FakeResponse:
    """Nachbau eines requests-Response-Objekts.

    Es hat nur die zwei Methoden, die fetch_weather tatsächlich benutzt.
    """

    def __init__(self, json_data, status_code):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        # Verhält sich wie das Original: Bei 4xx/5xx wird ein HTTPError geworfen.
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error", response=self)

    def json(self):
        return self._json_data


@pytest.fixture
def mock_api(monkeypatch):
    """Ersetzt requests.get durch eine Fake-Funktion (kein Internet nötig).

    Die Fixture gibt eine Funktion zurück, mit der jeder Test selbst
    festlegt, was die "API" antworten soll:

        calls = mock_api(json_data=..., status_code=200)

    In der Liste "calls" landet jeder Aufruf mit seinen Parametern,
    damit der Test prüfen kann, was an die API geschickt wurde.
    """
    calls = []

    def _mock(json_data=None, status_code=200):
        def fake_get(url, params, timeout):
            calls.append({"url": url, "params": params, "timeout": timeout})
            return FakeResponse(json_data, status_code)

        # requests.get innerhalb von wetter/api.py durch fake_get ersetzen.
        # monkeypatch macht das nach dem Test automatisch rückgängig.
        monkeypatch.setattr(api.requests, "get", fake_get)
        return calls

    return _mock
