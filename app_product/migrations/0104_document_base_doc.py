# Generated by Django 3.2.4 on 2021-12-19 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0103_alter_register_real_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='base_doc',
            field=models.IntegerField(null=True),
        ),
    ]
