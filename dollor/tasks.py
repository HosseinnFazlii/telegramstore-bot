import requests
import logging
from bs4 import BeautifulSoup
from django.utils import timezone
from celery import shared_task
from .models import DollorPrice
from django.utils.timezone import now, localdate

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
    title = "USD"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            usd_price = extract_usd_price(response.text)
            if usd_price:
                already_exists = DollorPrice.objects.filter(
                    title=title,
                    price=usd_price,
                    recorded_at__date=localdate()
                ).exists()

                if not already_exists:
                    DollorPrice.objects.create(
                        title=title,
                        price=usd_price,
                        recorded_at=timezone.now()
                    )
                    logging.info(f"✅ New USD price saved: {usd_price}")
                else:
                    logging.info(f"⚠️ USD price '{usd_price}' already exists today, skipping.")
        else:
            logging.error(f"Error fetching USD page: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Exception in fetch_and_save_usd_price: {e}")
