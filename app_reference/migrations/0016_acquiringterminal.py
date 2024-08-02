# Generated by Django 3.2.4 on 2024-02-26 10:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0015_shop_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcquiringTerminal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('TID', models.CharField(max_length=50)),
                ('commission', models.DecimalField(decimal_places=2, default=1, max_digits=3)),
                ('shop', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.shop')),
            ],
            options={
                'ordering': ('TID',),
            },
        ),
    ]
