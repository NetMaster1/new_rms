# Generated by Django 3.2.4 on 2024-12-31 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0045_dailysalerep_teko_payments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salereport',
            name='product',
            field=models.CharField(max_length=150, null=True),
        ),
    ]
