import os
from datetime import datetime

# Set BASE_DIR to use the environment variable directly, or fall back to local calculation
BASE_DIR = os.getenv("BASE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(f"[DEBUG] {BASE_DIR=}")

# Define paths based on BASE_DIR
BASE_URL = "https://stampar.hr/hr/peludna-prognoza"
DATE = datetime.now()
DATA_DIR = os.path.join(BASE_DIR, "data", str(DATE.year), str(DATE.month))
print(f"[DEBUG] {DATA_DIR=}")
DB_PATH = os.path.join(BASE_DIR, "db", "pollen_data.db")
print(f"[DEBUG] {DB_PATH=}")
LOG_FILE = os.path.join(BASE_DIR, "logs", "scraping.log")

# Telegram settings (replace with actual token and chat ID)
TELEGRAM_TOKEN = "your_telegram_token"
CHAT_ID = "your_chat_id"