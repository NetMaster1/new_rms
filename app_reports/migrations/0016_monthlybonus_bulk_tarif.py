# Generated by Django 3.2.4 on 2022-07-25 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0015_rename_gadjets_monthlybonus_gadgets'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlybonus',
            name='bulk_tarif',
            field=models.IntegerField(null=True),
        ),
    ]
