# Generated by Django 3.2.4 on 2021-11-04 21:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0015_auto_20211011_1008'),
        ('app_product', '0086_auto_20211105_0031'),
    ]

    operations = [
        migrations.AlterField(
            model_name='register',
            name='shop',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='shop', to='app_reference.shop'),
        ),
        migrations.AlterField(
            model_name='register',
            name='shop_sender',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='shop_sender', to='app_reference.shop'),
        ),
    ]
