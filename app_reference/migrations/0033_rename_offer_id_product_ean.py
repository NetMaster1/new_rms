# Generated by Django 3.2.4 on 2024-09-07 07:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0032_product_offer_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='offer_id',
            new_name='EAN',
        ),
    ]