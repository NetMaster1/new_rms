# Generated by Django 3.2.4 on 2021-08-06 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_cashback', '0003_alter_cashback_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cashback',
            name='size',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=3),
        ),
    ]