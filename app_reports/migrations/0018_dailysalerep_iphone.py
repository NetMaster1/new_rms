# Generated by Django 3.2.4 on 2021-12-30 23:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0017_dailysalerep'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysalerep',
            name='Iphone',
            field=models.IntegerField(null=True),
        ),
    ]
