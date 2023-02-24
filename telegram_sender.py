import os
import requests


def send_to_telegram(content):

    # print(os.environ)
    if "TELEGRAM_API_TOKEN_STAMPAR" in os.environ:
        api_token = os.environ["TELEGRAM_API_TOKEN_STAMPAR"]
        chat_id = os.environ["TELEGRAM_CHAT_ID"]

        api_url = f"https://api.telegram.org/bot{api_token}/sendMessage"

        try:
            response = requests.post(api_url, json={'chat_id': chat_id, 'text': content})
            print(response.text)
        except Exception as e:
            print(e)