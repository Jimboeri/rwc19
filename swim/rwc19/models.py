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
    is_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.username

    def totPoints(self):
        pList = Prediction.objects.filter(player=self)
        totScore = 0
        for p in pList:
            if p.game.finished:
                totScore = totScore + p.points
        self.totalPoints = totScore
        return

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
    high_point = models.FloatField(default=0, )

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
    override = models.BooleanField(default=False)
    

    class Meta:
        ordering = ["gamedate"]

    def __str__(self):
        return("Player : {}, Game : {}".format(self.player, self.game))

    def calcScore(self):
        # first determine if the player got the result right
        win_diff = 0.0
        bonus = 0
        self.result = False
        if self.game.finished:
            if self.game.score1 > self.game.score2:
                if self.score1 > self.score2:
                    self.result = True
                    win_diff = abs(self.game.score1 - self.score1)/2
                    if self.game.score1 == self.score1:
                        bonus = -5
            elif self.game.score1 == self.game.score2:
                if self.score1 == self.score2:
                    self.result = True
                    if self.game.score1 == self.score1:
                        bonus = -5
            elif self.game.score1 < self.game.score2:
                if self.score1 < self.score2:
                    self.result = True
                    win_diff = abs(self.game.score2 - self.score2)/2
                    if self.game.score2 == self.score2:
                        bonus = -5
            gameSpread = abs(self.game.score1 - self.game.score2)
            mySpread = abs(self.score1 - self.score2)
            if not self.override:
                if self.result == True:
                    self.points = win_diff + abs(gameSpread - mySpread) + bonus
                else:
                    self.points = 100
        return()
        