# Generated by Django 3.2.4 on 2024-04-10 09:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0014_register_updated'),
        ('app_kpi', '0004_alter_kpimonthlyplan_shop'),
    ]

    operations = [
        migrations.AddField(
            model_name='kpi_performance',
            name='identifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.identifier'),
        ),
    ]
