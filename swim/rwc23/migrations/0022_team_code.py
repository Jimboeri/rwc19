# Generated by Django 4.2.4 on 2023-09-05 07:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rwc23', '0021_remove_game_started_round_entryfee'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='code',
            field=models.CharField(default='   ', max_length=3),
        ),
    ]
