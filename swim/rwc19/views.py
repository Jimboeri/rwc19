from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import datetime
from django.utils import timezone

from .models import Profile, Prediction, Game
from .forms import PickDetailForm
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
    for g in games:
        p, created = Prediction.objects.get_or_create(player = request.user.profile, game = g)
        p.textname = "{} v {}".format(g.Team1, g.Team2)
        p.gamedate = g.gamedate
        if g.gamedate < timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone()):
            p.started = True
            g.started = True
        else:
            p.started = False
        p.save()
    usrProfile = Profile.objects.get(user=request.user)
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
