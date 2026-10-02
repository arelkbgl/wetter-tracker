# wetter-tracker

[![Tests](https://github.com/arelkbgl/wetter-tracker/actions/workflows/tests.yml/badge.svg)](https://github.com/arelkbgl/wetter-tracker/actions/workflows/tests.yml)

Ein kleines Python-Projekt, das Wetterdaten abruft, speichert und auswertet.

## Was das Projekt macht

```
Open-Meteo API  →  JSON  →  Liste von Dictionaries  →  SQLite  →  SQL-Auswertung
```

1. **Abruf:** `wetter/api.py` holt über die kostenlose [Open-Meteo-API](https://open-meteo.com/) (ohne API-Key) die Tageswerte der letzten 7 Tage für Düsseldorf: Datum, Höchst- und Tiefsttemperatur sowie Niederschlag.
2. **Verarbeitung:** `parse_response` wandelt die JSON-Antwort in eine Liste von Dictionaries um. Diese Funktion ist bewusst vom HTTP-Aufruf getrennt, damit sie ohne Internet testbar ist.
3. **Speicherung:** `wetter/db.py` speichert die Daten in einer SQLite-Datenbank. Ein Upsert sorgt dafür, dass es pro Datum nur eine Zeile gibt, auch wenn das Programm mehrmals läuft.
4. **Auswertung:** Die Durchschnittstemperatur wird direkt per SQL (`AVG`) berechnet.

## Installation und Ausführung

Voraussetzung: Python 3.13. Befehle für Windows (PowerShell):

```powershell
git clone https://github.com/arelkbgl/wetter-tracker.git
cd wetter-tracker

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python main.py
```

Beispielausgabe:

```
Datum         Max °C  Min °C  Regen mm
2026-09-25      22.2    10.4       0.0
2026-09-26      22.4    13.0       0.0
...
Durchschnittstemperatur: 20.7 °C
```

## Teststrategie

Die Tests sind mit **pytest** geschrieben und laufen **komplett ohne Internet**. Insgesamt sind es **27 Tests**.

| Ebene | Datei | Was geprüft wird |
|---|---|---|
| Unit-Tests | `tests/test_api.py` | `parse_response` und `fetch_weather` isoliert |
| Unit-Tests | `tests/test_db.py` | Speichern, Upsert, Durchschnitt, Datenbankpfad |
| Integrationstests | `tests/test_integration.py` | API, Parsing und Datenbank zusammen |
| End-to-End-Tests | `tests/test_integration.py` | `main()` komplett inkl. Konsolenausgabe |

- **Mocking:** Der HTTP-Aufruf (`requests.get`) wird mit `monkeypatch` durch eine Fake-Funktion ersetzt. Dadurch sind die Tests schnell, stabil und unabhängig von der echten API.
- **Isolation:** Jeder Datenbanktest nutzt über `tmp_path` eine eigene temporäre Datenbank. Die echte `wetter.db` wird nie verändert.
- **Randfälle:** leere Daten, fehlende Felder, `None`-Werte, ungleich lange Listen, leere Datenbank, doppeltes Speichern sowie HTTP-Fehler (400, 404, 500, 503) und Verbindungsabbrüche.
- **Gemeinsame Fixtures** (Beispiel-JSON, gemockte API, Test-Datenbank) liegen in `tests/conftest.py`. Mit `pytest.mark.parametrize` wird ein Test für mehrere Eingaben ausgeführt.

Tests ausführen:

```powershell
pytest -v
```

Bei jedem Push und Pull Request auf `main` laufen die Tests automatisch über GitHub Actions (siehe Badge oben).

## Qualitätsprozess

Gefundene Fehler werden als GitHub-Issues dokumentiert und per **Test-Driven Development** behoben:

1. 🔴 **Rot:** Zuerst einen Test schreiben, der den Fehler nachweist. Er muss fehlschlagen.
2. 🟢 **Grün:** Dann den Code so ändern, dass der Test (und alle bestehenden Tests) bestehen.

Bisher behoben:

- [Issue #1](https://github.com/arelkbgl/wetter-tracker/issues/1): `zip()` hat bei ungleich langen API-Listen Daten still abgeschnitten. Jetzt wird mit `zip(..., strict=True)` ein Fehler ausgelöst.
- [Issue #2](https://github.com/arelkbgl/wetter-tracker/issues/2): Der Datenbankpfad war relativ zum Arbeitsverzeichnis. Jetzt ist er relativ zum Projektordner (`Path(__file__)`).

## Entwicklung mit KI

Das Projekt wurde mit **Claude Code** als Coding Agent entwickelt. Ich habe die Anforderungen, die Teststrategie und das Review übernommen.

## Projektstruktur

```
wetter-tracker/
├── .github/workflows/tests.yml   # CI: Tests bei Push und Pull Request
├── wetter/
│   ├── api.py                    # Abruf und Parsing der Open-Meteo-Daten
│   └── db.py                     # SQLite: Speichern, Upsert, Auswertung
├── tests/
│   ├── conftest.py               # gemeinsame Fixtures
│   ├── test_api.py
│   ├── test_db.py
│   └── test_integration.py
├── main.py                       # Einstiegspunkt
├── pytest.ini
└── requirements.txt
```
