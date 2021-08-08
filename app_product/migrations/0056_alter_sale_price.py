# Generated by Django 3.2.4 on 2021-08-06 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0055_alter_sale_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
    ]