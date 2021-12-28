# Generated by Django 3.2.4 on 2021-12-28 08:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0105_remainderhistory_inventory_doc'),
        ('app_cash', '0023_cash_sender'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentRegister',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateField(auto_now_add=True)),
                ('cash', models.IntegerField(default=0)),
                ('card', models.IntegerField(default=0)),
                ('credit', models.IntegerField(default=0)),
                ('document', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.document')),
            ],
        ),
    ]
