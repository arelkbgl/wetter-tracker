"""Tests für wetter/db.py.

Jeder Test bekommt über die pytest-Fixture "tmp_path" einen eigenen,
leeren temporären Ordner. Dort legen wir eine Test-Datenbank an, damit
die echte wetter.db nie verändert wird.
"""

from pathlib import Path

import pytest

from wetter import db
from wetter.db import average_temperature, get_all_records, init_db, save_records

# Projektordner = eine Ebene über dem Ordner tests/, in dem diese Datei liegt.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def db_path(tmp_path):
    """Erstellt eine frische Test-Datenbank und gibt ihren Pfad zurück.

    Jeder Test, der "db_path" als Parameter hat, bekommt diesen Pfad
    automatisch von pytest übergeben.
    """
    path = tmp_path / "test.db"
    init_db(path)
    return path


def make_record(date, temp_max, temp_min, precipitation=0.0):
    """Kleine Hilfsfunktion, damit die Tests kürzer und lesbarer sind."""
    return {
        "date": date,
        "temp_max": temp_max,
        "temp_min": temp_min,
        "precipitation": precipitation,
    }


def test_save_records_stores_all_days(db_path):
    records = [
        make_record("2026-09-25", 20.0, 10.0),
        make_record("2026-09-26", 22.0, 12.0),
    ]
    save_records(records, db_path)

    rows = get_all_records(db_path)
    assert len(rows) == 2
    # Jede Zeile ist ein Tupel: (date, temp_max, temp_min, precipitation)
    assert rows[0] == ("2026-09-25", 20.0, 10.0, 0.0)


def test_save_records_twice_creates_no_duplicates(db_path):
    records = [make_record("2026-09-25", 20.0, 10.0)]

    # Zweimal dieselben Daten speichern, wie bei zwei Programmstarts.
    save_records(records, db_path)
    save_records(records, db_path)

    assert len(get_all_records(db_path)) == 1


def test_save_records_updates_existing_day(db_path):
    save_records([make_record("2026-09-25", 20.0, 10.0)], db_path)
    # Gleiches Datum, neue Werte -> die alte Zeile soll überschrieben werden.
    save_records([make_record("2026-09-25", 25.0, 15.0, 4.2)], db_path)

    rows = get_all_records(db_path)
    assert rows == [("2026-09-25", 25.0, 15.0, 4.2)]


def test_average_temperature(db_path):
    save_records(
        [
            make_record("2026-09-25", 20.0, 10.0),  # Tagesmitte: 15.0
            make_record("2026-09-26", 30.0, 20.0),  # Tagesmitte: 25.0
        ],
        db_path,
    )
    # Durchschnitt aus 15.0 und 25.0 = 20.0
    # pytest.approx vergleicht Kommazahlen mit kleiner Toleranz,
    # weil Fließkommazahlen manchmal minimal ungenau sind.
    assert average_temperature(db_path) == pytest.approx(20.0)


def test_average_temperature_empty_db_returns_none(db_path):
    assert average_temperature(db_path) is None


def test_average_temperature_ignores_days_with_missing_values(db_path):
    save_records(
        [
            make_record("2026-09-25", 20.0, 10.0),  # Tagesmitte: 15.0
            make_record("2026-09-26", None, 12.0),  # fehlt -> wird ignoriert
        ],
        db_path,
    )
    assert average_temperature(db_path) == pytest.approx(15.0)


def test_db_path_points_to_project_folder_from_any_cwd(tmp_path, monkeypatch):
    # Issue #2: Wir simulieren, dass main.py aus einem anderen Ordner
    # gestartet wird, indem wir das Arbeitsverzeichnis wechseln.
    monkeypatch.chdir(tmp_path)

    # resolve() macht aus dem Pfad einen absoluten Pfad. Bei einem relativen
    # Pfad hängt das Ergebnis vom aktuellen Arbeitsverzeichnis ab, bei einem
    # korrekten Pfad zeigt er trotzdem immer in den Projektordner.
    assert Path(db.DB_PATH).resolve() == PROJECT_ROOT / "wetter.db"
