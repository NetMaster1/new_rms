# Generated by Django 3.2.4 on 2024-04-07 21:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0019_month_year'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='month',
            name='key',
        ),
        migrations.RemoveField(
            model_name='year',
            name='key',
        ),
    ]
