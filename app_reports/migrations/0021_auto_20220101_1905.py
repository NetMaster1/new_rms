# Generated by Django 3.2.4 on 2022-01-01 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0020_auto_20220101_1539'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysalerep',
            name='card',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='dailysalerep',
            name='cash_move',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='dailysalerep',
            name='credit',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='dailysalerep',
            name='expenses',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='dailysalerep',
            name='salary',
            field=models.IntegerField(null=True),
        ),
    ]
