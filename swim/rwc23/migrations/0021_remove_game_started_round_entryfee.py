# Generated by Django 4.2.4 on 2023-09-03 04:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rwc23', '0020_profile_fullypaid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='started',
        ),
        migrations.AddField(
            model_name='round',
            name='entryFee',
            field=models.FloatField(default=5, help_text='Entry fee for round'),
        ),
    ]
