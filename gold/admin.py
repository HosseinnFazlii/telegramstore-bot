from django.contrib import admin
from .models import GoldPrice

@admin.register(GoldPrice)
class GoldPriceAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "price", "recorded_at")
    list_filter = ("title", "description", "recorded_at")
    search_fields = ("title", "description", "price")
    ordering = ("-recorded_at",)
    actions = ['delete_selected']  # ✅ explicitly allow deletion

    def has_delete_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return True
