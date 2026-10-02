"""Speichern und Auswerten der Wetterdaten in einer SQLite-Datenbank.

SQLite ist in Python bereits eingebaut (Modul sqlite3) und speichert
die ganze Datenbank in einer einzigen Datei.
"""

import sqlite3
from pathlib import Path

# Pfad zur Datenbankdatei. Sie wird beim ersten Zugriff automatisch angelegt.
# __file__ ist der Pfad dieser Datei (wetter/db.py). .parent.parent geht zwei
# Ebenen hoch zum Projektordner. So liegt die Datenbank immer dort, egal aus
# welchem Ordner das Programm gestartet wird.
DB_PATH = Path(__file__).resolve().parent.parent / "wetter.db"


def get_connection(db_path=None):
    """Öffnet eine Verbindung zur Datenbank.

    Ohne Angabe wird DB_PATH verwendet. Wir lesen DB_PATH bewusst erst hier
    beim Aufruf (und nicht als Standardwert db_path=DB_PATH), damit Tests
    den Pfad mit monkeypatch auf eine Test-Datenbank umbiegen können.
    """
    if db_path is None:
        db_path = DB_PATH
    return sqlite3.connect(db_path)


def init_db(db_path=None):
    """Legt die Tabelle an, falls sie noch nicht existiert."""
    # "with" sorgt dafür, dass Änderungen am Ende gespeichert (commit) werden.
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weather (
                date          TEXT PRIMARY KEY,  -- z. B. '2026-09-25', pro Tag nur eine Zeile
                temp_max      REAL,              -- Höchsttemperatur in °C
                temp_min      REAL,              -- Tiefsttemperatur in °C
                precipitation REAL               -- Niederschlag in mm
            )
            """
        )
    # Hinweis: "with" schließt die Verbindung nicht, das machen wir selbst.
    conn.close()


def save_records(records, db_path=None):
    """Speichert eine Liste von Tageswerten (Upsert).

    Gibt es für ein Datum schon eine Zeile, werden ihre Werte
    überschrieben, statt eine zweite Zeile anzulegen.
    """
    with get_connection(db_path) as conn:
        # executemany führt die Anweisung einmal pro Dictionary aus.
        # :date, :temp_max usw. werden durch die Werte aus dem Dictionary
        # ersetzt. Solche Platzhalter schützen vor SQL-Injection.
        conn.executemany(
            """
            INSERT INTO weather (date, temp_max, temp_min, precipitation)
            VALUES (:date, :temp_max, :temp_min, :precipitation)
            ON CONFLICT(date) DO UPDATE SET
                temp_max      = excluded.temp_max,
                temp_min      = excluded.temp_min,
                precipitation = excluded.precipitation
            """,
            records,
        )
        # "excluded" steht für die Zeile, die wir gerade einfügen wollten.
    conn.close()


def average_temperature(db_path=None):
    """Berechnet die Durchschnittstemperatur über alle gespeicherten Tage.

    Pro Tag nehmen wir die Mitte aus Höchst- und Tiefstwert und bilden
    davon den Durchschnitt. Gibt None zurück, wenn die Tabelle leer ist.
    """
    conn = get_connection(db_path)
    # AVG ignoriert Zeilen, in denen ein Wert fehlt (NULL).
    row = conn.execute(
        "SELECT AVG((temp_max + temp_min) / 2.0) FROM weather"
    ).fetchone()
    conn.close()

    # fetchone() liefert ein Tupel mit einem Element, z. B. (14.2,).
    return row[0]


def get_all_records(db_path=None):
    """Gibt alle gespeicherten Tage sortiert nach Datum zurück."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT date, temp_max, temp_min, precipitation FROM weather ORDER BY date"
    ).fetchall()
    conn.close()
    return rows
