import os
from pathlib import Path
from datetime import datetime

# Set BASE_DIR to use the environment variable directly, or fall back to local calculation
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define paths based on BASE_DIR
BASE_URL = "https://stampar.hr/hr/peludna-prognoza"
DATE = datetime.now()
today = datetime.today()
DATA_DIR = Path("data") / str(today.year) / str(today.month) / str(today.day)
DB_PATH = os.path.join(BASE_DIR, "db", "pollen_data.db")
LOG_FILE = os.path.join(BASE_DIR, "logs", "scraping.log")

# Telegram settings (replace with actual token and chat ID)
TELEGRAM_TOKEN = "your_telegram_token"
CHAT_ID = "your_chat_id"
