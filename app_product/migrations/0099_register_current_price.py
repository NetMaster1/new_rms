# Generated by Django 3.2.4 on 2021-12-06 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0098_rename_receiver_register_cash_receiver'),
    ]

    operations = [
        migrations.AddField(
            model_name='register',
            name='current_price',
            field=models.IntegerField(null=True),
        ),
    ]
