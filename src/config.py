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

# Modelled ragweed pollen from CAMS, served as JSON by Open-Meteo (no API key).
# Covers the last 92 days plus a 4-day forecast, Europe only.
CAMS_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
CAMS_PAST_DAYS = 92
CAMS_FORECAST_DAYS = 4

# Only used to pick a CAMS grid cell (~11 km), so city-centre precision is ample.
CITY_COORDS = {
    "Beli Manastir": (45.7728, 18.6094),
    "Bjelovar": (45.8988, 16.8489),
    "Dubrovnik": (42.6507, 18.0944),
    "Karlovac": (45.4870, 15.5478),
    "Koprivnica": (46.1639, 16.8328),
    "Kutina": (45.4764, 16.7783),
    "Labin": (45.0856, 14.1200),
    "Metković": (43.0533, 17.6486),
    "Našice": (45.4903, 18.0958),
    "Osijek": (45.5550, 18.6955),
    "Pazin": (45.2400, 13.9375),
    "Popovača": (45.5722, 16.6250),
    "Poreč": (45.2269, 13.5947),
    "Pula": (44.8666, 13.8496),
    "Rijeka": (45.3271, 14.4422),
    "Sisak": (45.4853, 16.3736),
    "Slavonski Brod": (45.1603, 18.0156),
    "Split": (43.5081, 16.4402),
    "Varaždin": (46.3057, 16.3366),
    "Virovitica": (45.8319, 17.3844),
    "Zadar": (44.1194, 15.2314),
    "Zagreb": (45.8150, 15.9819),
    "Đakovo": (45.3081, 18.4103),
    "Šibenik": (43.7350, 15.8952),
}

SEA_URL = "https://vrijeme.hr/more_n.xml"
SEA_HOUR = "08"
SEA_STATIONS = ("Split", "Pula", "Dubrovnik", "Opatija", "Crikvenica", "Zadar")
