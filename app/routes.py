import sqlite3
from datetime import date, datetime, timedelta

import requests
from flask import abort, jsonify, make_response, render_template, request

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


def _bad_request(message):
    abort(make_response(jsonify({'error': message}), 400))


def _rows(sql, *params):
    conn = sqlite3.connect(DB_PATH)
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def _city():
    return request.args.get('city', '').strip() or _bad_request('city is required')


def _date_range():
    """Read date_from/date_to query params, defaulting to the current month."""
    today = datetime.today()
    date_from = request.args.get('date_from', '').strip() or today.replace(day=1).strftime('%Y-%m-%d')
    date_to = request.args.get('date_to', '').strip() or today.strftime('%Y-%m-%d')

    try:
        parsed = [datetime.strptime(d, '%Y-%m-%d') for d in (date_from, date_to)]
    except ValueError:
        _bad_request('invalid date format, expected YYYY-MM-DD')

    if parsed[0] > parsed[1]:
        _bad_request('date_from must not be after date_to')

    return date_from, date_to


@app.route('/')
def index():
    # Fetch unique cities, plants, and months for the dropdowns
    cities = [row[0] for row in _rows('SELECT DISTINCT city FROM pollen_data')]
    plants = [row[0] for row in _rows('SELECT DISTINCT plant FROM pollen_data')]
    months = [row[0] for row in _rows(
        'SELECT DISTINCT strftime("%Y-%m", date) as month FROM pollen_data ORDER BY month')]

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

    data = _rows(query + ' ORDER BY date DESC', *params)
    return render_template('index.html', data=data, cities=cities, plants=plants, months=months,
                           selected_city=selected_city, selected_plant=selected_plant, selected_month=selected_month)


@app.route('/graph')
@app.route('/compare')
def pollen_chart():
    """Both chart pages: same dropdowns, different template.

    The current year is always offered even before its first reading lands.
    """
    cities = [row[0] for row in
              _rows('SELECT DISTINCT city FROM pollen_data ORDER BY city ASC')]
    stored_years = {row[0] for row in
                    _rows('SELECT DISTINCT strftime("%Y", date) FROM pollen_data')}
    years = sorted(stored_years | {str(date.today().year)}, reverse=True)
    return render_template(f'{request.path.lstrip("/")}.html',
                           cities=cities, years=years)


@app.route('/temps')
def temps():
    """Air vs sea temperature. Cities come from config rather than the tables,
    so a station shows up here before its first reading lands.
    """
    cities = sorted(set(AIR_STATIONS.values()) | set(SEA_STATIONS))
    return render_template('temps.html', cities=cities)


@app.route('/api/plants')
def plants():
    return jsonify([row[0] for row in _rows(
        'SELECT DISTINCT plant FROM pollen_data WHERE city = ? ORDER BY plant ASC',
        _city()
    )])


@app.route('/api/graph-data')
def graph_data():
    city = _city()
    date_from_str, date_to_str = _date_range()

    rows = _rows(
        # Legacy rows store date as a full timestamp, so a plain string
        # BETWEEN would drop the last day of the range.
        'SELECT plant, date(date), pollen_concentration FROM pollen_data '
        'WHERE city = ? AND date(date) BETWEEN ? AND ? ORDER BY date ASC',
        city, date_from_str, date_to_str
    )

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
    city = _city()
    date_from_str, date_to_str = _date_range()

    rows = _rows(
        'SELECT station, date, rain_mm FROM rain_data '
        'WHERE city = ? AND date BETWEEN ? AND ? ORDER BY date ASC',
        city, date_from_str, date_to_str
    )
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
    city = _city()
    date_from_str, date_to_str = _date_range()

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
    city = _city()
    date_from_str, date_to_str = _date_range()

    air = _rows(
        'SELECT date, temp_c FROM air_temp_data '
        'WHERE city = ? AND date BETWEEN ? AND ? ORDER BY date ASC',
        city, date_from_str, date_to_str
    )
    sea = _rows(
        'SELECT date, temp_c FROM sea_temp_data '
        'WHERE station = ? AND date BETWEEN ? AND ? ORDER BY date ASC',
        city, date_from_str, date_to_str
    )

    return jsonify({
        'air': [{'date': d, 'temp': t} for d, t in air],
        'sea': [{'date': d, 'temp': t} for d, t in sea],
    })
