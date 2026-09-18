from src import db_handler
from src.main import RAGWEED, ragweed_alerts, trend_message


def test_three_ascending_days_alert():
    assert "raste" in trend_message("Zagreb", [5.0, 6.0, 7.0])


def test_flat_or_mixed_days_are_silent():
    assert trend_message("Zagreb", [7.0, 6.0, 7.0]) is None
    assert trend_message("Zagreb", [6.0, 6.0, 6.0]) is None


def test_drop_over_one_point_alerts():
    assert "pala za 1.5" in trend_message("Split", [3.0, 5.0, 3.5])


def test_drop_of_exactly_one_point_is_silent():
    assert trend_message("Split", [3.0, 5.0, 4.0]) is None


def test_single_day_of_data_is_silent():
    assert trend_message("Split", [5.0]) is None


def test_alerts_read_the_three_newest_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(db_handler, "DB_PATH", str(tmp_path / "t.db"))
    conn = db_handler.setup_db()
    for date, value in [("2026-09-01", "9.0"), ("2026-09-04", "1.0"),
                        ("2026-09-05", "2.0"), ("2026-09-06", "3.0")]:
        db_handler.insert(conn, "pollen_data", city="Zagreb", plant=RAGWEED,
                          pollen_concentration=value, date=date)
    db_handler.insert(conn, "pollen_data", city="Split", plant=RAGWEED,
                      pollen_concentration="0.5", date="2026-09-06")

    assert ragweed_alerts(conn) == [
        "Ambrozija Zagreb: raste treći dan zaredom (1.0 -> 2.0 -> 3.0)"
    ]
    conn.close()


def test_other_cities_are_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr(db_handler, "DB_PATH", str(tmp_path / "t.db"))
    conn = db_handler.setup_db()
    for date, value in [("2026-09-04", "1.0"), ("2026-09-05", "2.0"),
                        ("2026-09-06", "3.0")]:
        db_handler.insert(conn, "pollen_data", city="Osijek", plant=RAGWEED,
                          pollen_concentration=value, date=date)

    assert ragweed_alerts(conn) == []
    conn.close()
