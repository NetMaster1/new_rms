# Generated by Django 3.2.4 on 2022-02-20 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0037_alter_dailysalerep_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysalerep',
            name='pay_cards',
            field=models.IntegerField(null=True),
        ),
    ]
