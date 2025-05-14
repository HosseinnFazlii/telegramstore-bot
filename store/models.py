import uuid
from django.db import models

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    coefficient=models.DecimalField(max_digits=12, decimal_places=2)
    weight = models.DecimalField(max_digits=6, decimal_places=2, help_text="Weight in grams")

    def __str__(self):
        return self.name

# Product image model (linked to Product)
class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return f"Image for {self.product.name}"

# Telegram Bot Token model
class TelegramBotToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token created at {self.created_at}"

# Prepared Message (for marketing)
class PreparedMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# Telegram Bot User (for phone numbers)
class TelegramUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    telegram_id = models.BigIntegerField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.telegram_id)
    


class ChannelMessage(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    # Example: 'daily:08:00' or 'once:2025-05-13 21:00'
    schedule_type = models.CharField(max_length=10, choices=[('daily', 'Daily'), ('once', 'Once')])
    scheduled_time = models.TimeField(null=True, blank=True)       # for daily
    scheduled_datetime = models.DateTimeField(null=True, blank=True)  # for once
    sent = models.BooleanField(default=False)  # To prevent re-sending 'once'

    def __str__(self):
        return self.title