# Generated by Django 3.2.4 on 2024-04-25 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0039_dailysalerep_rt_equipment'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlybonus',
            name='RT_equipment',
            field=models.IntegerField(null=True),
        ),
    ]
