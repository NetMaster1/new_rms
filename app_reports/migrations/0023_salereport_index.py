# Generated by Django 3.2.4 on 2023-03-10 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0022_alter_clientreport_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='salereport',
            name='index',
            field=models.IntegerField(default=0),
        ),
    ]
