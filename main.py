import csv
import datetime
import os
from time import perf_counter
import sqlite3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

import biljke
import telegram_sender


def setup_db():
    """Create a connection and setup the pollen database."""
    conn = sqlite3.connect('pollen_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pollen_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            plant TEXT NOT NULL,
            pollen_concentration TEXT NOT NULL,
            date DATE NOT NULL,
            UNIQUE(city, plant, date)
        )
    ''')
    conn.commit()
    return conn

def insert_into_db(conn, city, plant, pollen_concentration, date):
    """Insert pollen data into the database."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO pollen_data (city, plant, pollen_concentration, date)
        VALUES (?, ?, ?, ?)
    ''', (city, plant, pollen_concentration, date))
    conn.commit()

def main():
    start = perf_counter()
    url = "https://stampar.hr/hr/peludna-prognoza"

    s = Service()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('ignore-certificate-errors')
    driver = webdriver.Chrome(service=s, options=chrome_options)
    driver.maximize_window()
    driver.get(url)

    # Initialize database connection
    conn = setup_db()

    izbornik = Select(driver.find_element(By.CSS_SELECTOR, "select[id^='edit-title']"))

    gradovi = [grad.text for grad in izbornik.options]

    date = datetime.datetime.now()
    if not os.path.exists(f"data/{date.year}/{date.month}"):
        os.makedirs(f"data/{date.year}/{date.month}")

    try:
        driver.find_element(By.CSS_SELECTOR, "#perpetuum-cookie-bar .perpetuum-button-dismiss a").click()
    except Exception as e:
        print(f"Error clicking cookie dismiss button: {e}")

    def nove_biljke():
        _rezultat = driver.find_elements(By.XPATH, "//div[@class='biljka-naslov']//span")
        return [r.text for r in _rezultat]

    postojece_biljke = [biljka.value for biljka in biljke.Biljka]

    spomenute_biljke = []
    for grad in gradovi:
        izbornik = Select(driver.find_element(By.CSS_SELECTOR, "select[id^='edit-title']"))
        izbornik.select_by_visible_text(grad)
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ajax-progress-fullscreen")))
        # provjeri ima li novih biljaka
        spomenute_biljke.append(nove_biljke())
        # provjeri koncentraciju peluda za biljku
        for biljka in biljke.Biljka:
            xpath = (
                f"//div[@class='biljka-naslov'][contains(., '{biljka.value}')]/following-sibling::div//div[@class='mjerenje-container']//div[contains(@class, 'field-field-vrijednost')][2]")
            rezultat = len(driver.find_elements(By.XPATH, xpath))
            if rezultat:
                pelud = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, xpath))).text
                print(f"{grad}, {biljka.value}: {pelud}")

                # Write to CSV
                with open(
                        f"data/{date.year}/{date.month}/{grad} - "
                        f"{biljka.name} pelud za {date.month}.{date.year}", "a", newline='') as f:
                    writer = csv.writer(f, escapechar=" ", quoting=csv.QUOTE_NONE)
                    writer.writerow([f"{pelud} {date.today()}"])

                # Write to DB
                insert_into_db(conn, grad, biljka.value, pelud, date)


    # pretvara listu lista u obicnu listu:
    flat_spomenute_biljke = [item for sublist in spomenute_biljke for item in sublist]
    flat_spomenute_biljke.sort()

    # izbaci duplikate
    res = list(dict.fromkeys(flat_spomenute_biljke))

    print(res)
    # usporedi sa postojecim popisom
    razlika = set(res).difference(set(postojece_biljke))
    try:
        if len(razlika) > 0:
            content = f"Nove biljke: {razlika}"
            telegram_sender.send_to_telegram(content)
            print(f">>>> Poslano na telegram: {content}.")

    except Exception as e:
        print(e)

    driver.quit()
    print(f"Vrijeme izvršavanja: {perf_counter() - start} sekundi.")


if __name__ == "__main__":
    main()
