# Generated by Django 3.2.4 on 2022-02-20 20:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0044_remove_dailysalerep_sub_total'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dailysalerep',
            name='sum',
        ),
    ]
