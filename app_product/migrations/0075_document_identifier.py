# Generated by Django 3.2.4 on 2021-10-12 16:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0074_document_posted'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='identifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.identifier'),
        ),
    ]
