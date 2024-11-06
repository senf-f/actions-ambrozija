import csv
import datetime
import os
from time import perf_counter

from src import db_handler, scraper
from src.config import DATA_DIR
print(f"[DEBUG] DATA_DIR path: {DATA_DIR}")


def save_to_csv(city, plant, pollen_data):
    """Write pollen data to a CSV file."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    print(f"[DEBUG] Confirmed DATA_DIR exists: {DATA_DIR}")
    file_path = os.path.join(DATA_DIR,
                             f"{city} - {plant} pelud za {datetime.datetime.now().month}.{datetime.datetime.now().year}.csv")
    print(f"[DEBUG] Saving data to {file_path}")

    if not os.access(DATA_DIR, os.W_OK):
        print(f"[ERROR] No write permissions for directory: {DATA_DIR}")
    else:
        print(f"[DEBUG] Write permissions confirmed for directory: {DATA_DIR}")

    with open(file_path, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f, escapechar=" ", quoting=csv.QUOTE_NONE)
        writer.writerow([f"{pollen_data} {datetime.datetime.today()}"])
    print("[INFO] Rows saved to csv.")


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