# Generated by Django 3.2.4 on 2022-09-21 23:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0021_auto_20220921_2344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientreport',
            name='count',
            field=models.IntegerField(null=True),
        ),
    ]
