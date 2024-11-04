import csv
import datetime
import os
from time import perf_counter

from src import db_handler, scraper
from src.config import DATA_DIR


def save_to_csv(city, plant, pollen_data):
    """Write pollen data to a CSV file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR,
                             f"{city} - {plant} pelud za {datetime.datetime.now().month}.{datetime.datetime.now().year}.csv")
    with open(file_path, "a", newline='') as f:
        writer = csv.writer(f, escapechar=" ", quoting=csv.QUOTE_NONE)
        writer.writerow([f"{pollen_data} {datetime.datetime.today()}"])


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
