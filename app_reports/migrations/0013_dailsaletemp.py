# Generated by Django 3.2.4 on 2021-12-29 13:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0017_shop_retail'),
        ('app_reports', '0012_auto_20211209_0142'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailSaleTemp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shop', models.CharField(max_length=50, null=True)),
                ('sum', models.IntegerField(null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.productcategory')),
            ],
        ),
    ]