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
    playerList = Profile.objects.order_by('totalPoints').filter(is_admin = "False")
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
    PickFormSet = modelformset_factory(Prediction, form=PickDetailForm, extra=0)
    #fPicks = PickFormSet(queryset = Prediction.objects.filter(player=usrProfile))

    if request.method == 'POST':
        fPicks = PickFormSet(request.POST, queryset = Prediction.objects.filter(player=usrProfile).exclude(started=True).order_by('gamedate'))
        
        #print(len(fPicks))
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

@login_required
def playerDets(request, player_id):
    player = get_object_or_404(Profile, user = player_id)
    picks = player.prediction_set.all().order_by('gamedate')

    context = {'player': player, 'picks':picks}
    return render(request, 'rwc19/playerDets.html', context)

@login_required
def gameEdit(request, game_id):
    game = get_object_or_404(Game, id = game_id)

    players = Profile.objects.all().filter(is_admin = "False")
    
    for player in players:
        p, created = Prediction.objects.get_or_create(player = player, game = game)
        p.textname = "{} v {}".format(game.Team1, game.Team2)
        p.gamedate = game.gamedate
        if game.gamedate < timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone()):
            p.started = True
            game.started = True
            p.calcScore()
        else:
            p.started = False
        p.save()

    PickFormSet = modelformset_factory(Prediction, form=PickDetailForm, extra=0)

    if request.method == 'POST':
        gForm = gameForm(request.POST, instance = game)
        fPicks = PickFormSet(request.POST, queryset = Prediction.objects.filter(game=game).order_by('player__user__username'))
        highPoint = 0
        print("BP1")
        if gForm.is_valid():
            print("BP2")
            gForm.save()
            if fPicks.is_valid():
                print("Valid picks")
                fPicks.save()
            else:
                print(fPicks.errors)
            pList = Prediction.objects.filter(game=game)
            for p in pList:
                if not p.override:
                    p.calcScore()
                    if p.result:
                        if p.points > highPoint:
                            highPoint = p.points
                p.save()
            game.high_point = highPoint
            game.save()
            for p in pList:
                if not p.result and not p.override:
                    p.points = game.high_point
                    p.save()

            players = Profile.objects.all()
            for player in players:
                player.totPoints()
                player.save()
            
            return HttpResponseRedirect(reverse('rwc19:index'))
        else:
            print("invalid response, error = {}".format(fPicks.errors))
            
     # if a GET (or any other method) we'll create a blank form
    else:
        gForm = gameForm(instance = game)
        fPicks = PickFormSet(queryset = Prediction.objects.filter(game=game).order_by('player__user__username'))
    context = {'gForm': gForm, 'formset': fPicks}
    return render(request, 'rwc19/gameEdit.html', context)

@login_required
def gameView(request, game_id):
    game = get_object_or_404(Game, id = game_id)

    picks = Prediction.objects.all().filter(game = game).order_by('player__user__username')

    print(len(picks))
    context = {'picks': picks, 'game': game}
    return render(request, 'rwc19/gameView.html', context)

@login_required
def about(request):

    #context = {'picks': picks, 'game': game}
    return render(request, 'rwc19/about.html')
