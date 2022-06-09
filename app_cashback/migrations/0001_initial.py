# Generated by Django 3.2.4 on 2022-06-09 05:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_reference', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cashback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.DecimalField(decimal_places=2, default=0, max_digits=3)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='app_reference.productcategory')),
            ],
        ),
    ]
