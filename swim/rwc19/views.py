from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import datetime
from django.utils import timezone

import smtplib
from email.mime.text import MIMEText
import os

from .models import Profile, Prediction, Game
from .forms import PickDetailForm, gameForm, PickAdminDetailForm
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
        if g.gamedate < timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone()) + datetime.timedelta(minutes=15):
            p.started = True
            g.started = True
            p.calcScore()
            totPoints = totPoints + float(p.points)
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
            #p.calcScore()
        else:
            p.started = False
        p.save()

    PickFormSet = modelformset_factory(Prediction, form=PickAdminDetailForm, extra=0)

    if request.method == 'POST':
        gForm = gameForm(request.POST, instance = game)
        fPicks = PickFormSet(request.POST, queryset = Prediction.objects.filter(game=game).order_by('score1', 'player__user__username'))
        highPoint = 0
        pTot = 0.0
        pNum = 0
        #print("BP1")
        if gForm.is_valid():
            #print("BP2")
            gForm.save()
            if fPicks.is_valid():
                #print("Valid picks")
                fPicks.save()
            else:
                print(fPicks.errors)
            pList = Prediction.objects.filter(game=game)

            if game.finished:
                #print("Picks pass 1")
                for p in pList:             # first pass works out scores for those with the right result
                    if not p.override:
                        p.calcScore()
                        p.save()
                        if p.result:
                            if p.points > highPoint:
                                highPoint = p.points
                #print("Picks pass 2")
                for p in pList:             # second pass gives worst winning result to losers
                    if not p.result:
                        if not p.override:
                            p.points = game.high_point
                            p.save()

                    if not p.noPicks:     # player defaulted
                        print("pTot is {}".format(pTot))
                        pTot = pTot + p.points
                        pNum = pNum + 1
                    
                #print("Total is {} and number counted is {}".format(pTot, pNum))
                game.high_point = highPoint
                game.average = pTot / pNum
                game.save()
            for p in pList:             # third pass - apply average to defaulters
                if not p.override:
                    if p.noPicks:     # player defaulted
                        #print("Default found ")
                        p.points = game.average
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
        fPicks = PickFormSet(queryset = Prediction.objects.filter(game=game).order_by('score1', 'player__user__username'))
    context = {'gForm': gForm, 'formset': fPicks}
    return render(request, 'rwc19/gameEdit.html', context)

@login_required
def gameView(request, game_id):
    game = get_object_or_404(Game, id = game_id)

    if game.finished:
        picks = Prediction.objects.all().filter(game = game).order_by('points')
    else:
        picks = Prediction.objects.all().filter(game = game).order_by('player__user__username')
    print(len(picks))
    context = {'picks': picks, 'game': game}
    return render(request, 'rwc19/gameView.html', context)

@login_required
def about(request):

    #context = {'picks': picks, 'game': game}
    return render(request, 'rwc19/about.html')


@login_required
def email_results(request, game_id):
    game = get_object_or_404(Game, id = game_id)
    if game.finished:
        print("Sending email, game is finished")
        picks = Prediction.objects.all().filter(game = game).order_by('points')
        winner = picks[0]
        print("Winner is {}".format(winner.player.user.username))

        eSmtp_host = os.getenv("AKLC_SMTP_HOST", "smtp.gmail.com")
        eSmtp_port = os.getenv("AKLC_SMTP_PORT", "465")
        eSmtp_user = os.getenv("AKLC_SMTP_USER", "aklciot@gmail.com")
        eSmtp_password = os.getenv("AKLC_SMTP_PASSWORD", "")

        try:

            print(eSmtp_host)
            print(int(eSmtp_port))
            email_server = smtplib.SMTP_SSL(eSmtp_host, int(eSmtp_port))
            email_server.login(eSmtp_user, eSmtp_password)

            #msg = MIMEText(jPayload['Body'], 'html')
            #msg['From'] = jPayload['From']
            #msg['To'] = jPayload['To']
            #msg['Subject'] = jPayload['Subject']

            #email_server.sendmail(jPayload['From'], jPayload['To'], msg.as_string())
            #email_server.close()
            #print("email sent")
        except Exception as e:
            print(e)
            print("Houston, we have an email error {}".format(e))

    return render(request, 'rwc19/index.html')

@login_required
def pointsView(request, pick_id):
    pick = get_object_or_404(Prediction, id = pick_id)
    nBonus = 0
    win_diff = 0.0
    if pick.game.score1 > pick.game.score2:
        game_res = "{} won".format(pick.game.Team1)
        if pick.result:
            if pick.score1 == pick.game.score1:
                nBonus = -5
            win_diff = abs(pick.game.score1 - pick.score1)/2
    elif pick.game.score1 < pick.game.score2:
        game_res = "{} won".format(pick.game.Team2)
        if pick.result: 
            if pick.score2 == pick.game.score2:
                nBonus = -5
            win_diff = abs(pick.game.score2 - pick.score2)/2
    else:
        if pick.noPicks:
            game_res = "No selection made"
        else:
            game_res = "Draw"

    if pick.score1 > pick.score2:
        player_choice = "{} won".format(pick.game.Team1)
    elif pick.score1 < pick.score2:
        player_choice = "{} won".format(pick.game.Team2)
    else:
        player_choice = "Draw"
    
    gameSpread = abs(pick.game.score1 - pick.game.score2)
    mySpread = abs(pick.score1 - pick.score2)


    context = {'pick': pick, 'game_res': game_res, 'player_choice': player_choice, 
        'nBonus': nBonus, 'win_diff': win_diff, 'spread': abs(gameSpread - mySpread), 
        'gameSpread': gameSpread, 'mySpread': mySpread}
    return render(request, 'rwc19/pointsView.html', context)