# Generated by Django 3.2.4 on 2025-02-20 10:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0038_alter_sku_ean'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='EAN',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.sku'),
        ),
    ]
