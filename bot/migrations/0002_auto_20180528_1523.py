# Generated by Django 2.0.5 on 2018-05-28 14:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bot',
            old_name='api_keys',
            new_name='api_key',
        ),
    ]
