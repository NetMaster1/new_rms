# Generated by Django 3.2.4 on 2021-07-01 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0003_productcategory_cashback_percent'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcategory',
            name='bonus_percent',
            field=models.IntegerField(default=1),
        ),
    ]
