# Generated by Django 2.2.5 on 2019-09-25 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rwc19', '0009_prediction_gamedate'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='game',
            options={'ordering': ['gamedate']},
        ),
        migrations.AlterModelOptions(
            name='prediction',
            options={'ordering': ['gamedate']},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={'ordering': ['teamID']},
        ),
        migrations.AddField(
            model_name='profile',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
    ]
