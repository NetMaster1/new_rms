# Generated by Django 4.0.5 on 2022-06-09 08:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app_reference', '0001_initial'),
        ('app_clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated', models.DateTimeField(auto_now=True)),
                ('imei', models.CharField(max_length=250)),
                ('name', models.CharField(max_length=250, null=True)),
                ('current_remainder', models.IntegerField(default=0)),
                ('av_price', models.IntegerField(null=True)),
                ('sum', models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('base_doc', models.IntegerField(null=True)),
                ('posted', models.BooleanField(default=False)),
                ('sum', models.IntegerField(null=True)),
                ('cashback_off', models.IntegerField(default=0)),
                ('sum_minus_cashback', models.IntegerField(blank=True, null=True)),
                ('client', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_clients.customer')),
            ],
        ),
        migrations.CreateModel(
            name='Identifier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RemainderHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(default=0, null=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('name', models.CharField(max_length=250)),
                ('imei', models.CharField(max_length=250)),
                ('sub_total', models.IntegerField(default=0)),
                ('wholesale_price', models.IntegerField(default=0, null=True)),
                ('av_price', models.IntegerField(default=0, null=True)),
                ('retail_price', models.IntegerField(default=0)),
                ('pre_remainder', models.IntegerField(default=0)),
                ('incoming_quantity', models.IntegerField(null=True)),
                ('outgoing_quantity', models.IntegerField(null=True)),
                ('current_remainder', models.BigIntegerField(default=0)),
                ('update_check', models.BooleanField(default=False)),
                ('status', models.BooleanField(default=False)),
                ('cash_back_awarded', models.IntegerField(blank=True, null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.productcategory')),
                ('document', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.document')),
                ('inventory_doc', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='inventory', to='app_product.document')),
                ('product_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.product')),
                ('rho_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.documenttype')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.shop')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.supplier')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='RemainderCurrent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated', models.DateTimeField(auto_now=True)),
                ('imei', models.CharField(max_length=250)),
                ('name', models.CharField(max_length=250, null=True)),
                ('current_remainder', models.IntegerField(default=0)),
                ('retail_price', models.IntegerField(default=0, null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.productcategory')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.shop')),
            ],
            options={
                'ordering': ('category', 'name'),
            },
        ),
        migrations.CreateModel(
            name='Register',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(null=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('imei', models.CharField(max_length=250, null=True)),
                ('name', models.CharField(max_length=250, null=True)),
                ('quantity', models.IntegerField(default=1)),
                ('real_quantity', models.IntegerField(null=True)),
                ('current_price', models.IntegerField(null=True)),
                ('price', models.IntegerField(default=0)),
                ('sub_total', models.BigIntegerField(default=0)),
                ('new', models.BooleanField(default=False)),
                ('deleted', models.BooleanField(default=False)),
                ('cash_receiver', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('contributor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.contributor')),
                ('doc_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.documenttype')),
                ('document', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.document')),
                ('expense', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.expense')),
                ('identifier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.identifier')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.product')),
                ('shop', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='shop', to='app_reference.shop')),
                ('supplier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.supplier')),
                ('voucher', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.voucher')),
            ],
        ),
        migrations.AddField(
            model_name='document',
            name='identifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.identifier'),
        ),
        migrations.AddField(
            model_name='document',
            name='shop_receiver',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='shop_receiver', to='app_reference.shop'),
        ),
        migrations.AddField(
            model_name='document',
            name='shop_sender',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='shop_sender', to='app_reference.shop'),
        ),
        migrations.AddField(
            model_name='document',
            name='supplier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.supplier'),
        ),
        migrations.AddField(
            model_name='document',
            name='title',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.documenttype'),
        ),
        migrations.AddField(
            model_name='document',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='CashOff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('date', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('sub_total', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.shop')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
