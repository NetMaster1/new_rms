# Generated by Django 3.2.4 on 2022-06-09 05:36

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_reference', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MonthlyBonus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_name', models.CharField(max_length=50, null=True)),
                ('smarphones', models.IntegerField(null=True)),
                ('accessories', models.IntegerField(null=True)),
                ('sim_cards', models.IntegerField(null=True)),
                ('phones', models.IntegerField(null=True)),
                ('iphone', models.IntegerField(null=True)),
                ('insuranсе', models.IntegerField(null=True)),
                ('wink', models.IntegerField(null=True)),
                ('services', models.IntegerField(null=True)),
                ('credit', models.IntegerField(null=True)),
                ('sub_total', models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReportTempId',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('existance_check', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='SaleReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=50, null=True)),
                ('product', models.CharField(max_length=50, null=True)),
                ('av_sum', models.IntegerField(default=0)),
                ('quantity', models.IntegerField(default=0)),
                ('retail_sum', models.IntegerField(default=0)),
                ('margin', models.IntegerField(default=0)),
                ('report_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reports.reporttempid')),
            ],
        ),
        migrations.CreateModel(
            name='ReportTemp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, null=True)),
                ('imei', models.CharField(max_length=50, null=True)),
                ('quantity_in', models.IntegerField(null=True)),
                ('quantity_out', models.IntegerField(null=True)),
                ('price', models.IntegerField(null=True)),
                ('initial_remainder', models.IntegerField(null=True)),
                ('end_remainder', models.IntegerField(null=True)),
                ('existance_check', models.BooleanField(default=True)),
                ('report_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reports.reporttempid')),
            ],
        ),
        migrations.CreateModel(
            name='ProductHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document', models.CharField(default=0, max_length=50)),
                ('document_id', models.CharField(default=0, max_length=50)),
                ('shop', models.CharField(max_length=50, null=True)),
                ('name', models.CharField(max_length=50)),
                ('imei', models.CharField(max_length=50)),
                ('quantity_in', models.IntegerField(null=True)),
                ('quantity_out', models.IntegerField(null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.productcategory')),
                ('supplier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.supplier')),
            ],
        ),
        migrations.CreateModel(
            name='PayCardReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shop', models.CharField(max_length=50, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('product', models.CharField(max_length=50, null=True)),
                ('pre_remainder', models.IntegerField(default=0)),
                ('incoming_quantity', models.IntegerField(default=0)),
                ('outgoing_quantity', models.IntegerField(default=0)),
                ('current_remainder', models.IntegerField(default=0)),
                ('report_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reports.reporttempid')),
            ],
        ),
        migrations.CreateModel(
            name='DailySaleRep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shop', models.CharField(max_length=50, null=True)),
                ('created', models.CharField(max_length=50, null=True)),
                ('opening_balance', models.IntegerField(null=True)),
                ('smartphones', models.IntegerField(null=True)),
                ('accessories', models.IntegerField(null=True)),
                ('sim_cards', models.IntegerField(null=True)),
                ('pay_cards', models.IntegerField(null=True)),
                ('phones', models.IntegerField(null=True)),
                ('iphone', models.IntegerField(null=True)),
                ('insuranсе', models.IntegerField(null=True)),
                ('wink', models.IntegerField(null=True)),
                ('services', models.IntegerField(null=True)),
                ('gadgets', models.IntegerField(null=True)),
                ('modems', models.IntegerField(null=True)),
                ('net_sales', models.IntegerField(null=True)),
                ('credit', models.IntegerField(null=True)),
                ('card', models.IntegerField(null=True)),
                ('salary', models.IntegerField(null=True)),
                ('expenses', models.IntegerField(null=True)),
                ('cash_move', models.IntegerField(null=True)),
                ('return_sum', models.IntegerField(null=True)),
                ('final_balance', models.IntegerField(null=True)),
                ('report_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reports.reporttempid')),
            ],
        ),
    ]
