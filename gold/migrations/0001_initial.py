# Generated by Django 4.2.9 on 2025-02-24 06:02

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GoldPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('price', models.CharField(max_length=50)),
                ('recorded_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
