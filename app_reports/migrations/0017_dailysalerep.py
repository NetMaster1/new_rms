# Generated by Django 3.2.4 on 2021-12-30 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0016_delete_dailysaletemp'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailySaleRep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shop', models.CharField(max_length=50, null=True)),
                ('smarphones', models.IntegerField(null=True)),
                ('accessories', models.IntegerField(null=True)),
                ('sim_cards', models.IntegerField(null=True)),
                ('phones', models.IntegerField(null=True)),
                ('insuranсе', models.IntegerField(null=True)),
                ('wink', models.IntegerField(null=True)),
                ('services', models.IntegerField(null=True)),
                ('sub_total', models.IntegerField(null=True)),
            ],
        ),
    ]