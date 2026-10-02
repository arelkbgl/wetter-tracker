"""Einstiegspunkt: Wetter für Düsseldorf abrufen, speichern und ausgeben."""

from wetter.api import fetch_weather
from wetter.db import average_temperature, get_all_records, init_db, save_records

# Koordinaten von Düsseldorf
LAT = 51.22
LON = 6.78


def main():
    # 1. Tabelle anlegen (passiert nur beim allerersten Start wirklich).
    init_db()

    # 2. Daten der letzten 7 Tage aus dem Internet holen.
    records = fetch_weather(LAT, LON)

    # 3. In der Datenbank speichern (bereits vorhandene Tage werden aktualisiert).
    save_records(records)

    # 4. Alle gespeicherten Tage als Tabelle ausgeben.
    #    :<12 bedeutet "linksbündig, 12 Zeichen breit", :>8 "rechtsbündig, 8 breit".
    #    str() sorgt dafür, dass auch fehlende Werte (None) ausgegeben werden können.
    print(f"{'Datum':<12}{'Max °C':>8}{'Min °C':>8}{'Regen mm':>10}")
    for date, temp_max, temp_min, precipitation in get_all_records():
        print(f"{date:<12}{str(temp_max):>8}{str(temp_min):>8}{str(precipitation):>10}")

    # 5. Durchschnitt per SQL berechnen lassen und ausgeben.
    avg = average_temperature()
    if avg is None:
        print("\nKeine Daten vorhanden.")
    else:
        # :.1f rundet auf eine Nachkommastelle.
        print(f"\nDurchschnittstemperatur: {avg:.1f} °C")


# Dieser Block läuft nur, wenn die Datei direkt gestartet wird
# (python main.py), nicht wenn sie von einer anderen Datei importiert wird.
if __name__ == "__main__":
    main()
