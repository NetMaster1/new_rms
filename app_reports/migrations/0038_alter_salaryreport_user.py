# Generated by Django 3.2.4 on 2024-02-28 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0037_salaryreport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salaryreport',
            name='user',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
