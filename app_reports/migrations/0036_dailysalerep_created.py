# Generated by Django 3.2.4 on 2022-02-20 11:59

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0035_auto_20220220_1328'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysalerep',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
    ]
