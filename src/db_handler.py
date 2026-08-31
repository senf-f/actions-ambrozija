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

def insert_into_db(conn, city, plant, pollen_concentration, date):
    """Insert pollen data into the database, avoiding duplicates."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO pollen_data (city, plant, pollen_concentration, date)
        VALUES (?, ?, ?, ?)
    ''', (city, plant, pollen_concentration, date))
    conn.commit()

def insert_into_rain_db(conn, station, city, rain_mm, date):
    """Insert rain data into the database, avoiding duplicates."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO rain_data (station, city, rain_mm, date)
        VALUES (?, ?, ?, ?)
    ''', (station, city, rain_mm, date))
    conn.commit()

def insert_into_air_temp_db(conn, station, city, temp_c, hour, date):
    """Insert air temperature into the database, avoiding duplicates."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO air_temp_data (station, city, temp_c, hour, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (station, city, temp_c, hour, date))
    conn.commit()

def insert_into_sea_temp_db(conn, station, temp_c, hour, date):
    """Insert sea temperature into the database, avoiding duplicates."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO sea_temp_data (station, temp_c, hour, date)
        VALUES (?, ?, ?, ?)
    ''', (station, temp_c, hour, date))
    conn.commit()
