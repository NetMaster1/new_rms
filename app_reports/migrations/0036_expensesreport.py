# Generated by Django 3.2.4 on 2024-02-28 10:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0035_alter_deliveryreport_supplier'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpensesReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('shop', models.CharField(max_length=50, null=True)),
                ('sum', models.IntegerField(null=True)),
                ('report_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reports.reporttempid')),
            ],
        ),
    ]
