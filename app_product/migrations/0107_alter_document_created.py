# Generated by Django 3.2.4 on 2022-01-02 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0106_document_shop'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='created',
            field=models.DateTimeField(null=True),
        ),
    ]
