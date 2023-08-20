# Generated by Django 4.2.3 on 2023-07-30 01:42

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gamedate', models.DateTimeField(blank=True, null=True)),
                ('score1', models.IntegerField(default=0, help_text='Score of 1st team', validators=[django.core.validators.MinValueValidator(0, 'Negative scores not allowed!')])),
                ('score2', models.IntegerField(default=0, help_text='Score of 2nd team', validators=[django.core.validators.MinValueValidator(0, 'Negative scores not allowed!')])),
                ('started', models.BooleanField(default=False)),
                ('finished', models.BooleanField(default=False)),
                ('high_point', models.FloatField(default=0)),
                ('average', models.DecimalField(decimal_places=1, default=0, max_digits=5)),
            ],
            options={
                'ordering': ['gamedate'],
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teamID', models.CharField(max_length=30)),
                ('descr', models.TextField(blank=True, null=True)),
                ('pool', models.CharField(blank=True, max_length=1, null=True)),
            ],
            options={
                'ordering': ['teamID'],
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phoneNumber', models.CharField(blank=True, max_length=50, null=True)),
                ('totalPoints', models.FloatField(default=0, help_text='Total For and away points')),
                ('is_admin', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='RWC23_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Prediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score1', models.IntegerField(default=0, help_text='Score of 1st team', validators=[django.core.validators.MinValueValidator(0, 'Negative scores not allowed!')])),
                ('score2', models.IntegerField(default=0, help_text='Score of 2nd team', validators=[django.core.validators.MinValueValidator(0, 'Negative scores not allowed!')])),
                ('result', models.BooleanField(default=False)),
                ('points', models.FloatField(default=0, help_text='For and away points')),
                ('textname', models.CharField(blank=True, max_length=50, null=True)),
                ('started', models.BooleanField(default=False)),
                ('gamedate', models.DateTimeField(blank=True, null=True)),
                ('override', models.BooleanField(default=False)),
                ('noPicks', models.BooleanField(default=False)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rwc23.game')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rwc23.profile')),
            ],
            options={
                'ordering': ['gamedate'],
            },
        ),
        migrations.AddField(
            model_name='game',
            name='Team1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rwc23.team'),
        ),
        migrations.AddField(
            model_name='game',
            name='Team2',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team2', to='rwc23.team'),
        ),
    ]