# Generated by Django 3.2.4 on 2022-07-11 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='status',
            field=models.BooleanField(default=False),
        ),
    ]
