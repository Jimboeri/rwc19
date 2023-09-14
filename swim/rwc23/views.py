from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User

# from django.views import generic
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
from .forms import (
    PickDetailForm,
    gameForm,
    PickAdminDetailForm,
    CustomUserCreationForm,
    adminUserForm,
    adminProfileForm,
    adminPlayerRoundForm,
)
from django.forms import inlineformset_factory, modelformset_factory

# Create your views here.


@login_required
def index(request):  # RWC23 unused
    playerList = Profile.objects.order_by("totalPoints").filter(is_admin="False")
    context = {"playerList": playerList}
    context["rounds"] = Round.objects.all()
    context["games"] = Game.objects.all().order_by("Round", "gamedate")
    return render(request, "rwc23/index.html", context)


@login_required
def currRound(request):  # RWC23 OK
    if request.user.is_superuser:
        rounds = Round.objects.all()
        currRndOrder = 0
        logging.debug(
            f"Reference date {timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())}"
        )
        for rnd in rounds:
            logging.debug(f"Round {rnd.Name}, processing games")

            allFinished = True
            for gm in rnd.game_set.all():
                logging.debug(f"{gm.Team1.teamID} v {gm.Team2.teamID} on {gm.gamedate}")

                # Check if round has finished
                if gm.finished:
                    logging.debug(
                        f"    Game {gm.Team1.teamID} v {gm.Team2.teamID} is finished"
                    )
                else:
                    logging.debug(
                        f"    Game {gm.Team1.teamID} v {gm.Team2.teamID} is not finished"
                    )
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

    currRound = Round.objects.filter(status="C").first()
    currPlayerRound, create = PlayerRound.objects.get_or_create(
        player=request.user, round=currRound
    )
    # ensure all games have a prediction
    for g in currRound.game_set.all():
        Prediction.objects.get_or_create(playerRound=currPlayerRound, game=g)

    currPlayerRound.totPoints()
    cPred = Prediction.objects.filter(playerRound=currPlayerRound).all()

    playerList = PlayerRound.objects.order_by("-totalPoints", "player__first_name").filter(round=currRound)
    context = {"playerList": playerList}
    context["currRound"] = currRound
    context["currPredictions"] = cPred
    return render(request, "rwc23/currRound.html", context)


@login_required
def dispRound(request, player_id, round_id):  # RWC23 OK
    # get the round object
    cRound = Round.objects.filter(id=round_id).first()

    # get the player object
    cPlayer = User.objects.filter(id=player_id).first()

    # ensure a record exists for this player and this round
    playerRound, created = PlayerRound.objects.get_or_create(
        player=cPlayer, round=cRound
    )
    playerRound.totPoints()

    playerList = PlayerRound.objects.order_by("-totalPoints", "player__first_name").filter(round=cRound)
    context = {"playerList": playerList}
    context["currRound"] = cRound
    context["currPredictions"] = Prediction.objects.filter(
        playerRound=playerRound
    ).order_by("game__gamedate")
    return render(request, "rwc23/currRound.html", context)


@login_required
def makePicks(request, rnd_id):  # RWC23 OK
    logging.debug(" ")
    logging.debug(f"Enter makePics, request method = {request.method}")
    # currRound = Round.objects.filter(status='C').first()
    currRound = Round.objects.filter(id=rnd_id).first()
    logging.debug(f"Round = {currRound.Name}")
    currPlayerRound = PlayerRound.objects.filter(
        player=request.user, round=currRound
    ).first()
    logging.debug(f"PlayerRound = {currPlayerRound}")
    pastPreds = (
        Prediction.objects.filter(playerRound=currPlayerRound)
        .filter(game__gamedate__lt = timezone.now() )
        .order_by("game__gamedate")
    )

    PickFormSet = modelformset_factory(Prediction, form=PickDetailForm, extra=0)

    querySet = (
        Prediction.objects.filter(playerRound=currPlayerRound)
        .exclude(game__gamedate__lt = timezone.now())
        .order_by("game__gamedate")
    )

    if request.method == "POST":
        fPicks = PickFormSet(request.POST, queryset=querySet)
        # fPicks = PickFormSet(queryset = querySet)
        logging.debug(fPicks)
        for p in fPicks:
            logging.debug(p)

        logging.debug("----------------")
        # print(len(fPicks))
        if fPicks.is_valid():
            fPicks.save()
            for pick in querySet:
                if pick.result == 3:
                    pick.spread = 0
                    pick.save()
            return HttpResponseRedirect(
                reverse("rwc23:dispRound", args=(request.user.id, rnd_id))
            )
        else:
            print("invalid response, error = {}".format(fPicks.errors))
            for x in fPicks:
                logging.debug(x.errors)

    # if a GET (or any other method) we'll create a blank form
    else:
        fPicks = PickFormSet(queryset=querySet)

    context = {"formset": fPicks, "pastPreds": pastPreds, "currRound": currRound}
    return render(request, "rwc23/pickUpdate.html", context)


@login_required
def playerDets(request, player_id):
    player = get_object_or_404(User, id=player_id)
    for plRnd in PlayerRound.objects.filter(player=player).all():
        plRnd.totPoints()

    context = {"player": player}
    return render(request, "rwc23/playerDets.html", context)


@login_required
def gameEdit(request, game_id):  # RWC23 OK
    """
    Screen to allow game updates - scores etc
    Also to allow admin to override results
    Must only be available to staff
    """
    game = get_object_or_404(Game, id=game_id)

    players = Profile.objects.all().filter(is_admin="False")

    for player in players:
        plRnd, created = PlayerRound.objects.get_or_create(
            player=player.user, round=game.Round
        )
        p, created = Prediction.objects.get_or_create(playerRound=plRnd, game=game)
        p.textname = f"{game.Team1} v {game.Team2}"
        p.gamedate = game.gamedate
        if game.gamedate < timezone.make_aware(
            datetime.datetime.now(), timezone.get_current_timezone()
        ):
            p.started = True
            game.started = True
            # p.calcScore()
        else:
            p.started = False
        p.save()

    PickFormSet = modelformset_factory(Prediction, form=PickAdminDetailForm, extra=0)

    if request.method == "POST":
        gForm = gameForm(request.POST, instance=game)
        fPicks = PickFormSet(
            request.POST,
            queryset=Prediction.objects.filter(game=game).order_by(
                "points", "playerRound__player__username"
            ),
        )

        if gForm.is_valid():
            gForm.save()
            if fPicks.is_valid():
                fPicks.save()
                for pick in Prediction.objects.filter(game=game):
                    if pick.result == 3:
                        pick.spread = 0
                        pick.save()
            else:
                logging.info(fPicks.errors)
            pList = Prediction.objects.filter(game=game)

            if game.finished:
                game.resText()
                for p in pList:  # update scores
                    if not p.override:
                        p.calcScore()
                        p.save()
                        p.playerRound.totPoints()

            return HttpResponseRedirect(reverse("rwc23:gameView", args=(game.id,)))
        else:
            print("invalid response, error = {}".format(fPicks.errors))

    # if a GET (or any other method) we'll create a blank form
    else:
        gForm = gameForm(instance=game)
        fPicks = PickFormSet(
            queryset=Prediction.objects.filter(game=game).order_by(
                "points", "playerRound__player__username"
            )
        )
    context = {"gForm": gForm, "formset": fPicks}
    return render(request, "rwc23/gameEdit.html", context)


@login_required
def gameView(request, game_id):  # checked for rwc23
    """
    View to show the picks for a game, and also results if the game has been played
    """
    game = get_object_or_404(Game, id=game_id)

    if game.finished:
        picks = Prediction.objects.all().filter(game=game).order_by("-points")
    else:
        picks = (
            Prediction.objects.all()
            .filter(game=game)
            .order_by("playerRound__player__username")
        )
    logging.debug(f"Number of picks {len(picks)}")
    context = {"picks": picks, "game": game}
    return render(request, "rwc23/gameView.html", context)


@login_required
def otherRounds(request):  # checked for rwc23
    rounds = Round.objects.all().order_by("Order")
    context = {"rounds": rounds}
    return render(request, "rwc23/otherRounds.html", context)


@login_required
def about(request):  # checked for rwc23
    # context = {'picks': picks, 'game': game}
    return render(request, "rwc23/about.html")


@login_required
def email_results(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if game.finished:
        print("Sending email, game is finished")
        picks = Prediction.objects.all().filter(game=game).order_by("points")
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

        except Exception as e:
            print(e)
            print("Houston, we have an email error {}".format(e))

    return render(request, "rwc23/index.html")


@login_required
def pointsView(request, pick_id):
    prediction = get_object_or_404(Prediction, id=pick_id)

    context = {"prediction": prediction}
    return render(request, "rwc23/pointsView.html", context)


def adminGeneral(request):  # checked for rwc23
    # function processed players and generates playerRound records
    player = User.objects.all()
    rounds = Round.objects.all()

    for p in player:
        for r in rounds:
            pr, created = PlayerRound.objects.get_or_create(player=p, round=r)
            pr.totPoints()
            pr.save()
    return HttpResponseRedirect(reverse("rwc23:index"))


@login_required
def adminUsers(request):  # checked for rwc23
    """
    Show list of all players for management & payment processing
    """
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse("rwc23:index"))

    # function processed players and generates playerRound records
    players = User.objects.all().order_by("first_name")
    for pl in players:
        pl.RWC23_user.makeRounds()

    context = {"players": players}
    return render(request, "rwc23/adminUsers.html", context)


@login_required
def adminUserDetail(request, player_id):  # RWC23 OK
    """
    Page to manage admin details of a user
    """
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse("rwc23:index"))

    player = get_object_or_404(User, id=player_id)
    profile = get_object_or_404(Profile, user=player)

    if request.method == "POST":
        userForm = adminUserForm(request.POST, instance=player)
        profileForm = adminProfileForm(request.POST, instance=profile)

        if userForm.is_valid() and profileForm.is_valid():  # and fRounds.is_valid():
            userForm.save()
            profileForm.save()

            return HttpResponseRedirect(reverse("rwc23:adminUsers"))
        else:
            logging.debug(
                f"Invalid response userForm: {userForm.is_valid()} profileForm: {profileForm.is_valid()}"
            )

    # if a GET (or any other method) we'll create a blank form
    else:
        userForm = adminUserForm(instance=player)
        profileForm = adminProfileForm(instance=profile)
    context = {"player": player, "userForm": userForm, "profileForm": profileForm}
    return render(request, "rwc23/adminPlayerDets.html", context)


@login_required
def adminUserPayment(request, player_id):  # RWC23 OK
    """
    Page to manage payment details of a user
    """
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse("rwc23:index"))

    player = get_object_or_404(User, id=player_id)

    # RoundFormSet = modelformset_factory(PlayerRound, form=adminPlayerRoundForm, extra=0)
    RoundFormSet = modelformset_factory(
        PlayerRound, fields=["paid", "paidAmount"], extra=0
    )
    rndQuerySet = PlayerRound.objects.filter(player=player)

    logging.debug(f"Number of rounds {len(rndQuerySet)}")

    if request.method == "POST":
        fRounds = RoundFormSet(request.POST, queryset=rndQuerySet)

        if fRounds.is_valid():
            fRounds.save()
            lFullPay = True
            for pr in rndQuerySet:
                if pr.paidAmount >= pr.round.entryFee:
                    pr.paid = True
                else:  
                    pr.paid = False
                    lFullPay = False
                pr.save()
            pr.player.RWC23_user.FullyPaid = lFullPay # reset fully paid flag
            pr.player.RWC23_user.save()

            return HttpResponseRedirect(reverse("rwc23:adminUsers"))

        else:
            logging.debug(f"Invalid response userForm: {fRounds.is_valid()}")

    # if a GET (or any other method) we'll create a blank form
    else:
        fRounds = RoundFormSet(queryset=rndQuerySet)
    context = {"player": player, "formset": fRounds}
    return render(request, "rwc23/adminPlayerPayment.html", context)

def adminUserFullPayment(request, player_id):  # RWC23 OK
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse("rwc23:index"))

    player = get_object_or_404(User, id=player_id)
    player.RWC23_user.FullyPaid = True
    player.RWC23_user.save()
    for pr in PlayerRound.objects.filter(player=player).all():
        pr.paid = True
        pr.paidAmount = pr.round.entryFee
        pr.save()
    return HttpResponseRedirect(reverse("rwc23:adminUsers"))

def login(request):  # checked for rwc23
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


def logout(request):  # checked for rwc23
    auth.logout(request)
    return render(request, "accounts/logout.html")


def regEmail(request):  # checked for rwc23
    return render(request, "rwc23/regEmail.html")


def signup(request):  # checked for rwc23
    if request.user.is_authenticated:
        return redirect("rwc23:index")

    if request.method == "POST":
        f = CustomUserCreationForm(request.POST)
        if f.is_valid():
            f.save(request)
            messages.success(
                request, "Account created successfully, please check your email"
            )
            return redirect("rwc23:regEmail")

    else:
        f = CustomUserCreationForm()

    return render(request, "accounts/signup.html", {"form": f})


def activate_account(request, uidb64, token):  # checked for rwc23
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
                plPred, created = Prediction.objects.get_or_create(
                    game=gm, playerRound=plRnd
                )
                plPred.save()

    else:
        messages.add_message(
            request,
            messages.INFO,
            "Link Expired. Contact admin to activate your account.",
        )

    return redirect("rwc23:login")
