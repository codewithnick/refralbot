# Generated by Django 2.0.5 on 2018-05-30 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0005_setting_bonus_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='referral',
            name='code',
            field=models.IntegerField(default=123),
        ),
    ]