# Generated by Django 3.2.4 on 2022-02-03 15:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0128_document_client'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='register',
            name='client_phone',
        ),
    ]
