import requests
import logging
from decimal import Decimal, InvalidOperation
from celery import shared_task
from bs4 import BeautifulSoup
from django.utils import timezone

from .models import GoldPrice, Coin  # ✅ Include Coin model
from store.models import Product

# Mapping Persian titles to short internal keys
TITLE_MAPPING = {
    "هرگرم طلای 18 عیار": "price-5",
    "هرگرم(طلای آب شده18عیار)": "price-6",
    "سکه تمام طرح امام (جدید)": "price-4",
    "سکه نیم بهار آزادی": "price-10",
    "سکه ربع بهار آزادی": "price-3",
    "سکه تمام تاریخ پایین": "price-9",
    "سکه نیم تاریخ پایین": "price-7",
    "سکه ربع تاریخ پایین": "price-8",
}

def extract_gold_prices(html):
    soup = BeautifulSoup(html, "html.parser")
    prices = {}
    for persian_title, price_id in TITLE_MAPPING.items():
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

        prices = extract_gold_prices(response.text)
        changed_prices = {}

        for title, data in prices.items():
            new_price = data["price"]
            description = data["description"]

            last_record = GoldPrice.objects.filter(title=title).order_by("-recorded_at").first()
            if not last_record or last_record.price != new_price:
                if last_record:
                    last_record.price = new_price
                    last_record.recorded_at = timezone.now()
                    last_record.description = description
                    last_record.save()
                else:
                    GoldPrice.objects.create(
                        title=title,
                        price=new_price,
                        description=description,
                        recorded_at=timezone.now()
                    )
                changed_prices[title] = new_price

        # ✅ If price-5 (18-carat gold) changed → update product and coin prices
        if "price-5" in changed_prices:
            try:
                price5 = Decimal(changed_prices["price-5"].replace(",", "").strip())

                # Update product prices
                for product in Product.objects.all():
                    base = price5 * product.weight
                    markup = base * (product.coefficient / Decimal("100"))
                    product.price = base + markup
                    product.save()

                # Update coin prices
                for coin in Coin.objects.all():
                    base = price5 * coin.weight
                    markup = base * Decimal("0.07")  # 7%
                    coin.price = base + markup + Decimal("15000")
                    coin.save()

            except (InvalidOperation, Exception) as e:
                logging.error(f"❌ Failed to update product/coin prices: {e}")

    except Exception as e:
        logging.error(f"❌ Exception in fetch_and_save_gold_prices: {e}")






from .models import ScheduledSMS
from store.models import TelegramUser
from .utils import send_bulk_sms
from django.utils.timezone import localtime, now

@shared_task
def send_scheduled_sms():
    current_time = localtime(now()).time()

    sms_obj = ScheduledSMS.objects.filter(is_active=True, scheduled_time__hour=current_time.hour, scheduled_time__minute=current_time.minute).first()

    if sms_obj:
        phone_numbers = list(TelegramUser.objects.filter(phone_number__isnull=False).values_list('phone_number', flat=True))
        # Remove leading 0 and add 98 for SMS.ir format
        formatted = [f"98{p[1:]}" for p in phone_numbers if p.startswith('0')]
        send_bulk_sms(sms_obj.message, formatted[:100])  # SMS.ir max 100 numbers per request