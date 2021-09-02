# Generated by Django 3.2.4 on 2021-08-20 09:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0010_remove_productcategory_cashback_percent'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app_product', '0058_signoff'),
    ]

    operations = [
        migrations.CreateModel(
            name='Return',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('name', models.CharField(max_length=250)),
                ('imei', models.CharField(max_length=250)),
                ('price', models.IntegerField(default=0)),
                ('quantity', models.IntegerField(default=0)),
                ('sub_total', models.IntegerField(default=0)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.document')),
                ('identifier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.identifier')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.shop')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'return',
                'verbose_name_plural': 'returns',
            },
        ),
    ]