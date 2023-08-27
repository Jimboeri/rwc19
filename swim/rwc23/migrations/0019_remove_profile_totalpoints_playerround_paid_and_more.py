# Generated by Django 4.2.4 on 2023-08-26 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rwc23', '0018_alter_playerround_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='totalPoints',
        ),
        migrations.AddField(
            model_name='playerround',
            name='paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='playerround',
            name='paidAmount',
            field=models.FloatField(default=0, help_text='Amount paid'),
        ),
        migrations.AddField(
            model_name='profile',
            name='blocked',
            field=models.BooleanField(default=False),
        ),
    ]
