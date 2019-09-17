from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .models import Profile, Prediction, Game
from .forms import PickDetailForm
from django.forms import inlineformset_factory
# Create your views here.

@login_required
def index(request):
    playerList = Profile.objects.order_by('totalPoints')
    context = {'playerList': playerList}
    return render(request, 'rwc19/index.html', context)

@login_required
def makePicks(request):
    games = Game.objects.all()
    #picks = request.user.profile.prediction_set.all
    picksFormSet = inlineformset_factory(Profile, Prediction, fields=('score1', 'score2', ))
    if request.method == 'POST':
        nf = PickDetailForm(instance=request.user.profile)
        if nf.is_valid():
            for pck in nf:
                pck.save()
            return HttpResponseRedirect(reverse('rwc19:index'))
     # if a GET (or any other method) we'll create a blank form
    else:
        nf = PickDetailForm(instance=request.user.profile)
    context = {'form': nf}
    return render(request, 'rwc19/pickUpdate.html', context)
