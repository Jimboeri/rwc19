from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.forms import modelformset_factory
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..forms import PickForm
from ..models import Competition, Game, Membership, PlayerRound, Prediction, Round
from ..permissions import competition_member_required


@login_required(login_url="arena:login")
def dashboard(request):
    memberships = (
        Membership.objects.filter(user=request.user)
        .select_related("competition")
        .order_by("competition__name")
    )
    joinable = Competition.objects.joinable().exclude(
        id__in=memberships.values_list("competition_id", flat=True)
    )
    context = {"memberships": memberships, "joinable": joinable}
    return render(request, "arena/player/dashboard.html", context)


@login_required(login_url="arena:login")
def join(request, slug):
    competition = get_object_or_404(Competition, slug=slug)
    if competition.is_member(request.user):
        return redirect("arena:competition_home", slug=slug)
    if competition.visibility != Competition.Visibility.PUBLIC:
        return HttpResponseForbidden("This competition is invite-only.")

    if request.method == "POST":
        membership, _ = Membership.objects.get_or_create(user=request.user, competition=competition)
        membership.ensure_player_rounds()
        return redirect("arena:competition_home", slug=slug)

    return render(request, "arena/player/join.html", {"competition": competition})


@competition_member_required
def competition_home(request, slug):
    competition = request.competition
    current_round = competition.rounds.filter(status=Round.Status.CURRENT).first()
    membership = Membership.objects.filter(user=request.user, competition=competition).first()

    context = {"competition": competition, "current_round": current_round}

    if current_round:
        leaderboard = (
            PlayerRound.objects.filter(round=current_round)
            .select_related("membership__user")
            .order_by("-total_points", "membership__user__first_name")
        )
        context["leaderboard"] = leaderboard

        if membership:
            player_round, _ = PlayerRound.objects.get_or_create(membership=membership, round=current_round)
            player_round.ensure_predictions()
            player_round.recalc_total()
            context["player_round"] = player_round
            context["predictions"] = player_round.predictions.select_related(
                "game__team1", "game__team2"
            ).order_by("game__gamedate")

    return render(request, "arena/player/competition_home.html", context)


@competition_member_required
def pick_update(request, slug, round_id):
    competition = request.competition
    round_obj = get_object_or_404(Round, id=round_id, competition=competition)
    membership = get_object_or_404(Membership, user=request.user, competition=competition)
    player_round, _ = PlayerRound.objects.get_or_create(membership=membership, round=round_obj)
    player_round.ensure_predictions()

    past_predictions = player_round.predictions.filter(
        game__gamedate__lt=timezone.now()
    ).order_by("game__gamedate")

    PickFormSet = modelformset_factory(Prediction, form=PickForm, extra=0)
    queryset = player_round.predictions.exclude(game__gamedate__lt=timezone.now()).order_by("game__gamedate")

    if request.method == "POST":
        formset = PickFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            for pick in queryset:
                if pick.result == Prediction.Result.DRAW and pick.spread != 0:
                    pick.spread = 0
                    pick.save(update_fields=["spread"])
            return redirect("arena:disp_round", slug=slug, user_id=request.user.id, round_id=round_id)
    else:
        formset = PickFormSet(queryset=queryset)

    context = {
        "competition": competition,
        "round": round_obj,
        "formset": formset,
        "past_predictions": past_predictions,
    }
    return render(request, "arena/player/pick_update.html", context)


@competition_member_required
def player_details(request, slug, user_id):
    competition = request.competition
    player = get_object_or_404(User, id=user_id)
    membership = get_object_or_404(Membership, user=player, competition=competition)
    for player_round in membership.player_rounds.all():
        player_round.recalc_total()

    context = {"competition": competition, "player": player, "membership": membership}
    return render(request, "arena/player/player_details.html", context)


@competition_member_required
def other_rounds(request, slug):
    competition = request.competition
    return render(request, "arena/player/other_rounds.html", {"competition": competition, "rounds": competition.rounds.all()})


@competition_member_required
def disp_round(request, slug, user_id, round_id):
    competition = request.competition
    round_obj = get_object_or_404(Round, id=round_id, competition=competition)
    player = get_object_or_404(User, id=user_id)
    membership = get_object_or_404(Membership, user=player, competition=competition)
    player_round, _ = PlayerRound.objects.get_or_create(membership=membership, round=round_obj)
    player_round.recalc_total()

    leaderboard = (
        PlayerRound.objects.filter(round=round_obj)
        .select_related("membership__user")
        .order_by("-total_points", "membership__user__first_name")
    )
    predictions = player_round.predictions.select_related("game__team1", "game__team2").order_by("game__gamedate")

    context = {
        "competition": competition,
        "round": round_obj,
        "player": player,
        "predictions": predictions,
        "leaderboard": leaderboard,
    }
    return render(request, "arena/player/disp_round.html", context)


@competition_member_required
def game_view(request, slug, game_id):
    competition = request.competition
    game = get_object_or_404(Game, id=game_id, round__competition=competition)

    if game.finished:
        picks = game.predictions.select_related("player_round__membership__user").order_by("-points")
    else:
        picks = game.predictions.select_related("player_round__membership__user").order_by(
            "player_round__membership__user__username"
        )

    context = {"competition": competition, "game": game, "picks": picks}
    return render(request, "arena/player/game_view.html", context)


@competition_member_required
def points_view(request, slug, prediction_id):
    competition = request.competition
    prediction = get_object_or_404(
        Prediction, id=prediction_id, player_round__membership__competition=competition
    )
    return render(request, "arena/player/points_view.html", {"competition": competition, "prediction": prediction})


@competition_member_required
def about(request, slug):
    return render(request, "arena/player/about.html", {"competition": request.competition})
