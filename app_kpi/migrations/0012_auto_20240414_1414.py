# Generated by Django 3.2.4 on 2024-04-14 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_kpi', '0011_gi_report_gi_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='gi_report',
            name='date_before_current',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='gi_report',
            name='days_of_the_month',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
