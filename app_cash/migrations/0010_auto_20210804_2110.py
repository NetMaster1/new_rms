# Generated by Django 3.2.4 on 2021-08-04 18:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0053_avprice'),
        ('app_cash', '0009_rename_credit_remainder_credit_sum'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='document',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.document'),
        ),
        migrations.AddField(
            model_name='credit',
            name='document',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.document'),
        ),
    ]
