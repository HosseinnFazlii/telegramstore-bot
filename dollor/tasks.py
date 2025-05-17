import requests
import logging
from bs4 import BeautifulSoup
from django.utils import timezone
from celery import shared_task
from .models import DollorPrice

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
                # Get or create one row only
                obj, created = DollorPrice.objects.get_or_create(title=title, defaults={
                    "price": usd_price,
                    "recorded_at": timezone.now()
                })

                if not created and obj.price != usd_price:
                    obj.price = usd_price
                    obj.recorded_at = timezone.now()
                    obj.save()
                    logging.info(f"✅ USD price updated to {usd_price}")
                elif not created:
                    logging.info(f"ℹ️ USD price unchanged: {usd_price}")
        else:
            logging.error(f"❌ Error fetching USD page: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Exception in fetch_and_save_usd_price: {e}")
