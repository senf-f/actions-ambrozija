from src.rain_scraper import parse_rain

SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<dnevna_oborina>
  <datumtermin><datum>26.08.2026.</datum><termin>8</termin></datumtermin>
  <grad><ime>Bjelovar</ime><kolicina>0.2</kolicina></grad>
  <grad><ime>Split-aerodrom</ime><kolicina>0.4</kolicina></grad>
  <grad><ime>Zagreb-Maksimir</ime><kolicina>1.3</kolicina></grad>
  <grad><ime>Zagreb-aerodrom</ime><kolicina>2.1</kolicina></grad>
</dnevna_oborina>
"""


def test_parse_rain_decodes_utf8_bytes():
    """The feed is fetched as bytes; diacritics must survive the parse."""
    raw = SAMPLE.replace("<ime>Zagreb-Maksimir</ime>", "<ime>Zagreb-Grič</ime>").encode("utf-8")
    _, rows = parse_rain(raw)
    assert ("Zagreb-Grič", "Zagreb", 1.3) in rows


def test_parse_rain_filters_and_parses():
    date, rows = parse_rain(SAMPLE)
    assert date == "2026-08-26"
    # only Split + Zagreb kept (Bjelovar dropped), all 3 target stations present
    assert rows == [
        ("Split-aerodrom", "Split", 0.4),
        ("Zagreb-Maksimir", "Zagreb", 1.3),
        ("Zagreb-aerodrom", "Zagreb", 2.1),
    ]
