# Generated by Django 3.2.4 on 2021-07-02 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_personnel', '0008_remove_bonusaccount_smarts'),
    ]

    operations = [
        migrations.AddField(
            model_name='bonusaccount',
            name='smarts',
            field=models.IntegerField(default=0),
        ),
    ]
