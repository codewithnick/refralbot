# Generated by Django 2.0.5 on 2018-05-28 22:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_person_pending_input'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='current_stage',
            field=models.IntegerField(default=0),
        ),
    ]
