from src.temp_scraper import parse_tmax, parse_sea

TMAX = """<?xml version="1.0" encoding="UTF-8"?>
<maksimalnatemperatura>
  <datumtermin>
    <datum>31.08.2026</datum>
    <termin>20</termin>
  </datumtermin>
  <grad><ime>Bjelovar</ime><tempmax>29.0</tempmax></grad>
  <grad><ime>Zagreb-Maksimir</ime><tempmax> 30.1</tempmax></grad>
  <grad><ime>Pula-aerodrom</ime><tempmax>27.4</tempmax></grad>
  <grad><ime>Pula</ime><tempmax>28.2</tempmax></grad>
  <grad><ime>Rijeka</ime><tempmax>-</tempmax></grad>
</maksimalnatemperatura>
"""

SEA = """<?xml version="1.0" encoding="UTF-8"?>
<Temperature_mora>
  <Datum>31.08.2026</Datum>
  <Podatci><Postaja>Postaja \\ Termin mjerenja</Postaja>
    <Termin>07</Termin><Termin>08</Termin><Termin>11</Termin></Podatci>
  <Podatci><Postaja>Bo&#382;ava</Postaja>
    <Termin>25.2</Termin><Termin/><Termin/></Podatci>
  <Podatci><Postaja>Split</Postaja>
    <Termin>26.0</Termin><Termin>26.4</Termin><Termin>26.9</Termin></Podatci>
  <Podatci><Postaja>Zadar</Postaja>
    <Termin>25.1</Termin><Termin/><Termin>25.5</Termin></Podatci>
</Temperature_mora>
"""


def test_parse_tmax_filters_targets_and_skips_missing():
    date, termin, rows = parse_tmax(TMAX)
    assert (date, termin) == ("2026-08-31", "20")
    # Bjelovar and Pula-aerodrom are not targets; Rijeka has no reading
    assert rows == [("Zagreb-Maksimir", "Zagreb", 30.1), ("Pula", "Pula", 28.2)]


def test_parse_tmax_date_comes_from_feed_not_today():
    """The feed normally serves yesterday's maxima, so its own date must win."""
    date, _, _ = parse_tmax(TMAX.replace("31.08.2026", "01.09.2026"))
    assert date == "2026-09-01"


def test_parse_sea_picks_08_column():
    date, rows = parse_sea(SEA)
    assert date == "2026-08-31"
    # Božava not a target; Zadar has no 08h reading
    assert rows == [("Split", 26.4)]
