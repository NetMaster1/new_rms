# Generated by Django 3.2.4 on 2021-10-11 09:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_cash', '0017_cash_rho_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cash',
            old_name='rho_type',
            new_name='cho_type',
        ),
    ]