"""Abruf von Wetterdaten über die kostenlose Open-Meteo-API.

Der HTTP-Aufruf (fetch_weather) ist bewusst von der Verarbeitung der
Antwort (parse_response) getrennt. So lässt sich parse_response ohne
Internetverbindung mit selbst gebauten Beispieldaten testen.
"""

import requests

# Basis-URL der Open-Meteo-Vorhersage-API (kein API-Key nötig).
API_URL = "https://api.open-meteo.com/v1/forecast"

# Nach so vielen Sekunden bricht die Anfrage ab, statt ewig zu warten.
TIMEOUT_SECONDS = 10


def fetch_weather(lat, lon):
    """Ruft die täglichen Wetterwerte der letzten 7 Tage ab.

    Gibt eine Liste von Dictionaries zurück (siehe parse_response).
    """
    # Diese Parameter hängt requests automatisch als ?key=value&... an die URL.
    params = {
        "latitude": lat,
        "longitude": lon,
        # Welche Tageswerte wir haben möchten:
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        # 7 vergangene Tage, aber keine Vorhersage für die Zukunft:
        "past_days": 7,
        "forecast_days": 0,
        # Zeitzone, damit die Tage nach deutscher Zeit eingeteilt werden.
        "timezone": "Europe/Berlin",
    }

    response = requests.get(API_URL, params=params, timeout=TIMEOUT_SECONDS)

    # Wirft eine Exception, wenn der Server einen Fehler meldet (z. B. 400 oder 500).
    response.raise_for_status()

    # Die Antwort ist JSON; .json() macht daraus ein Python-Dictionary.
    return parse_response(response.json())


def parse_response(json_data):
    """Wandelt die API-Antwort in eine Liste von Dictionaries um.

    Die API liefert die Werte spaltenweise, also je eine Liste pro Messgröße:
        {"daily": {"time": [...], "temperature_2m_max": [...], ...}}

    Wir machen daraus eine Liste mit einem Dictionary pro Tag:
        [{"date": "2026-09-25", "temp_max": 18.3, "temp_min": 9.1,
          "precipitation": 0.4}, ...]
    """
    daily = json_data["daily"]

    records = []
    # zip() geht die vier Listen parallel durch: erstes Element jeder Liste,
    # dann das zweite usw. So gehören Datum und Werte immer zusammen.
    # strict=True: Sind die Listen unterschiedlich lang, wirft zip einen
    # ValueError, statt die überzähligen Werte still wegzulassen.
    for date, temp_max, temp_min, precipitation in zip(
        daily["time"],
        daily["temperature_2m_max"],
        daily["temperature_2m_min"],
        daily["precipitation_sum"],
        strict=True,
    ):
        records.append(
            {
                "date": date,
                "temp_max": temp_max,
                "temp_min": temp_min,
                "precipitation": precipitation,
            }
        )

    return records
