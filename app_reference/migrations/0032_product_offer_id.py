# Generated by Django 3.2.4 on 2024-09-01 23:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0031_alter_product_ozon_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='offer_id',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
