# Generated by Django 3.2.4 on 2024-08-09 23:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0024_productcategory_bonus_percent_1'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='ozon_id',
            field=models.CharField(max_length=50, null=True, unique=True),
        ),
    ]
