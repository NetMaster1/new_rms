# Generated by Django 3.2.4 on 2021-12-04 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_cash', '0022_alter_cash_cash_contributor'),
    ]

    operations = [
        migrations.AddField(
            model_name='cash',
            name='sender',
            field=models.BooleanField(default=False),
        ),
    ]
