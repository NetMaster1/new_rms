# Generated by Django 3.2.4 on 2021-07-04 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0024_alter_remainderhistory_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='remaindercurrent',
            name='retail_price',
            field=models.IntegerField(default=0, null=True),
        ),
    ]