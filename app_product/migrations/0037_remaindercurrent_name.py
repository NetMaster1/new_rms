# Generated by Django 3.2.4 on 2021-07-08 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0036_alter_document_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='remaindercurrent',
            name='name',
            field=models.CharField(max_length=250, null=True),
        ),
    ]