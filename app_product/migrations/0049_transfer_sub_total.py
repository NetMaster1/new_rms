# Generated by Django 3.2.4 on 2021-07-21 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0048_remainderhistory_wholesale_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='transfer',
            name='sub_total',
            field=models.IntegerField(default=0),
        ),
    ]
