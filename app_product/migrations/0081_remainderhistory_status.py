# Generated by Django 3.2.4 on 2021-11-04 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0080_auto_20211101_1316'),
    ]

    operations = [
        migrations.AddField(
            model_name='remainderhistory',
            name='status',
            field=models.BooleanField(default=False),
        ),
    ]