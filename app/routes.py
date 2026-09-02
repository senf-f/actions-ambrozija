import sqlite3
from datetime import date, datetime, timedelta

import requests
from flask import jsonify, render_template, request

from app import app
from src.config import (
    AIR_STATIONS,
    CAMS_FORECAST_DAYS,
    CAMS_PAST_DAYS,
    CAMS_URL,
    CITY_COORDS,
    DB_PATH,
    SEA_STATIONS,
)


def _date_range():
    """Read date_from/date_to query params, defaulting to the current month.

    Returns (date_from, date_to, None) or (None, None, (payload, status)).
    """
    today = datetime.today()
    date_from = request.args.get('date_from', '').strip() or today.replace(day=1).strftime('%Y-%m-%d')
    date_to = request.args.get('date_to', '').strip() or today.strftime('%Y-%m-%d')

    try:
        parsed_from = datetime.strptime(date_from, '%Y-%m-%d')
        parsed_to = datetime.strptime(date_to, '%Y-%m-%d')
    except ValueError:
        return None, None, ({'error': 'invalid date format, expected YYYY-MM-DD'}, 400)

    if parsed_from > parsed_to:
        return None, None, ({'error': 'date_from must not be after date_to'}, 400)

    return date_from, date_to, None


@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        # Fetch unique cities, plants, and months for the dropdowns
        cursor.execute('SELECT DISTINCT city FROM pollen_data')
        cities = [row[0] for row in cursor.fetchall()]

        cursor.execute('SELECT DISTINCT plant FROM pollen_data')
        plants = [row[0] for row in cursor.fetchall()]

        cursor.execute('SELECT DISTINCT strftime("%Y-%m", date) as month FROM pollen_data ORDER BY month')
        months = [row[0] for row in cursor.fetchall()]

        # Get filter parameters. On a fresh visit (no params) default to
        # Zagreb + current month so we don't load the whole table.
        if not request.args:
            selected_city = 'Zagreb'
            selected_plant = None
            selected_month = datetime.today().strftime('%Y-%m')
        else:
            selected_city = request.args.get('city')
            selected_plant = request.args.get('plant')
            selected_month = request.args.get('month')

        # Build the query with filters
        query = 'SELECT city, plant, pollen_concentration, date FROM pollen_data WHERE 1=1'
        params = []

        if selected_city:
            query += ' AND city = ?'
            params.append(selected_city)

        if selected_plant:
            query += ' AND plant = ?'
            params.append(selected_plant)

        if selected_month:
            query += ' AND strftime("%Y-%m", date) = ?'
            params.append(selected_month)

        query += ' ORDER BY date DESC'
        cursor.execute(query, params)
        data = cursor.fetchall()
    finally:
        conn.close()
    return render_template('index.html', data=data, cities=cities, plants=plants, months=months,
                           selected_city=selected_city, selected_plant=selected_plant, selected_month=selected_month)


@app.route('/graph')
def graph():
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT city FROM pollen_data ORDER BY city ASC')
        cities = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()
    return render_template('graph.html', cities=cities)


@app.route('/compare')
def compare():
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT city FROM pollen_data ORDER BY city ASC')
        cities = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()
    return render_template('compare.html', cities=cities)


@app.route('/temps')
def temps():
    """Air vs sea temperature. Cities come from config rather than the tables,
    so a station shows up here before its first reading lands.
    """
    cities = sorted(set(AIR_STATIONS.values()) | set(SEA_STATIONS))
    return render_template('temps.html', cities=cities)


@app.route('/api/plants')
def plants():
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({'error': 'city is required'}), 400

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT DISTINCT plant FROM pollen_data WHERE city = ? ORDER BY plant ASC',
            (city,)
        )
        result = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

    return jsonify(result)


@app.route('/api/graph-data')
def graph_data():
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({'error': 'city is required'}), 400

    date_from_str, date_to_str, err = _date_range()
    if err:
        return jsonify(err[0]), err[1]

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            # Legacy rows store date as a full timestamp, so a plain string
            # BETWEEN would drop the last day of the range.
            'SELECT plant, date(date), pollen_concentration FROM pollen_data '
            'WHERE city = ? AND date(date) BETWEEN ? AND ? ORDER BY date ASC',
            (city, date_from_str, date_to_str)
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    result = []
    for plant, date, concentration in rows:
        try:
            result.append({
                'plant': plant,
                'date': date,
                'concentration': float(concentration)
            })
        except ValueError:
            pass  # skip non-numeric rows

    return jsonify(result)


@app.route('/api/rain-data')
def rain_data():
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({'error': 'city is required'}), 400

    date_from_str, date_to_str, err = _date_range()
    if err:
        return jsonify(err[0]), err[1]

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT station, date, rain_mm FROM rain_data '
            'WHERE city = ? AND date BETWEEN ? AND ? ORDER BY date ASC',
            (city, date_from_str, date_to_str)
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    return jsonify([{'station': s, 'date': d, 'mm': mm} for s, d, mm in rows])


@app.route('/api/cams-data')
def cams_data():
    """Daily maximum modelled ragweed pollen (grains/m3) for a city.

    CAMS is a model, not a trap count, and its unit is not the stampar.hr
    scale — the two belong on separate axes.

    Fetched live instead of stored: the upstream window (92 days back plus a
    4-day forecast) already covers every range this graph offers, so there is
    nothing to scrape or commit.
    ponytail: no archive kept, so a range older than the window returns []. Add
    a daily scraper if long history is wanted.
    """
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({'error': 'city is required'}), 400

    date_from_str, date_to_str, err = _date_range()
    if err:
        return jsonify(err[0]), err[1]

    coords = CITY_COORDS.get(city)
    if not coords:
        return jsonify([])

    today = date.today()
    start = max(datetime.strptime(date_from_str, '%Y-%m-%d').date(),
                today - timedelta(days=CAMS_PAST_DAYS))
    end = min(datetime.strptime(date_to_str, '%Y-%m-%d').date(),
              today + timedelta(days=CAMS_FORECAST_DAYS))
    if start > end:
        return jsonify([])

    lat, lon = coords
    try:
        resp = requests.get(CAMS_URL, timeout=15, params={
            'latitude': lat,
            'longitude': lon,
            'hourly': 'ragweed_pollen',
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'timezone': 'Europe/Zagreb',
        })
        resp.raise_for_status()
        hourly = resp.json().get('hourly', {})
    except (requests.RequestException, ValueError):
        return jsonify({'error': 'CAMS upstream unavailable'}), 502

    daily = {}
    for stamp, value in zip(hourly.get('time', []), hourly.get('ragweed_pollen', [])):
        if value is None:
            continue
        day = stamp[:10]
        daily[day] = max(value, daily.get(day, value))

    return jsonify([{'date': d, 'grains': daily[d]} for d in sorted(daily)])


@app.route('/api/temp-data')
def temp_data():
    """Daily maximum air temperature and sea temperature (08h) for a city.

    Sea stations are named after the city itself, so the same name filters both.
    A city may legitimately have one series and not the other.
    """
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({'error': 'city is required'}), 400

    date_from_str, date_to_str, err = _date_range()
    if err:
        return jsonify(err[0]), err[1]

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT date, temp_c FROM air_temp_data '
            'WHERE city = ? AND date BETWEEN ? AND ? ORDER BY date ASC',
            (city, date_from_str, date_to_str)
        )
        air = [{'date': d, 'temp': t} for d, t in cursor.fetchall()]

        cursor.execute(
            'SELECT date, temp_c FROM sea_temp_data '
            'WHERE station = ? AND date BETWEEN ? AND ? ORDER BY date ASC',
            (city, date_from_str, date_to_str)
        )
        sea = [{'date': d, 'temp': t} for d, t in cursor.fetchall()]
    finally:
        conn.close()

    return jsonify({'air': air, 'sea': sea})
