# Generated by Django 5.1.4 on 2025-01-08 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buy', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='buyerprod',
            old_name='issued',
            new_name='is_used',
        ),
        migrations.AddField(
            model_name='buyerprod',
            name='count',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
