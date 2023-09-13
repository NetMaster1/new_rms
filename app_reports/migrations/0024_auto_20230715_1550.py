# Generated by Django 3.2.4 on 2023-07-15 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0023_salereport_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producthistory',
            name='name',
            field=models.CharField(max_length=80),
        ),
        migrations.AlterField(
            model_name='reporttemp',
            name='name',
            field=models.CharField(max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='salereport',
            name='product',
            field=models.CharField(max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='sim_report',
            name='name',
            field=models.CharField(max_length=80, null=True),
        ),
    ]