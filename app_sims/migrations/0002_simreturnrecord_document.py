# Generated by Django 4.0.5 on 2022-07-12 10:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0001_initial'),
        ('app_sims', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='simreturnrecord',
            name='document',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.document'),
        ),
    ]