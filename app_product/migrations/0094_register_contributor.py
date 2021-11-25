# Generated by Django 3.2.4 on 2021-11-25 22:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0016_contributor'),
        ('app_product', '0093_alter_register_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='register',
            name='contributor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.contributor'),
        ),
    ]
