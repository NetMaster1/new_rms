# Generated by Django 4.1.7 on 2023-12-05 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0010_shop_shift_status_updated'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shop',
            name='shift_status_updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
