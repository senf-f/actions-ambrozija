"""Telegram alerts. Silently skipped when the bot is not configured (local runs)."""
import os

import requests


def send(text):
    token = os.environ.get("TELEGRAM_API_TOKEN_STAMPAR")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id):
        print(f"[telegram] not configured, skipping: {text}")
        return

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        # An undelivered alert must not fail a scrape whose data is already stored.
        print(f"[telegram] send failed: {e}")
