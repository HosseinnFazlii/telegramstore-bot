from django.contrib import admin
from .models import (
    Product, ProductImage,
    TelegramBotToken, PreparedMessage,
    TelegramUser
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    min_num = 1
    max_num = 10

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'weight']
    search_fields = ['name', 'description']
    list_filter = ['price', 'weight']
    inlines = [ProductImageInline]

@admin.register(TelegramBotToken)
class TelegramBotTokenAdmin(admin.ModelAdmin):
    list_display = ['token', 'created_at']
    readonly_fields = ['created_at']
    search_fields = ['token']
    list_filter = ['created_at']

@admin.register(PreparedMessage)
class PreparedMessageAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at']
    list_filter = ['created_at']

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'phone_number', 'started_at']
    search_fields = ['telegram_id', 'phone_number']
    readonly_fields = ['started_at']
    list_filter = ['started_at']
