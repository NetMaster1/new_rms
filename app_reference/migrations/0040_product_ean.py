# Generated by Django 3.2.4 on 2025-02-20 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0039_product_ean'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='ean',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
