# Generated by Django 3.2.4 on 2021-09-12 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0065_alter_register_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='register',
            name='quantity',
            field=models.IntegerField(default=1),
        ),
    ]