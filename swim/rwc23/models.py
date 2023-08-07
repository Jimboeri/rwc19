from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User,
                                related_name="RWC23_user",
                                on_delete=models.CASCADE)
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

class Round(models.Model):
    Name = models.CharField(max_length=50)
    Order = models.IntegerField(default=0, help_text="Order of round")
    start = models.DateTimeField(blank=True, null=True)
    finish = models.DateTimeField(blank=True, null=True)
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    status = models.CharField(max_length=1, default="N")

    class Meta:
        ordering = ["Order"]

    def __str__(self):
        return(f"{self.Name}")    


class Game(models.Model):
    Team1 = models.ForeignKey(Team, on_delete=models.CASCADE)
    Team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team2",)
    #Round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="RWC23")
    Round = models.ForeignKey(Round, on_delete=models.CASCADE)
    gamedate = models.DateTimeField(blank=True, null=True)
    score1 = models.IntegerField(default=0, help_text="Score of 1st team", validators=[MinValueValidator(0,'Negative scores not allowed!')])
    score2 = models.IntegerField(default=0, help_text="Score of 2nd team", validators=[MinValueValidator(0,'Negative scores not allowed!')])
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    high_point = models.FloatField(default=0, )
    average = models.DecimalField(default=0, max_digits=5, decimal_places=1)

    class Meta:
        ordering = ["Round", "gamedate"]

    def __str__(self):
        return(f"{self.Team1} v {self.Team2} ({self.Round.Name})")

class Prediction(models.Model):
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    result = models.IntegerField(default=0,
                                 validators=[MinValueValidator(0,'Negative scores not allowed!'), MaxValueValidator(3,'Invalid result')])
    spread = models.IntegerField(default=0, help_text="Difference between scores", validators=[MinValueValidator(0,'Must have a points difference!')])
    points = models.FloatField(default=0)
    override = models.BooleanField(default=False)
    lastUpdated = models.DateTimeField(auto_now=True)    

    #class Meta:
    #    ordering = ["gamedate"]

    def __str__(self):
        return("Player : {}, Game : {}".format(self.player, self.game))

    def calcScore(self):
        # first determine if the player got the result right

        if self.game.finished:
            game_win_diff = abs(self.game.score1 - self.game.score2)
            if self.result == 1:
                if self.game.score1 > self.game.score2:  # Team 1 wins
                    points = (20 - abs(game_win_diff - self.spread))
                    if points < 5:
                        points = 5
            elif self.result == 3:  #draw
                if self.game.score1 == self.game.score2:
                    points = 25
            elif self.result == 2:  #Team 2 wins
                if self.game.score1 < self.game.score2:
                    points = (20 - abs(game_win_diff - self.spread))
                    if points < 5:
                        points = 5
            else: # Team 2 wins
                points = 0
            self.points = points
            self.save()

        return()

