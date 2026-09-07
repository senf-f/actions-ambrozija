import csv
import datetime
import os
import sys
from time import perf_counter

from src import db_handler, scraper, telegram
from src.biljke import BILJKA_LOOKUP, Biljka
from src.config import BASE_DIR

TEST_CSV = os.path.join(BASE_DIR, "data", "test", "test_output.csv")


def save_to_csv(city, plant, pollen_data):
    """Write pollen data to a CSV file."""
    now = datetime.datetime.now()
    dir_path = os.path.join(BASE_DIR, "data", str(now.year), str(now.month))
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    enum_biljke = BILJKA_LOOKUP.get(plant, None)
    if enum_biljke:
        plant = enum_biljke

    file_path = os.path.join(
        dir_path,
        f"{city} - {plant} pelud za {now.month}.{now.year}.csv"
    )

    file_exists = os.path.isfile(file_path)
    with open(file_path, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["pollen_concentration", "timestamp"])

        writer.writerow([pollen_data, now.strftime("%Y-%m-%d %H:%M:%S")])


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


def main(dry_run=False):
    """Scrape every city. dry_run stores nothing but the single test CSV, so a
    probe run can prove the site is still scrapable without touching the data.
    """
    start = perf_counter()
    conn = None if dry_run else db_handler.setup_db()
    driver = scraper.initialize_driver()
    scraper.accept_cookies(driver)

    now = datetime.datetime.now()
    seen_plants = set()
    scraped = []
    for city in scraper.get_cities(driver):
        pollen_data = scraper.get_pollen_data(driver, city)
        seen_plants.update(pollen_data)
        for plant, value in pollen_data.items():
            print(f"{city}: {plant}: {value}")
            scraped.append((city, plant, value, now.strftime("%Y-%m-%d %H:%M:%S")))
            if not dry_run:
                save_to_csv(city=city, plant=plant, pollen_data=value)
                db_handler.insert(conn, "pollen_data", city=city, plant=plant,
                                  pollen_concentration=value,
                                  date=now.date().isoformat())

    driver.quit()
    if conn:
        conn.close()
    if dry_run:
        save_test_csv(scraped)
        print(f"\nResults written to {TEST_CSV}")

    nove = unknown_plants(seen_plants)
    if nove:
        telegram.send(f"Nove biljke: {', '.join(nove)}")

    print(f"Execution time: {perf_counter() - start} seconds.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
