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

    try:
        line_number = int(settings.SMSIR_LINE_NUMBER)
    except Exception as e:
        logging.error(f"⚠️ Invalid line number in settings: {e}")
        return None

# Format phone numbers (e.g., 0912... to 98912...)
    formatted_numbers = [f"98{p[1:]}" if p.startswith("09") else p for p in phone_list]
    # formatted_numbers=formatted_numbers[:10]
    payload = {
        "lineNumber": line_number,
        "messageText": message,
        "mobiles": formatted_numbers,
        "sendDateTime": None  # Optional: schedule if needed
    }

    logging.warning("📤 Sending SMS bulk request to SMS.ir")
    logging.warning(f"🔢 Line Number: {line_number}")
    logging.warning(f"📨 Message Text: {message}")
    logging.warning(f"📱 Mobiles: {formatted_numbers}")
    logging.warning(f"📦 Payload: {payload}")

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        logging.warning(f"📥 Response status: {res.status_code}")
        logging.warning(f"📥 Response text: {res.text}")

        res.raise_for_status()
        return res.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"❌ HTTP Error sending bulk SMS: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Request Exception sending bulk SMS: {e}")
    except Exception as e:
        logging.error(f"❌ General Exception sending bulk SMS: {e}")

    return None
