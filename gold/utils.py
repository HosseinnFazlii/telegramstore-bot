import requests
from django.conf import settings
import logging
from decouple import config

def send_bulk_sms(message, phone_list):
    url = "https://api.sms.ir/v1/send/bulk"
    api_key = config('SMSIR_API_KEY')
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "lineNumber": int(settings.SMSIR_LINE_NUMBER),
        "messageText": message,
        "mobiles": phone_list,
        "sendDateTime": None  # Optional: schedule if needed
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logging.error(f"❌ Error sending bulk SMS: {e}")
        return None
