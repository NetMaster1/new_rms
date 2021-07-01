# Generated by Django 3.2.4 on 2021-06-26 22:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0003_productcategory_cashback_percent'),
        ('app_cash', '0003_cash_document'),
    ]

    operations = [
        migrations.CreateModel(
            name='CashRemainder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remainder', models.IntegerField(default=0)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.shop')),
            ],
        ),
    ]
