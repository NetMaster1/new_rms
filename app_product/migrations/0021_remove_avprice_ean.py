# Generated by Django 3.2.4 on 2025-03-06 14:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0020_auto_20250306_1435'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='avprice',
            name='ean',
        ),
    ]
