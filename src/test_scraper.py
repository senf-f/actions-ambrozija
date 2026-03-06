"""Test script that runs the scraper and writes all results to a single test CSV."""
import csv
import datetime
import os
from time import perf_counter

from src import scraper
from src.config import BASE_DIR


def main():
    start = perf_counter()
    driver = scraper.initialize_driver()
    scraper.accept_cookies(driver)

    cities = scraper.get_cities(driver)
    now = datetime.datetime.now()

    file_path = os.path.join(BASE_DIR, "data", "test_output.csv")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["city", "plant", "pollen_concentration", "timestamp"])

        for city in cities:
            pollen_data = scraper.get_pollen_data(driver, city)
            if pollen_data:
                for plant, value in pollen_data.items():
                    print(f"{city}: {plant}: {value}")
                    writer.writerow([city, plant, value, now.strftime("%Y-%m-%d %H:%M:%S")])

    scraper.close_driver(driver)
    print(f"\nResults written to {file_path}")
    print(f"Execution time: {perf_counter() - start} seconds.")


if __name__ == "__main__":
    main()
