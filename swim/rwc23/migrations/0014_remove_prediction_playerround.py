# Generated by Django 4.2.3 on 2023-08-08 03:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rwc23', '0013_remove_prediction_player_prediction_playerround'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prediction',
            name='playerRound',
        ),
    ]
