from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

from src.config import BASE_URL


def initialize_driver():
    """Initialize Selenium WebDriver with options."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("ignore-certificate-errors")
    driver = webdriver.Chrome(options=options)
    driver.get(BASE_URL)
    driver.maximize_window()
    return driver


def close_driver(driver):
    driver.quit()


def accept_cookies(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, "#perpetuum-cookie-bar .perpetuum-button-dismiss a").click()
    except Exception as e:
        print(f"Error accepting cookies: {e}")


def get_cities(driver):
    """Retrieve the list of cities from the dropdown menu."""
    select = Select(driver.find_element(By.CSS_SELECTOR, "select[id^='edit-title']"))
    cities = [option.text for option in select.options]
    if "Izaberi grad" in cities: cities.remove("Izaberi grad")
    return cities


def get_pollen_data(driver, city):
    """Retrieve pollen data for a given city and plant."""
    select = Select(driver.find_element(By.CSS_SELECTOR, "select[id^='edit-title']"))
    select.select_by_visible_text(city)
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ajax-progress-fullscreen"))
    )
    # Define your XPath based on the plant name
    biljke = driver.find_elements(By.XPATH, "//div[contains(@class, 'paragraph--type--biljka-grupa')]")

    pollen_data = {}
    if len(biljke) > 0:
        for biljka in biljke:
            sekcije = biljka.find_elements(By.XPATH, ".//div[contains(@class, 'mjerenje-container')]")
            ime_biljke = biljka.find_element(By.XPATH, "./div[@class='biljka-naslov']").text
            for sekcija in sekcije:
                mjerenja = sekcija.find_elements(By.XPATH,
                                                 ".//div[contains(@class, 'field-field-vrijednost')]/div[contains(@class, 'field-item')]")
                for mjerenje in mjerenja:
                    if "." in mjerenje.text:
                        pollen_data[ime_biljke] = mjerenje.text
    return pollen_data
