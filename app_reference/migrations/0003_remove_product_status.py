# Generated by Django 3.2.4 on 2022-07-11 23:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0002_product_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='status',
        ),
    ]
