# Generated by Django 3.2.4 on 2021-07-25 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0049_transfer_sub_total'),
    ]

    operations = [
        migrations.CreateModel(
            name='AveragePriceCurrent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated', models.DateTimeField(auto_now=True)),
                ('imei', models.CharField(max_length=250)),
                ('name', models.CharField(max_length=250, null=True)),
                ('av_price_current', models.IntegerField(null=True)),
            ],
        ),
    ]