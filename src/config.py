import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "https://stampar.hr/hr/peludna-prognoza"
DB_PATH = os.path.join(BASE_DIR, "db", "pollen_data.db")

RAIN_URL = "https://vrijeme.hr/oborina.xml"
RAIN_CITIES = ("Split", "Zagreb")

# {station name as it appears in the XML feed: short city name}
AIR_URL = "https://vrijeme.hr/hrvatska_n.xml"
AIR_STATIONS = {
    "Zagreb-Maksimir": "Zagreb",
    "Split-Marjan": "Split",
    "Dubrovnik": "Dubrovnik",
    "RC Osijek-Čepin": "Osijek",
    "Pula-aerodrom": "Pula",
    "Rijeka": "Rijeka",
}

SEA_URL = "https://vrijeme.hr/more_n.xml"
SEA_HOUR = "08"
SEA_STATIONS = ("Split", "Pula", "Dubrovnik", "Opatija", "Crikvenica", "Zadar")
