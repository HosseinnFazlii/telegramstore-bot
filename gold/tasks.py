import requests
import logging
from decimal import Decimal, InvalidOperation
from celery import shared_task
from bs4 import BeautifulSoup
from django.utils import timezone

from .models import GoldPrice
from store.models import Product


def extract_gold_prices(html):
    soup = BeautifulSoup(html, "html.parser")
    # Persian display name → HTML ID
    target_titles = {
        "هرگرم طلای 18 عیار": "price-5",
        "هرگرم(طلای آب شده18عیار)": "price-6",
        "سکه تمام طرح امام (جدید)": "price-4",
        "سکه نیم بهار آزادی": "price-10",
        "سکه ربع بهار آزادی": "price-3",
    }

    prices = {}
    for persian_title, price_id in target_titles.items():
        price_tag = soup.find("div", id=price_id) or soup.find("span", id=price_id)
        if price_tag:
            prices[price_id] = {
                "price": price_tag.get_text(strip=True),
                "description": persian_title
            }

    return prices


@shared_task
def fetch_and_save_gold_prices():
    url = "https://savehzar.ir/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logging.error(f"Error fetching gold prices: HTTP {response.status_code}")
            return

        extracted = extract_gold_prices(response.text)
        changed_prices = {}

        for price_id, data in extracted.items():
            new_price = data["price"]
            description = data["description"]

            last_entry = GoldPrice.objects.filter(title=price_id).order_by('-recorded_at').first()
            if not last_entry or last_entry.price != new_price:
                GoldPrice.objects.create(
                    title=price_id,
                    price=new_price,
                    description=description,
                    recorded_at=timezone.now()
                )
                changed_prices[price_id] = new_price

        # ✅ Update products only if price-5 (18K gold) changed
        if "price-5" in changed_prices:
            try:
                raw_price = changed_prices["price-5"].replace(",", "").strip()
                base_price = Decimal(raw_price)

                for product in Product.objects.all():
                    base = base_price * product.weight
                    markup = base * (product.coefficient / Decimal("100"))
                    product.price = base + markup
                    product.save()

            except (InvalidOperation, Exception) as e:
                logging.error(f"❌ Failed to update product prices: {e}")

    except Exception as e:
        logging.error(f"❌ Exception in fetch_and_save_gold_prices: {e}")
