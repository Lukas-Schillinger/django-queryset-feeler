# Generated by Django 4.0.6 on 2022-08-06 14:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('test_app', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='topping',
            old_name='vegetation',
            new_name='vegetarian',
        ),
    ]
