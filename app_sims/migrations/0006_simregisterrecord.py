# Generated by Django 4.1.7 on 2023-12-18 14:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0005_register_av_price'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app_reference', '0014_delete_subdealer'),
        ('app_sims', '0005_rename_rho_type_simreturnrecord_srr_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimRegisterRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enumerator', models.IntegerField(default=0, null=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('name', models.CharField(max_length=50)),
                ('imei', models.CharField(max_length=50)),
                ('document', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_product.document')),
                ('sim_reg_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.documenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]