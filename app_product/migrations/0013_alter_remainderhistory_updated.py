# Generated by Django 3.2.4 on 2024-03-22 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0012_remainderhistory_updated'),
    ]

    operations = [
        migrations.AlterField(
            model_name='remainderhistory',
            name='updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
