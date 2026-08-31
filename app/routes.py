import sqlite3
from datetime import datetime

from flask import jsonify, render_template, request

from app import app
from src.config import DB_PATH


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
            'SELECT plant, date, pollen_concentration FROM pollen_data '
            'WHERE city = ? AND date BETWEEN ? AND ? ORDER BY date ASC',
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


@app.route('/api/temp-data')
def temp_data():
    """Air temperature (15h) and sea temperature (08h) for a city.

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
