# Generated by Django 4.2.4 on 2023-08-27 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rwc23', '0019_remove_profile_totalpoints_playerround_paid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='FullyPaid',
            field=models.BooleanField(default=False),
        ),
    ]