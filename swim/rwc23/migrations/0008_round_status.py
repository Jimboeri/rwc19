# Generated by Django 4.2.3 on 2023-08-06 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rwc23', '0007_round_finish_round_start'),
    ]

    operations = [
        migrations.AddField(
            model_name='round',
            name='status',
            field=models.CharField(default='N', max_length=1),
        ),
    ]
