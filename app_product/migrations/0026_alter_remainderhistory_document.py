# Generated by Django 3.2.4 on 2021-07-04 11:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0025_remaindercurrent_retail_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='remainderhistory',
            name='document',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.document'),
        ),
    ]