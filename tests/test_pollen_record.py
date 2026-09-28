import csv
import datetime
import os

from src import backfill_db, db_handler, main as main_module, pollen_record

NEW_SPECIES = "Maslačak (Taraxacum sp.)"
MORNING = datetime.datetime(2026, 9, 28, 7, 0, 0)
NOON = datetime.datetime(2026, 9, 28, 12, 30, 0)


def _db(monkeypatch, path):
    monkeypatch.setattr(db_handler, "DB_PATH", str(path))
    return db_handler.setup_db()


def _rows(conn):
    return conn.execute("SELECT city, plant, pollen_concentration, date "
                        "FROM pollen_data ORDER BY city, plant").fetchall()


def _csv_rows(tmp_path, city, plant):
    with open(pollen_record.csv_path(str(tmp_path), city, plant, NOON),
              newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_rerunning_a_day_replaces_it_in_both_stores(tmp_path, monkeypatch):
    conn = _db(monkeypatch, tmp_path / "t.db")
    pollen_record.record(conn, {"Zagreb": {"Trave (Poaceae)": "1.0"}}, MORNING, str(tmp_path))
    pollen_record.record(conn, {"Zagreb": {"Trave (Poaceae)": "2.5"}}, NOON, str(tmp_path))

    assert _rows(conn) == [("Zagreb", "Trave (Poaceae)", "2.5", "2026-09-28")]
    assert _csv_rows(tmp_path, "Zagreb", "Trave (Poaceae)") == [
        ["pollen_concentration", "timestamp"], ["2.5", "2026-09-28 12:30:00"]]
    conn.close()


def test_earlier_days_in_the_month_are_kept(tmp_path, monkeypatch):
    conn = _db(monkeypatch, tmp_path / "t.db")
    pollen_record.record(conn, {"Split": {"Trave (Poaceae)": "1.0"}},
                         NOON - datetime.timedelta(days=1), str(tmp_path))
    pollen_record.record(conn, {"Split": {"Trave (Poaceae)": "2.0"}}, NOON, str(tmp_path))

    assert [row[0] for row in _csv_rows(tmp_path, "Split", "Trave (Poaceae)")[1:]] == ["1.0", "2.0"]
    conn.close()


def test_backfill_rebuilds_what_record_wrote(tmp_path, monkeypatch):
    scraped = {"Zagreb": {"Trave (Poaceae)": "1.5", NEW_SPECIES: "0.3"},
               "Split": {"Ambrozija (Ambrosia sp.)": "4.0"}}
    conn = _db(monkeypatch, tmp_path / "t.db")
    pollen_record.record(conn, scraped, NOON, str(tmp_path / "data"))
    written = _rows(conn)
    conn.close()

    rebuilt_db = _db(monkeypatch, tmp_path / "rebuilt.db")
    rebuilt_db.close()
    monkeypatch.setattr(backfill_db, "DATA_DIR", str(tmp_path / "data"))
    backfill_db.main()

    conn = db_handler.setup_db()
    assert _rows(conn) == written
    assert ("Zagreb", NEW_SPECIES, "0.3", "2026-09-28") in written
    conn.close()


def test_removed_enum_name_is_not_imported_as_a_plant():
    assert pollen_record.parse_filename("Zagreb - STARI_HRAST pelud za 9.2026.csv") is None


def test_main_records_and_alerts(tmp_path, monkeypatch):
    class FakeDriver:
        def quit(self):
            pass

    monkeypatch.setattr(main_module.scraper, "initialize_driver", lambda: FakeDriver())
    monkeypatch.setattr(main_module.scraper, "accept_cookies", lambda driver: None)
    monkeypatch.setattr(main_module.scraper, "get_cities", lambda driver: ["Zagreb"])
    monkeypatch.setattr(main_module.scraper, "get_pollen_data",
                        lambda driver, city: {NEW_SPECIES: "0.3"})
    monkeypatch.setattr(db_handler, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setattr(pollen_record, "DATA_DIR", str(tmp_path / "data"))
    sent = []
    monkeypatch.setattr(main_module.telegram, "send", sent.append)

    main_module.main()

    conn = db_handler.setup_db()
    assert [row[:3] for row in _rows(conn)] == [("Zagreb", NEW_SPECIES, "0.3")]
    conn.close()
    assert sum(len(files) for _, _, files in os.walk(tmp_path / "data")) == 1
    assert sent == [f"Nove biljke: {NEW_SPECIES}"]
