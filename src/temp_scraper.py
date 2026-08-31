"""Scrape air temperature (15h) and sea temperature (08h) from DHMZ XML feeds."""
import datetime
import xml.etree.ElementTree as ET

import requests

from src import db_handler
from src.config import (
    AIR_HOUR,
    AIR_STATIONS,
    AIR_URL,
    SEA_HOUR,
    SEA_STATIONS,
    SEA_URL,
)


def _iso(datum):
    return datetime.datetime.strptime(datum.strip().rstrip("."), "%d.%m.%Y").date().isoformat()


def _float(text):
    """DHMZ uses padded numbers and '-' / empty for missing readings."""
    try:
        return float((text or "").strip())
    except ValueError:
        return None


def parse_air(xml_text):
    """Parse hrvatska_n.xml. Returns (iso_date, hour, [(station, city, temp_c), ...]).

    The feed only ever holds the latest measurement hour, so the caller must
    check `hour` before trusting the rows.
    """
    root = ET.fromstring(xml_text)
    iso_date = _iso(root.findtext("DatumTermin/Datum", ""))
    hour = root.findtext("DatumTermin/Termin", "").strip().zfill(2)

    rows = []
    for grad in root.findall("Grad"):
        station = (grad.findtext("GradIme") or "").strip()
        if station not in AIR_STATIONS:
            continue
        temp = _float(grad.findtext("Podatci/Temp"))
        if temp is not None:
            rows.append((station, AIR_STATIONS[station], temp))
    return iso_date, hour, rows


def parse_sea(xml_text, hour=SEA_HOUR):
    """Parse more_n.xml, which holds every measurement hour of the day at once.

    Returns (iso_date, [(station, temp_c), ...]) for the requested hour.
    """
    root = ET.fromstring(xml_text)
    iso_date = _iso(root.findtext("Datum", ""))

    blocks = root.findall("Podatci")
    header = [t.text.strip().zfill(2) for t in blocks[0].findall("Termin") if t.text]
    col = header.index(hour)

    rows = []
    for block in blocks[1:]:
        station = (block.findtext("Postaja") or "").strip()
        if station not in SEA_STATIONS:
            continue
        temp = _float(block.findall("Termin")[col].text)
        if temp is not None:
            rows.append((station, temp))
    return iso_date, rows


def _get(url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def main():
    conn = db_handler.setup_db()
    try:
        date, hour, rows = parse_air(_get(AIR_URL))
        if hour != AIR_HOUR:
            print(f"[air] skipped: feed is at {hour}h, want {AIR_HOUR}h")
        else:
            for station, city, temp in rows:
                db_handler.insert_into_air_temp_db(conn, station, city, temp, hour, date)
            print(f"[air] {date} {hour}h: stored {len(rows)} station(s)")

        date, rows = parse_sea(_get(SEA_URL))
        for station, temp in rows:
            db_handler.insert_into_sea_temp_db(conn, station, temp, SEA_HOUR, date)
        print(f"[sea] {date} {SEA_HOUR}h: stored {len(rows)} station(s)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
