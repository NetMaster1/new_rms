# Generated by Django 3.2.4 on 2024-03-21 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0009_remove_document_shop_being_inventoried'),
    ]

    operations = [
        migrations.AlterField(
            model_name='register',
            name='reevaluation_price',
            field=models.IntegerField(default=0),
        ),
    ]