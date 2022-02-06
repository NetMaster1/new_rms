# Generated by Django 3.2.4 on 2022-01-09 18:35

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_product', '0108_alter_document_created'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='remaindercurrent',
            options={'ordering': ('category', 'name')},
        ),
        migrations.AlterModelOptions(
            name='remainderhistory',
            options={'ordering': ('-created',)},
        ),
        migrations.AddField(
            model_name='identifier',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
    ]