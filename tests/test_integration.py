"""Integrationstests: api, parse_response und db arbeiten zusammen.

Unit-Tests prüfen jede Funktion einzeln. Hier prüfen wir, ob die Teile
auch zusammenpassen, z. B. ob die Dictionaries aus parse_response genau
die Schlüssel haben, die save_records erwartet.
Nur das Internet wird ersetzt (gemockt), alles andere läuft echt.
"""

import pytest

import main
from wetter.api import fetch_weather
from wetter.db import average_temperature, get_all_records, init_db, save_records


def test_fetch_save_and_average(mock_api, sample_json, tmp_path):
    mock_api(json_data=sample_json)
    db_path = tmp_path / "test.db"

    # Der komplette Ablauf wie in main.py, nur mit Test-Datenbank.
    init_db(db_path)
    records = fetch_weather(51.22, 6.78)
    save_records(records, db_path)

    rows = get_all_records(db_path)
    assert rows == [
        ("2026-09-25", 20.0, 10.0, 0.0),
        ("2026-09-26", 30.0, 20.0, 3.2),
    ]
    # Tagesmitten 15.0 und 25.0 -> Durchschnitt 20.0
    assert average_temperature(db_path) == pytest.approx(20.0)


def test_main_end_to_end(mock_api, sample_json, tmp_path, monkeypatch, capsys):
    """Startet main() wie "python main.py", aber ohne Internet.

    - monkeypatch.chdir wechselt für diesen Test in den temporären Ordner.
      Da DB_PATH ein relativer Pfad ist, landet wetter.db dort und nicht
      im Projektordner.
    - capsys fängt alles ab, was mit print() ausgegeben wird.
    """
    mock_api(json_data=sample_json)
    monkeypatch.chdir(tmp_path)

    main.main()

    output = capsys.readouterr().out
    assert "2026-09-25" in output
    assert "2026-09-26" in output
    assert "Durchschnittstemperatur: 20.0 °C" in output
    # Die Datenbank wurde wirklich im temporären Ordner angelegt.
    assert (tmp_path / "wetter.db").exists()


def test_main_twice_creates_no_duplicates(mock_api, sample_json, tmp_path, monkeypatch, capsys):
    # Wie zwei Programmstarts hintereinander mit denselben API-Daten.
    mock_api(json_data=sample_json)
    monkeypatch.chdir(tmp_path)

    main.main()
    main.main()

    # get_all_records ohne Pfad nutzt "wetter.db" im aktuellen Ordner (tmp_path).
    assert len(get_all_records()) == 2
