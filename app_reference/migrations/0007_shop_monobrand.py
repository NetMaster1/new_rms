# Generated by Django 4.1.7 on 2023-10-01 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0006_teko_pay'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='monobrand',
            field=models.BooleanField(default=True),
        ),
    ]
