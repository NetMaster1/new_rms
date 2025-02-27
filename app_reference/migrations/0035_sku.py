# Generated by Django 3.2.4 on 2025-02-19 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_reference', '0034_product_image_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='SKU',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True)),
                ('emumerator', models.IntegerField(null=True)),
                ('name', models.CharField(max_length=160)),
                ('ozon_id', models.CharField(max_length=50, null=True, unique=True)),
                ('EAN', models.CharField(max_length=50, null=True)),
                ('image_file_1', models.FileField(null=True, upload_to='uploads')),
                ('image_file_2', models.FileField(null=True, upload_to='uploads')),
                ('image_file_3', models.FileField(null=True, upload_to='uploads')),
                ('video_file', models.FileField(null=True, upload_to='uploads')),
            ],
        ),
    ]
