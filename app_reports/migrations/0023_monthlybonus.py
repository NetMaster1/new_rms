# Generated by Django 3.2.4 on 2022-01-06 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reports', '0022_dailysalerep_return_sum'),
    ]

    operations = [
        migrations.CreateModel(
            name='MonthlyBonus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('smarphones', models.IntegerField(null=True)),
                ('accessories', models.IntegerField(null=True)),
                ('sim_cards', models.IntegerField(null=True)),
                ('phones', models.IntegerField(null=True)),
                ('iphone', models.IntegerField(null=True)),
                ('insuranсе', models.IntegerField(null=True)),
                ('wink', models.IntegerField(null=True)),
                ('services', models.IntegerField(null=True)),
                ('sub_total', models.IntegerField(null=True)),
                ('credit', models.IntegerField(null=True)),
                ('final_balance', models.IntegerField(null=True)),
            ],
        ),
    ]
