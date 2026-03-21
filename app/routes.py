import sqlite3
from datetime import datetime

from flask import jsonify, render_template, request

from app import app
from src.config import DB_PATH


@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch unique cities, plants, and months for the dropdowns
    cursor.execute('SELECT DISTINCT city FROM pollen_data')
    cities = [row[0] for row in cursor.fetchall()]

    cursor.execute('SELECT DISTINCT plant FROM pollen_data')
    plants = [row[0] for row in cursor.fetchall()]

    cursor.execute('SELECT DISTINCT strftime("%Y-%m", date) as month FROM pollen_data ORDER BY month')
    months = [row[0] for row in cursor.fetchall()]

    # Get filter parameters
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


@app.route('/api/graph-data')
def graph_data():
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({'error': 'city is required'}), 400

    today = datetime.today()
    first_of_month = today.replace(day=1)

    date_from_str = request.args.get('date_from', '').strip() or first_of_month.strftime('%Y-%m-%d')
    date_to_str = request.args.get('date_to', '').strip() or today.strftime('%Y-%m-%d')

    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'invalid date format, expected YYYY-MM-DD'}), 400

    if date_from > date_to:
        return jsonify({'error': 'date_from must not be after date_to'}), 400

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
