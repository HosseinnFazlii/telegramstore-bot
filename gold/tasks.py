import requests
import logging
from celery import shared_task
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import GoldPrice
from store.models import Product  # ✅ Needed for updating product prices

def extract_gold_prices(html):
    soup = BeautifulSoup(html, "html.parser")
    target_titles = {
        "هرگرم طلای 18 عیار": "price-5",
        "هرگرم(طلای آب شده18عیار)": "price-6",
        "سکه تمام طرح امام (جدید)": "price-4",
        "سکه نیم بهار آزادی": "price-10",
        "سکه ربع بهار آزادی": "price-3",
    }

    prices = {}
    for title, price_id in target_titles.items():
        price_tag = soup.find("div", id=price_id) or soup.find("span", id=price_id)
        if price_tag:
            prices[title] = price_tag.get_text(strip=True)

    return prices


@shared_task
def fetch_and_save_gold_prices():
    url = "https://savehzar.ir/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logging.error(f"Error fetching page: HTTP {response.status_code}")
            return

        prices = extract_gold_prices(response.text)
        changed_prices = {}

        for title, new_price in prices.items():
            last_price = GoldPrice.get_last_price(title)
            if last_price != new_price:
                changed_prices[title] = new_price
                GoldPrice.objects.create(
                    title=title, price=new_price, recorded_at=timezone.now()
                )

        # ✅ If 18-carat gold price changed → update all products
        if "هرگرم طلای 18 عیار" in changed_prices:
            try:
                raw_price = changed_prices["هرگرم طلای 18 عیار"]
                base_price = int(raw_price.replace(",", "").strip())

                for product in Product.objects.all():
                    base = base_price * product.weight
                    markup = base * (product.coefficient / 100)
                    product.price = int(base + markup)
                    product.save()

            except Exception as e:
                logging.error(f"❌ Failed to update product prices: {e}")

    except Exception as e:
        logging.error(f"Exception in fetch_and_save_gold_prices: {e}")