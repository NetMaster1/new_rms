# Generated by Django 3.2.4 on 2024-02-26 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0014_delete_subdealer'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
