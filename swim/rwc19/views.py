from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.urls import reverse

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
        p.save()
    picks = request.user.profile.prediction_set.all()
    #for p in picks:
    #    print(p.game)
    picksFormSet = modelformset_factory(Prediction, fields=('score1', 'score2', ))
    if request.method == 'POST':
        formset = picksFormSet(request.POST, request.FILES, queryset = picks)
        print(len(formset))
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(reverse('rwc19:index'))
     # if a GET (or any other method) we'll create a blank form
    else:
        formset = picksFormSet(request.POST, queryset = picks)
        print(len(formset))
    context = {'formset': formset}
    return render(request, 'rwc19/pickUpdate.html', context)
