# Generated by Django 3.2.4 on 2021-06-07 09:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sale',
            name='category',
        ),
    ]
