# Generated by Django 3.2.4 on 2024-03-21 11:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0007_document_shop_being_invetoried'),
    ]

    operations = [
        migrations.RenameField(
            model_name='document',
            old_name='shop_being_invetoried',
            new_name='shop_being_inventoried',
        ),
    ]
