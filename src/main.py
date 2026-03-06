import csv
import datetime
import os
from time import perf_counter

from src import db_handler, scraper
from src.biljke import BILJKA_LOOKUP


def save_to_csv(city, plant, pollen_data):
    """Write pollen data to a CSV file.

    CSV files are written into the same directory structure used by the top-level
    main.py: data/{year}/{month}/
    """
    now = datetime.datetime.now()
    # Use the same per-year/per-month directory layout as main.py
    dir_path = os.path.join("data", str(now.year), str(now.month))
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
            writer.writerow(["pollen_concentration", "date"])

        writer.writerow([pollen_data, now.strftime("%Y-%m-%d")])


def main():
    start = perf_counter()
    conn = db_handler.setup_db()
    driver = scraper.initialize_driver()
    scraper.accept_cookies(driver)

    cities = scraper.get_cities(driver)

    for city in cities:
        pollen_data = scraper.get_pollen_data(driver, city)
        if pollen_data:
            # Save to CSV and DB
            for key, value in pollen_data.items():
                print(f"{city}: {key}: {value}")
                save_to_csv(city=city, plant=key, pollen_data=value)
                db_handler.insert_into_db(conn=conn, city=city, plant=key, pollen_concentration=value,
                                          date=datetime.datetime.today())

    scraper.close_driver(driver)
    conn.close()

    print(f"Execution time: {perf_counter() - start} seconds.")


if __name__ == "__main__":
    main()
