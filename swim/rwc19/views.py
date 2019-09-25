from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import datetime
from django.utils import timezone

from .models import Profile, Prediction, Game
from .forms import PickDetailForm, gameForm
from django.forms import inlineformset_factory, modelformset_factory
# Create your views here.

@login_required
def index(request):
    playerList = Profile.objects.order_by('totalPoints')
    context = {'playerList': playerList}
    return render(request, 'rwc19/index.html', context)

@login_required
def makePicks(request):
    games = Game.objects.all()
    totPoints = 0
    for g in games:
        p, created = Prediction.objects.get_or_create(player = request.user.profile, game = g)
        p.textname = "{} v {}".format(g.Team1, g.Team2)
        p.gamedate = g.gamedate
        if g.gamedate < timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone()):
            p.started = True
            g.started = True
            p.calcScore()
            totPoints = totPoints + p.points
        else:
            p.started = False
        p.save()
    usrProfile = Profile.objects.get(user=request.user)
    usrProfile.totalPoints = totPoints
    usrProfile.save()
    PickFormSet = modelformset_factory(Prediction, fields = ('id', 'score1', 'score2'), extra=0)
    #fPicks = PickFormSet(queryset = Prediction.objects.filter(player=usrProfile))

    if request.method == 'POST':
        fPicks = PickFormSet(request.POST, queryset = Prediction.objects.filter(player=usrProfile).exclude(started=True).order_by('gamedate'))
        
        print(len(fPicks))
        if fPicks.is_valid():
            fPicks.save()
            return HttpResponseRedirect(reverse('rwc19:index'))
        else:
            print("invalid response, error = {}".format(fPicks.errors))
            for x in fPicks:
                print(x.errors)
     # if a GET (or any other method) we'll create a blank form
    else:
        fPicks = PickFormSet(queryset = Prediction.objects.filter(player=usrProfile).exclude(started=True).order_by('gamedate'))
        
    context = {'formset': fPicks}
    return render(request, 'rwc19/pickUpdate.html', context)

def playerDets(request, player_id):
    player = get_object_or_404(Profile, user = player_id)
    picks = player.prediction_set.all().order_by('gamedate')

    context = {'player': player, 'picks':picks}
    return render(request, 'rwc19/playerDets.html', context)

def gameEdit(request, game_id):
    game = get_object_or_404(Game, id = game_id)
    print(game)
    if request.method == 'POST':
        gForm = gameForm(request.POST, instance = game)
        
        if gForm.is_valid():
            gForm.save()
            pList = Prediction.objects.filter(game=game)
            for p in pList:
                p.calcScore()
                p.save()

            players = Profile.objects.all()
            for p in players:
                p.totPoints()
                p.save()

            return HttpResponseRedirect(reverse('rwc19:index'))
        else:
            print("invalid response, error = {}".format(fPicks.errors))
            
     # if a GET (or any other method) we'll create a blank form
    else:
        gForm = gameForm(instance = game)
        
    context = {'gForm': gForm, 'test': "Jim"}
    return render(request, 'rwc19/gameEdit.html', context)