from flask import Flask

from src.db_handler import setup_db

app = Flask(__name__)

# Initialize DB once at startup
setup_db()

from app import routes