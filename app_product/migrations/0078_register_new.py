# Generated by Django 3.2.4 on 2021-10-17 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0077_register_supplier'),
    ]

    operations = [
        migrations.AddField(
            model_name='register',
            name='new',
            field=models.BooleanField(default=False),
        ),
    ]