import csv
import datetime
import os
import sys
from time import perf_counter

from src import db_handler, pollen_record, scraper, telegram
from src.biljke import Biljka
from src.config import BASE_DIR

TEST_CSV = os.path.join(BASE_DIR, "data", "test", "test_output.csv")

RAGWEED = Biljka.AMBROZIJA.value
TREND_CITIES = ("Zagreb", "Split")


def save_test_csv(rows):
    """One file with everything a run scraped, for the CI probe to eyeball."""
    os.makedirs(os.path.dirname(TEST_CSV), exist_ok=True)
    with open(TEST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["city", "plant", "pollen_concentration", "timestamp"])
        writer.writerows(rows)


def unknown_plants(scraped_names):
    """Scraped plant names the Biljka enum does not know yet.

    The enum drives CSV file naming, so a species stampar.hr starts publishing
    is stored under its full Croatian name until someone adds it.
    """
    return sorted(set(scraped_names) - {biljka.value for biljka in Biljka})


def trend_message(city, values):
    """One ragweed alert line for a city, or None. Values oldest to newest."""
    if len(values) >= 3 and values[-3] < values[-2] < values[-1]:
        return (f"Ambrozija {city}: raste treći dan zaredom "
                f"({values[-3]:.1f} -> {values[-2]:.1f} -> {values[-1]:.1f})")
    if len(values) >= 2 and values[-2] - values[-1] > 1:
        return (f"Ambrozija {city}: pala za {values[-2] - values[-1]:.1f} "
                f"({values[-2]:.1f} -> {values[-1]:.1f})")
    return None


def ragweed_alerts(conn):
    """Trend alerts from the three most recently stored days per city.

    Deliberately compares stored rows, not calendar days, so a gap in scraping
    still gets compared instead of silently skipped.
    """
    messages = []
    for city in TREND_CITIES:
        rows = conn.execute(
            "SELECT pollen_concentration FROM pollen_data "
            "WHERE city = ? AND plant = ? ORDER BY date DESC LIMIT 3",
            (city, RAGWEED),
        ).fetchall()
        message = trend_message(city, [float(row[0]) for row in reversed(rows)])
        if message:
            messages.append(message)
    return messages


def main(dry_run=False):
    """Scrape every city. dry_run stores nothing but the single test CSV, so a
    probe run can prove the site is still scrapable without touching the data.
    """
    start = perf_counter()
    driver = scraper.initialize_driver()
    scraper.accept_cookies(driver)

    now = datetime.datetime.now()
    scraped = {}
    for city in scraper.get_cities(driver):
        scraped[city] = scraper.get_pollen_data(driver, city)
        for plant, value in scraped[city].items():
            print(f"{city}: {plant}: {value}")
    driver.quit()

    alerts = []
    if dry_run:
        stamp = now.strftime("%Y-%m-%d %H:%M:%S")
        save_test_csv([(city, plant, value, stamp)
                       for city, plants in scraped.items()
                       for plant, value in plants.items()])
        print(f"\nResults written to {TEST_CSV}")
    else:
        conn = db_handler.setup_db()
        pollen_record.record(conn, scraped, now)
        alerts = ragweed_alerts(conn)
        conn.close()

    nove = unknown_plants({plant for plants in scraped.values() for plant in plants})
    if nove:
        alerts.insert(0, f"Nove biljke: {', '.join(nove)}")
    if alerts:
        telegram.send("\n".join(alerts))

    print(f"Execution time: {perf_counter() - start} seconds.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
