import os
from datetime import datetime

# URL and paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BASE_URL = "https://stampar.hr/hr/peludna-prognoza"
DATE = datetime.now()
DATA_DIR = os.path.join(BASE_DIR, "data", str(DATE.year), str(DATE.month))
DB_PATH = os.path.join(BASE_DIR, "db", "pollen_data.db")
LOG_FILE = os.path.join(BASE_DIR, "logs", "scraping.log")

# Telegram settings (replace with actual token and chat ID)
TELEGRAM_TOKEN = "your_telegram_token"
CHAT_ID = "your_chat_id"