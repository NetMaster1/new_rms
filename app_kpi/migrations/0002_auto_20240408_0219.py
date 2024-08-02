# Generated by Django 3.2.4 on 2024-04-07 23:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0021_month_number_of_days'),
        ('app_kpi', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='kpimonthlyplan',
            name='period_reported',
        ),
        migrations.AddField(
            model_name='kpimonthlyplan',
            name='month_reported',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.month'),
        ),
        migrations.AddField(
            model_name='kpimonthlyplan',
            name='year_reported',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.year'),
        ),
    ]
