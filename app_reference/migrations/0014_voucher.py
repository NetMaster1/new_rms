# Generated by Django 3.2.4 on 2021-10-11 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0013_expense'),
    ]

    operations = [
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
    ]
