# Generated by Django 4.2.3 on 2023-08-08 03:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rwc23', '0014_remove_prediction_playerround'),
    ]

    operations = [
        migrations.AddField(
            model_name='prediction',
            name='playerRound',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='playerRound', to='rwc23.playerround'),
            preserve_default=False,
        ),
    ]
