# Generated by Django 3.2.4 on 2024-02-28 11:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app_reports', '0036_expensesreport'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalaryReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('sum', models.IntegerField(null=True)),
                ('report_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reports.reporttempid')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
