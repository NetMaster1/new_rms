# Generated by Django 3.2.4 on 2024-02-26 10:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0029_acquiringdreport'),
    ]

    operations = [
        migrations.RenameField(
            model_name='acquiringdreport',
            old_name='shop',
            new_name='TID',
        ),
    ]
