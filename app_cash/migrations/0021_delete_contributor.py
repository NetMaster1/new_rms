# Generated by Django 3.2.4 on 2021-11-25 22:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_cash', '0020_alter_contributor_name'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Contributor',
        ),
    ]