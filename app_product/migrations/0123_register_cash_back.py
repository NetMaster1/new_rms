# Generated by Django 3.2.4 on 2022-02-02 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0122_alter_remainderhistory_supplier'),
    ]

    operations = [
        migrations.AddField(
            model_name='register',
            name='cash_back',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]