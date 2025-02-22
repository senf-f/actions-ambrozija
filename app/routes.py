from flask import render_template
from app import app
from src.db_handler import setup_db

@app.route('/')
def index():
    conn = setup_db()
    cursor = conn.cursor()
    query = '''
        SELECT city, plant, pollen_concentration, date
        FROM pollen_data
        ORDER BY date DESC
    '''
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return render_template('index.html', data=data)