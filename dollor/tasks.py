import requests
import logging
from bs4 import BeautifulSoup
from django.utils import timezone
from celery import shared_task
from .models import DollorPrice
import pytz
from django.utils.timezone import now

# Load Telegram credentials
def extract_usd_price(html):
    """Extracts the USD price from Mazaneh.net HTML."""
    soup = BeautifulSoup(html, "html.parser")
    usd_div = soup.find("div", id="USD")
    
    if usd_div:
        price_div = usd_div.find("div", class_="CurrencyPrice")
        if price_div:
            return price_div.get_text(strip=True)
    return None

@shared_task
def fetch_and_save_usd_price():
    url = "https://mazaneh.net/"
    title = "USD"  # Title used in your model to track this value
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            usd_price = extract_usd_price(response.text)
            if usd_price:
                last_price = DollorPrice.get_last_price(title)
                if last_price != usd_price:
                    # Save new USD price to the database
                    DollorPrice.objects.create(
                        title=title,
                        price=usd_price,
                        recorded_at=timezone.now()
                    )
        else:
            logging.error(f"Error fetching USD page: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"Exception in fetch_and_save_usd_price: {e}")