# Generated by Django 5.1.4 on 2024-12-30 07:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('product', '0006_remove_buyerprod_id_shop_remove_buyerprod_product_and_more'),
        ('shops', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuyerProd',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_operation', models.IntegerField()),
                ('issued', models.BooleanField(default=False)),
                ('id_shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.shops')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.productmodel')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
    ]