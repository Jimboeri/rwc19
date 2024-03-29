from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
#from django.views import generic
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import datetime
from django.utils import timezone
from django.contrib import auth, messages
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

import smtplib
from email.mime.text import MIMEText
import os
import logging

from rwc23.models import Profile, Prediction, Game, Round, PlayerRound, Team
from .forms import PickDetailForm, gameForm, PickAdminDetailForm, CustomUserCreationForm
from django.forms import inlineformset_factory, modelformset_factory
# Create your views here.

@login_required
def index(request):
    playerList = Profile.objects.order_by('totalPoints').filter(is_admin = "False")
    context = {'playerList': playerList}
    context["rounds"] = Round.objects.all()
    context["games"] = Game.objects.all().order_by("Round", "gamedate")
    return render(request, 'rwc23/index.html', context)


@login_required
def dispRound(request, player_id, round_id):         # checked for rwc23
    
    # get the round object
    cRound = Round.objects.filter(id = round_id).first()

    # get the player object
    cPlayer = User.objects.filter(id = player_id).first()
    
    # ensure a record exists for this player and this round
    playerRound, created = PlayerRound.objects.get_or_create(player = cPlayer, round = cRound)
    playerRound.totPoints()

    playerList = PlayerRound.objects.order_by('totalPoints').filter(round = cRound)

    context = {'playerList': playerList}
    context["currRound"] = cRound
    context["currPredictions"] = Prediction.objects.filter(playerRound = playerRound).all()
    
    return render(request, 'rwc23/currRound.html', context)

@login_required
def currRound(request):         # checked for rwc23
    if request.user.is_superuser:
        rounds = Round.objects.all()
        currRndOrder = 0
        logging.debug(f"Reference date {timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())}")
        for rnd in rounds:
            logging.debug(f"Round {rnd.Name}, processing games")

            allFinished = True
            for gm in rnd.game_set.all():
                logging.debug(f"{gm.Team1.teamID} v {gm.Team2.teamID} on {gm.gamedate}")
                
                # Check if round has finished
                if gm.finished:
                    logging.debug(f"    Game {gm.Team1.teamID} v {gm.Team2.teamID} is finished")
                else:
                    logging.debug(f"    Game {gm.Team1.teamID} v {gm.Team2.teamID} is not finished")
                    allFinished = False
            if allFinished:
                logging.debug(f"Round {rnd.Name} is finished")
                rnd.started = True
                rnd.finished = True
                rnd.status = "F"
                rnd.save()
                continue
                
           # OK, all finished rounds marked.
            if currRndOrder == 0:
                rnd.status = "C"
                rnd.started = True
                currRndOrder = rnd.Order
            else:
                rnd.status = "N"
                rnd.started = False
            rnd.finished = False
            rnd.save()

    currRound = Round.objects.filter(status = "C").first()
    currPlayerRound = PlayerRound.objects.filter(player = request.user, round = currRound).first()
    # ensure all games have a prediction
    for g in currRound.game_set.all():
        Prediction.objects.get_or_create(playerRound = currPlayerRound, game = g)

    return HttpResponseRedirect(reverse('rwc23:dispRound', args=(request.user.id, currRound.id,)))

    #dispRound(request, request.user.id, currRound.id)
    #return

    #currPlayerRound.totPoints()
    #cPred = Prediction.objects.filter(playerRound = currPlayerRound).all()

    #playerList = PlayerRound.objects.order_by('totalPoints').filter(round = currRound)
    #context = {'playerList': playerList}
    #context["currRound"] = currRound
    #context["currPredictions"] = cPred
    #return render(request, 'rwc23/currRound.html', context)

@login_required
def makePicks_old(request, rnd_id):         # checked for rwc23

    #currRound = Round.objects.filter(id=rnd_id).first()
    currRound = Round.objects.filter(status='C').first()
    logging.debug(f"Round = {currRound.Name}")
    currPlayerRound = PlayerRound.objects.filter(player = request.user, round = currRound).first()
    logging.debug(f"PlayerRound = {currPlayerRound}")
    pastPreds = []
    futurePreds = []

    # lets ensure that all games have a prediction
    for g in currRound.game_set.all():
        pred, create = Prediction.objects.get_or_create(playerRound = currPlayerRound, game = g)
        pred.save()

    allPreds = Prediction.objects.filter(playerRound = currPlayerRound).order_by('game__gamedate')
    for pr in allPreds:
        pr.calcScore()
        if pr.game.gamedate < timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone()):
            pastPreds.append(pr)
        else:    
            futurePreds.append(pr)
    #logging.debug(f"Number of past predictions = {len(pastPreds)}, number of future predictions = {len(futurePreds)}")

    # update the total points for the player
    #usrProfile = Profile.objects.get(user=request.user)
    #usrProfile.totalPoints = totPoints
    #usrProfile.save()
    
    PickFormSet = modelformset_factory(Prediction, form=PickDetailForm, extra=0)
    
    querySet = Prediction.objects.filter(playerRound = currPlayerRound).exclude(game__finished=True).order_by('game__gamedate')
    logging.debug(f"Predictions selected = {len(querySet)}")

    if request.method == 'POST':
        fPicks = PickFormSet(request.POST, queryset = querySet)
        #fPicks = PickFormSet(queryset = querySet)
        logging.debug(f"request.POST = {request.POST}")
        logging.debug(f"querySet = {querySet}")

        if fPicks.is_valid():
            fPicks.save()
            return HttpResponseRedirect(reverse('rwc23:index'))
        else:
            print("Invalid response, error = {}".format(fPicks.errors))
            for x in fPicks:
                print(x.errors)
     # if a GET (or any other method) we'll create a blank form
    else:
        fPicks = PickFormSet(queryset = querySet)
        logging.debug(f"fPicks = {fPicks}")

    logging.debug(f"Number of past predictions = {len(pastPreds)}")    
    context = {'formset': fPicks, 'pastPreds': pastPreds, 'round': rnd_id, 'futurePreds': futurePreds}
    return render(request, 'rwc23/pickUpdate.html', context)

@login_required
def makePicks(request):         # checked for rwc23

    #currRound = Round.objects.filter(id=rnd_id).first()
    currRound = Round.objects.filter(status='C').first()
    logging.debug(f"Round = {currRound.Name}")
    currPlayerRound = PlayerRound.objects.filter(player = request.user, round = currRound).first()
    logging.debug(f"PlayerRound = {currPlayerRound}")
    pastPreds = []
    futurePreds = []

    # lets ensure that all games have a prediction
    for g in currRound.game_set.all():
        pred, create = Prediction.objects.get_or_create(playerRound = currPlayerRound, game = g)
        pred.save()

    allPreds = Prediction.objects.filter(playerRound = currPlayerRound).order_by('game__gamedate')
    for pr in allPreds:
        pr.calcScore()
        if pr.game.gamedate < timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone()):
            pastPreds.append(pr)
        else:    
            futurePreds.append(pr)
    #logging.debug(f"Number of past predictions = {len(pastPreds)}, number of future predictions = {len(futurePreds)}")

    # update the total points for the player
    #usrProfile = Profile.objects.get(user=request.user)
    #usrProfile.totalPoints = totPoints
    #usrProfile.save()
    
    PickFormSet = modelformset_factory(Prediction, form=PickDetailForm, extra=0)
    
    querySet = Prediction.objects.filter(playerRound = currPlayerRound).exclude(game__finished=True).order_by('game__gamedate')
    logging.debug(f"Predictions selected = {len(querySet)}")

    if request.method == 'POST':
        fPicks = PickFormSet(request.POST, queryset = querySet)
        #fPicks = PickFormSet(queryset = querySet)
        logging.debug(f"request.POST = {request.POST}")
        logging.debug(f"querySet = {querySet}")

        if fPicks.is_valid():
            fPicks.save()
            return HttpResponseRedirect(reverse('rwc23:index'))
        else:
            print("Invalid response, error = {}".format(fPicks.errors))
            for x in fPicks:
                print(x.errors)
     # if a GET (or any other method) we'll create a blank form
    else:
        fPicks = PickFormSet(queryset = querySet)
        logging.debug(f"fPicks = {fPicks}")

    logging.debug(f"Number of past predictions = {len(pastPreds)}")    
    context = {'formset': fPicks, 'pastPreds': pastPreds, 'futurePreds': futurePreds}
    return render(request, 'rwc23/pickUpdate.html', context)

@login_required
def playerDets(request, player_id):
    player = get_object_or_404(User, id = player_id)
    #picks = player.prediction_set.all().order_by('gamedate')

    context = {'player': player}
    return render(request, 'rwc23/playerDets.html', context)

@login_required
def gameEdit(request, game_id):
    game = get_object_or_404(Game, id = game_id)

    players = Profile.objects.all().filter(is_admin = "False")
       
    for player in players:
        plRnd, created = PlayerRound.objects.get_or_create(player = player.user, round = game.Round)
        p, created = Prediction.objects.get_or_create(playerRound = plRnd, game = game)
        p.textname = f"{game.Team1} v {game.Team2}"
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
        fPicks = PickFormSet(request.POST, queryset = Prediction.objects.filter(game=game).order_by('points', 'playerRound__player__username'))
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
                logging.info(fPicks.errors)
            pList = Prediction.objects.filter(game=game)

            if game.finished:
                for p in pList:             # first pass works out scores for those with the right result
                    if not p.override:
                        p.calcScore()
                        p.save()
           
            return HttpResponseRedirect(reverse('rwc23:gameView', args=(game.id,)))
        else:
            print("invalid response, error = {}".format(fPicks.errors))
            
     # if a GET (or any other method) we'll create a blank form
    else:
        gForm = gameForm(instance = game)
        fPicks = PickFormSet(queryset = Prediction.objects.filter(game=game).order_by('points', 'playerRound__player__username'))
    context = {'gForm': gForm, 'formset': fPicks}
    return render(request, 'rwc23/gameEdit.html', context)

@login_required
def gameView(request, game_id):         # checked for rwc23
    """
    View to show the picks for a game, and also results if the game has been played
    """
    game = get_object_or_404(Game, id = game_id)

    if game.finished:
        picks = Prediction.objects.all().filter(game = game).order_by('-points')
    else:
        picks = Prediction.objects.all().filter(game = game).order_by('playerRound__player__username')
    logging.debug(f"Number of picks {len(picks)}")
    context = {'picks': picks, 'game': game}
    return render(request, 'rwc23/gameView.html', context)

@login_required
def otherRounds(request):         # checked for rwc23

    rounds = Round.objects.all()
    context = {'rounds': rounds, 'user': request.user}
    return render(request, 'rwc23/otherRounds.html', context)

@login_required
def about(request):         # checked for rwc23

    #context = {'picks': picks, 'game': game}
    return render(request, 'rwc23/about.html')

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

    return render(request, 'rwc23/index.html')

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
    return render(request, 'rwc23/pointsView.html', context)

def adminGeneral(request):         # checked for rwc23
    # function processed players and generates playerRound records
    player = User.objects.all()
    rounds = Round.objects.all()

    for p in player:
        for r in rounds:
            pr, created = PlayerRound.objects.get_or_create(player = p, round = r)
            pr.totPoints()
            pr.save()
    return HttpResponseRedirect(reverse('rwc23:index'))

def login(request):         # checked for rwc23
    if request.user.is_authenticated:
        return redirect("rwc23:index")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            # correct username and password login the user
            auth.login(request, user)
            return redirect("rwc23:index")

        else:
            messages.error(request, "Error wrong username/password")

    return render(request, "accounts/login.html")

def logout(request):         # checked for rwc23
    auth.logout(request)
    return render(request, "accounts/logout.html")

def signup(request):         # checked for rwc23

    if request.user.is_authenticated:
        return redirect("rwc23:index")

    if request.method == "POST":
        f = CustomUserCreationForm(request.POST)
        if f.is_valid():
            f.save(request)
            messages.success(request, "Account created successfully, please check your email")
            return redirect("rwc23:login")

    else:
        f = CustomUserCreationForm()

    return render(request, "accounts/signup.html", {"form": f})

def activate_account(request, uidb64, token):          # checked for rwc23
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.add_message(request, messages.INFO, "Account activated. Please login.")

        # Create player associated records
        for rnd in Round.objects.all():
            plRnd, created = PlayerRound.objects.get_or_create(player=user, round=rnd)
            plRnd.save()
            for gm in rnd.game_set.all():
                plPred, created = Prediction.objects.get_or_create(game=gm, playerRound=plRnd)
                plPred.save()

    else:
        messages.add_message(
            request,
            messages.INFO,
            "Link Expired. Contact admin to activate your account.",
        )

    return redirect("rwc23:login")
