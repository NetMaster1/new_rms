# Generated by Django 3.2.4 on 2024-08-09 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0014_register_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='remainderhistory',
            name='for_mp_sale',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='remainderhistory',
            name='mp_RRP',
            field=models.IntegerField(null=True),
        ),
    ]