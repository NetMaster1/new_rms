# Generated by Django 3.2.4 on 2024-08-10 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0025_product_ozon_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='for_mp_sale',
            field=models.BooleanField(default=False),
        ),
    ]