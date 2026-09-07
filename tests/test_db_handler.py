from src import db_handler


def test_insert_maps_columns_and_replaces_on_conflict(tmp_path, monkeypatch):
    monkeypatch.setattr(db_handler, "DB_PATH", str(tmp_path / "test.db"))
    conn = db_handler.setup_db()

    db_handler.insert(conn, "pollen_data", city="Zagreb", plant="Trave (Poaceae)",
                      pollen_concentration="1.5", date="2026-09-07")
    db_handler.insert(conn, "pollen_data", city="Zagreb", plant="Trave (Poaceae)",
                      pollen_concentration="9.9", date="2026-09-07")
    db_handler.insert(conn, "sea_temp_data", station="Split", temp_c=24.5,
                      hour="08", date="2026-09-07")

    assert conn.execute(
        "SELECT city, plant, pollen_concentration, date FROM pollen_data"
    ).fetchall() == [("Zagreb", "Trave (Poaceae)", "9.9", "2026-09-07")]
    assert conn.execute(
        "SELECT station, temp_c, hour, date FROM sea_temp_data"
    ).fetchall() == [("Split", 24.5, "08", "2026-09-07")]

    conn.close()
