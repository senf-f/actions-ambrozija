import os
from datetime import datetime

# Use GITHUB_WORKSPACE if available (in GitHub Actions), else fall back to local logic
BASE_DIR = os.getenv("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define paths based on BASE_DIR
BASE_URL = "https://stampar.hr/hr/peludna-prognoza"
DATE = datetime.now()
DATA_DIR = os.path.join(BASE_DIR, "data", str(DATE.year), str(DATE.month))
DB_PATH = os.path.join(BASE_DIR, "db", "pollen_data.db")
LOG_FILE = os.path.join(BASE_DIR, "logs", "scraping.log")

# Telegram settings (replace with actual token and chat ID)
TELEGRAM_TOKEN = "your_telegram_token"
CHAT_ID = "your_chat_id"