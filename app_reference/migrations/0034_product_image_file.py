# Generated by Django 3.2.4 on 2025-02-19 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0033_rename_offer_id_product_ean'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image_file',
            field=models.FileField(null=True, upload_to='uploads'),
        ),
    ]
