# Generated by Django 2.2.6 on 2019-10-16 07:06

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rwc19', '0014_auto_20191014_1157'),
    ]

    operations = [
        migrations.AddField(
            model_name='prediction',
            name='noPicks',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='game',
            name='score1',
            field=models.IntegerField(default=0, help_text='Score of 1st team', validators=[django.core.validators.MinValueValidator(0, 'Negative scores not allowed!')]),
        ),
        migrations.AlterField(
            model_name='game',
            name='score2',
            field=models.IntegerField(default=0, help_text='Score of 2nd team', validators=[django.core.validators.MinValueValidator(0, 'Negative scores not allowed!')]),
        ),
        migrations.AlterField(
            model_name='prediction',
            name='score1',
            field=models.IntegerField(default=0, help_text='Score of 1st team', validators=[django.core.validators.MinValueValidator(0, 'Negative scores not allowed!')]),
        ),
        migrations.AlterField(
            model_name='prediction',
            name='score2',
            field=models.IntegerField(default=0, help_text='Score of 2nd team', validators=[django.core.validators.MinValueValidator(0, 'Negative scores not allowed!')]),
        ),
    ]
