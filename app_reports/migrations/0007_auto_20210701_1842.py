# Generated by Django 3.2.4 on 2021-07-01 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0006_alter_producthistory_imei'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='producthistory',
            name='quantity',
        ),
        migrations.AddField(
            model_name='producthistory',
            name='quantity_in',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='producthistory',
            name='quantity_out',
            field=models.IntegerField(null=True),
        ),
    ]
