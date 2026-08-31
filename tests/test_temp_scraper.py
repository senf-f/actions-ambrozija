from src.temp_scraper import parse_air, parse_sea

AIR = """<?xml version="1.0" encoding="UTF-8"?>
<Hrvatska>
<DatumTermin><Datum>31.08.2026</Datum><Termin>15</Termin></DatumTermin>
<Grad><GradIme>Bjelovar</GradIme><Podatci><Temp> 29.0</Temp></Podatci></Grad>
<Grad><GradIme>Zagreb-Maksimir</GradIme><Podatci><Temp> 30.1</Temp></Podatci></Grad>
<Grad><GradIme>Pula-aerodrom</GradIme><Podatci><Temp>27.4</Temp></Podatci></Grad>
<Grad><GradIme>Rijeka</GradIme><Podatci><Temp>-</Temp></Podatci></Grad>
</Hrvatska>
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


def test_parse_air_filters_targets_and_skips_missing():
    date, hour, rows = parse_air(AIR)
    assert (date, hour) == ("2026-08-31", "15")
    # Bjelovar not a target; Rijeka has no reading
    assert rows == [("Zagreb-Maksimir", "Zagreb", 30.1), ("Pula-aerodrom", "Pula", 27.4)]


def test_parse_air_reports_wrong_hour():
    _, hour, _ = parse_air(AIR.replace("<Termin>15</Termin>", "<Termin>11</Termin>"))
    assert hour == "11"


def test_parse_sea_picks_08_column():
    date, rows = parse_sea(SEA)
    assert date == "2026-08-31"
    # Božava not a target; Zadar has no 08h reading
    assert rows == [("Split", 26.4)]
