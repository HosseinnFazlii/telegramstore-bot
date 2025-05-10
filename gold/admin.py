from django.contrib import admin
from .models import GoldPrice

@admin.register(GoldPrice)
class GoldPriceAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "recorded_at")
    list_filter = ("title", "recorded_at")
    search_fields = ("title", "price")
    ordering = ("-recorded_at",)
    actions = ["delete_selected"]  # ✅ Enable delete in list view
