import sqlite3
import pytest
from app import app as flask_app
from src import db_handler


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Flask test client over an isolated DB built by the production schema."""
    db_path = str(tmp_path / "test.db")
    # Patch the local DB_PATH binding inside each module (that's what the code
    # actually references after `from src.config import DB_PATH`).
    monkeypatch.setattr("app.routes.DB_PATH", db_path)
    monkeypatch.setattr(db_handler, "DB_PATH", db_path)
    db_handler.setup_db().close()

    flask_app.config["TESTING"] = True
    return flask_app.test_client()


@pytest.fixture
def client_with_data(client):
    """Same client but pre-populated with test rows."""
    import app.routes as routes_module
    db_path = routes_module.DB_PATH  # already patched by `client` fixture

    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO pollen_data (city, plant, pollen_concentration, date) VALUES (?, ?, ?, ?)",
        [
            ("Zagreb", "Breza (Betula sp.)", "2.5", "2026-03-01"),
            ("Zagreb", "Breza (Betula sp.)", "3.0", "2026-03-02"),
            ("Zagreb", "Trave (Poaceae)", "1.0", "2026-03-01"),
            ("Zagreb", "Trave (Poaceae)", "bad_value", "2026-03-03"),  # non-numeric — must be excluded
            ("Split", "Maslina (Olea sp.)", "4.0", "2026-03-01"),
        ],
    )
    conn.executemany(
        "INSERT INTO air_temp_data (station, city, temp_c, hour, date) VALUES (?, ?, ?, ?, ?)",
        [
            ("Zagreb-Maksimir", "Zagreb", 12.5, "15", "2026-03-01"),
            ("Zagreb-Maksimir", "Zagreb", 14.0, "15", "2026-03-02"),
            ("Split-Marjan", "Split", 17.2, "15", "2026-03-01"),
        ],
    )
    conn.executemany(
        "INSERT INTO sea_temp_data (station, temp_c, hour, date) VALUES (?, ?, ?, ?)",
        [
            ("Split", 14.1, "08", "2026-03-01"),
            ("Split", 14.3, "08", "2026-03-02"),
        ],
    )
    conn.commit()
    conn.close()
    return client
