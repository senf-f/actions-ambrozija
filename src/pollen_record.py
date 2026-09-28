"""Where a scrape lands: the monthly CSVs under data/ and the pollen_data table.

The CSVs are the source backfill_db rebuilds the table from, so writing and
reading their layout live here together.
"""
import csv
import os
import re

from src.biljke import BILJKA_LOOKUP, Biljka
from src.config import BASE_DIR

DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_HEADER = ["pollen_concentration", "timestamp"]
FILENAME_RE = re.compile(r'^(.+?) - (.+) pelud za (\d+)\.(\d+)(\.csv)?$')
UPSERT = ("INSERT OR REPLACE INTO pollen_data "
          "(city, plant, pollen_concentration, date) VALUES (?, ?, ?, ?)")


def csv_path(data_dir, city, plant, day):
    """Known species are filed under their enum name, new ones under the full name."""
    name = BILJKA_LOOKUP.get(plant, plant)
    return os.path.join(data_dir, str(day.year), str(day.month),
                        f"{city} - {name} pelud za {day.month}.{day.year}.csv")


def parse_filename(filename):
    """(city, full plant name) for a CSV this module wrote, or None."""
    match = FILENAME_RE.match(filename)
    if not match:
        return None
    city, name = match.group(1), match.group(2)
    if name in Biljka.__members__:
        return city, Biljka[name].value
    if name.isupper():
        return None  # an enum member that has since been removed
    return city, name


def record(conn, scraped, now, data_dir=None):
    """Store one scrape, {city: {plant: value}}, taken at `now`.

    Both stores key on the calendar day, so re-running a day replaces its
    values in the CSV the same way INSERT OR REPLACE does in the table.
    """
    data_dir = data_dir or DATA_DIR
    stamp = now.strftime("%Y-%m-%d %H:%M:%S")
    with conn:
        for city, plants in scraped.items():
            for plant, value in plants.items():
                _write_day(csv_path(data_dir, city, plant, now), value, stamp)
                conn.execute(UPSERT, (city, plant, value, now.date().isoformat()))


def _write_day(path, value, stamp):
    kept = []
    if os.path.isfile(path):
        with open(path, newline="", encoding="utf-8") as f:
            kept = [row for row in csv.reader(f)
                    if row and row != CSV_HEADER and row[-1][:10] != stamp[:10]]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([CSV_HEADER, *kept, [value, stamp]])
