# Generated by Django 3.2.4 on 2024-02-25 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0026_alter_sim_report_wd_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlybonus',
            name='cashback',
            field=models.IntegerField(null=True),
        ),
    ]
