# Generated by Django 5.1.4 on 2024-12-30 07:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_alter_productmodel_category_delete_categories'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='buyerprod',
            name='id_shop',
        ),
        migrations.RemoveField(
            model_name='buyerprod',
            name='product',
        ),
        migrations.RemoveField(
            model_name='buyerprod',
            name='user',
        ),
        migrations.DeleteModel(
            name='Shops',
        ),
        migrations.DeleteModel(
            name='BuyerProd',
        ),
        migrations.DeleteModel(
            name='User',
        ),
    ]
