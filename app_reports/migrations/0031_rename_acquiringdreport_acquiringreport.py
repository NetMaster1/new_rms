# Generated by Django 3.2.4 on 2024-02-26 10:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0030_rename_shop_acquiringdreport_tid'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AcquiringdReport',
            new_name='AcquiringReport',
        ),
    ]
