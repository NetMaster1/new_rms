# Generated by Django 3.2.4 on 2022-02-02 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0119_remainderhistory_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='remainderhistory',
            name='cash_back_paid',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
