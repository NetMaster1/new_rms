# Generated by Django 3.2.4 on 2024-04-10 20:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_kpi', '0006_remove_kpi_performance_identifier'),
    ]

    operations = [
        migrations.RenameField(
            model_name='kpi_performance',
            old_name='HomeInternet',
            new_name='HomeInternet_RT',
        ),
        migrations.AddField(
            model_name='kpi_performance',
            name='HomeInternet_T2',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
