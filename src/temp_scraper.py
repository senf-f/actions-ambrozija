"""Scrape daily maximum air temperature and sea temperature (08h) from DHMZ XML feeds."""
import datetime
import xml.etree.ElementTree as ET

import requests

from src import db_handler
from src.config import (
    AIR_STATIONS,
    SEA_HOUR,
    SEA_STATIONS,
    SEA_URL,
    TMAX_URL,
)


def _iso(datum):
    return datetime.datetime.strptime(datum.strip().rstrip("."), "%d.%m.%Y").date().isoformat()


def _float(text):
    """DHMZ uses padded numbers and '-' / empty for missing readings."""
    try:
        return float((text or "").strip())
    except ValueError:
        return None


def parse_tmax(xml_text):
    """Parse tx.xml. Returns (iso_date, termin, [(station, city, temp_max_c), ...]).

    `datum` is the day the maxima belong to, which is normally yesterday — the
    file is published after its cut-off and then served all of the next day.
    Callers must store against it rather than against today's date.
    """
    root = ET.fromstring(xml_text)
    iso_date = _iso(root.findtext("datumtermin/datum", ""))
    termin = root.findtext("datumtermin/termin", "").strip().zfill(2)

    rows = []
    for grad in root.findall("grad"):
        station = (grad.findtext("ime") or "").strip()
        if station not in AIR_STATIONS:
            continue
        temp = _float(grad.findtext("tempmax"))
        if temp is not None:
            rows.append((station, AIR_STATIONS[station], temp))
    return iso_date, termin, rows


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
    # bytes, not resp.text: DHMZ sends no charset, so requests would
    # decode the UTF-8 feed as ISO-8859-1 and mangle station names.
    return resp.content


def main():
    conn = db_handler.setup_db()
    try:
        # A daily maximum does not depend on when we run, so a late run is
        # harmless as long as the row is filed under the feed's own date.
        date, termin, rows = parse_tmax(_get(TMAX_URL))
        for station, city, temp in rows:
            db_handler.insert_into_air_temp_db(conn, station, city, temp, termin, date)
        print(f"[air max] {date} (termin {termin}h): stored {len(rows)} station(s)")

        date, rows = parse_sea(_get(SEA_URL))
        for station, temp in rows:
            db_handler.insert_into_sea_temp_db(conn, station, temp, SEA_HOUR, date)
        print(f"[sea] {date} {SEA_HOUR}h: stored {len(rows)} station(s)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
