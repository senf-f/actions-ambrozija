import csv

from src import db_handler, main as main_module


class FakeDriver:
    def quit(self):
        pass


def test_dry_run_writes_only_the_test_csv(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("a dry run must not store anything")

    monkeypatch.setattr(main_module.scraper, "initialize_driver", lambda: FakeDriver())
    monkeypatch.setattr(main_module.scraper, "accept_cookies", lambda driver: None)
    monkeypatch.setattr(main_module.scraper, "get_cities", lambda driver: ["Zagreb"])
    monkeypatch.setattr(main_module.scraper, "get_pollen_data",
                        lambda driver, city: {"Trave (Poaceae)": "1.5"})
    monkeypatch.setattr(main_module, "save_to_csv", fail)
    monkeypatch.setattr(db_handler, "insert", fail)
    monkeypatch.setattr(db_handler, "setup_db", fail)
    monkeypatch.setattr(main_module, "TEST_CSV", str(tmp_path / "test_output.csv"))

    main_module.main(dry_run=True)

    with open(main_module.TEST_CSV, encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows == [["city", "plant", "pollen_concentration", "timestamp"],
                    ["Zagreb", "Trave (Poaceae)", "1.5", rows[1][3]]]
