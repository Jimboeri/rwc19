from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .models import Profile
#from .forms import NodeDetailForm, NodeNotifyForm

# Create your views here.
#def index(request):
#    return HttpResponse("Hello, world. You're at the rwc19 index.")
def index(request):
    playerList = Profile.objects.order_by('totalPoints')
    #playerList = nodeList.exclude(status = 'M')
    context = {'playerList': playerList}
    return render(request, 'rwc19/index.html', context)
