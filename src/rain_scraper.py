import datetime
import xml.etree.ElementTree as ET

import requests

from src import db_handler
from src.config import RAIN_CITIES, RAIN_URL


def parse_rain(xml_text):
    """Parse oborina.xml, keeping only RAIN_CITIES stations.

    Returns (iso_date, [(station, city, mm), ...]).
    """
    root = ET.fromstring(xml_text)
    datum = root.findtext("datumtermin/datum", "").strip().rstrip(".")
    iso_date = datetime.datetime.strptime(datum, "%d.%m.%Y").date().isoformat()

    rows = []
    for grad in root.findall("grad"):
        station = (grad.findtext("ime") or "").strip()
        city = station.split("-")[0].strip()
        if city not in RAIN_CITIES:
            continue
        rows.append((station, city, float(grad.findtext("kolicina"))))
    return iso_date, rows


def main():
    conn = db_handler.setup_db()
    try:
        resp = requests.get(RAIN_URL, timeout=30)
        resp.raise_for_status()
        date, rows = parse_rain(resp.text)
        for station, city, mm in rows:
            db_handler.insert_into_rain_db(conn, station, city, mm, date)
        print(f"[rain] {date}: stored {len(rows)} station(s)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
