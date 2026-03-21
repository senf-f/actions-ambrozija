import sqlite3
import pytest
from app import app as flask_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Flask test client with an isolated SQLite DB containing a known schema."""
    db_path = str(tmp_path / "test.db")
    # Patch the local DB_PATH binding inside app.routes (that's what route
    # functions actually reference after `from src.config import DB_PATH`).
    monkeypatch.setattr("app.routes.DB_PATH", db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE pollen_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            plant TEXT NOT NULL,
            pollen_concentration TEXT NOT NULL,
            date DATE NOT NULL,
            UNIQUE(city, plant, date)
        )
    """)
    conn.commit()
    conn.close()

    flask_app.config["TESTING"] = True
    return flask_app.test_client()


@pytest.fixture
def client_with_data(client, tmp_path, monkeypatch):
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
    conn.commit()
    conn.close()
    return client
