# Generated by Django 3.2.4 on 2024-10-27 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0044_effectivenessreport'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysalerep',
            name='teko_payments',
            field=models.IntegerField(null=True),
        ),
    ]
