from django.db import models
from django.utils import timezone
import uuid

class GoldPrice(models.Model):
    title = models.CharField(max_length=255)  # e.g., "price-5"
    description = models.CharField(max_length=255, blank=True)  # e.g., "طلای ۱۸ عیار"
    price = models.CharField(max_length=50)
    recorded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.description or self.title}: {self.price} ({self.recorded_at.strftime('%Y-%m-%d %H:%M')})"

    @staticmethod
    def get_last_price(title):
        last_entry = GoldPrice.objects.filter(title=title).order_by('-recorded_at').first()
        return last_entry.price if last_entry else None
    



class Coin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, )
    description = models.TextField(blank=True, )
    price = models.DecimalField(max_digits=12, decimal_places=2, )
    weight = models.DecimalField(max_digits=6, decimal_places=2, )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.price} تومان"