# Generated by Django 3.2.4 on 2022-01-01 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0021_auto_20220101_1905'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysalerep',
            name='return_sum',
            field=models.IntegerField(null=True),
        ),
    ]
