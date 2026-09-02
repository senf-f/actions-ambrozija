import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "https://stampar.hr/hr/peludna-prognoza"
DB_PATH = os.path.join(BASE_DIR, "db", "pollen_data.db")

RAIN_URL = "https://vrijeme.hr/oborina.xml"
RAIN_CITIES = ("Split", "Zagreb")

# Daily maximum air temperature. Covers the climatological day ending at 18 UTC
# (termin 19 in CET, 20 in CEST), is published that evening and then served
# unchanged all of the following day.
TMAX_URL = "https://vrijeme.hr/tx.xml"

# {station name as it appears in the XML feed: short city name}
AIR_STATIONS = {
    "Zagreb-Maksimir": "Zagreb",
    "Split": "Split",
    "Dubrovnik": "Dubrovnik",
    "Osijek": "Osijek",
    "Pula": "Pula",
    "Rijeka": "Rijeka",
}

SEA_URL = "https://vrijeme.hr/more_n.xml"
SEA_HOUR = "08"
SEA_STATIONS = ("Split", "Pula", "Dubrovnik", "Opatija", "Crikvenica", "Zadar")
