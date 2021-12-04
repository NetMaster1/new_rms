# Generated by Django 3.2.4 on 2021-10-02 12:57

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0010_auto_20211002_1554'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportTempId',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='reporttemp',
            name='created',
        ),
        migrations.AddField(
            model_name='reporttemp',
            name='report_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reports.reporttempid'),
        ),
    ]