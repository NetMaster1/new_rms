# Generated by Django 3.2.4 on 2022-02-03 16:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0131_auto_20220203_1855'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='remainderhistory',
            name='cash_back_awarded',
        ),
    ]