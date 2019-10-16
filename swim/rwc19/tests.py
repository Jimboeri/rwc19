from django.test import TestCase
from rwc19.models import Profile, Team, Game
from django.contrib.auth.models import User
import datetime
from django.utils import timezone

# Create your tests here.

def create_profiles():
    user_jim = User.objects.create(username = 'jim', email = 'jim@west.net.nz', password = 'jimpassword')
    user_jim.save()
    profile_jim = Profile.objects.get(user__username = 'jim')
    profile_jim.phoneNumber = '021466721'
    profile_jim.save()

    user_john = User.objects.create(username = 'john', email = 'john@west.net.nz', password = 'johnpassword')
    user_john.save()

    user_jane = User.objects.create(username = 'jane', email = 'jane@west.net.nz', password = 'janepassword')
    user_jane.save()    
    #profile_jane, created = Profile.objects.get_or_create(user__username = 'jane')
    #profile_jane.save()

def create_games():
    team_nz = Team(teamID='New Zealand')
    team_nz.save()
    team_au = Team(teamID='Australia')
    team_au.save()
    team_uk = Team(teamID='England')
    team_uk.save()

    # Game 1 is in the past, and NZ wins
    game1 = Game(Team1 = team_nz, Team2 = team_au)
    game1.gamedate = timezone.now() - datetime.timedelta(days=1)
    game1.finished = True
    game1.score1 = 23
    game1.score2 = 7
    game1.save()
    
    game2 = Game(Team1 = team_nz, Team2 = team_uk)
    game2.gamedate = timezone.now() + datetime.timedelta(minutes=10)
    game2.save()
    
    game3 = Game(Team1 = team_uk, Team2 = team_au)
    game3.gamedate = timezone.now() + datetime.timedelta(days=1)
    game3.save()
    

class ProfileModelTests(TestCase):
    def test_positive_total_points(self):
        create_profiles()
        create_games()
        #user_jim = User.objects.get(username='jim')
        profile_jim = Profile.objects.get(user__username = 'jim')
        self.assertIs(profile_jim.totalPoints >= 0, True )