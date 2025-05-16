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


from django.contrib import admin
from .models import ChannelMessage
from django import forms

class ChannelMessageForm(forms.ModelForm):
    class Meta:
        model = ChannelMessage
        fields = '__all__'
        widgets = {
            'scheduled_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'scheduled_datetime': forms.DateTimeInput(format='%Y-%m-%d %H:%M', attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        schedule_type = cleaned_data.get("schedule_type")
        scheduled_time = cleaned_data.get("scheduled_time")
        scheduled_datetime = cleaned_data.get("scheduled_datetime")

        if schedule_type == "daily" and not scheduled_time:
            raise forms.ValidationError("برای حالت روزانه، زمان باید مشخص شود.")
        if schedule_type == "once" and not scheduled_datetime:
            raise forms.ValidationError("برای ارسال یک‌باره، تاریخ و زمان باید مشخص شود.")

@admin.register(ChannelMessage)
class ChannelMessageAdmin(admin.ModelAdmin):
    form = ChannelMessageForm
    list_display = ['title', 'schedule_type', 'scheduled_time', 'scheduled_datetime', 'sent']
    list_filter = ['schedule_type', 'sent']