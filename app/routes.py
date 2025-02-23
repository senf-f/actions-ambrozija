from flask import render_template, request

from app import app
from src.db_handler import setup_db


@app.route('/')
def index():
    conn = setup_db()
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
