from django.contrib import admin
from .models import DollorPrice  # Adjust the import path if needed

@admin.register(DollorPrice)
class DollorPriceAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'recorded_at')
    list_filter = ('title', 'recorded_at')
    search_fields = ('title', 'price', 'description')
    ordering = ('-recorded_at',)
