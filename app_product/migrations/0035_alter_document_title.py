# Generated by Django 3.2.4 on 2021-07-05 17:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0009_documenttype'),
        ('app_product', '0034_alter_document_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.documenttype'),
        ),
    ]
