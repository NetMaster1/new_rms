# Generated by Django 4.0.5 on 2022-07-12 10:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0009_alter_sim_report_return_mark'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sim_report',
            old_name='doc_type',
            new_name='status',
        ),
    ]
