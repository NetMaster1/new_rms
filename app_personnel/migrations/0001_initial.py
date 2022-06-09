# Generated by Django 4.0.5 on 2022-06-09 07:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Salary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('paid', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BonusAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('smarts', models.IntegerField(default=0)),
                ('phones', models.IntegerField(default=0)),
                ('acces', models.IntegerField(default=0)),
                ('sims', models.IntegerField(default=0)),
                ('modems', models.IntegerField(default=0)),
                ('insurance', models.IntegerField(default=0)),
                ('esset', models.IntegerField(default=0)),
                ('wink', models.IntegerField(default=0)),
                ('service', models.IntegerField(default=0)),
                ('other', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
