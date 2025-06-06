# Generated by Django 5.2 on 2025-05-22 12:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_payment_date_order_transaction_id'),
        ('products', '0007_remove_product_specification'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='selected_color',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.color'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='selected_size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.size'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='selected_color',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.color'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='selected_color_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='selected_size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.size'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='selected_size_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together={('cart', 'product', 'selected_color', 'selected_size')},
        ),
    ]
