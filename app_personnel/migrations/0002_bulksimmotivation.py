# Generated by Django 3.2.4 on 2022-07-25 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_personnel', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BulkSimMotivation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sim_price', models.IntegerField(default=0)),
                ('bonus_per_sim', models.IntegerField(default=0)),
            ],
        ),
    ]