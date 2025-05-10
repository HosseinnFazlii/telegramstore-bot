import requests
import logging
from decimal import Decimal, InvalidOperation
from celery import shared_task
from bs4 import BeautifulSoup
from django.utils import timezone
from datetime import timedelta

from .models import GoldPrice
from store.models import Product


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
            logging.error(f"Error fetching gold prices: HTTP {response.status_code}")
            return

        prices = extract_gold_prices(response.text)
        changed_prices = {}
        now_time = timezone.now()

        for title, new_price in prices.items():
            # ✅ Prevent duplicate saves within 30 minutes for same title/price
            exists = GoldPrice.objects.filter(
                title=title,
                price=new_price,
                recorded_at__gte=now_time - timedelta(minutes=30)
            ).exists()

            if not exists:
                changed_prices[title] = new_price
                GoldPrice.objects.create(
                    title=title,
                    price=new_price,
                    recorded_at=now_time
                )

        # ✅ If 18-carat gold changed → update all products
        if "هرگرم طلای 18 عیار" in changed_prices:
            try:
                raw_price = changed_prices["هرگرم طلای 18 عیار"].replace(",", "").strip()
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
