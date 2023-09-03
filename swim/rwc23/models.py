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
    is_admin = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    FullyPaid = models.BooleanField(default=False)
    
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

class Round(models.Model):
    Name = models.CharField(max_length=50)
    Order = models.IntegerField(default=0, help_text="Order of round")
    start = models.DateTimeField(blank=True, null=True)
    finish = models.DateTimeField(blank=True, null=True)
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    status = models.CharField(max_length=1, default="N")
    entryFee = models.FloatField(default=5, help_text="Entry fee for round")

    class Meta:
        ordering = ["Order"]

    def __str__(self):
        return(f"{self.Name}")    

class Game(models.Model):
    Team1 = models.ForeignKey(Team, on_delete=models.CASCADE)
    Team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team2",)
    Round = models.ForeignKey(Round, on_delete=models.CASCADE)
    gamedate = models.DateTimeField(blank=True, null=True)
    score1 = models.IntegerField(default=0, help_text="Score of 1st team", validators=[MinValueValidator(0,'Negative scores not allowed!')])
    score2 = models.IntegerField(default=0, help_text="Score of 2nd team", validators=[MinValueValidator(0,'Negative scores not allowed!')])
    finished = models.BooleanField(default=False)
    high_point = models.FloatField(default=0, )
    average = models.DecimalField(default=0, max_digits=5, decimal_places=1)
    resultText = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ["Round", "gamedate"]

    def __str__(self):
        return(f"{self.Team1} v {self.Team2}")
    
    def resText(self):
        if self.finished:
            if self.score1 > self.score2:
                resText = f"{self.Team1.teamID} win by {self.score1 - self.score2}"
            elif self.score1 < self.score2:
                resText = f"{self.Team2.teamID} win by {self.score2 - self.score1}"
            else:
                resText = "Draw"
        else:
            resText = "Game not finished"
        self.resultText = resText
        self.save()
        return resText
    
    def result(self):
        if self.finished:
            if self.score1 > self.score2:
                res = 1
            elif self.score1 < self.score2:
                res = 2
            else:
                res = 3
        else:
            res = 0
        return res
    
    def spread(self):
        if self.finished:
            return abs(self.score1 - self.score2)
        else:
            return 0
        
    def started(self):
        return self.gamedate < timezone.now()

class PlayerRound(models.Model):
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    totalPoints = models.FloatField(default=0, help_text="Total points")
    lastUpdated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    paidAmount = models.FloatField(default=0, help_text="Amount paid")

    class Meta:
        ordering = ["round__Order"]

    def __str__(self):
        return(f"Player : {self.player}, Round : {self.round}")

    def totPoints(self):
        self.makePreds()
        pList = Prediction.objects.filter(playerRound = self).all()
        totScore = 0
        for p in pList:
            p.calcScore()
            if p.game.finished:
                totScore = totScore + p.points
        
        if totScore != self.totalPoints:
            self.totalPoints = totScore
            self.lastUpdated = timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())
            self.save()

        return
    
    def makePreds(self):
        """
        Ensure there are predictions for all games for this player
        """
        gList = Game.objects.filter(Round=self.round).all()
        for g in gList:
            p = Prediction.objects.filter(playerRound=self, game=g).first()
            if p == None:
                p = Prediction(playerRound=self, game=g)
                p.save()

        return

class Prediction(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    playerRound = models.ForeignKey(PlayerRound, on_delete=models.CASCADE)
    result = models.IntegerField(default=0,
                                 validators=[MinValueValidator(0,'Negative scores not allowed!'), MaxValueValidator(3,'Invalid result')])
    spread = models.IntegerField(default=0, help_text="Difference between scores", validators=[MinValueValidator(0,'Must have a points difference!')])
    points = models.FloatField(default=0)
    override = models.BooleanField(default=False)
    lastUpdated = models.DateTimeField(auto_now=True)    

    class Meta:
        ordering = ["game__gamedate"]

    def __str__(self):
        return(f"Player : {self.playerRound.player}, Game : {self.game}")

    def calcScore(self):
        # first determine if the player got the result right
        points = 0
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

        return(self.points)

    def resText(self):
        resText = ""
        if self.result == 1:
            resText = f"{self.game.Team1.teamID} by {self.spread}"
        elif self.result == 2:
            resText = f"{self.game.Team2.teamID} by {self.spread}"
        elif self.result == 3:
            resText = "Draw"
        else:
            resText = "No selection"

        return resText
    
    def spreadDiff(self):
        if self.game.finished:
            return abs(self.spread - abs(self.game.score1 - self.game.score2))
        else:
            return 0