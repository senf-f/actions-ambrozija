import csv
import datetime
import os
from time import perf_counter

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import biljke
import email_sender


def main():
    start = perf_counter()
    url = "https://stampar.hr/hr/peludna-prognoza"

    # https://medium.com/@mikelcbrowne/running-chromedriver-with-python-selenium-on-heroku-acc1566d161c
    s = Service(ChromeDriverManager().install())
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=s, options=chrome_options)
    driver.maximize_window()
    driver.get(url)

    driver.find_element(By.CSS_SELECTOR, "#perpetuum-cookie-bar .perpetuum-button-dismiss a").click()

    gradovi = ["Zagreb", "Split", "Pula", "Zadar", "Dubrovnik"]

    def nove_biljke_su():
        # uzmi vrijednosti iz //div[@class='biljka-naslov']//span
        _rezultat = driver.find_elements(By.XPATH, "//div[@class='biljka-naslov']//span")
        _biljke = []
        if len(_rezultat) > 0:
            for r in _rezultat:
                _biljke.append(r.text)

        return _biljke

    stare_biljke = []
    for biljka in biljke.Biljka:
        stare_biljke.append(biljka.value)

    spomenute_biljke = []
    date = datetime.datetime.now()

    if not os.path.exists(f"data/{date.year}/{date.month}"):
        os.makedirs(f"data/{date.year}/{date.month}")

    for grad in gradovi:
        izbornik = Select(driver.find_element(By.CSS_SELECTOR, "select[id^='edit-title']"))
        izbornik.select_by_visible_text(grad)
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ajax-progress-fullscreen")))
        # provjeri ima li novih biljaka
        spomenute_biljke.append((nove_biljke_su()))
        # provjeri koncentraciju peluda za biljku
        for biljka in biljke.Biljka:
            xpath = (
                f"//div[@class='biljka-naslov'][contains(., '{biljka.value}')]/following-sibling::div//div[@class='mjerenje-container']//div[contains(@class, 'field-field-vrijednost')][2]")
            rezultat = len(driver.find_elements(By.XPATH, xpath))
            if rezultat:
                pelud = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, xpath))).text
                print(f"{grad}, {biljka.value}: {pelud}")

                with open(
                        f"data/{date.year}/{date.month}/{grad} - "
                        f"+{biljka.name} pelud za {date.month}.{date.year}", "a", newline='') as f:
                    writer = csv.writer(f, escapechar=" ", quoting=csv.QUOTE_NONE)
                    writer.writerow([f"{pelud} {date.today()}"])

                # https://stackoverflow.com/questions/23882024/using-python-csv-writer-without-quotations

    # spomenute_biljke je lista lista, sljedeca linija to pretvara u obicnu listu
    flat_spomenute_biljke = [item for sublist in spomenute_biljke for item in sublist]
    flat_spomenute_biljke.sort()

    # izbaci duplikate
    res = []
    [res.append(x) for x in flat_spomenute_biljke if x not in res]

    print(res)
    # usporedi sa postojecim popisom
    razlika = set(res).difference(set(stare_biljke))
    if len(razlika) > 0:
        email_sender.send_email('Nove biljke na peludnoj prognozi', 'senfsend@outlook.com', 'mate.mrse@gmail.com',
                                f"Nove biljke: {razlika}")
        print(razlika)
        print("Email poslan!")

    driver.quit()
    print(f"Vrijeme izvršavanja: {perf_counter() - start} sekundi.")


if __name__ == "__main__":
    main()
