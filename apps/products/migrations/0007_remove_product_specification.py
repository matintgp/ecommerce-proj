# Generated by Django 5.2 on 2025-05-16 21:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_product_specification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='specification',
        ),
    ]
