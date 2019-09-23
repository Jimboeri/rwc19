from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
from django.utils import timezone

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phoneNumber = models.CharField(max_length=50, blank=True, null=True)
    totalPoints = models.FloatField(default=0, help_text="Total For and away points")
    
    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
	instance.profile.save()

class Team(models.Model):
    teamID = models.CharField(max_length=30)
    descr = models.TextField(blank=True, null=True)
    pool = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        ordering = ["teamID"]
    
    def __str__(self):
        return self.teamID

class Game(models.Model):
    Team1 = models.ForeignKey(Team, on_delete=models.CASCADE)
    Team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team2",)
    gamedate = models.DateTimeField(blank=True, null=True)
    score1 = models.IntegerField(default=0, help_text="Score of 1st team")
    score2 = models.IntegerField(default=0, help_text="Score of 2nd team")
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    class Meta:
        ordering = ["gamedate"]

    def __str__(self):
        return("{} v {}".format(self.Team1, self.Team2))

class Prediction(models.Model):
    player = models.ForeignKey(Profile, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    score1 = models.IntegerField(default=0, help_text="Score of 1st team")
    score2 = models.IntegerField(default=0, help_text="Score of 2nd team")
    result = models.BooleanField(default=False)
    points = models.FloatField(default=0, help_text="For and away points")
    textname = models.CharField(max_length=50, blank=True, null=True)
    started = models.BooleanField(default=False)
    gamedate = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["gamedate"]

    def __str__(self):
        return("Player : {}, Game : {}".format(self.player, self.game))