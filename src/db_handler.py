import os
import sqlite3
from src.config import DB_PATH

def setup_db():
    """Set up the pollen database."""

    # Ensure the parent directory for the database exists
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"[DEBUG] Created directory: {db_dir}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pollen_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            plant TEXT NOT NULL,
            pollen_concentration TEXT NOT NULL,
            date DATE NOT NULL,
            UNIQUE(city, plant, date)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rain_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station TEXT NOT NULL,
            city TEXT NOT NULL,
            rain_mm REAL NOT NULL,
            date DATE NOT NULL,
            UNIQUE(station, date)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS air_temp_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station TEXT NOT NULL,
            city TEXT NOT NULL,
            temp_c REAL NOT NULL,
            hour TEXT NOT NULL,
            date DATE NOT NULL,
            UNIQUE(station, date)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sea_temp_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station TEXT NOT NULL,
            temp_c REAL NOT NULL,
            hour TEXT NOT NULL,
            date DATE NOT NULL,
            UNIQUE(station, date)
        )
    ''')
    conn.commit()
    return conn

def insert(conn, table, **columns):
    """Insert one row, replacing an existing one with the same UNIQUE key.

    Table and column names are interpolated, so they must stay literals from
    this repo, never request or feed data.
    """
    names = ", ".join(columns)
    placeholders = ", ".join("?" * len(columns))
    conn.execute(
        f'INSERT OR REPLACE INTO {table} ({names}) VALUES ({placeholders})',
        tuple(columns.values())
    )
    conn.commit()
